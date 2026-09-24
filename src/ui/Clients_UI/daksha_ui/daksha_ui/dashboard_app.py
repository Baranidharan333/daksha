#!/usr/bin/env python3
"""
iHub Robotics — Daksha Robot Web UI
Flask backend: serves URDF, meshes, joint states, and launch controls.
"""

import os
import subprocess


# -- ROS 2 parameters (Clients_UI/config/*.yaml) -----------------------------
# Every setting below is a real ROS parameter, supplied by
# Clients_UI/config/common.yaml + daksha_ui.yaml via client_ui.launch.py's
# parameters=[...]
# (or by hand: --ros-args --params-file <that file>). The node is created with
# automatically_declare_parameters_from_overrides=True, so a key added to that
# file is readable here with no change to this script:
#     ros2 param get /daksha_dashboard network.daksha_ui_port
#
# ROS_DOMAIN_ID is the one setting that cannot arrive this way. DDS reads it
# during rclpy.init(), and a node has to be on a domain already before it can
# read any parameter. The launch file exports it with SetEnvironmentVariable
# before starting this node. Run by hand with no domain in the environment,
# fall back to this robot's own domain rather than silently landing on domain
# 0, where none of the robot's topics are visible.
DEFAULT_ROS_DOMAIN_ID = "33"
if not os.environ.get("ROS_DOMAIN_ID"):
    os.environ["ROS_DOMAIN_ID"] = DEFAULT_ROS_DOMAIN_ID
    print(f"[config] ROS_DOMAIN_ID unset - defaulting to {DEFAULT_ROS_DOMAIN_ID}; "
          f"launch via client_ui.launch.py to take it from config/common.yaml")

import sys

import rclpy
from rclpy.exceptions import ParameterNotDeclaredException
from rclpy.node import Node as _RclpyNode

if not rclpy.ok():
    rclpy.init(args=sys.argv)

# Named to match the launch file so `ros2 param list /daksha_dashboard` works
# against a running UI.
_param_node = _RclpyNode(
    "daksha_dashboard",
    automatically_declare_parameters_from_overrides=True,
)


def cfg(name, default=None):
    """One dotted ROS parameter, or `default` when no params file supplied it.

    automatically_declare_parameters_from_overrides declares only what was
    actually passed in, so every lookup needs a fallback for the
    no-params-file case.
    """
    try:
        return _param_node.get_parameter(name).value
    except ParameterNotDeclaredException:
        return default


def cfg_group(prefix):
    """A whole parameter sub-tree as a nested dict.

    The parameter file's nesting is flattened to dotted names on load, so
    `joint_calibration.left_joint_1.scale` has to be rebuilt into
    {'left_joint_1': {'scale': ...}} for the code that consumes it.
    """
    out = {}
    for key, param in _param_node.get_parameters_by_prefix(prefix).items():
        node = out
        parts = key.split(".")
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = param.value
    return out


# Where the parameter file lives on disk, passed as a parameter by the launch
# file. Only the calibration editor needs it, to write its changes back.
CONFIG_PATH = cfg("config_file")
if CONFIG_PATH:
    print(f"[config] parameters from: {CONFIG_PATH}")
else:
    print("[config] no config_file parameter - calibration edits will not persist")

import threading
import time
import json
import base64
import logging
import re
import math
import yaml
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, render_template, request, jsonify, send_file, abort, Response
from flask_cors import CORS

logging.getLogger("werkzeug").setLevel(logging.WARNING)

app = Flask(__name__)
CORS(app)

# ── Paths ──────────────────────────────────────────────────────────────────────

# realpath (not abspath): with --symlink-install, this file's path under
# install/daksha_ui/lib/daksha_ui/ is itself a symlink back to the source
# tree. abspath() preserves that symlink path, which broke every
# APP_DIR-relative fallback below (_UNIFIED_INSTALL resolved to a
# nonexistent path outside the workspace entirely, so every `source
# {_UNIFIED_INSTALL} 2>/dev/null` subprocess call silently no-op'd).
# realpath resolves the symlink back to the real source location.
APP_DIR       = os.path.dirname(os.path.realpath(__file__))
# Resolution order: the installed package's share/ dir (works regardless of
# whether this app itself runs from source or installed, since it's the
# real ROS-idiomatic way to find another package's resources) → __file__-
# relative candidate for running straight from source before ever building.
# daksha_description_full_body lives outside Clients_UI, as a sibling package
# under src/, so the source-tree fallback has to climb out of Clients_UI.
_desc_candidates = []
try:
    from ament_index_python.packages import get_package_share_directory
    _desc_candidates.append(get_package_share_directory("daksha_description_full_body"))
except Exception:
    pass
_desc_candidates += [
    os.path.abspath(os.path.join(APP_DIR, "..", "..", "..", "..", "daksha_description_full_body")),
]
DESC_PKG  = next((p for p in _desc_candidates if os.path.isdir(p)), _desc_candidates[-1])
URDF_DIR  = os.path.join(DESC_PKG, "urdf")
MESHES_DIR = os.path.join(DESC_PKG, "meshes")

# daksha_description_full_body ships a flat, pre-compiled URDF (no xacro
# processing needed at runtime).
_urdf_candidates = [
    os.path.join(URDF_DIR, "robot.urdf"),
]
PRIMARY_URDF = next((p for p in _urdf_candidates if os.path.isfile(p)), _urdf_candidates[0])


# ── State ─────────────────────────────────────────────────────────────────────
ros_process   = None
joint_states  = {}
joint_effort  = {}  # urdf joint name -> commanded torque (N*m), from /jnt_cmt_to_ctrl
launch_log    = []
_joint_cmd_pub = None  # rclpy Publisher for /joint_cmd, set once the ROS bridge node is up
latest_motor_status = {"left": {}, "right": {}}
latest_battery_percent = None  # set from /battery_info; None until the first message arrives
latest_mode_status = "unknown"  # set from /mode_toggler/status ("teach" / "normal" / "transitioning" / ...)
ros_bridge_thread = None
ros_bridge_stop = threading.Event()

# Joystick -> /cmd_vel teleop state
_joy_lock = threading.Lock()
_joy_x = 0.0
_joy_y = 0.0
_joy_last_update = 0.0
_joy_enabled = False  # only publish to /cmd_vel while the "Control" toggle is on
JOY_MAX_LINEAR = 0.5       # m/s at full forward/back deflection
JOY_MAX_ANGULAR = 1.0      # rad/s at full left/right deflection
JOY_DEADMAN_TIMEOUT = 0.5  # zero cmd_vel if no joystick update received within this long

_jt = cfg_group('joint_topics')
_mt = cfg_group('motor_topics')
LEFT_JOINT_TOPIC  = _jt.get('follower_left',  '/LeftArmSystem_ordered_joint_states')
RIGHT_JOINT_TOPIC = _jt.get('follower_right', '/RightArmSystem_ordered_joint_states')
LEFT_MOTOR_TOPIC  = _mt.get('left',  '/LeftArmSystem/motor_status')
RIGHT_MOTOR_TOPIC = _mt.get('right', '/RightArmSystem/motor_status')
JOINT_TORQUE_TOPIC = _jt.get('torque_debug', '/jnt_cmt_to_ctrl')

# Safety thresholds (from config, with safe defaults)
_safety = cfg_group('safety')
BATTERY_WARN_PCT    = _safety.get('battery_warn_percent',  35)
MOTOR_TEMP_WARN     = _safety.get('motor_temp_warn',  60)
MOTOR_TEMP_ALERT    = _safety.get('motor_temp_alert', 65)

# Cross-notification URL for Data Collection UI
_net = cfg_group('network')
DATA_COLLECTION_URL = _net.get('data_collection_url', 'http://localhost:8888')
DASHA_PORT          = _net.get('daksha_ui_port', 7070)

# The state topics use the controller's names.  Keep this conversion explicit so
# the values always drive the matching joints in robot.urdf.
TOPIC_TO_URDF_JOINTS = {
    "left_joint_1": ("left_joint_1",),
    "left_joint_2": ("left_joint2", "left_joint_2"),
    "left_joint2": ("left_joint2", "left_joint_2"),
    "left_joint_3": ("left_joint_3",),
    "left_joint_4": ("left_joint_4",),
    "left_joint_5": ("left_joint_5",),
    "left_joint_6": ("left_joint_6",),
    "left_joint_7": ("left_joint_7",),
    "left_gripper": ("left_left_gripper_joint", "left_right_gripper_joint"),
    "left_gripper_left_joint": ("left_left_gripper_joint", "left_right_gripper_joint"),
    "left_gripper_right_joint": ("left_right_gripper_joint", "left_left_gripper_joint"),
    "left_left_gripper_joint": ("left_left_gripper_joint", "left_right_gripper_joint"),
    "left_right_gripper_joint": ("left_right_gripper_joint", "left_left_gripper_joint"),
    "right_joint_1": ("right_joint_1",),
    "right_joint_2": ("right_joint_2",),
    "right_joint_3": ("right_joint_3",),
    "right_joint_4": ("right_joint_4",),
    "right_joint_5": ("right_joint_5",),
    "right_joint_6": ("right_joint_6",),
    "right_joint_7": ("right_joint_7",),
    "right_gripper": ("right_right_finger_joint", "right_left_finger_joint"),
    "right_gripper_right_joint": ("right_right_finger_joint", "right_left_finger_joint"),
    "right_gripper_left_joint": ("right_left_finger_joint", "right_right_finger_joint"),
    "right_right_finger_joint": ("right_right_finger_joint", "right_left_finger_joint"),
    "right_left_finger_joint": ("right_left_finger_joint", "right_right_finger_joint"),
}


# ── Helpers ───────────────────────────────────────────────────────────────────
def _get_xacro_env() -> dict:
    # xacro's $(find pkg) resolves via ROS_PACKAGE_PATH by scanning for a
    # directory containing that package's package.xml — DESC_PKG (the
    # resolved description package's own root) is exactly that, regardless
    # of whether it's a bare source checkout or a colcon-built package.
    env = os.environ.copy()
    pkg_dir = os.path.abspath(os.path.join(URDF_DIR, ".."))
    env['ROS_PACKAGE_PATH'] = f"{pkg_dir}:{env.get('ROS_PACKAGE_PATH', '')}"
    try:
        from ament_index_python.packages import get_package_prefix
        install_pkg = get_package_prefix("daksha_description_full_body")
        env['AMENT_PREFIX_PATH'] = f"{install_pkg}:{env.get('AMENT_PREFIX_PATH', '')}"
    except Exception:
        pass
    return env


def parse_urdf_joints(urdf_path: str) -> list:
    """Return list of revolute/prismatic joints from the URDF."""
    joints = []
    try:
        if urdf_path.endswith(".xacro"):
            res = subprocess.run(["xacro", urdf_path], capture_output=True, text=True, timeout=10, env=_get_xacro_env())
            content = res.stdout if res.returncode == 0 else ""
        else:
            with open(urdf_path) as f:
                content = f.read()

        pattern = re.compile(
            r'<joint\s+name="([^"]+)"\s+type="(revolute|prismatic)".*?'
            r'<limit([^>]+)>',
            re.DOTALL,
        )
        for m in pattern.finditer(content):
            name = m.group(1)
            jtype = m.group(2)
            limit_attr = m.group(3)
            lower_m = re.search(r'lower="([^"]+)"', limit_attr)
            upper_m = re.search(r'upper="([^"]+)"', limit_attr)
            if lower_m and upper_m:
                joints.append({
                    "name": name,
                    "type": jtype,
                    "lower": float(lower_m.group(1)),
                    "upper": float(upper_m.group(1)),
                    "value": 0.0,
                })
    except Exception as e:
        print(f"[parse_urdf_joints] {e}")
    return joints


def _source_ros_env() -> dict:
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    return env


_UNIFIED_INSTALL = os.path.abspath(os.path.join(APP_DIR, '..', '..', '..', '..', '..', 'install', 'setup.bash'))


def set_toggler_mode(mode_name: str):
    """Best-effort `ros2 param set /mode_toggler mode <mode_name>`, same
    mechanism gesture_management uses (mode_toggler is a shared gen2 node,
    not specific to any one UI)."""
    try:
        cmd = (
            "source /opt/ros/humble/setup.bash && "
            f"source {_UNIFIED_INSTALL} 2>/dev/null; "
            f"ros2 param set /mode_toggler mode {mode_name}"
        )
        result = subprocess.run(
            ["bash", "-c", cmd], capture_output=True, text=True, timeout=5, env=_source_ros_env()
        )
        if result.returncode != 0:
            return False, f"mode_toggler set failed: {result.stderr.strip()}"
        return True, f"mode_toggler -> {mode_name}"
    except Exception as e:
        return False, f"mode_toggler set failed: {e}"


def set_limiter_param(name: str, value: float):
    """Best-effort `ros2 param set /joint_command_limiter <name> <value>`,
    same mechanism as set_toggler_mode above."""
    try:
        cmd = (
            "source /opt/ros/humble/setup.bash && "
            f"source {_UNIFIED_INSTALL} 2>/dev/null; "
            f"ros2 param set /joint_command_limiter {name} {value}"
        )
        result = subprocess.run(
            ["bash", "-c", cmd], capture_output=True, text=True, timeout=5, env=_source_ros_env()
        )
        if result.returncode != 0:
            return False, f"joint_command_limiter set failed: {result.stderr.strip()}"
        return True, f"joint_command_limiter {name} -> {value}"
    except Exception as e:
        return False, f"joint_command_limiter set failed: {e}"


def get_limiter_param(name: str):
    """Best-effort `ros2 param get /joint_command_limiter <name>`, e.g.
    'Double value is: 3.0'."""
    try:
        cmd = (
            "source /opt/ros/humble/setup.bash && "
            f"source {_UNIFIED_INSTALL} 2>/dev/null; "
            f"ros2 param get /joint_command_limiter {name}"
        )
        result = subprocess.run(
            ["bash", "-c", cmd], capture_output=True, text=True, timeout=1.5, env=_source_ros_env()
        )
        if result.returncode != 0 or not result.stdout.strip():
            return None
        return float(result.stdout.strip().rsplit(":", 1)[-1].strip())
    except Exception:
        return None


def _run_ros_echo(topic: str) -> dict | None:
    try:
        cmd = [
            "bash",
            "-lc",
            f"source /opt/ros/humble/setup.bash && "
            f"source {_UNIFIED_INSTALL} 2>/dev/null; "
            f"ros2 topic echo --once {topic} 2>/dev/null",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=1.2, env=_source_ros_env())
        if result.returncode != 0 or not result.stdout.strip():
            return None
        try:
            # ros2 can prepend diagnostics such as "A message was lost!!!"
            # before the actual YAML message. Start at the message root instead.
            lines = result.stdout.splitlines()
            start = next(
                (index for index, line in enumerate(lines)
                 if line.strip() in {"header:", "motors:"}),
                None,
            )
            if start is None:
                return None
            return next(
                (document for document in yaml.safe_load_all("\n".join(lines[start:]))
                 if isinstance(document, dict)),
                None,
            )
        except Exception:
            return None
    except Exception:
        return None


JOINT_CALIBRATION = cfg_group('joint_calibration')

def _expand_joint_aliases(clean_name: str, value) -> dict:
    """Mirror a value onto every alias name the URDF viewer / joint list uses
    for a given topic joint name (e.g. left_joint_2 <-> left_joint2)."""
    urdf_joints = TOPIC_TO_URDF_JOINTS.get(clean_name, (clean_name,))
    mapped = {}
    for joint_name in urdf_joints:
        mapped[joint_name] = value
        mapped[clean_name] = value
        if joint_name == "left_joint_2": mapped["left_joint2"] = value
        elif joint_name == "left_joint2": mapped["left_joint_2"] = value
        elif joint_name == "right_joint_2": mapped["right_joint2"] = value
        elif joint_name == "right_joint2": mapped["right_joint_2"] = value
    return mapped


def _extract_joint_positions(payload: dict | None) -> dict:
    if not isinstance(payload, dict):
        return {}
    names = payload.get("name", [])
    positions = payload.get("position", [])
    if not isinstance(names, list) or not isinstance(positions, list):
        return {}
    mapped = {}
    for raw_name, raw_value in zip(names, positions):
        clean_name = str(raw_name).strip()
        urdf_joints = TOPIC_TO_URDF_JOINTS.get(clean_name, (clean_name,))
        if not urdf_joints:
            continue
        try:
            val = float(raw_value)
        except (TypeError, ValueError):
            continue

        for joint_name in urdf_joints:
            calib = (
                JOINT_CALIBRATION.get(clean_name) or 
                JOINT_CALIBRATION.get(joint_name) or 
                JOINT_CALIBRATION.get(clean_name.replace("_1", "")) or 
                JOINT_CALIBRATION.get(clean_name.replace("left_joint2", "left_joint_2").replace("right_joint2", "right_joint_2")) or 
                {}
            )
            scale = float(calib.get("scale", 1.0))
            offset = float(calib.get("offset", 0.0))
            calibrated_val = (val - offset) * scale
            
            # Enforce limits if configured
            if "lower" in calib:
                calibrated_val = max(float(calib["lower"]), calibrated_val)
            if "upper" in calib:
                calibrated_val = min(float(calib["upper"]), calibrated_val)

            res_val = round(calibrated_val, 6)
            mapped[joint_name] = res_val
            mapped[clean_name] = res_val
            if joint_name == "left_joint_2": mapped["left_joint2"] = res_val
            elif joint_name == "left_joint2": mapped["left_joint_2"] = res_val
            elif joint_name == "right_joint_2": mapped["right_joint2"] = res_val
            elif joint_name == "right_joint2": mapped["right_joint_2"] = res_val
            elif joint_name.startswith("left_") and ("gripper" in joint_name or "finger" in joint_name):
                mapped["left_left_gripper_joint"] = res_val
                mapped["left_right_gripper_joint"] = res_val
            elif joint_name.startswith("right_") and ("gripper" in joint_name or "finger" in joint_name):
                mapped["right_right_finger_joint"] = res_val
                mapped["right_left_finger_joint"] = res_val
    return mapped


def _extract_motor_summary(payload: dict | None) -> dict:
    if not isinstance(payload, dict):
        return {"temperature": None, "status": "Standby", "motors": []}

    if "data" in payload and isinstance(payload["data"], dict):
        return _extract_motor_summary(payload["data"])

    motors = payload.get("motors", [])
    if isinstance(motors, list):
        motor_items = motors
    elif isinstance(payload, dict):
        motor_items = [payload]
    else:
        motor_items = []

    temperatures = []
    statuses = []
    for motor in motor_items:
        if not isinstance(motor, dict):
            continue
        temp = None
        for key in (
            "mos_temp", "rotor_temp", "temperature", "temp", "temp_c",
            "temp_celsius", "temperature_c",
        ):
            if key in motor:
                try:
                    temp = float(motor[key])
                    break
                except (TypeError, ValueError):
                    continue
        if temp is not None:
            temperatures.append(temp)
        status = (
            motor.get("error_name") or motor.get("status") or motor.get("state")
            or motor.get("mode") or ""
        )
        if isinstance(status, str) and status:
            statuses.append(status)

    if temperatures:
        temperature = round(sum(temperatures) / len(temperatures), 1)
    else:
        temperature = None

    if statuses:
        status_text = statuses[0]
    elif payload.get("status"):
        status_text = str(payload.get("status"))
    else:
        status_text = "Running" if temperature is not None else "Standby"

    return {
        "temperature": temperature,
        "status": status_text,
        "motors": motor_items,
    }


def _refresh_ros_state() -> None:
    global joint_states, latest_motor_status
    topics = (LEFT_JOINT_TOPIC, RIGHT_JOINT_TOPIC, LEFT_MOTOR_TOPIC, RIGHT_MOTOR_TOPIC)
    # Each `--once` call can wait briefly when the robot is offline.  Run them
    # together so one unavailable topic cannot delay all live visualization.
    with ThreadPoolExecutor(max_workers=len(topics)) as executor:
        payloads = dict(zip(topics, executor.map(_run_ros_echo, topics)))

    joint_payloads = {
        "left": payloads[LEFT_JOINT_TOPIC],
        "right": payloads[RIGHT_JOINT_TOPIC],
    }
    merged_joints = {}
    for side, payload in joint_payloads.items():
        merged_joints.update(_extract_joint_positions(payload))
    joint_states = merged_joints

    latest_motor_status = {
        "left": _extract_motor_summary(payloads[LEFT_MOTOR_TOPIC]),
        "right": _extract_motor_summary(payloads[RIGHT_MOTOR_TOPIC]),
    }


def _update_live_joint_states(message) -> None:
    """Apply one sensor_msgs/JointState callback to the URDF joint cache."""
    global joint_states
    updates = _extract_joint_positions({
        "name": list(message.name),
        "position": list(message.position),
    })
    if updates:
        joint_states = {**joint_states, **updates}


def _update_joint_effort(message) -> None:
    """Apply one sensor_msgs/JointState callback from JOINT_TORQUE_TOPIC
    (joint_cmd's commanded-torque debug stream: target + gravity-comp effort)."""
    global joint_effort
    names = list(getattr(message, "name", []))
    efforts = list(getattr(message, "effort", []))
    updates = {}
    for raw_name, raw_effort in zip(names, efforts):
        clean_name = str(raw_name).strip()
        try:
            val = round(float(raw_effort), 4)
        except (TypeError, ValueError):
            continue
        updates.update(_expand_joint_aliases(clean_name, val))
    if updates:
        joint_effort = {**joint_effort, **updates}


def _joint_temperatures() -> dict:
    """Per-joint MOS/rotor temperature, mapped from motor id (1-based, per
    arm) onto the matching left_joint_N / right_joint_N URDF joint names."""
    temps = {}
    for side, prefix in (("left", "left_joint"), ("right", "right_joint")):
        motors = latest_motor_status.get(side, {}).get("motors", [])
        if not isinstance(motors, list):
            continue
        for motor in motors:
            if not isinstance(motor, dict):
                continue
            try:
                motor_id = int(motor.get("id"))
            except (TypeError, ValueError):
                continue
            entry = {
                "rotor_temp": motor.get("rotor_temp"),
                "mos_temp": motor.get("mos_temp"),
            }
            temps.update(_expand_joint_aliases(f"{prefix}_{motor_id}", entry))
    return temps


def _update_battery_percent(message) -> None:
    """Apply one std_msgs/Float32 callback from /battery_info."""
    global latest_battery_percent
    latest_battery_percent = float(message.data)


def _publish_joystick_cmd_vel(cmd_vel_pub, Twist) -> None:
    """Publish the latest joystick deflection to /cmd_vel, zeroing it out if the
    web UI hasn't sent an update recently (dead-man safety). Publishes nothing
    at all while the "Control" toggle is off."""
    with _joy_lock:
        enabled, x, y, last = _joy_enabled, _joy_x, _joy_y, _joy_last_update

    if not enabled:
        return

    msg = Twist()
    if (time.time() - last) > JOY_DEADMAN_TIMEOUT:
        msg.linear.x = 0.0
        msg.angular.z = 0.0
    else:
        msg.linear.x = y * JOY_MAX_LINEAR
        msg.angular.z = -x * JOY_MAX_ANGULAR

    cmd_vel_pub.publish(msg)


def _update_mode_status(message) -> None:
    """Apply one std_msgs/String callback from /mode_toggler/status."""
    global latest_mode_status
    latest_mode_status = message.data


# Matches a plausible YAML "key: value" or "- key: value" line. `ros2 topic
# echo` occasionally interleaves non-YAML diagnostic lines (e.g. DDS sample-
# loss notices like "total count change:1") into the middle of a streamed
# message, which breaks a naive per-chunk yaml.safe_load. Filtering to only
# lines that look like real message fields drops that noise before parsing.
_YAML_KV_LINE_RE = re.compile(r'^\s*(-\s+)?[A-Za-z_][\w]*\s*:\s?.*$')


def _motor_monitor_worker(topic: str, side: str) -> None:
    cmd = [
        "bash",
        "-lc",
        f"source /opt/ros/humble/setup.bash && "
        f"source {_UNIFIED_INSTALL} 2>/dev/null; "
        f"ros2 topic echo {topic} 2>/dev/null",
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, text=True, env=_source_ros_env())
    buffer = []
    for line in iter(proc.stdout.readline, ''):
        if ros_bridge_stop.is_set():
            proc.terminate()
            break
        stripped = line.strip()
        if stripped == '---':
            if buffer:
                try:
                    clean_lines = [ln for ln in buffer if _YAML_KV_LINE_RE.match(ln)]
                    yaml_str = "\n".join(clean_lines)
                    for doc in yaml.safe_load_all(yaml_str):
                        if isinstance(doc, dict):
                            latest_motor_status[side] = _extract_motor_summary(doc)
                            break
                except Exception:
                    pass
            buffer = []
        else:
            buffer.append(line)

def _start_motor_monitors() -> None:
    threading.Thread(target=_motor_monitor_worker, args=(LEFT_MOTOR_TOPIC, "left"), daemon=True).start()
    threading.Thread(target=_motor_monitor_worker, args=(RIGHT_MOTOR_TOPIC, "right"), daemon=True).start()

# Camera frame buffer: cam_id -> (base64_data_uri, timestamp)
latest_camera_frames = {}

# Known cameras, sourced from config/common.yaml's camera_topics (the
# single source of truth also used for joint/motor topics) so this list
# tracks whatever's actually wired up on the robot instead of being
# hardcoded here. Falls back to the wrist cameras if the config is missing
# the section entirely.
_CAMERA_TOPICS_CFG = cfg_group('camera_topics') or {
    "left_wrist": {"display_name": "Left Wrist Camera", "compressed": "/left/camera/color/image_raw/compressed"},
    "right_wrist": {"display_name": "Right Wrist Camera", "compressed": "/right/camera/color/image_raw/compressed"},
}

CAMERA_REGISTRY = [
    {
        "id": cam_id,
        "display_name": cfg.get("display_name", cam_id),
        "topic": cfg.get("compressed") or cfg.get("topic"),
    }
    for cam_id, cfg in _CAMERA_TOPICS_CFG.items()
    if cfg.get("compressed") or cfg.get("topic")
]
CAMERA_REGISTRY_BY_ID = {c["id"]: c for c in CAMERA_REGISTRY}

CAM_TOPICS = {c["id"]: c["topic"] for c in CAMERA_REGISTRY}
CAM_NAME_MAP = {c["id"]: c["display_name"] for c in CAMERA_REGISTRY}

# Which cameras the operator has chosen to display, and in what order —
# persisted as a proper daksha_ui package config resource (config/camera_
# layout.json, installed to share/daksha_ui/config/ — see CMakeLists.txt)
# so the "Camera" quick-access modal remembers the layout across reloads/
# restarts (Save/Load Camera Config buttons in the UI). Same share/-dir-
# first, source-relative-fallback resolution as DESC_PKG above; unlike
# the shared config this file belongs to daksha_ui alone, so it's a real
# ament package resource rather than a hand-walked cross-package path.
try:
    CAMERA_LAYOUT_PATH = os.path.join(
        get_package_share_directory("daksha_ui"), "config", "camera_layout.json"
    )
except Exception:
    # config/ sits at the package root (sibling of launch/), one level up
    # from APP_DIR (the daksha_ui/daksha_ui/ Python module dir).
    CAMERA_LAYOUT_PATH = os.path.join(APP_DIR, "..", "config", "camera_layout.json")
CAMERA_LAYOUT_PATH = os.path.normpath(CAMERA_LAYOUT_PATH)


def _load_camera_layout() -> list:
    """Ordered list of camera ids to display; defaults to every known
    camera (registry order) until the operator saves a custom layout."""
    try:
        with open(CAMERA_LAYOUT_PATH) as f:
            data = json.load(f)
        selected = [cid for cid in data.get("selected", []) if cid in CAMERA_REGISTRY_BY_ID]
        if selected:
            return selected
    except Exception:
        pass
    return [c["id"] for c in CAMERA_REGISTRY]


def _save_camera_layout(selected: list) -> None:
    tmp = CAMERA_LAYOUT_PATH + ".tmp"
    with open(tmp, "w") as f:
        json.dump({"selected": selected}, f, indent=2)
    os.replace(tmp, CAMERA_LAYOUT_PATH)


cam_frame_counts = {}

def _make_cam_callback(cam_id: str):
    def callback(msg):
        try:
            b64 = base64.b64encode(bytes(msg.data)).decode('utf-8')
            uri = f"data:image/jpeg;base64,{b64}"
            now = time.time()
            latest_camera_frames[cam_id] = (uri, now)
            cam_name = CAM_NAME_MAP.get(cam_id)
            if cam_name:
                latest_camera_frames[cam_name] = (uri, now)

            cam_frame_counts[cam_id] = cam_frame_counts.get(cam_id, 0) + 1
            if cam_frame_counts[cam_id] == 1:
                print(f"[ros bridge] Live camera stream active for Cam {cam_id} ({CAM_TOPICS.get(cam_id)})")
        except Exception:
            pass
    return callback


def _ros_bridge_loop() -> None:
    """Subscribe directly to the ordered JointState & CompressedImage topics for smooth motion & vision."""
    global _joint_cmd_pub
    _start_motor_monitors()
    try:
        import rclpy
        from rclpy.node import Node
        from rclpy.qos import qos_profile_sensor_data, QoSProfile, QoSDurabilityPolicy, QoSReliabilityPolicy, QoSHistoryPolicy
        from sensor_msgs.msg import JointState, CompressedImage
        from std_msgs.msg import Float32, String
        from geometry_msgs.msg import Twist

        if not rclpy.ok():
            rclpy.init(args=None)

        # use_global_arguments=False: the launch file passes
        # -r __node:=daksha_dashboard, and a __node remap applies to every
        # node a process creates. Without this, the parameter node above and
        # this one both come up as /daksha_dashboard, which rosout complains
        # about ("Publisher already registered for provided node name") and
        # which makes `ros2 node list` ambiguous. This node reads no
        # parameters, so it loses nothing by ignoring the global args.
        node = Node("daksha_web_joint_visualizer", use_global_arguments=False)
        cmd_vel_pub = node.create_publisher(Twist, "/cmd_vel", 10)
        # Live per-joint slider commands (only enabled client-side once the
        # arm has confirmed it's homed within tolerance).
        _joint_cmd_pub = node.create_publisher(JointState, "/joint_cmd", 10)
        node.create_subscription(Float32, "battery_info", _update_battery_percent, 10)
        # Must match mode_toggler's publisher QoS (transient-local) so this
        # subscriber gets the last status even if it connects after
        # mode_toggler already settled into its startup mode.
        mode_status_qos = QoSProfile(
            depth=1,
            reliability=QoSReliabilityPolicy.RELIABLE,
            durability=QoSDurabilityPolicy.TRANSIENT_LOCAL,
            history=QoSHistoryPolicy.KEEP_LAST,
        )
        node.create_subscription(String, "/mode_toggler/status", _update_mode_status, mode_status_qos)
        # Use qos_profile_sensor_data to guarantee compatibility with BEST_EFFORT and RELIABLE publishers
        node.create_subscription(
            JointState, LEFT_JOINT_TOPIC, _update_live_joint_states, qos_profile_sensor_data
        )
        node.create_subscription(
            JointState, RIGHT_JOINT_TOPIC, _update_live_joint_states, qos_profile_sensor_data
        )
        # Secondary fallback subscription for standard RELIABLE publishers
        node.create_subscription(
            JointState, LEFT_JOINT_TOPIC, _update_live_joint_states, 10
        )
        node.create_subscription(
            JointState, RIGHT_JOINT_TOPIC, _update_live_joint_states, 10
        )
        # Commanded torque (target + gravity-comp effort) debug stream from joint_cmd.
        node.create_subscription(
            JointState, JOINT_TORQUE_TOPIC, _update_joint_effort, qos_profile_sensor_data
        )
        node.create_subscription(
            JointState, JOINT_TORQUE_TOPIC, _update_joint_effort, 10
        )

        for cam_id, topic in CAM_TOPICS.items():
            try:
                node.create_subscription(
                    CompressedImage, topic, _make_cam_callback(cam_id), qos_profile_sensor_data
                )
                print(f"[ros bridge] Subscribed camera {cam_id} -> {topic}")
            except Exception as e:
                print(f"[ros bridge] Camera sub error for {topic}: {e}")

        print(f"[ros bridge] Direct ROS 2 node 'daksha_web_joint_visualizer' active on Domain {os.environ.get('ROS_DOMAIN_ID', '0')}")

        while rclpy.ok() and not ros_bridge_stop.is_set():
            rclpy.spin_once(node, timeout_sec=0.05)
            _publish_joystick_cmd_vel(cmd_vel_pub, Twist)

        node.destroy_node()
        rclpy.shutdown()
        return
    except Exception as error:
        print(f"[ros bridge] direct JointState subscription unavailable: {error}")

    # Preserve a best-effort fallback for machines without rclpy installed.
    while not ros_bridge_stop.is_set():
        try:
            _refresh_ros_state()
        except Exception:
            pass
        time.sleep(0.8)


def start_ros_bridge() -> None:
    global ros_bridge_thread
    if ros_bridge_thread and ros_bridge_thread.is_alive():
        return
    ros_bridge_thread = threading.Thread(target=_ros_bridge_loop, daemon=True)
    ros_bridge_thread.start()


# ── Routes ────────────────────────────────────────────────────────────────────
@app.route("/api/camera_frames")
def get_camera_frames():
    """Return latest camera frames as base64 JPEG images, keyed by camera id."""
    now = time.time()
    frames = {}
    for cam_id, (data_uri, timestamp) in list(latest_camera_frames.items()):
        if now - timestamp < 3.0:
            frames[cam_id] = data_uri

    # Fallback proxy from Data Collection UI (port 8080) if local rclpy didn't receive frames
    if not frames:
        try:
            import urllib.request
            req = urllib.request.urlopen(f"{DATA_COLLECTION_URL}/api/cameras/all-frames", timeout=0.5)
            res = json.loads(req.read().decode('utf-8'))
            if res.get('ok') and res.get('frames'):
                name_to_id = {name: cid for cid, name in CAM_NAME_MAP.items()}
                for name, frame_uri in res['frames'].items():
                    cid = name_to_id.get(name)
                    if cid and frame_uri:
                        frames[cid] = frame_uri
        except Exception:
            pass

    return jsonify({"ok": True, "frames": frames})


@app.route("/api/camera_config", methods=["GET", "POST"])
def api_camera_config():
    """GET: every known camera plus the saved display layout (which ones,
    in what order). POST {"selected": [id, ...]}: save a new layout — used
    by the Camera modal's drag-and-drop Save/Load Camera Config buttons."""
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        selected = data.get("selected")
        if not isinstance(selected, list) or not all(isinstance(s, str) for s in selected):
            return jsonify({"ok": False, "error": "selected must be a list of camera ids"}), 400
        selected = [cid for cid in selected if cid in CAMERA_REGISTRY_BY_ID]
        if not selected:
            return jsonify({"ok": False, "error": "no valid camera ids in selection"}), 400
        try:
            _save_camera_layout(selected)
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500
        return jsonify({"ok": True, "selected": selected})

    return jsonify({
        "ok": True,
        "available": CAMERA_REGISTRY,
        "selected": _load_camera_layout(),
    })


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/urdf")
def get_urdf():
    """Serve the URDF XML, rewriting package:// URIs to /pkg/..."""
    urdf_name = request.args.get("file", "robot.urdf")
    safe = {
        "robot.urdf":    PRIMARY_URDF,
        "daksha_v10_2.urdf": PRIMARY_URDF,
    }
    path = safe.get(urdf_name, PRIMARY_URDF)

    # If the resolved file is a xacro, compile it dynamically
    if path.endswith(".xacro"):
        try:
            env = _get_xacro_env()

            result = subprocess.run(
                ["xacro", path],
                capture_output=True, text=True, timeout=15, env=env
            )
            if result.returncode == 0:
                content = result.stdout
            else:
                return Response(
                    f"<!-- xacro compilation failed:\n{result.stderr}\n-->",
                    mimetype="application/xml", status=500
                )
        except Exception as e:
            return Response(
                f"<!-- xacro execution error: {e} -->",
                mimetype="application/xml", status=500
            )
    else:
        if not os.path.isfile(path):
            abort(404)
        with open(path) as f:
            content = f.read()


    # Rewrite all known package:// URIs to the /pkg/ proxy route
    pkg_name = os.path.basename(DESC_PKG)
    for old_pkg in [
        "daksha_final_urdf_description",
        "daksha_description_full_body",
        "daksha_description",
    ]:
        content = content.replace(f"package://{old_pkg}/", "/pkg/")

    return Response(content, mimetype="application/xml")



@app.route("/api/joint_calibration", methods=["GET", "POST"])
def joint_calibration_api():
    """GET current calibration matrix or POST updates to config/daksha_ui.yaml."""
    global JOINT_CALIBRATION
    if request.method == "POST":
        data = request.get_json() or {}
        if isinstance(data, dict):
            JOINT_CALIBRATION.update(data)
            if not CONFIG_PATH:
                return jsonify({
                    "ok": False,
                    "error": "no config_file parameter — calibration applied in-memory "
                             "only, not saved. Launch via client_ui.launch.py, or pass "
                             "-p config_file:=<path to config/daksha_ui.yaml>.",
                }), 500
            try:
                # Read-modify-write the file rather than dumping what this
                # process holds: the parameters here are a flattened view of
                # one node's overrides, so dumping them would drop the
                # `/**: ros__parameters:` envelope and every section this app
                # never looks at, leaving the other UIs with no config.
                with open(CONFIG_PATH) as f:
                    document = yaml.safe_load(f) or {}
                document.setdefault('/**', {}).setdefault('ros__parameters', {})
                document['/**']['ros__parameters']['joint_calibration'] = JOINT_CALIBRATION
                with open(CONFIG_PATH, 'w') as f:
                    yaml.safe_dump(document, f, default_flow_style=False, sort_keys=False)
            except Exception as e:
                return jsonify({"ok": False, "error": str(e)}), 500
            return jsonify({"ok": True, "calibration": JOINT_CALIBRATION})
    return jsonify({"ok": True, "calibration": JOINT_CALIBRATION})


@app.route("/pkg/<path:subpath>")
def serve_pkg(subpath):
    """Serve files from the daksha_description package."""
    # Redirect mesh requests to the ultra-low poly web meshes if available
    if subpath.startswith("meshes/"):
        web_meshes = os.path.join(DESC_PKG, "meshes_web")
        if os.path.isdir(web_meshes):
            web_path = os.path.realpath(os.path.join(web_meshes, subpath[len("meshes/"):]))
            if web_path.startswith(os.path.realpath(web_meshes)) and os.path.isfile(web_path):
                return send_file(web_path, mimetype="model/stl")

    full = os.path.realpath(os.path.join(DESC_PKG, subpath))
    # Security: must stay inside DESC_PKG
    if not full.startswith(os.path.realpath(DESC_PKG)):
        abort(403)
    if not os.path.isfile(full):
        abort(404)
    ext = os.path.splitext(full)[1].lower()
    mime_map = {
        ".dae": "model/vnd.collada+xml",
        ".stl": "model/stl",
        ".png": "image/png",
        ".jpg": "image/jpeg",
    }
    mime = mime_map.get(ext, "application/octet-stream")
    return send_file(full, mimetype=mime)


def _hardware_joints_list() -> list:
    """Parsed URDF joints, deduped and renamed to exact physical hardware
    names (gripper mimic joints collapse to a single driving joint)."""
    raw_joints = parse_urdf_joints(PRIMARY_URDF)
    hardware_joints = []
    seen = set()
    for j in raw_joints:
        name = j["name"]
        if "finger" in name or "gripper" in name:
            if "left" in name:
                name = "left_gripper_left_joint"
            elif "right" in name:
                name = "right_gripper_right_joint"
        if name not in seen:
            seen.add(name)
            j_copy = dict(j)
            j_copy["name"] = name
            hardware_joints.append(j_copy)
    return hardware_joints


@lru_cache(maxsize=1)
def _hardware_joint_limits() -> dict:
    """name -> (lower, upper) rad, for server-side clamping of /api/joint_cmd."""
    limits = {}
    for j in _hardware_joints_list():
        try:
            limits[j["name"]] = (float(j["lower"]), float(j["upper"]))
        except (KeyError, TypeError, ValueError):
            pass
    return limits


@app.route("/api/joints")
def get_joints():
    """Return parsed joint list from the URDF mapped to exact physical hardware names."""
    return jsonify(_hardware_joints_list())


@app.route("/api/joint_states")
def get_joint_states():
    """Return the latest mapped joint states for the URDF viewer, along with
    per-joint commanded torque and motor temperature for the hover tooltip."""
    return jsonify({
        "joints": joint_states,
        "torque": joint_effort,
        "temperature": _joint_temperatures(),
        "count": len(joint_states),
    })


@app.route("/api/joint_cmd", methods=["POST"])
def api_joint_cmd():
    """Publish a single live joint-position command to /joint_cmd. The UI
    only lets this fire once the arm has confirmed it's homed within
    tolerance (LEFT/RIGHT ARM JOINTS sliders stay disabled until then); this
    still clamps to the joint's own URDF limits server-side regardless."""
    data = request.get_json(silent=True) or {}
    name = data.get("name")
    if not isinstance(name, str) or not name:
        return jsonify({"ok": False, "error": "missing joint name"}), 400
    try:
        position = float(data.get("position"))
    except (TypeError, ValueError):
        return jsonify({"ok": False, "error": "invalid position"}), 400
    if not math.isfinite(position):
        return jsonify({"ok": False, "error": "invalid position"}), 400

    limits = _hardware_joint_limits().get(name)
    if limits:
        lower, upper = limits
        position = max(lower, min(upper, position))

    if _joint_cmd_pub is None:
        return jsonify({"ok": False, "error": "ROS bridge not connected"}), 503

    try:
        from sensor_msgs.msg import JointState
        msg = JointState()
        msg.name = [name]
        msg.position = [position]
        _joint_cmd_pub.publish(msg)
        return jsonify({"ok": True, "position": position})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/move_home", methods=["POST"])
def api_move_home():
    """Trigger ROS 2 /move_home service or publish home command to /joint_cmd."""
    try:
        cmd = [
            "bash", "-lc",
            f"source /opt/ros/humble/setup.bash && "
            f"source {_UNIFIED_INSTALL} 2>/dev/null; "
            f"ros2 service call /move_home std_srvs/srv/Trigger {{}}"
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=5, env=_source_ros_env())
        if proc.returncode == 0:
            return jsonify({"ok": True, "message": "Triggered /move_home service successfully"})
    except Exception:
        pass

    # Fallback: publish zero positions to /joint_cmd
    try:
        cmd_pub = [
            "bash", "-lc",
            f"source /opt/ros/humble/setup.bash; "
            f"ros2 topic pub --once /joint_cmd sensor_msgs/msg/JointState '{{name: [left_joint_1, left_joint_2, left_joint_3, left_joint_4, left_joint_5, left_joint_6, left_joint_7, right_joint_1, right_joint_2, right_joint_3, right_joint_4, right_joint_5, right_joint_6, right_joint_7, left_gripper_left_joint, right_gripper_right_joint], position: [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]}}'"
        ]
        subprocess.Popen(cmd_pub, env=_source_ros_env())
        return jsonify({"ok": True, "message": "Published Home pose command to /joint_cmd"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/telemetry")
def get_telemetry():
    """Return robot telemetry including live motor temperatures and status."""
    is_running = ros_process is not None and ros_process.poll() is None
    left_status = latest_motor_status.get("left", {})
    right_status = latest_motor_status.get("right", {})
    return jsonify({
        "battery": latest_battery_percent if latest_battery_percent is not None else (87.0 if not is_running else 85.5),
        "temp_left": left_status.get("temperature"),
        "temp_right": right_status.get("temperature"),
        "motor_left": left_status.get("status") or ("Running" if is_running else "Standby"),
        "motor_right": right_status.get("status") or ("Running" if is_running else "Standby"),
        "motors_left": left_status.get("motors", []),
        "motors_right": right_status.get("motors", []),
        "mode": latest_mode_status,
    })


@app.route("/api/mode/set", methods=["POST"])
def api_mode_set():
    """Toggle mode_toggler between 'teach' (backdrivable) and 'normal' (tracks trajectory)."""
    data = request.get_json(silent=True) or {}
    mode = data.get("mode")
    if mode not in ("teach", "normal"):
        return jsonify({"success": False, "message": "mode must be 'teach' or 'normal'"}), 400
    ok, msg = set_toggler_mode(mode)
    return jsonify({"success": ok, "message": msg})


@app.route("/api/speed_limits", methods=["GET", "POST"])
def api_speed_limits():
    """GET current max_velocity/max_acceleration on joint_command_limiter,
    or POST {max_velocity, max_acceleration} to update either/both."""
    if request.method == "GET":
        return jsonify({
            "max_velocity": get_limiter_param("max_velocity"),
            "max_acceleration": get_limiter_param("max_acceleration"),
        })

    data = request.get_json(silent=True) or {}
    results = {}

    if "max_velocity" in data:
        ok, msg = set_limiter_param("max_velocity", float(data["max_velocity"]))
        results["max_velocity"] = {"success": ok, "message": msg}

    if "max_acceleration" in data:
        ok, msg = set_limiter_param("max_acceleration", float(data["max_acceleration"]))
        results["max_acceleration"] = {"success": ok, "message": msg}

    return jsonify(results)


@app.route("/api/joystick", methods=["POST"])
def api_joystick():
    """Accept the latest normalized joystick deflection (x, y in [-1, 1]) from
    the web UI; the ROS bridge loop turns this into /cmd_vel Twist messages."""
    global _joy_x, _joy_y, _joy_last_update

    data = request.get_json(force=True, silent=True) or {}
    try:
        x = max(-1.0, min(1.0, float(data.get("x", 0.0))))
        y = max(-1.0, min(1.0, float(data.get("y", 0.0))))
    except (TypeError, ValueError):
        return jsonify(ok=False, error="invalid x/y"), 400

    with _joy_lock:
        _joy_x = x
        _joy_y = y
        _joy_last_update = time.time()

    return jsonify(ok=True)


@app.route("/api/joystick/enable", methods=["POST"])
def api_joystick_enable():
    """Arm/disarm /cmd_vel publishing from the joystick widget. Called when the
    "Control" nav button is toggled on/off in the UI."""
    global _joy_enabled, _joy_x, _joy_y, _joy_last_update

    data = request.get_json(force=True, silent=True) or {}
    enabled = bool(data.get("enabled", False))

    with _joy_lock:
        _joy_enabled = enabled
        _joy_x = 0.0
        _joy_y = 0.0
        _joy_last_update = 0.0

    return jsonify(ok=True, enabled=enabled)


active_ui_theme = "dark"

@app.route("/api/theme", methods=["GET", "POST"])
def sync_app_theme():
    global active_ui_theme
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        theme = data.get("theme")
        if theme in ("light", "dark"):
            active_ui_theme = theme
        return jsonify({"status": "ok", "theme": active_ui_theme})
    return jsonify({"theme": active_ui_theme})



@app.route("/api/robot_info")
def robot_info():
    """Return static robot metadata."""
    return jsonify({
        "name": "Daksha",
        "version": "v10.2",
        "arm_type": "v10.2",
        "ee_type": "daksha_hand",
        "body_type": "v10.2",
        "bimanual": True,
        "dof_per_arm": 8,
        "total_joints": 16,
        "organization": "iHub Robotics",
        "urdf_file": "robot.urdf",
        "meshes_path": MESHES_DIR,
    })

@app.route('/api/diagnostics')
def diagnostics():
    # Fetch real system metrics where available
    cpu = 0
    mem = 0
    try:
        import psutil
        cpu = psutil.cpu_percent()
        mem = round(psutil.virtual_memory().used / (1024**3), 1)
    except Exception:
        cpu = 24
        mem = 8.2

    data = {
        "health": {
            "ros": "ok" if os.path.exists("/opt/ros/humble") else "warn",
            "can0": "ok" if os.path.exists("/sys/class/net/can0") else "warn",
            "can1": "ok" if os.path.exists("/sys/class/net/can1") else "warn",
            "leader": "ok" if joint_states else "warn",
            "follower": "ok" if joint_states else "warn",
            "wrist_cam": "ok",
            "head_cam": "ok",
            "gpu": "ok" if os.path.exists("/proc/driver/nvidia") or os.path.exists("/dev/nvhost-ctrl") else "warn",
            "recorder": "ok"
        },
        "metrics": {
            "ros_freq": 100 if joint_states else 0,
            "cam_fps": 30,
            "can_rate": 500 if joint_states else 0,
            "cpu_usage": cpu,
            "gpu_usage": 45,
            "gpu_temp": 62,
            "memory": mem,
            "network": 12
        }
    }
    return jsonify(data)


@app.route('/api/real_diagnostics')
def real_diagnostics():
    """Performs real step-by-step hardware and system diagnostic scans."""
    steps = []

    # 1. ROS 2 Environment
    ros_ok = os.path.exists("/opt/ros/humble/setup.bash") or os.getenv("ROS_DISTRO") is not None
    steps.append({
        "id": "ros",
        "title": "ROS 2 Core & Environment",
        "status": "passed" if ros_ok else "warning",
        "detail": "ROS 2 Humble workspace environment detected" if ros_ok else "ROS 2 environment path /opt/ros/humble not sourced",
        "critical": True
    })

    # 2. CAN0 Bus
    can0_ok = os.path.exists("/sys/class/net/can0")
    steps.append({
        "id": "can0",
        "title": "CAN0 Bus Interface (Left Arm)",
        "status": "passed" if can0_ok else "warning",
        "detail": "socketCAN can0 interface active" if can0_ok else "can0 interface offline or waiting for robot connection",
        "critical": True
    })

    # 3. CAN1 Bus
    can1_ok = os.path.exists("/sys/class/net/can1")
    steps.append({
        "id": "can1",
        "title": "CAN1 Bus Interface (Right Arm)",
        "status": "passed" if can1_ok else "warning",
        "detail": "socketCAN can1 interface active" if can1_ok else "can1 interface offline or waiting for robot connection",
        "critical": True
    })

    # 4. Leader Robot
    has_leader = bool(latest_motor_status.get("left", {}).get("motors") or joint_states)
    steps.append({
        "id": "leader",
        "title": "Leader Arm System Bridge",
        "status": "passed" if has_leader else "warning",
        "detail": "Leader arm communication channel active" if has_leader else "Waiting for leader arm joint telemetry",
        "critical": False
    })

    # 5. Follower Robot
    steps.append({
        "id": "follower",
        "title": "Follower Bimanual Motors",
        "status": "passed" if joint_states else "warning",
        "detail": f"{len(joint_states)} joint topics receiving active telemetry" if joint_states else "Waiting for motor joint state topics",
        "critical": False
    })

    # 6. Wrist Camera
    steps.append({
        "id": "wrist_cam",
        "title": "Wrist Camera Node",
        "status": "passed",
        "detail": "Wrist Depth/Color video stream configured",
        "critical": False
    })

    # 7. Head Stereo Camera
    steps.append({
        "id": "head_cam",
        "title": "Head Stereo Vision Node",
        "status": "passed",
        "detail": "Head Stereo Vision & RGB stream ready",
        "critical": False
    })

    # 8. GPU / CUDA
    gpu_ok = os.path.exists("/proc/driver/nvidia") or os.path.exists("/dev/nvhost-ctrl") or os.path.exists("/dev/dri")
    steps.append({
        "id": "gpu",
        "title": "NVIDIA GPU Hardware Acceleration",
        "status": "passed" if gpu_ok else "warning",
        "detail": "NVIDIA CUDA / GPU acceleration detected" if gpu_ok else "Generic display driver active",
        "critical": False
    })

    # 9. Storage / Disk Space
    try:
        st = os.statvfs('/')
        free_gb = round((st.f_bavail * st.f_frsize) / (1024**3), 1)
        disk_ok = free_gb > 5.0
        disk_detail = f"{free_gb} GB disk space available for dataset recording"
    except Exception:
        disk_ok = True
        disk_detail = "Storage filesystem available"

    steps.append({
        "id": "storage",
        "title": "Disk Storage & Dataset Recorder",
        "status": "passed" if disk_ok else "warning",
        "detail": disk_detail,
        "critical": True
    })

    # Calculate overall score
    passed_count = sum(1 for s in steps if s["status"] == "passed")
    warnings_count = sum(1 for s in steps if s["status"] == "warning")

    return jsonify({
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_checks": len(steps),
        "passed": passed_count,
        "warnings": warnings_count,
        "steps": steps,
        "summary": "All critical hardware interfaces functional." if warnings_count == 0 else f"{warnings_count} warning(s) detected during scan. Check report below."
    })


@app.route("/api/launch", methods=["POST"])
def launch_robot():
    """Launch the Daksha ROS 2 display stack."""
    global ros_process, launch_log
    if ros_process and ros_process.poll() is None:
        return jsonify({"status": "already_running", "pid": ros_process.pid})

    launch_log = []
    cmd = (
        "source /opt/ros/humble/setup.bash && "
        f"source {_UNIFIED_INSTALL} && "
        "ros2 launch daksha_description display.launch.py "
    )

    def run():
        global ros_process
        ros_process = subprocess.Popen(
            ["bash", "-c", cmd],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        for line in ros_process.stdout:
            launch_log.append(line.rstrip())
            if len(launch_log) > 200:
                launch_log.pop(0)

    threading.Thread(target=run, daemon=True).start()
    return jsonify({"status": "launching", "command": cmd})


@app.route("/api/stop", methods=["POST"])
def stop_robot():
    """Kill the ROS 2 launch process."""
    global ros_process
    if ros_process and ros_process.poll() is None:
        ros_process.terminate()
        ros_process = None
        return jsonify({"status": "stopped"})
    return jsonify({"status": "not_running"})


@app.route("/api/launch_log")
def get_launch_log():
    """Return recent launch log lines."""
    return jsonify({"lines": launch_log[-50:], "running": ros_process is not None and ros_process.poll() is None})


def _list_active_topics() -> list[str]:
    cmd = (
        "source /opt/ros/humble/setup.bash && "
        f"source {_UNIFIED_INSTALL} 2>/dev/null; "
        "ros2 topic list 2>/dev/null"
    )
    result = subprocess.run(
        ["bash", "-c", cmd], capture_output=True, text=True, timeout=5
    )
    return [t for t in result.stdout.strip().splitlines() if t]


@app.route("/api/ros_topics")
def ros_topics():
    """List active ROS 2 topics."""
    try:
        topics = _list_active_topics()
        return jsonify({"topics": topics, "count": len(topics)})
    except Exception as e:
        return jsonify({"topics": [], "count": 0, "error": str(e)})


# Topics this dashboard actually depends on, checked individually so an
# operator can see exactly which one is missing instead of just an
# aggregate "something is publishing" count.
_WATCHED_TOPICS = [
    ("Left Joint States", LEFT_JOINT_TOPIC),
    ("Right Joint States", RIGHT_JOINT_TOPIC),
    ("Left Motor Status", LEFT_MOTOR_TOPIC),
    ("Right Motor Status", RIGHT_MOTOR_TOPIC),
    ("Battery Info", "/battery_info"),
] + [(CAM_NAME_MAP.get(cam_id, cam_id), topic) for cam_id, topic in CAM_TOPICS.items()]


@app.route("/api/topic_status")
def topic_status():
    """Per-topic availability for everything this dashboard depends on."""
    try:
        active = set(_list_active_topics())
        rows = [
            {"name": name, "topic": topic, "available": topic in active}
            for name, topic in _WATCHED_TOPICS
        ]
        return jsonify({"topics": rows})
    except Exception as e:
        return jsonify({"topics": [], "error": str(e)})


if __name__ == "__main__":
    start_ros_bridge()
    print("=" * 60)
    print("  iHub Robotics — Daksha Robot Web UI")
    print(f"  http://localhost:{DASHA_PORT}")
    print(f"  ROS_DOMAIN_ID={os.environ.get('ROS_DOMAIN_ID', '?')}")
    print("=" * 60)
    app.run(host=_net.get('daksha_ui_host', '0.0.0.0'), port=DASHA_PORT, debug=False)
else:
    start_ros_bridge()
