#!/usr/bin/env python3
"""
Gesture Management — a Flask operator console for recording and replaying
robot-arm joint trajectories ("gestures") over ROS 2.

Records  sensor_msgs/JointState  from a source topic (default /joint_states)
and replays it as sensor_msgs/JointState to a command topic (default /joint_cmd).

Mode-toggler handshake (native rclpy `set_parameters` service calls, no CLI):
  * RECORD  -> /mode_toggler mode=teach   (backdrivable / teach mode).
  * PLAY    -> /mode_toggler mode=normal  (tracks the trajectory).

Run (after sourcing your ROS 2 workspace):
    pip install flask pandas pyarrow fastparquet
    python3 gesture_management_app.py    # open http://<hostname>:8110
"""

import os
import re
import json
import math
import time
import threading
import collections
import logging
import socket
from datetime import datetime

import pandas as pd
from flask import Flask, request, jsonify, render_template

logging.getLogger("werkzeug").setLevel(logging.WARNING)

# ROS is optional at import time so the UI can be previewed without a sourced
# workspace; record/replay endpoints return a clear error if it's missing.
try:
    import rclpy
    from rclpy.node import Node
    from rclpy.executors import MultiThreadedExecutor
    from rclpy.callback_groups import ReentrantCallbackGroup
    from rclpy.qos import QoSProfile, QoSDurabilityPolicy, QoSReliabilityPolicy, QoSHistoryPolicy
    from rclpy.parameter import Parameter as RclpyParameter
    from sensor_msgs.msg import JointState
    from std_msgs.msg import String
    from std_srvs.srv import Trigger
    from rcl_interfaces.srv import SetParameters, GetParameters
    from rcl_interfaces.msg import Parameter, ParameterValue, ParameterType
    from gesture_management.srv import (
        StartRecording, PlayRecording, PlaySequence,
        SaveSequence, DeleteSequence, ListSequences, GetReplayStatus,
    )
    # Must match mode_toggler's publisher QoS (transient-local) so this
    # subscriber gets the last status even if it connects after mode_toggler
    # already settled into its startup mode, instead of waiting forever.
    MODE_STATUS_QOS = QoSProfile(
        depth=1,
        reliability=QoSReliabilityPolicy.RELIABLE,
        durability=QoSDurabilityPolicy.TRANSIENT_LOCAL,
        history=QoSHistoryPolicy.KEEP_LAST,
    )
    ROS_AVAILABLE = True
except Exception as _e:  # pragma: no cover
    ROS_AVAILABLE = False
    ROS_IMPORT_ERROR = str(_e)
    Node = object

# Motor status (hw_interface) is a separate optional dependency — the UI's
# "Motor Status" panel just stays empty if it isn't available.
try:
    from hw_interface.msg import MotorStatusArray
    MOTOR_STATUS_AVAILABLE = ROS_AVAILABLE
except Exception as _e:
    MOTOR_STATUS_AVAILABLE = False
    MOTOR_STATUS_IMPORT_ERROR = str(_e)

# --------------------------------------------------------------------------- #
# Configuration
#
# The literals below are just the process's startup defaults (needed at
# import time, before rclpy/any node exists, e.g. for RECORDINGS_DIR's
# os.makedirs() call and for Flask preview mode without ROS). Once
# GestureNode starts, its __init__ declares each of these as a real ROS 2
# node parameter (see config/gesture_management_params.yaml) and overwrites
# these same globals with the resolved parameter values, so the rest of this
# file (Flask routes included) always reads the current, ROS-parameter-driven
# value through one plain module global, same as before.
# --------------------------------------------------------------------------- #

def _default_recordings_dir():
    """Persistent recordings folder inside the package *source* tree, so files
    survive `colcon build` and appear in the package's own recordings/ folder.
    Override anytime with: GESTURE_RECORDINGS_DIR=/abs/path python3 gesture_management_app.py"""
    # realpath (not abspath): with --symlink-install the installed executable
    # is a symlink back to this source file; realpath resolves back to the
    # real source tree either way, so the source and installed copies agree
    # on the same persistent recordings/ dir (package root, sibling of
    # launch/ and CMakeLists.txt -- matches CMakeLists.txt's conditional
    # install(DIRECTORY recordings ...) block).
    here = os.path.dirname(os.path.realpath(__file__))
    return os.path.normpath(os.path.join(here, "..", "recordings"))


RECORDINGS_DIR = os.environ.get("GESTURE_RECORDINGS_DIR", _default_recordings_dir())
INDEX_PATH = os.path.join(RECORDINGS_DIR, "gesture_index.json")

DEFAULT_SOURCE_TOPIC = "/joint_states"
DEFAULT_OUTPUT_TOPIC = "/joint_cmd"
GESTURE_STATUS_TOPIC = "/gesture_status_topic"
GESTURE_STATUS_PERIOD_S = 0.25  # matches the UI's own /api/state poll rate
SETTLE_DELAY_S = 0.4  # let a fresh subscriber connect before streaming
MODE_SETTLE_TIMEOUT_S = 6.0  # how long to wait for /mode_toggler/status to confirm

# ---- Pre-replay "move to start" ramp ---------------------------------------- #
# Before streaming a recorded trajectory, each joint is walked to the
# recording's first-frame position at a fixed, slow rate, then the arm's
# actual /joint_states are checked against that target before playback
# starts — instead of jumping straight to frame 0 from wherever the arm
# currently sits.
RAMP_VELOCITY_RAD_S = 0.1      # per-joint speed while moving to the start pose
RAMP_VELOCITY_MIN = 0.01       # safety bounds for the value settable from the UI / ros2 param set
RAMP_VELOCITY_MAX = 1.0
RAMP_RATE_HZ = 50.0
RAMP_POSITION_TOLERANCE_DEG = 11.46   # ~0.2 rad; arrival tolerance, settable from the UI / ros2 param set
RAMP_POSITION_TOLERANCE_DEG_MIN = 0.5
RAMP_POSITION_TOLERANCE_DEG_MAX = 30.0
RAMP_MOVE_TIMEOUT_S = 30.0
RAMP_FEEDBACK_TIMEOUT_S = 3.0   # how long to wait for live /joint_states

os.makedirs(RECORDINGS_DIR, exist_ok=True)

# --------------------------------------------------------------------------- #
# Live event log (shown in the UI's "System Log" panel)
# --------------------------------------------------------------------------- #

_log_lock = threading.Lock()
_log_seq = 0
_log_entries = collections.deque(maxlen=500)


def log_event(message, level="info"):
    global _log_seq
    with _log_lock:
        _log_seq += 1
        _log_entries.append({
            "id": _log_seq,
            "ts": datetime.now().strftime("%H:%M:%S"),
            "level": level,
            "message": message,
        })


def _param_value_for(value):
    """Builds an rcl_interfaces ParameterValue matching a Python value's type."""
    if isinstance(value, bool):
        return ParameterValue(type=ParameterType.PARAMETER_BOOL, bool_value=value)
    if isinstance(value, int):
        return ParameterValue(type=ParameterType.PARAMETER_INTEGER, integer_value=value)
    if isinstance(value, float):
        return ParameterValue(type=ParameterType.PARAMETER_DOUBLE, double_value=value)
    return ParameterValue(type=ParameterType.PARAMETER_STRING, string_value=str(value))


def _call_set_parameters(client, param_name, value, timeout_s=5.0):
    """Calls a node's `~/set_parameters` service directly over rclpy (no CLI/subprocess)."""
    if not client.service_is_ready() and not client.wait_for_service(timeout_sec=min(timeout_s, 2.0)):
        return False, "set_parameters service not available"
    request = SetParameters.Request(parameters=[Parameter(name=param_name, value=_param_value_for(value))])
    future = client.call_async(request)
    deadline = time.monotonic() + timeout_s
    while not future.done():
        if time.monotonic() > deadline:
            return False, "set_parameters call timed out"
        time.sleep(0.01)
    if future.exception() is not None:
        return False, f"set_parameters call raised: {future.exception()}"
    results = future.result().results
    if not results or not results[0].successful:
        reason = results[0].reason if results else "no result returned"
        return False, f"set_parameters rejected: {reason}"
    return True, None


def _call_get_parameters(client, param_name, timeout_s=1.5):
    """Calls a node's `~/get_parameters` service directly over rclpy (no CLI/subprocess)."""
    if not client.service_is_ready() and not client.wait_for_service(timeout_sec=min(timeout_s, 1.0)):
        return None
    future = client.call_async(GetParameters.Request(names=[param_name]))
    deadline = time.monotonic() + timeout_s
    while not future.done():
        if time.monotonic() > deadline:
            return None
        time.sleep(0.01)
    if future.exception() is not None:
        return None
    values = future.result().values
    if not values:
        return None
    pvalue = values[0]
    if pvalue.type == ParameterType.PARAMETER_DOUBLE:
        return pvalue.double_value
    if pvalue.type == ParameterType.PARAMETER_INTEGER:
        return float(pvalue.integer_value)
    return None


def set_toggler_mode(mode_name):
    """Sets `/mode_toggler`'s `mode` parameter via its `set_parameters` service."""
    if node is None:
        msg = "mode_toggler set failed: ROS node not available"
        log_event(msg, level="error")
        return False, msg
    ok, err = _call_set_parameters(node.mode_toggler_set_client, "mode", mode_name)
    if not ok:
        msg = f"mode_toggler set failed: {err}"
        log_event(msg, level="error")
        return False, msg
    msg = f"mode_toggler -> {mode_name}"
    log_event(msg)
    return True, msg


def get_limiter_param(name):
    """Reads a `/joint_command_limiter` parameter via its `get_parameters` service."""
    if node is None:
        return None
    return _call_get_parameters(node.limiter_get_client, name)


def set_limiter_param(name, value):
    """Sets a `/joint_command_limiter` parameter via its `set_parameters` service."""
    if node is None:
        msg = f"joint_command_limiter {name} set failed: ROS node not available"
        log_event(msg, level="error")
        return False, msg
    ok, err = _call_set_parameters(node.limiter_set_client, name, float(value))
    if not ok:
        msg = f"joint_command_limiter {name} set failed: {err}"
        log_event(msg, level="error")
        return False, msg
    msg = f"joint_command_limiter {name} -> {value}"
    log_event(msg)
    return True, msg

# --------------------------------------------------------------------------- #
# Parquet + index helpers (pure, no ROS)
# --------------------------------------------------------------------------- #

def read_parquet_robust(path):
    """Read a parquet file, falling back to fastparquet for legacy files
    written with old pyarrow extension types."""
    try:
        return pd.read_parquet(path)
    except Exception:
        return pd.read_parquet(path, engine="fastparquet")


def compute_metadata(df, name, topic, file_path):
    ts = sorted(df["timestamp_ns"].unique()) if "timestamp_ns" in df else []
    frames = len(ts)
    if frames > 1:
        duration = (ts[-1] - ts[0]) / 1e9
        rate = round((frames - 1) / duration, 1) if duration > 0 else 0.0
    else:
        duration, rate = 0.0, 0.0
    joints = int(df["joint_name"].nunique()) if "joint_name" in df else 0
    return {
        "name": name,
        "file": os.path.basename(file_path),
        "frames": int(frames),
        "rows": int(len(df)),
        "joints": joints,
        "duration_s": round(float(duration), 3),
        "rate_hz": float(rate),
        "topic": topic or "",
        "size_bytes": os.path.getsize(file_path) if os.path.exists(file_path) else 0,
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }


_index_lock = threading.Lock()


def load_index(recordings_dir):
    index_path = os.path.join(recordings_dir, "gesture_index.json")
    if os.path.exists(index_path):
        try:
            with open(index_path) as f:
                idx = json.load(f)
        except Exception:
            idx = {}
    else:
        idx = {}
    idx.setdefault("total_recorded", 0)
    idx.setdefault("recordings", {})
    return idx


def save_index(idx, recordings_dir):
    index_path = os.path.join(recordings_dir, "gesture_index.json")
    tmp = index_path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(idx, f, indent=2)
    os.replace(tmp, index_path)


def reconcile_index(recordings_dir):
    """Sync the JSON index with what's actually on disk so pre-existing
    .parquet files show up and deleted ones disappear."""
    with _index_lock:
        idx = load_index(recordings_dir)
        recs = idx["recordings"]
        
        # Ensure the directory exists before listing its contents
        os.makedirs(recordings_dir, exist_ok=True)

        for fn in sorted(os.listdir(recordings_dir)):
            if not fn.endswith(".parquet"):
                continue
            name = fn[:-len(".parquet")]
            if name in recs:
                continue
            fp = os.path.join(recordings_dir, fn)
            try:
                df = read_parquet_robust(fp)
                recs[name] = compute_metadata(df, name, "", fp)
            except Exception as e:
                recs[name] = {
                    "name": name, "file": fn, "frames": 0, "rows": 0,
                    "joints": 0, "duration_s": 0.0, "rate_hz": 0.0,
                    "topic": "", "size_bytes": os.path.getsize(fp),
                    "created_at": "", "error": str(e),
                }
        for name in list(recs.keys()):
            fn = recs[name].get("file", name + ".parquet")
            if not os.path.exists(os.path.join(recordings_dir, fn)):
                del recs[name]
        save_index(idx, recordings_dir)
        return idx


def index_add(meta, recordings_dir):
    with _index_lock:
        idx = load_index(recordings_dir)
        existed = meta["name"] in idx["recordings"]
        idx["recordings"][meta["name"]] = meta
        if not existed:
            idx["total_recorded"] += 1
        save_index(idx, recordings_dir)


def index_delete(name, recordings_dir):
    with _index_lock:
        idx = load_index(recordings_dir)
        idx["recordings"].pop(name, None)
        save_index(idx, recordings_dir)


def index_rename(old_name, new_name, recordings_dir):
    with _index_lock:
        idx = load_index(recordings_dir)
        recs = idx["recordings"]
        meta = recs.pop(old_name, None)
        if meta is None:
            return
        meta["name"] = new_name
        meta["file"] = f"{new_name}.parquet"
        recs[new_name] = meta
        save_index(idx, recordings_dir)


_VALID_NAME_RE = re.compile(r'^[\w\-. ]+$')


def rename_recording(old_name, new_name, recordings_dir):
    old_name = (old_name or "").strip()
    new_name = (new_name or "").strip()
    if not old_name:
        return False, "No recording specified."
    if not new_name:
        return False, "New name cannot be empty."
    if not _VALID_NAME_RE.match(new_name):
        return False, "Name can only contain letters, numbers, spaces, '-', '_', '.'."
    if new_name == old_name:
        return False, "New name is the same as the current name."
    old_fp = os.path.join(recordings_dir, f"{old_name}.parquet")
    new_fp = os.path.join(recordings_dir, f"{new_name}.parquet")
    if not os.path.exists(old_fp):
        return False, f"Recording '{old_name}' not found."
    if os.path.exists(new_fp):
        return False, f"A recording named '{new_name}' already exists."
    os.rename(old_fp, new_fp)
    index_rename(old_name, new_name, recordings_dir)
    sequences_fix_rename(old_name, new_name, recordings_dir)
    return True, f"Renamed '{old_name}' to '{new_name}'."

# --------------------------------------------------------------------------- #
# Sequence library (named, ordered lists of recordings) — pure, no ROS
# --------------------------------------------------------------------------- #

_sequence_lock = threading.Lock()


def load_sequences(recordings_dir):
    path = os.path.join(recordings_dir, "sequence_index.json")
    if os.path.exists(path):
        try:
            with open(path) as f:
                idx = json.load(f)
        except Exception:
            idx = {}
    else:
        idx = {}
    idx.setdefault("sequences", {})
    return idx


def save_sequences(idx, recordings_dir):
    path = os.path.join(recordings_dir, "sequence_index.json")
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(idx, f, indent=2)
    os.replace(tmp, path)


def sequence_save(name, recording_names, recordings_dir):
    name = (name or "").strip()
    if not name:
        return False, "Give the sequence a name."
    if not _VALID_NAME_RE.match(name):
        return False, "Name can only contain letters, numbers, spaces, '-', '_', '.'."
    recording_names = [n.strip() for n in (recording_names or []) if isinstance(n, str) and n.strip()]
    if not recording_names:
        return False, "Sequence must contain at least one gesture."
    with _sequence_lock:
        idx = load_sequences(recordings_dir)
        idx["sequences"][name] = {
            "name": name,
            "recording_names": recording_names,
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }
        save_sequences(idx, recordings_dir)
    return True, f"Saved sequence '{name}' ({len(recording_names)} gesture(s))."


def sequence_delete(name, recordings_dir):
    with _sequence_lock:
        idx = load_sequences(recordings_dir)
        idx["sequences"].pop(name, None)
        save_sequences(idx, recordings_dir)


def sequences_fix_rename(old_name, new_name, recordings_dir):
    """Keep saved sequences pointing at the right gesture after a rename."""
    with _sequence_lock:
        idx = load_sequences(recordings_dir)
        changed = False
        for seq in idx["sequences"].values():
            names = seq.get("recording_names", [])
            if old_name in names:
                seq["recording_names"] = [new_name if n == old_name else n for n in names]
                changed = True
        if changed:
            save_sequences(idx, recordings_dir)

# --------------------------------------------------------------------------- #
# ROS node
# --------------------------------------------------------------------------- #

class GestureNode(Node):
    def __init__(self):
        super().__init__("gesture_management")
        self._declare_config_parameters()
        self.recordings_dir = RECORDINGS_DIR
        self._gm_lock = threading.Lock()
        self._cb_group = ReentrantCallbackGroup()

        # recording state
        self._gm_sub = None
        self._records = []
        self.rec_status = {
            "active": False, "name": None, "topic": None,
            "frames": 0, "joints": 0, "elapsed_s": 0.0,
        }
        self._rec_start = None

        # replay state
        self._pub_cache = {}  # topic -> publisher (cached, persistent)
        self._replay_cancel = threading.Event()
        self.replay_status = {
            "active": False, "name": None, "output_topic": None,
            "speed": 1.0, "percent": 0.0, "frame": 0, "total": 0,
            "message": "idle", "mode_msg": "",
            "playlist": [], "playlist_index": 0, "playlist_total": 0,
            "repeat_mode": "once", "repeat_count": 1, "loop_count": 0,
            "interval_s": 0.0,
        }

        # live joint-state feedback — always subscribed (independent of
        # recording) so replay can verify the arm's real position before
        # and after moving to a recording's start pose.
        self._live_lock = threading.Lock()
        self._live_joint_states = {}
        self.create_subscription(
            JointState, DEFAULT_SOURCE_TOPIC, self._live_state_cb, 10,
            callback_group=self._cb_group,
        )

        # motor-status watchers — nothing subscribed until the UI adds one
        self._motor_lock = threading.Lock()
        self._motor_subs = {}    # topic -> subscription
        self._motor_latest = {}  # topic -> list of motor dicts

        # mode_toggler's real settled status ("teach" / "transitioning" /
        # "normal") — the only trustworthy signal for whether a requested
        # mode switch has actually landed on the hardware. The "mode"
        # *parameter* flips the instant a switch is requested, well
        # before gains are actually applied, so it can't be used to wait
        # on.
        self._mode_status_lock = threading.Lock()
        self._mode_status = "unknown"
        self.create_subscription(
            String, "/mode_toggler/status", self._mode_status_cb, MODE_STATUS_QOS,
            callback_group=self._cb_group,
        )

        # Publishes the same state the UI polls via /api/state (recording,
        # replay, mode, ramp velocity), as JSON, so other ROS nodes can
        # observe the gesture UI's status without hitting the Flask API.
        self._status_pub = self.create_publisher(String, GESTURE_STATUS_TOPIC, 10)
        self.create_timer(
            GESTURE_STATUS_PERIOD_S, self._publish_status, callback_group=self._cb_group,
        )

        # ROS services — the same record/replay/sequence/status surface the
        # Flask UI calls, so a ROS client can drive (and observe) everything
        # the UI does without going through HTTP at all.
        self.create_service(
            StartRecording, "record", self._srv_record,
            callback_group=self._cb_group,
        )
        self.create_service(
            PlayRecording, "play_recording", self._srv_play_recording,
            callback_group=self._cb_group,
        )
        self.create_service(
            PlaySequence, "play_sequence", self._srv_play_sequence,
            callback_group=self._cb_group,
        )
        self.create_service(
            Trigger, "stop_replay", self._srv_stop_replay,
            callback_group=self._cb_group,
        )
        self.create_service(
            GetReplayStatus, "get_status", self._srv_get_status,
            callback_group=self._cb_group,
        )
        self.create_service(
            SaveSequence, "save_sequence", self._srv_save_sequence,
            callback_group=self._cb_group,
        )
        self.create_service(
            DeleteSequence, "delete_sequence", self._srv_delete_sequence,
            callback_group=self._cb_group,
        )
        self.create_service(
            ListSequences, "list_sequences", self._srv_list_sequences,
            callback_group=self._cb_group,
        )

        # Native rclpy parameter-service clients — used instead of shelling
        # out to the `ros2 param` CLI (which depends on a sourced workspace
        # and a separate `ros2` process/daemon and was failing in practice).
        self.mode_toggler_set_client = self.create_client(
            SetParameters, "/mode_toggler/set_parameters",
            callback_group=self._cb_group,
        )
        self.limiter_set_client = self.create_client(
            SetParameters, "/joint_command_limiter/set_parameters",
            callback_group=self._cb_group,
        )
        self.limiter_get_client = self.create_client(
            GetParameters, "/joint_command_limiter/get_parameters",
            callback_group=self._cb_group,
        )

    # ----- Configuration via ROS 2 parameters ----- #
    # Declares this node's tunables as real ROS 2 parameters (defaults here,
    # overridable from config/gesture_management_params.yaml via the launch
    # file, or live via `ros2 param set`/the web UI), then mirrors the
    # resolved values into the plain module globals the rest of this file
    # (Flask routes included) already reads.

    def _declare_config_parameters(self):
        global RECORDINGS_DIR, INDEX_PATH
        global DEFAULT_SOURCE_TOPIC, DEFAULT_OUTPUT_TOPIC, GESTURE_STATUS_TOPIC
        global GESTURE_STATUS_PERIOD_S, SETTLE_DELAY_S, MODE_SETTLE_TIMEOUT_S
        global RAMP_VELOCITY_RAD_S, RAMP_VELOCITY_MIN, RAMP_VELOCITY_MAX, RAMP_RATE_HZ
        global RAMP_POSITION_TOLERANCE_DEG, RAMP_POSITION_TOLERANCE_DEG_MIN, RAMP_POSITION_TOLERANCE_DEG_MAX
        global RAMP_MOVE_TIMEOUT_S, RAMP_FEEDBACK_TIMEOUT_S

        # recordings_dir is launch/CLI-overridable (`ros2 launch ... recordings_dir:=...`
        # or `--ros-args -p recordings_dir:=...`) same as recorder_server.py/
        # replay_server.py, on top of the GESTURE_RECORDINGS_DIR env var default.
        self.declare_parameter("recordings_dir", RECORDINGS_DIR)
        recordings_dir = self.get_parameter("recordings_dir").value
        if recordings_dir != RECORDINGS_DIR:
            RECORDINGS_DIR = recordings_dir
            INDEX_PATH = os.path.join(RECORDINGS_DIR, "gesture_index.json")
            os.makedirs(RECORDINGS_DIR, exist_ok=True)

        self.declare_parameter("default_source_topic", DEFAULT_SOURCE_TOPIC)
        self.declare_parameter("default_output_topic", DEFAULT_OUTPUT_TOPIC)
        self.declare_parameter("gesture_status_topic", GESTURE_STATUS_TOPIC)
        self.declare_parameter("gesture_status_period_s", GESTURE_STATUS_PERIOD_S)
        self.declare_parameter("settle_delay_s", SETTLE_DELAY_S)
        self.declare_parameter("mode_settle_timeout_s", MODE_SETTLE_TIMEOUT_S)
        self.declare_parameter("ramp_velocity_rad_s", RAMP_VELOCITY_RAD_S)
        self.declare_parameter("ramp_velocity_min", RAMP_VELOCITY_MIN)
        self.declare_parameter("ramp_velocity_max", RAMP_VELOCITY_MAX)
        self.declare_parameter("ramp_rate_hz", RAMP_RATE_HZ)
        self.declare_parameter("ramp_position_tolerance_deg", RAMP_POSITION_TOLERANCE_DEG)
        self.declare_parameter("ramp_position_tolerance_deg_min", RAMP_POSITION_TOLERANCE_DEG_MIN)
        self.declare_parameter("ramp_position_tolerance_deg_max", RAMP_POSITION_TOLERANCE_DEG_MAX)
        self.declare_parameter("ramp_move_timeout_s", RAMP_MOVE_TIMEOUT_S)
        self.declare_parameter("ramp_feedback_timeout_s", RAMP_FEEDBACK_TIMEOUT_S)

        DEFAULT_SOURCE_TOPIC = self.get_parameter("default_source_topic").value
        DEFAULT_OUTPUT_TOPIC = self.get_parameter("default_output_topic").value
        GESTURE_STATUS_TOPIC = self.get_parameter("gesture_status_topic").value
        GESTURE_STATUS_PERIOD_S = self.get_parameter("gesture_status_period_s").value
        SETTLE_DELAY_S = self.get_parameter("settle_delay_s").value
        MODE_SETTLE_TIMEOUT_S = self.get_parameter("mode_settle_timeout_s").value
        RAMP_VELOCITY_RAD_S = self.get_parameter("ramp_velocity_rad_s").value
        RAMP_VELOCITY_MIN = self.get_parameter("ramp_velocity_min").value
        RAMP_VELOCITY_MAX = self.get_parameter("ramp_velocity_max").value
        RAMP_RATE_HZ = self.get_parameter("ramp_rate_hz").value
        RAMP_POSITION_TOLERANCE_DEG = self.get_parameter("ramp_position_tolerance_deg").value
        RAMP_POSITION_TOLERANCE_DEG_MIN = self.get_parameter("ramp_position_tolerance_deg_min").value
        RAMP_POSITION_TOLERANCE_DEG_MAX = self.get_parameter("ramp_position_tolerance_deg_max").value
        RAMP_MOVE_TIMEOUT_S = self.get_parameter("ramp_move_timeout_s").value
        RAMP_FEEDBACK_TIMEOUT_S = self.get_parameter("ramp_feedback_timeout_s").value

        # Only the two UI-facing tunables are validated + live-updatable via
        # `ros2 param set` after startup; the rest are read once above.
        self.add_on_set_parameters_callback(self._on_set_parameters)

    def _on_set_parameters(self, params):
        from rcl_interfaces.msg import SetParametersResult
        global RAMP_VELOCITY_RAD_S, RAMP_POSITION_TOLERANCE_DEG

        for p in params:
            if p.name == "ramp_velocity_rad_s" and not (RAMP_VELOCITY_MIN <= p.value <= RAMP_VELOCITY_MAX):
                return SetParametersResult(
                    successful=False,
                    reason=f"ramp_velocity_rad_s must be between {RAMP_VELOCITY_MIN} and {RAMP_VELOCITY_MAX}")
            if p.name == "ramp_position_tolerance_deg" and not (
                    RAMP_POSITION_TOLERANCE_DEG_MIN <= p.value <= RAMP_POSITION_TOLERANCE_DEG_MAX):
                return SetParametersResult(
                    successful=False,
                    reason=(f"ramp_position_tolerance_deg must be between "
                            f"{RAMP_POSITION_TOLERANCE_DEG_MIN} and {RAMP_POSITION_TOLERANCE_DEG_MAX}"))

        for p in params:
            if p.name == "ramp_velocity_rad_s":
                RAMP_VELOCITY_RAD_S = p.value
                log_event(f"Ramp velocity changed to {p.value} rad/s")
            elif p.name == "ramp_position_tolerance_deg":
                RAMP_POSITION_TOLERANCE_DEG = p.value
                log_event(f"Ramp position tolerance changed to {p.value}°")

        return SetParametersResult(successful=True)

    # ----- ROS service callbacks ----- #
    # Thin adapters: all real logic stays in the plain methods below (also
    # used by the Flask routes), so the UI and ROS clients can never diverge.

    def _srv_record(self, request, response):
        if request.action == "start":
            response.success, response.message = self.start_recording(
                request.topic_name, request.recording_name)
        elif request.action == "stop":
            ok, msg, _meta = self.stop_recording()
            response.success, response.message = ok, msg
        else:
            response.success = False
            response.message = f"Invalid action: {request.action}"
        return response

    def _srv_play_recording(self, request, response):
        response.success, response.message = self.start_replay(
            request.recording_name,
            request.output_topic or DEFAULT_OUTPUT_TOPIC,
            request.replay_speed or 1.0,
            request.repeat_mode or "once",
            request.repeat_count or 1,
            request.interval_s,
        )
        return response

    def _srv_play_sequence(self, request, response):
        names = list(request.recording_names)
        if request.sequence_name:
            idx = load_sequences(self.recordings_dir)
            seq = idx["sequences"].get(request.sequence_name)
            if not seq:
                response.success = False
                response.message = f"Sequence '{request.sequence_name}' not found."
                return response
            names = seq["recording_names"]
        response.success, response.message = self.start_sequence(
            names,
            request.output_topic or DEFAULT_OUTPUT_TOPIC,
            request.replay_speed or 1.0,
            request.repeat_mode or "once",
            request.repeat_count or 1,
            request.interval_s,
        )
        return response

    def _srv_stop_replay(self, request, response):
        response.success, response.message = self.stop_replay()
        return response

    def _srv_get_status(self, request, response):
        response.success = True
        response.status_json = json.dumps(self.get_status_dict())
        return response

    def _srv_save_sequence(self, request, response):
        response.success, response.message = sequence_save(
            request.name, list(request.recording_names), self.recordings_dir)
        return response

    def _srv_delete_sequence(self, request, response):
        sequence_delete(request.name, self.recordings_dir)
        response.success = True
        response.message = f"Deleted sequence '{request.name}'."
        return response

    def _srv_list_sequences(self, request, response):
        idx = load_sequences(self.recordings_dir)
        seqs = sorted(
            idx["sequences"].values(), key=lambda s: s.get("created_at", ""), reverse=True)
        response.success = True
        response.sequences_json = json.dumps(seqs)
        return response

    def get_status_dict(self):
        return {
            "ros": ROS_AVAILABLE,
            "recording": dict(self.rec_status),
            "replay": dict(self.replay_status),
            "ramp_velocity": RAMP_VELOCITY_RAD_S,
            "ramp_tolerance_deg": RAMP_POSITION_TOLERANCE_DEG,
            "mode": self.get_mode_status(),
        }

    def _publish_status(self):
        msg = String()
        msg.data = json.dumps(self.get_status_dict())
        self._status_pub.publish(msg)

    def _live_state_cb(self, msg):
        with self._live_lock:
            for i, jn in enumerate(msg.name):
                if i < len(msg.position):
                    self._live_joint_states[jn] = msg.position[i]

    def _mode_status_cb(self, msg):
        with self._mode_status_lock:
            self._mode_status = msg.data

    def get_mode_status(self):
        with self._mode_status_lock:
            return self._mode_status

    def wait_for_mode(self, target, timeout_s=MODE_SETTLE_TIMEOUT_S):
        """Blocks (bounded) until /mode_toggler/status reports `target`.
        Runs on the caller's thread (Flask request handler or the replay
        worker thread) — never on the ROS executor thread — so this is
        safe to call synchronously."""
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            with self._mode_status_lock:
                current = self._mode_status
            if current == target:
                return True, f"mode_toggler settled at '{target}'"
            time.sleep(0.05)
        with self._mode_status_lock:
            current = self._mode_status
        return False, f"mode_toggler did not settle at '{target}' in {timeout_s:.1f}s (last status: '{current}')"

    # ----- motor status (user-added watchers) ----- #
    def list_motor_topics(self):
        if not MOTOR_STATUS_AVAILABLE:
            return []
        found = []
        for name, types in self.get_topic_names_and_types():
            if "hw_interface/msg/MotorStatusArray" in types:
                found.append(name)
        return sorted(found)

    def watch_motor_topic(self, topic):
        if not MOTOR_STATUS_AVAILABLE:
            return False, "hw_interface motor_status message not available."
        with self._motor_lock:
            if topic in self._motor_subs:
                return True, f"Already watching {topic}."
            sub = self.create_subscription(
                MotorStatusArray, topic,
                lambda msg, topic=topic: self._motor_status_cb(topic, msg),
                10, callback_group=self._cb_group,
            )
            self._motor_subs[topic] = sub
            self._motor_latest[topic] = []
        log_event(f"Watching motor status topic: {topic}")
        return True, f"Watching {topic}."

    def unwatch_motor_topic(self, topic):
        with self._motor_lock:
            sub = self._motor_subs.pop(topic, None)
            self._motor_latest.pop(topic, None)
        if sub is not None:
            self.destroy_subscription(sub)
            log_event(f"Stopped watching motor status topic: {topic}")
        return True

    def _motor_status_cb(self, topic, msg):
        data = [{
            "arm_name": m.arm_name, "id": m.id, "error": m.error,
            "error_name": m.error_name,
            "mos_temp": round(float(m.mos_temp), 1),
            "rotor_temp": round(float(m.rotor_temp), 1),
        } for m in msg.motors]
        with self._motor_lock:
            if topic in self._motor_subs:
                self._motor_latest[topic] = data

    def get_motor_status(self):
        with self._motor_lock:
            return {t: list(v) for t, v in self._motor_latest.items()}

    # ----- recording ----- #
    def start_recording(self, topic_name, recording_name):
        with self._gm_lock:
            if self.rec_status["active"]:
                return False, "Already recording — stop the current capture first."

        # Switch to teach mode so the operator can move the arm by hand,
        # and wait for it to actually land on the hardware *before*
        # capturing starts — otherwise the first frames record the arm
        # still rigidly holding its previous (non-teach) position while
        # the mode switch is still in flight.
        set_ok, mmsg = set_toggler_mode("teach")
        if not set_ok:
            log_event(f"Recording not started: {mmsg}", level="error")
            return False, mmsg
        ok, wmsg = self.wait_for_mode("teach")
        if not ok:
            log_event(f"Recording not started: {wmsg}", level="error")
            return False, f"{mmsg}. {wmsg}"

        with self._gm_lock:
            if self.rec_status["active"]:
                return False, "Already recording — stop the current capture first."
            if self._gm_sub is not None:
                self.destroy_subscription(self._gm_sub)
                self._gm_sub = None
            self._records = []
            self._rec_start = time.time()
            self.rec_status = {
                "active": True, "name": recording_name, "topic": topic_name,
                "frames": 0, "joints": 0, "elapsed_s": 0.0,
            }
            self._gm_sub = self.create_subscription(
                JointState, topic_name, self._joint_cb, 10,
                callback_group=self._cb_group,
            )
        log_event(f"Recording started: '{recording_name}' from {topic_name}. {mmsg}")
        return True, f"Recording '{recording_name}' from {topic_name}. {mmsg}"

    def _joint_cb(self, msg):
        ts = msg.header.stamp.sec * 1_000_000_000 + msg.header.stamp.nanosec
        rows = []
        for i, jn in enumerate(msg.name):
            rows.append({
                "timestamp_ns": ts,
                "source_topic": self.rec_status["topic"],
                "joint_name": jn,
                "position": msg.position[i] if i < len(msg.position) else 0.0,
                "velocity": msg.velocity[i] if i < len(msg.velocity) else 0.0,
            })
        with self._gm_lock:
            self._records.extend(rows)
            self.rec_status["frames"] += 1
            self.rec_status["joints"] = len(msg.name)
            if self._rec_start is not None:
                self.rec_status["elapsed_s"] = round(time.time() - self._rec_start, 1)

    def stop_recording(self):
        with self._gm_lock:
            if not self.rec_status["active"]:
                return False, "Not currently recording.", None
            if self._gm_sub is not None:
                self.destroy_subscription(self._gm_sub)
                self._gm_sub = None
            name = self.rec_status["name"]
            topic = self.rec_status["topic"]
            records = self._records
            self._records = []
            self.rec_status["active"] = False

        if not records:
            log_event(f"Recording '{name}' stopped with no frames captured.", level="warn")
            return False, "No joint messages were received — nothing to save.", None

        file_path = os.path.join(self.recordings_dir, f"{name}.parquet")
        df = pd.DataFrame(records)
        df.to_parquet(file_path, engine="pyarrow", compression="snappy")
        meta = compute_metadata(df, name, topic, file_path)
        index_add(meta, self.recordings_dir)
        log_event(f"Recording saved: '{name}' ({meta['frames']} frames, {meta['duration_s']}s).")
        return True, f"Saved '{name}' ({meta['frames']} frames, {meta['duration_s']}s).", meta

    # ----- replay ----- #
    def _get_publisher(self, topic):
        pub = self._pub_cache.get(topic)
        if pub is None:
            pub = self.create_publisher(JointState, topic, 10)
            self._pub_cache[topic] = pub
        return pub

    def start_replay(self, recording_name, output_topic, speed,
                      repeat_mode="once", repeat_count=1, interval_s=0.0):
        if self.replay_status["active"]:
            return False, "A replay is already running."
        if self.rec_status["active"]:
            return False, "Stop recording before replaying."
        file_path = os.path.join(self.recordings_dir, f"{recording_name}.parquet")
        if not os.path.exists(file_path):
            return False, f"Recording '{recording_name}' not found."
        try:
            df = read_parquet_robust(file_path)
        except Exception as e:
            return False, f"Failed to read recording: {e}"

        if repeat_mode not in ("once", "count", "infinite"):
            repeat_mode = "once"
        repeat_count = max(1, int(repeat_count))
        interval_s = max(0.0, float(interval_s))

        loop_desc = {
            "once": "single playthrough",
            "count": f"{repeat_count}x loop, {interval_s}s interval",
            "infinite": f"looping until stopped, {interval_s}s interval",
        }[repeat_mode]
        log_event(f"Replay requested: '{recording_name}' -> {output_topic} @ {speed}x ({loop_desc})")
        self._replay_cancel.clear()
        t = threading.Thread(
            target=self._replay_worker,
            args=(df, recording_name, output_topic, max(float(speed), 0.01),
                  repeat_mode, repeat_count, interval_s),
            daemon=True,
        )
        t.start()
        return True, f"Replaying '{recording_name}' to {output_topic} ({loop_desc})."

    # ----- pre-replay "move to start" ramp ----- #
    def _wait_for_live_feedback(self, joint_names, timeout_s):
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            if self._replay_cancel.is_set():
                return False
            with self._live_lock:
                if all(jn in self._live_joint_states for jn in joint_names):
                    return True
            time.sleep(0.05)
        return False

    def _ramp_to_start(self, pub, joint_names, target_positions):
        """Walk each joint from its live position to `target_positions` at
        RAMP_VELOCITY_RAD_S, then confirm via live /joint_states that the
        arm actually arrived before the caller starts full-speed playback."""
        if not self._wait_for_live_feedback(joint_names, RAMP_FEEDBACK_TIMEOUT_S):
            return False, "no /joint_states feedback — can't verify arm position"

        with self._live_lock:
            current = {jn: self._live_joint_states[jn] for jn in joint_names}

        dt = 1.0 / RAMP_RATE_HZ
        max_step = RAMP_VELOCITY_RAD_S * dt
        deadline = time.time() + RAMP_MOVE_TIMEOUT_S
        tolerance_rad = math.radians(RAMP_POSITION_TOLERANCE_DEG)

        while True:
            if self._replay_cancel.is_set():
                return False, "cancelled"
            done = True
            velocities = []
            for jn in joint_names:
                err = target_positions[jn] - current[jn]
                if abs(err) > tolerance_rad:
                    done = False
                    step = max(-max_step, min(max_step, err))
                    velocities.append(math.copysign(RAMP_VELOCITY_RAD_S, err))
                else:
                    step = err
                    velocities.append(0.0)
                current[jn] += step
            msg = JointState()
            msg.header.stamp = self.get_clock().now().to_msg()
            msg.name = joint_names
            msg.position = [current[jn] for jn in joint_names]
            msg.velocity = velocities
            pub.publish(msg)
            if done:
                break
            if time.time() > deadline:
                return False, "timed out moving to start position"
            time.sleep(dt)

        # confirm arrival against live feedback, not just our own setpoint
        verify_deadline = time.time() + RAMP_FEEDBACK_TIMEOUT_S
        per_joint_err = {}
        while time.time() < verify_deadline:
            if self._replay_cancel.is_set():
                return False, "cancelled"
            with self._live_lock:
                per_joint_err = {
                    jn: abs(target_positions[jn] - self._live_joint_states.get(jn, float("inf")))
                    for jn in joint_names
                }
            if max(per_joint_err.values()) <= tolerance_rad:
                return True, "arm confirmed at start position"
            time.sleep(0.1)

        max_err = max(per_joint_err.values())
        offenders = ", ".join(
            f"{jn}={err:.3f}" for jn, err in sorted(per_joint_err.items(), key=lambda kv: -kv[1])
            if err > RAMP_POSITION_TOLERANCE_RAD
        )
        log_event(f"Ramp-to-start per-joint errors (rad): {offenders}", level="error")
        return False, f"arm did not reach start position (max error {max_err:.3f} rad, worst joint: {offenders.split(',')[0]})"

    def _play_one(self, pub, output_topic, df, name, speed, loop_tag=""):
        """Ramp from wherever the arm is now to this recording's first
        frame, verify arrival, then stream it at full speed. Returns True
        if playback ran to completion, False if it was aborted/cancelled
        (the caller should stop the outer loop in that case)."""
        grouped = list(df.groupby("timestamp_ns"))
        total = len(grouped)

        self.replay_status.update({
            "name": name, "frame": 0, "total": total, "percent": 0.0,
        })

        if total == 0:
            log_event(f"Replay '{name}': recording has no frames.{loop_tag}", level="warn")
            return True

        first_ts, first_group = grouped[0]
        joint_names = first_group["joint_name"].tolist()
        target_positions = dict(zip(first_group["joint_name"], first_group["position"]))

        self.replay_status["message"] = "moving to start"
        log_event(f"Replay '{name}': moving to start position at {RAMP_VELOCITY_RAD_S} rad/s per joint...{loop_tag}")
        ok, rmsg = self._ramp_to_start(pub, joint_names, target_positions)
        if not ok:
            self.replay_status["message"] = f"aborted: {rmsg}"
            log_event(f"Replay '{name}' aborted before playback: {rmsg}{loop_tag}", level="error")
            return False
        log_event(f"Replay '{name}': {rmsg}{loop_tag}")

        self.replay_status["message"] = "playing"
        log_event(f"Replay playing: '{name}' -> {output_topic} ({total} frames){loop_tag}")

        prev = None
        for i, (ts, group) in enumerate(grouped):
            if self._replay_cancel.is_set():
                self.replay_status["message"] = "stopped"
                log_event(f"Replay stopped: '{name}' at frame {i}/{total}{loop_tag}", level="warn")
                return False
            if prev is not None:
                time.sleep((ts - prev) / 1e9 / speed)
            msg = JointState()
            msg.header.stamp.sec = int(ts // 1_000_000_000)
            msg.header.stamp.nanosec = int(ts % 1_000_000_000)
            msg.name = group["joint_name"].tolist()
            msg.position = group["position"].tolist()
            msg.velocity = group["velocity"].tolist()
            pub.publish(msg)
            prev = ts
            self.replay_status["frame"] = i + 1
            self.replay_status["percent"] = round((i + 1) / total * 100, 1)
        return True

    def _sequence_worker(self, items, output_topic, speed,
                          repeat_mode="once", repeat_count=1, interval_s=0.0):
        """items: ordered list of (recording_name, DataFrame) tuples. A
        single replay is just a one-item sequence."""
        names = [n for n, _ in items]
        total_items = len(items)
        # None means "keep going until cancelled" (infinite loop)
        target_loops = repeat_count if repeat_mode == "count" else (1 if repeat_mode == "once" else None)
        self.replay_status.update({
            "active": True, "name": names[0], "output_topic": output_topic,
            "speed": speed, "percent": 0.0, "frame": 0, "total": 0,
            "message": "switching mode", "mode_msg": "",
            "playlist": names, "playlist_index": 0, "playlist_total": total_items,
            "repeat_mode": repeat_mode, "repeat_count": repeat_count,
            "loop_count": 0, "interval_s": interval_s,
        })
        seq_desc = f"'{names[0]}'" if total_items == 1 else f"[{' -> '.join(names)}]"
        # Switch to normal mode so the arms actually track the trajectory,
        # and wait for it to actually land on hardware before publishing
        # anything — otherwise the first second or so of playback is sent
        # while the arm may still be in teach mode (zero gains): those
        # commands go nowhere until the switch lands, then the arm
        # suddenly snaps into tracking.
        set_ok, mmsg = set_toggler_mode("normal")
        self.replay_status["mode_msg"] = mmsg
        if not set_ok:
            self.replay_status["message"] = f"aborted: {mmsg}"
            self.replay_status["active"] = False
            log_event(f"Replay {seq_desc} aborted before playback: {mmsg}", level="error")
            return
        ok, wmsg = self.wait_for_mode("normal")
        if not ok:
            self.replay_status["message"] = f"aborted: {wmsg}"
            self.replay_status["active"] = False
            log_event(f"Replay {seq_desc} aborted before playback: {wmsg}", level="error")
            return
        self.replay_status["mode_msg"] = f"{mmsg}. {wmsg}"

        pub = self._get_publisher(output_topic)
        self.replay_status["message"] = "connecting"
        time.sleep(SETTLE_DELAY_S)  # let the subscriber discover us

        loop_num = 0
        try:
            while True:
                if self._replay_cancel.is_set():
                    self.replay_status["message"] = "stopped"
                    break
                loop_num += 1
                self.replay_status["loop_count"] = loop_num
                loop_tag = "" if target_loops == 1 else f" [loop {loop_num}{'' if target_loops is None else '/' + str(target_loops)}]"

                aborted = False
                for idx, (name, df) in enumerate(items):
                    if self._replay_cancel.is_set():
                        self.replay_status["message"] = "stopped"
                        aborted = True
                        break
                    self.replay_status["playlist_index"] = idx
                    if not self._play_one(pub, output_topic, df, name, speed, loop_tag):
                        aborted = True
                        break
                    if idx < total_items - 1 and interval_s > 0:
                        self.replay_status["message"] = f"waiting {interval_s}s before next gesture"
                        wait_deadline = time.time() + interval_s
                        while time.time() < wait_deadline:
                            if self._replay_cancel.is_set():
                                aborted = True
                                break
                            time.sleep(min(0.1, max(0.0, wait_deadline - time.time())))
                        if aborted:
                            break
                if aborted:
                    break

                if target_loops is not None and loop_num >= target_loops:
                    self.replay_status["message"] = "completed"
                    log_event(f"Replay completed: {seq_desc} ({loop_num} loop{'s' if loop_num != 1 else ''}).")
                    break

                # more loops to go — wait the interval, watching for cancel
                if interval_s > 0:
                    self.replay_status["message"] = f"waiting {interval_s}s before next loop"
                    wait_deadline = time.time() + interval_s
                    while time.time() < wait_deadline:
                        if self._replay_cancel.is_set():
                            break
                        time.sleep(min(0.1, max(0.0, wait_deadline - time.time())))
                if self._replay_cancel.is_set():
                    self.replay_status["message"] = "stopped"
                    log_event(f"Replay stopped: {seq_desc} after loop {loop_num}", level="warn")
                    break
        except Exception as e:
            self.replay_status["message"] = f"error: {e}"
            log_event(f"Replay error: {seq_desc}: {e}", level="error")
        finally:
            self.replay_status["active"] = False

    def _replay_worker(self, df, name, output_topic, speed,
                        repeat_mode="once", repeat_count=1, interval_s=0.0):
        self._sequence_worker([(name, df)], output_topic, speed,
                               repeat_mode, repeat_count, interval_s)

    def start_sequence(self, recording_names, output_topic, speed,
                        repeat_mode="once", repeat_count=1, interval_s=0.0):
        if self.replay_status["active"]:
            return False, "A replay is already running."
        if self.rec_status["active"]:
            return False, "Stop recording before replaying."
        if not recording_names:
            return False, "No gestures selected."

        items = []
        for name in recording_names:
            file_path = os.path.join(self.recordings_dir, f"{name}.parquet")
            if not os.path.exists(file_path):
                return False, f"Recording '{name}' not found."
            try:
                df = read_parquet_robust(file_path)
            except Exception as e:
                return False, f"Failed to read recording '{name}': {e}"
            items.append((name, df))

        if repeat_mode not in ("once", "count", "infinite"):
            repeat_mode = "once"
        repeat_count = max(1, int(repeat_count))
        interval_s = max(0.0, float(interval_s))

        loop_desc = {
            "once": "single playthrough",
            "count": f"{repeat_count}x loop, {interval_s}s interval",
            "infinite": f"looping until stopped, {interval_s}s interval",
        }[repeat_mode]
        log_event(f"Sequence requested: [{' -> '.join(recording_names)}] -> {output_topic} @ {speed}x ({loop_desc})")
        self._replay_cancel.clear()
        t = threading.Thread(
            target=self._sequence_worker,
            args=(items, output_topic, max(float(speed), 0.01),
                  repeat_mode, repeat_count, interval_s),
            daemon=True,
        )
        t.start()
        return True, f"Playing sequence of {len(items)} gesture(s) to {output_topic} ({loop_desc})."

    def start_home(self, output_topic=None, speed=1.0):
        """Switch to normal mode and ramp every live joint back to 0 rad.
        Reuses _sequence_worker (mode switch + ramp-to-start) with a
        synthetic single-frame "recording" built from whatever joints are
        currently live on DEFAULT_SOURCE_TOPIC, instead of a hardcoded
        joint-name list."""
        if self.replay_status["active"]:
            return False, "A replay is already running."
        if self.rec_status["active"]:
            return False, "Stop recording before moving to home."

        with self._live_lock:
            joint_names = list(self._live_joint_states.keys())
        if not joint_names:
            msg = "No live /joint_states feedback yet — can't move to home safely."
            log_event(f"Go Home aborted: {msg}", level="error")
            return False, msg

        output_topic = (output_topic or DEFAULT_OUTPUT_TOPIC).strip() or DEFAULT_OUTPUT_TOPIC
        home_df = pd.DataFrame({
            "timestamp_ns": [0] * len(joint_names),
            "joint_name": joint_names,
            "position": [0.0] * len(joint_names),
            "velocity": [0.0] * len(joint_names),
        })

        log_event(f"Go Home requested -> {output_topic} ({len(joint_names)} joint(s))")
        self._replay_cancel.clear()
        t = threading.Thread(
            target=self._sequence_worker,
            args=([("home", home_df)], output_topic, max(float(speed), 0.01), "once", 1, 0.0),
            daemon=True,
        )
        t.start()
        return True, f"Switching to normal mode and moving {len(joint_names)} joint(s) to home."

    def stop_replay(self):
        if not self.replay_status["active"]:
            return False, "No replay is running."
        self._replay_cancel.set()
        return True, "Stopping replay."

# --------------------------------------------------------------------------- #
# Flask app
# --------------------------------------------------------------------------- #

app = Flask(__name__)
node = None  # set in main()


def _require_ros():
    if not ROS_AVAILABLE or node is None:
        return jsonify({"success": False,
                        "message": "ROS 2 is not connected. Source your workspace and restart."}), 503
    return None


@app.route("/")
def home():
    return render_template("index.html",
                           source_topic=DEFAULT_SOURCE_TOPIC,
                           output_topic=DEFAULT_OUTPUT_TOPIC,
                           ros_available=ROS_AVAILABLE,
                           recordings_dir=RECORDINGS_DIR,
                           ramp_velocity=RAMP_VELOCITY_RAD_S,
                           ramp_tolerance_deg=RAMP_POSITION_TOLERANCE_DEG)


@app.route("/api/state")
def api_state():
    if node:
        return jsonify(node.get_status_dict())
    rec = {"active": False, "frames": 0, "joints": 0, "elapsed_s": 0.0, "name": None, "topic": None}
    rep = {"active": False, "percent": 0.0, "frame": 0, "total": 0, "message": "no-ros", "name": None, "mode_msg": ""}
    return jsonify({"ros": ROS_AVAILABLE, "recording": rec, "replay": rep, "ramp_velocity": RAMP_VELOCITY_RAD_S,
                    "ramp_tolerance_deg": RAMP_POSITION_TOLERANCE_DEG, "mode": "unknown"})


@app.route("/api/mode/set", methods=["POST"])
def api_mode_set():
    err = _require_ros()
    if err:
        return err
    data = request.get_json(force=True)
    mode = data.get("mode")
    if mode not in ("teach", "normal"):
        return jsonify({"success": False, "message": "mode must be 'teach' or 'normal'"}), 400
    if node.rec_status["active"]:
        return jsonify({"success": False, "message": "Cannot change mode while recording."}), 409
    if node.replay_status["active"]:
        return jsonify({"success": False, "message": "Cannot change mode while replaying."}), 409
    set_ok, mmsg = set_toggler_mode(mode)
    if not set_ok:
        log_event(f"Manual mode switch failed: {mmsg}", level="error")
        return jsonify({"success": False, "message": mmsg})
    ok, wmsg = node.wait_for_mode(mode)
    msg = f"{mmsg}. {wmsg}"
    log_event(msg, level="info" if ok else "error")
    return jsonify({"success": ok, "message": msg})


@app.route("/api/set_ramp_velocity", methods=["POST"])
def set_ramp_velocity():
    global RAMP_VELOCITY_RAD_S
    data = request.get_json(force=True)
    try:
        v = float(data.get("velocity"))
    except (TypeError, ValueError):
        return jsonify({"success": False, "message": "Invalid velocity value."}), 400
    if not (RAMP_VELOCITY_MIN <= v <= RAMP_VELOCITY_MAX):
        return jsonify({"success": False,
                        "message": f"Velocity must be between {RAMP_VELOCITY_MIN} and {RAMP_VELOCITY_MAX} rad/s."}), 400
    if node is not None:
        # Goes through the node's ros2 parameter (declared in
        # _declare_config_parameters), so `ros2 param get` and the web UI
        # always agree, and the on-set-parameters callback is what actually
        # applies the new value to RAMP_VELOCITY_RAD_S.
        result = node.set_parameters([RclpyParameter("ramp_velocity_rad_s", value=v)])[0]
        if not result.successful:
            return jsonify({"success": False, "message": result.reason}), 400
    else:
        RAMP_VELOCITY_RAD_S = v
        log_event(f"Ramp velocity changed to {v} rad/s")
    return jsonify({"success": True, "velocity": RAMP_VELOCITY_RAD_S})


@app.route("/api/set_ramp_tolerance", methods=["POST"])
def set_ramp_tolerance():
    global RAMP_POSITION_TOLERANCE_DEG
    data = request.get_json(force=True)
    try:
        v = float(data.get("tolerance_deg"))
    except (TypeError, ValueError):
        return jsonify({"success": False, "message": "Invalid tolerance value."}), 400
    if not (RAMP_POSITION_TOLERANCE_DEG_MIN <= v <= RAMP_POSITION_TOLERANCE_DEG_MAX):
        return jsonify({"success": False,
                        "message": (f"Tolerance must be between {RAMP_POSITION_TOLERANCE_DEG_MIN} and "
                                    f"{RAMP_POSITION_TOLERANCE_DEG_MAX} degrees.")}), 400
    if node is not None:
        result = node.set_parameters([RclpyParameter("ramp_position_tolerance_deg", value=v)])[0]
        if not result.successful:
            return jsonify({"success": False, "message": result.reason}), 400
    else:
        RAMP_POSITION_TOLERANCE_DEG = v
        log_event(f"Ramp position tolerance changed to {v}°")
    return jsonify({"success": True, "tolerance_deg": RAMP_POSITION_TOLERANCE_DEG})


@app.route("/api/speed_limits", methods=["GET", "POST"])
def api_speed_limits():
    """GET current max_velocity/max_acceleration on joint_command_limiter,
    or POST {max_velocity, max_acceleration} to update either/both."""
    if request.method == "GET":
        return jsonify({
            "max_velocity": get_limiter_param("max_velocity"),
            "max_acceleration": get_limiter_param("max_acceleration"),
        })

    data = request.get_json(force=True)
    results = {}

    if "max_velocity" in data:
        try:
            v = float(data["max_velocity"])
            ok, msg = set_limiter_param("max_velocity", v)
        except (TypeError, ValueError):
            ok, msg = False, "Invalid max_velocity value."
        results["max_velocity"] = {"success": ok, "message": msg}

    if "max_acceleration" in data:
        try:
            v = float(data["max_acceleration"])
            ok, msg = set_limiter_param("max_acceleration", v)
        except (TypeError, ValueError):
            ok, msg = False, "Invalid max_acceleration value."
        results["max_acceleration"] = {"success": ok, "message": msg}

    return jsonify(results)


@app.route("/api/logs")
def api_logs():
    since = request.args.get("since", 0, type=int)
    with _log_lock:
        entries = [e for e in _log_entries if e["id"] > since]
    return jsonify({"logs": entries})


@app.route("/api/motor_topics")
def api_motor_topics():
    topics = node.list_motor_topics() if node else []
    return jsonify({"topics": topics, "available": MOTOR_STATUS_AVAILABLE})


@app.route("/api/motor_watch", methods=["POST"])
def api_motor_watch():
    err = _require_ros()
    if err:
        return err
    d = request.get_json(force=True)
    topic = (d.get("topic") or "").strip()
    if not topic:
        return jsonify({"success": False, "message": "No topic given."}), 400
    ok, msg = node.watch_motor_topic(topic)
    return jsonify({"success": ok, "message": msg}), (200 if ok else 409)


@app.route("/api/motor_unwatch", methods=["POST"])
def api_motor_unwatch():
    err = _require_ros()
    if err:
        return err
    d = request.get_json(force=True)
    topic = (d.get("topic") or "").strip()
    node.unwatch_motor_topic(topic)
    return jsonify({"success": True})


@app.route("/api/motor_status")
def api_motor_status():
    status = node.get_motor_status() if node else {}
    return jsonify({"status": status})


@app.route("/api/recordings")
def api_recordings():
    idx = reconcile_index(RECORDINGS_DIR) # Updated to pass recordings_dir
    recs = sorted(idx["recordings"].values(),
                  key=lambda r: r.get("created_at", ""), reverse=True)
    return jsonify({"count": len(recs), "total_recorded": idx["total_recorded"], "recordings": recs})


@app.route("/api/record/start", methods=["POST"])
def api_record_start():
    err = _require_ros()
    if err:
        return err
    d = request.get_json(force=True)
    name = (d.get("recording_name") or "").strip()
    topic = (d.get("topic_name") or DEFAULT_SOURCE_TOPIC).strip()
    if not name:
        return jsonify({"success": False, "message": "Give the gesture a name."}), 400
    ok, msg = node.start_recording(topic, name)
    return jsonify({"success": ok, "message": msg}), (200 if ok else 409)


@app.route("/api/record/stop", methods=["POST"])
def api_record_stop():
    err = _require_ros()
    if err:
        return err
    ok, msg, meta = node.stop_recording()
    return jsonify({"success": ok, "message": msg, "meta": meta}), (200 if ok else 409) # index_add is called inside stop_recording now


@app.route("/api/replay", methods=["POST"])
def api_replay():
    err = _require_ros()
    if err:
        return err
    d = request.get_json(force=True)
    name = (d.get("recording_name") or "").strip()
    topic = (d.get("output_topic") or DEFAULT_OUTPUT_TOPIC).strip()
    try:
        speed = float(d.get("replay_speed", 1.0))
    except (TypeError, ValueError):
        speed = 1.0
    repeat_mode = (d.get("repeat_mode") or "once").strip()
    try:
        repeat_count = int(d.get("repeat_count", 1))
    except (TypeError, ValueError):
        repeat_count = 1
    try:
        interval_s = float(d.get("interval_s", 0.0))
    except (TypeError, ValueError):
        interval_s = 0.0
    ok, msg = node.start_replay(name, topic, speed, repeat_mode, repeat_count, interval_s)
    return jsonify({"success": ok, "message": msg}), (200 if ok else 409)


@app.route("/api/replay_sequence", methods=["POST"])
def api_replay_sequence():
    err = _require_ros()
    if err:
        return err
    d = request.get_json(force=True)
    names = [n.strip() for n in (d.get("recording_names") or []) if isinstance(n, str) and n.strip()]
    topic = (d.get("output_topic") or DEFAULT_OUTPUT_TOPIC).strip()
    try:
        speed = float(d.get("replay_speed", 1.0))
    except (TypeError, ValueError):
        speed = 1.0
    repeat_mode = (d.get("repeat_mode") or "once").strip()
    try:
        repeat_count = int(d.get("repeat_count", 1))
    except (TypeError, ValueError):
        repeat_count = 1
    try:
        interval_s = float(d.get("interval_s", 0.0))
    except (TypeError, ValueError):
        interval_s = 0.0
    ok, msg = node.start_sequence(names, topic, speed, repeat_mode, repeat_count, interval_s)
    return jsonify({"success": ok, "message": msg}), (200 if ok else 409)


@app.route("/api/sequences")
def api_sequences():
    folder = node.recordings_dir if node else RECORDINGS_DIR
    idx = load_sequences(folder)
    seqs = sorted(idx["sequences"].values(), key=lambda s: s.get("created_at", ""), reverse=True)
    return jsonify({"count": len(seqs), "sequences": seqs})


@app.route("/api/sequences/save", methods=["POST"])
def api_sequences_save():
    d = request.get_json(force=True)
    name = (d.get("name") or "").strip()
    names = d.get("recording_names") or []
    folder = node.recordings_dir if node else RECORDINGS_DIR
    ok, msg = sequence_save(name, names, folder)
    if ok:
        log_event(msg)
    return jsonify({"success": ok, "message": msg}), (200 if ok else 400)


@app.route("/api/sequences/delete", methods=["POST"])
def api_sequences_delete():
    d = request.get_json(force=True)
    name = (d.get("name") or "").strip()
    folder = node.recordings_dir if node else RECORDINGS_DIR
    sequence_delete(name, folder)
    log_event(f"Deleted sequence '{name}'.")
    return jsonify({"success": True, "message": f"Deleted sequence '{name}'."})


@app.route("/api/sequences/play", methods=["POST"])
def api_sequences_play():
    err = _require_ros()
    if err:
        return err
    d = request.get_json(force=True)
    name = (d.get("name") or "").strip()
    folder = node.recordings_dir if node else RECORDINGS_DIR
    idx = load_sequences(folder)
    seq = idx["sequences"].get(name)
    if not seq:
        return jsonify({"success": False, "message": f"Sequence '{name}' not found."}), 404
    topic = (d.get("output_topic") or DEFAULT_OUTPUT_TOPIC).strip()
    try:
        speed = float(d.get("replay_speed", 1.0))
    except (TypeError, ValueError):
        speed = 1.0
    repeat_mode = (d.get("repeat_mode") or "once").strip()
    try:
        repeat_count = int(d.get("repeat_count", 1))
    except (TypeError, ValueError):
        repeat_count = 1
    try:
        interval_s = float(d.get("interval_s", 0.0))
    except (TypeError, ValueError):
        interval_s = 0.0
    ok, msg = node.start_sequence(seq["recording_names"], topic, speed, repeat_mode, repeat_count, interval_s)
    return jsonify({"success": ok, "message": msg}), (200 if ok else 409)


@app.route("/api/home", methods=["POST"])
def api_home():
    err = _require_ros()
    if err:
        return err
    d = request.get_json(silent=True) or {}
    topic = (d.get("output_topic") or DEFAULT_OUTPUT_TOPIC).strip()
    try:
        speed = float(d.get("replay_speed", 1.0))
    except (TypeError, ValueError):
        speed = 1.0
    ok, msg = node.start_home(topic, speed)
    return jsonify({"success": ok, "message": msg}), (200 if ok else 409)


@app.route("/api/replay/stop", methods=["POST"])
def api_replay_stop():
    err = _require_ros()
    if err:
        return err
    ok, msg = node.stop_replay()
    return jsonify({"success": ok, "message": msg})


@app.route("/api/recordings/delete", methods=["POST"])
def api_delete():
    d = request.get_json(force=True)
    name = (d.get("recording_name") or "").strip()
    
    folder = node.recordings_dir if node else RECORDINGS_DIR # Updated as per request
    fp = os.path.join(folder, f"{name}.parquet") # Updated as per request
    if os.path.exists(fp):
        os.remove(fp)
    index_delete(name, folder) # Updated to pass recordings_dir
    log_event(f"Deleted recording '{name}'.")
    return jsonify({"success": True, "message": f"Deleted '{name}'."})

@app.route("/api/recordings/rename", methods=["POST"])
def api_rename():
    d = request.get_json(force=True)
    old_name = (d.get("old_name") or "").strip()
    new_name = (d.get("new_name") or "").strip()
    folder = node.recordings_dir if node else RECORDINGS_DIR

    if node and node.rec_status["active"] and node.rec_status["name"] == old_name:
        return jsonify({"success": False, "message": "Cannot rename a recording that is currently being captured."}), 409
    if node and node.replay_status["active"] and old_name in node.replay_status.get("playlist", []):
        return jsonify({"success": False, "message": "Cannot rename a recording that is currently playing."}), 409

    ok, msg = rename_recording(old_name, new_name, folder)
    if ok:
        log_event(msg)
    return jsonify({"success": ok, "message": msg}), (200 if ok else 409)


@app.route("/api/list_dirs")
def api_list_dirs():
    path = request.args.get("path") or RECORDINGS_DIR
    path = os.path.abspath(os.path.expanduser(path))
    if not os.path.isdir(path):
        path = os.path.expanduser("~")
    try:
        dirs = sorted(
            d for d in os.listdir(path)
            if not d.startswith(".") and os.path.isdir(os.path.join(path, d))
        )
    except Exception:
        dirs = []
    parent = os.path.dirname(path)
    return jsonify({
        "path": path,
        "parent": parent if parent != path else None,
        "dirs": dirs,
    })


@app.route("/api/set_recordings_dir", methods=["POST"])
def set_recordings_dir():
    global RECORDINGS_DIR
    global INDEX_PATH
    data = request.get_json(force=True)
    folder = data.get("folder", "").strip()
    if not folder:
        return jsonify({
            "success": False,
            "message": "Invalid folder"
        })
    RECORDINGS_DIR = folder
    INDEX_PATH = os.path.join(RECORDINGS_DIR, "gesture_index.json")
    os.makedirs(folder, exist_ok=True)
    if node is not None:
        node.recordings_dir = folder
    reconcile_index(folder)
    log_event(f"Recordings folder changed to {folder}")
    return jsonify({
        "success": True,
        "folder": RECORDINGS_DIR
    })
# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #

def main():
    global node
    reconcile_index(RECORDINGS_DIR) # Updated to pass recordings_dir
    if ROS_AVAILABLE:
        rclpy.init()
        node = GestureNode()
        executor = MultiThreadedExecutor()
        executor.add_node(node)
        threading.Thread(target=executor.spin, daemon=True).start()
        node.get_logger().info(
            f"Gesture Management UI on http://{socket.gethostname().lower()}.local:8110 | recordings: {RECORDINGS_DIR}")
        log_event(f"Gesture Management UI started | recordings: {RECORDINGS_DIR}")
    else:
        print(f"[WARN] ROS 2 not available ({ROS_IMPORT_ERROR}). UI runs in preview mode.")
        print(f"[INFO] http://{socket.gethostname().lower()}.local:8110   recordings dir: {RECORDINGS_DIR}")
        log_event(f"ROS 2 not available ({ROS_IMPORT_ERROR}). UI running in preview mode.", level="warn")

    try:
        app.run(host="0.0.0.0", port=8110, threaded=True)
    finally:
        if ROS_AVAILABLE and node is not None:
            try:
                node.destroy_node()
            except Exception:
                pass
            if rclpy.ok():
                try:
                    rclpy.shutdown()
                except Exception:
                    pass


if __name__ == "__main__":
    main()
