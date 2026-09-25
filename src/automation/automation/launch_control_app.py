#!/usr/bin/env python3
"""
launch_control_app.py
----------------------
Small Flask control panel to launch and kill a ROS 2 launch file
(default: `ros2 launch gen2 bringup.launch.py`) from a web page instead
of a terminal.

Run (after sourcing your ROS 2 workspace):
    pip install flask
    python3 launch_control_app.py    # open http://<hostname>:8100
"""

import atexit
import collections
import logging
import os
import re
import shutil
import signal
import socket
import subprocess
import threading
import time
from datetime import datetime

import yaml
from flask import Flask, Response, abort, jsonify, render_template, request, send_file

logging.getLogger("werkzeug").setLevel(logging.WARNING)

# ROS 2 is optional at import time so this file still runs (in a degraded,
# no-motor-status mode) if launched outside a sourced ROS 2 environment.
ROS_IMPORT_ERROR = None
MOTOR_STATUS_IMPORT_ERROR = None
try:
    import rclpy
    from rclpy.node import Node
    from rclpy.executors import SingleThreadedExecutor
    from rclpy.qos import (QoSProfile, QoSReliabilityPolicy,
                           QoSDurabilityPolicy, QoSHistoryPolicy)
    from sensor_msgs.msg import JointState
    from std_msgs.msg import String, Float32
    from std_srvs.srv import Trigger
    from rcl_interfaces.srv import SetParameters, GetParameters
    from rcl_interfaces.msg import Parameter, ParameterValue, ParameterType
    ROS_AVAILABLE = True
except Exception as _e:  # pragma: no cover
    ROS_AVAILABLE = False
    ROS_IMPORT_ERROR = str(_e)
    Node = object

# Motor status (hw_interface) is a separate optional dependency, same as in
# gesture_management_app.py — the Motor Status panel just stays empty if
# it isn't available.
try:
    from hw_interface.msg import MotorStatusArray
    MOTOR_STATUS_AVAILABLE = ROS_AVAILABLE
except Exception as _e:
    MOTOR_STATUS_AVAILABLE = False
    MOTOR_STATUS_IMPORT_ERROR = str(_e)

app = Flask(__name__)

LAUNCH_PACKAGE = os.environ.get("BRINGUP_PACKAGE", "gen2")
LAUNCH_FILE = os.environ.get("BRINGUP_LAUNCH_FILE", "bringup.launch.py")
KILL_GRACE_PERIOD_S = 8.0  # how long to wait for SIGINT before SIGKILL

# Fixed topics (same names used across the rest of the workspace, e.g.
# config/daksha_ui.yaml's motor_topics section) — this panel isn't a generic
# topic picker, just a live view of the two arms while bringup is running.
LEFT_MOTOR_TOPIC = "/LeftArmSystem/motor_status"
RIGHT_MOTOR_TOPIC = "/RightArmSystem/motor_status"
# Published by gen2/arm_recovery_watchdog.py: a JointState whose name[]/
# position[] pairs are "<ArmName>_motor_<id>" -> how many times recovery
# has been triggered for that motor.
RECOVERY_COUNT_TOPIC = "/arm_recovery/recovery_counts"
# Measured joint positions for the 3D view, published by hw_interface's
# ArmHardwareInterface::read() (arm_interface.cpp). The name[] entries are
# the ros2_control joint names from gen2/config/controllers.yaml, which are
# the URDF's own joint names, so they drive the 3D model without remapping.
LEFT_JOINT_STATE_TOPIC = "/LeftArmSystem_ordered_joint_states"
RIGHT_JOINT_STATE_TOPIC = "/RightArmSystem_ordered_joint_states"

# Command topics for the dashboard's joint sliders and navigation joystick.
# Same names and units the rest of the workspace already uses: /joint_cmd is
# what daksha_api_bridge_leader's joint_cmd_api_suscriber.py listens on, and
# the /cmd_vel limits match web_nav_site's teleop so the two feel the same.
JOINT_CMD_TOPIC = "/joint_cmd"
CMD_VEL_TOPIC = "/cmd_vel"

# Shared gen2 nodes this panel drives, same ones daksha_ui and
# gesture_management use. /move_home is a std_srvs/Trigger served by
# gen2/HomeMoveService.py; the other two are plain parameters on nodes that
# bringup starts, reached through their own set_parameters services rather
# than by shelling out to `ros2 param set`.
MOVE_HOME_SERVICE = "/move_home"
MODE_TOGGLER_NODE = "/mode_toggler"
MODE_STATUS_TOPIC = "/mode_toggler/status"
LIMITER_NODE = "/joint_command_limiter"
LIMITER_PARAMS = ("max_velocity", "max_acceleration")
# gen2/teach_mode_node.py's per-motor stiffness/damping, reached the same way
# as the two nodes above -- see its normal_kp_<n>/normal_kd_<n> parameters
# (n = 1..GAIN_NUM_MOTORS). One value per motor id, not per arm:
# teach_mode_node sends the same kp/kd array to both LeftArmSystem and
# RightArmSystem (its send_gains()), so this panel's Motor Status gains
# table has 8 rows, not 16.
GAIN_NODE = "/teach_mode_node"
GAIN_NUM_MOTORS = 8
GAIN_MOTOR_IDS = list(range(1, GAIN_NUM_MOTORS + 1))
# Published by gen2/battery_info.py: a std_msgs/Float32 battery percentage
# (0-100). Not gated behind MOTOR_STATUS_AVAILABLE -- it's a plain
# std_msgs topic, not hw_interface's custom message, so it works even where
# that package isn't built.
BATTERY_TOPIC = "/battery_info"
TELEOP_MAX_LINEAR = 0.5     # m/s at full forward deflection
TELEOP_MAX_ANGULAR = 1.0    # rad/s at full sideways deflection
TELEOP_PUBLISH_HZ = 20.0
# Zero the base if the browser stops sending updates for this long — a
# dropped connection with the stick pushed forward must not keep it driving.
TELEOP_DEADMAN_S = 0.5

# ── Robot model (URDF + meshes) for the 3D view ───────────────────────────
# Resolution order: the description package's installed share/ dir (the
# ROS-idiomatic lookup, and the only one that exists on the robot) -> a
# source-tree path relative to this file, so the panel still renders a robot
# when run straight from a checkout that has never been built. The 3D view
# just stays empty if neither is there.
APP_DIR = os.path.dirname(os.path.realpath(__file__))
DESC_PACKAGE = "daksha_description_full_body"
_desc_candidates = []
try:
    from ament_index_python.packages import get_package_share_directory
    _desc_candidates.append(get_package_share_directory(DESC_PACKAGE))
except Exception:
    pass
_desc_candidates.append(os.path.abspath(os.path.join(APP_DIR, "..", "..", DESC_PACKAGE)))

DESC_PKG = next((p for p in _desc_candidates if os.path.isdir(p)), None)
ROBOT_URDF = os.path.join(DESC_PKG, "urdf", "robot.urdf") if DESC_PKG else None
ROBOT_MODEL_AVAILABLE = bool(ROBOT_URDF and os.path.isfile(ROBOT_URDF))

# ROS 2 param-style yaml (installed alongside templates/static, see
# CMakeLists.txt) listing joints whose rotation direction the 3D viewer
# should flip. This never touches the URDF or the real hardware's positive
# direction -- it only fixes which way the on-screen model spins.
VIEWER_JOINT_OVERRIDES_YAML = os.path.join(APP_DIR, "config", "viewer_joint_overrides.yaml")

# Applications table (see config/applications.yaml) for the main page and
# /ports -- kept out of this file so the port list can be edited without
# touching code.
APPLICATIONS_YAML = os.path.join(APP_DIR, "config", "applications.yaml")


def _load_port_table(path):
    if not os.path.isfile(path):
        logging.getLogger(__name__).error("Applications config not found: %s", path)
        return []
    try:
        with open(path) as f:
            doc = yaml.safe_load(f) or {}
        return list(doc.get("applications", []))
    except Exception:
        logging.getLogger(__name__).exception("Could not read %s", path)
        return []


def _load_viewer_joint_overrides(path):
    if not os.path.isfile(path):
        return []
    try:
        with open(path) as f:
            doc = yaml.safe_load(f) or {}
        for node_params in doc.values():
            joints = (node_params or {}).get("ros__parameters", {}).get(
                "viewer_joint_axis_overrides")
            if joints:
                return list(joints)
    except Exception:
        logging.getLogger(__name__).exception(
            "Could not read %s", path)
    return []


def _parse_motor_joint_map(urdf_path):
    """URDF joint name -> {"arm": <ros2_control name>, "id": <motor id>}.

    Read from the URDF's own <ros2_control> blocks rather than assumed: the
    <param name="motor_ids"> list is positional against the <joint> elements
    in the same block, which is exactly how hw_interface pairs them
    (arm_interface.cpp walks motor_ids_[i] alongside info_.joints[i]). A
    guess of "motor N drives joint_N" holds for the seven arm joints and
    then puts the gripper's motor 8 on a joint that doesn't exist.

    The hover readout on the 3D view is the only thing that needs this, so a
    URDF it can't parse costs the tooltip its motor rows, nothing more.
    """
    mapping = {}
    if not urdf_path or not os.path.isfile(urdf_path):
        return mapping
    try:
        import xml.etree.ElementTree as ET
        root = ET.parse(urdf_path).getroot()
        for block in root.iter("ros2_control"):
            arm = block.get("name")
            ids = None
            for param in block.findall("./hardware/param"):
                if param.get("name") == "motor_ids" and param.text:
                    ids = [p.strip() for p in param.text.split(",")]
            if not arm or not ids:
                continue
            for motor_id, joint in zip(ids, block.findall("joint")):
                name = joint.get("name")
                if not name:
                    continue
                try:
                    mapping[name] = {"arm": arm, "id": int(motor_id)}
                except ValueError:
                    continue
    except Exception as e:
        log_event(f"Could not read motor/joint mapping from the URDF: {e}", level="warn")
    return mapping


def _parse_joint_limits(urdf_path):
    """URDF joint name -> {"type", "lower", "upper"} for every actuated joint.

    These bound the sliders in the UI and, more importantly, clamp what this
    panel will publish: a position command outside a joint's limit is the
    kind of thing that drives an arm into itself.
    """
    limits = {}
    if not urdf_path or not os.path.isfile(urdf_path):
        return limits
    try:
        import xml.etree.ElementTree as ET
        root = ET.parse(urdf_path).getroot()
        for joint in root.findall("joint"):
            jtype = joint.get("type")
            if jtype not in ("revolute", "prismatic"):
                continue
            limit = joint.find("limit")
            if limit is None:
                continue
            name = joint.get("name")
            mimic = joint.find("mimic")
            try:
                limits[name] = {
                    "type": jtype,
                    "lower": float(limit.get("lower", 0.0)),
                    "upper": float(limit.get("upper", 0.0)),
                    # A mimic joint is driven by its target, not commanded on
                    # its own, so the UI shows no slider for it.
                    "mimic": mimic.get("joint") if mimic is not None else None,
                }
            except (TypeError, ValueError):
                continue
    except Exception as e:
        log_event(f"Could not read joint limits from the URDF: {e}", level="warn")
    return limits


# Built on first use rather than at import: both helpers log through
# log_event(), which is defined further down this file.
_robot_meta = {}


def robot_meta():
    """{"motors": ..., "limits": ...} parsed from the URDF, cached."""
    if not _robot_meta:
        _robot_meta["motors"] = _parse_motor_joint_map(ROBOT_URDF)
        _robot_meta["limits"] = _parse_joint_limits(ROBOT_URDF)
    return _robot_meta

# Reference data for the Applications list on the main page (and the
# standalone /ports page) — the workspace's 8100-8199 port
# consolidation (see port_report.pdf in this same directory and
# config/applications.yaml, which is the actual source of this table).
# "kind" drives whether the UI renders a clickable link: "http" gets one,
# "tcp"/"udp" sockets and "reserved" (declared in config but not actually
# bound by any script yet) are shown as plain badges instead, since a link
# there would just fail to load.
PORT_TABLE = _load_port_table(APPLICATIONS_YAML)
_ENTRIES_BY_PORT = {entry["port"]: entry for entry in PORT_TABLE}

# This panel's own port. Stopping or restarting it would kill the process
# serving the page, so both are refused for this one row.
SELF_PORT = 8100

# Per-app process control for the Applications table. Key is the port, value
# is the argv this panel runs to bring that service up on its own -- built
# from each entry's "command" in config/applications.yaml (always a
# `ros2 run`/`ros2 launch` argv there, never a raw `python3 script.py`, so
# Start brings a service up the same way an operator would by hand).
#
# A port missing a "command" in that file is status-only here: its row still
# shows Running / Not Running and the Open link, but Start and Restart stay
# disabled. Stop works regardless, since that only needs the PID holding the
# port.
#
# Most of these services are normally started as children of the bringup
# launch, so a command here should match what the launch file already uses.
# Otherwise starting one from this table gives you a second copy of a node
# that is already running - the same duplicate-broadcaster problem that
# endpoint.launch.py warns about for quest_tf (see the per-port notes in
# config/applications.yaml).
APP_COMMANDS = {
    entry["port"]: entry["command"]
    for entry in PORT_TABLE
    if entry.get("command")
}

# Processes this panel started itself, port -> Popen. Used to reap them and
# to keep their output in the launch log; a service that was already running
# when the panel started is not in here, and is controlled by PID instead.
_app_procs = {}
_app_proc_lock = threading.Lock()

PORT_SCAN_TTL_S = 1.0
_port_scan_lock = threading.Lock()
_port_scan = {"at": 0.0, "map": {}}


def _scan_listening_ports():
    """port -> owning pid (or None) for every listening socket on this host.

    One `ss` call covers the whole table. Probing thirteen ports individually
    with connect() would be slower and blind to the PID, which stop_app()
    needs, and would miss the UDP row entirely.
    """
    try:
        out = subprocess.run(
            ["ss", "-lntupH"], capture_output=True, text=True, timeout=3.0,
        ).stdout
    except Exception:
        return _probe_ports_fallback()

    found = {}
    for line in out.splitlines():
        parts = line.split()
        if len(parts) < 5:
            continue
        local = parts[4]
        try:
            port = int(local.rsplit(":", 1)[-1])
        except ValueError:
            continue
        pid_match = re.search(r"pid=(\d+)", line)
        pid = int(pid_match.group(1)) if pid_match else None
        # Keep the first PID seen: a service bound on both :: and 0.0.0.0
        # shows up twice and they are the same process.
        found.setdefault(port, pid)
    return found


def _probe_ports_fallback():
    """Used only where `ss` is unavailable. TCP connect per port, no PIDs."""
    found = {}
    for entry in PORT_TABLE:
        if entry["kind"] in ("udp", "process"):
            continue
        s = socket.socket()
        s.settimeout(0.15)
        try:
            if s.connect_ex(("127.0.0.1", entry["port"])) == 0:
                found[entry["port"]] = None
        except OSError:
            pass
        finally:
            s.close()
    return found


def listening_ports(force=False):
    """Cached view of _scan_listening_ports(); the table polls once a second
    per client and the scan shells out, so repeat callers share one result."""
    if not force:
        with _port_scan_lock:
            if time.time() - _port_scan["at"] < PORT_SCAN_TTL_S:
                return _port_scan["map"]

    scanned = _scan_listening_ports()
    with _port_scan_lock:
        _port_scan["at"] = time.time()
        _port_scan["map"] = scanned
    return scanned


def _process_pid(match, timeout_s=3.0):
    """PID of the first process whose command line matches this `pgrep -f`
    pattern, or None. Used for table rows that have no port of their own to
    scan -- background ROS nodes like battery_info / arm_recovery_watchdog
    (config/applications.yaml's "match" field, in place of a real "port")."""
    try:
        result = subprocess.run(
            ["pgrep", "-f", match], capture_output=True, text=True, timeout=timeout_s,
        )
        if result.returncode == 0 and result.stdout.strip():
            return int(result.stdout.split()[0])
    except Exception:
        pass
    return None


def _scan_process_matches():
    """The _scan_listening_ports() equivalent for "match"-tracked rows."""
    found = {}
    for entry in PORT_TABLE:
        match = entry.get("match")
        if not match:
            continue
        pid = _process_pid(match)
        if pid is not None:
            found[entry["port"]] = pid
    return found


def live_map(force=False):
    """port -> owning pid for every Applications-table row, combining the
    listening-socket scan (networked services) with the process-match scan
    (port-less background nodes). Callers that used to read
    listening_ports() directly for this table now read this instead, so a
    "match" row behaves exactly like a "port" one everywhere: Running
    status, Start's already-running check, Stop, Restart."""
    merged = dict(listening_ports(force=force))
    merged.update(_scan_process_matches())
    return merged


def app_list():
    live = live_map()
    apps = []
    for index, entry in enumerate(PORT_TABLE, start=1):
        port = entry["port"]
        apps.append({
            "index": index,
            "port": port,
            "service": entry["service"],
            "file": entry["file"],
            "kind": entry["kind"],
            "running": port in live,
            "pid": live.get(port),
            "is_self": port == SELF_PORT,
            # Whether Start/Restart can do anything for this row.
            "startable": port in APP_COMMANDS and port != SELF_PORT,
        })
    return apps


def _app_reader_thread(port, proc):
    for line in iter(proc.stdout.readline, ""):
        if not line:
            break
        log_event(f"[{port}] {line.rstrip()}")
    proc.stdout.close()
    code = proc.wait()

    with _app_proc_lock:
        if _app_procs.get(port) is proc:
            del _app_procs[port]

    log_event(f"[{port}] exited (code {code})", level="info" if code == 0 else "error")


def start_app(port):
    command = APP_COMMANDS.get(port)
    if not command:
        return False, f"No start command configured for port {port}."
    if port == SELF_PORT:
        return False, "Refusing to start a second launch-control panel."
    if port in live_map(force=True):
        return False, f"Port {port} is already in use."

    try:
        proc = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            # Own session, same as the bringup: lets stop_app() signal the
            # whole tree rather than just the parent.
            preexec_fn=os.setsid,
        )
    except Exception as e:
        log_event(f"[{port}] failed to start: {e}", level="error")
        return False, f"Failed to start: {e}"

    with _app_proc_lock:
        _app_procs[port] = proc

    threading.Thread(target=_app_reader_thread, args=(port, proc), daemon=True).start()
    log_event(f"[{port}] started: {' '.join(command)} (pid {proc.pid})")
    return True, f"Started {' '.join(command)} (pid {proc.pid})."


def stop_app(port):
    if port == SELF_PORT:
        return False, "Refusing to stop the launch-control panel itself."

    # A "match"-tracked row (see live_map()) has no port to listen on, so its
    # not-found message shouldn't talk about one.
    owner = "the process" if _ENTRIES_BY_PORT.get(port, {}).get("match") else f"port {port}"

    live = live_map(force=True)
    if port not in live:
        return False, f"Nothing found for {owner}."

    pid = live[port]
    if pid is None:
        return False, f"Could not determine which process owns {owner}."

    try:
        pgid = os.getpgid(pid)
    except ProcessLookupError:
        return False, f"Process {pid} is already gone."

    # preexec_fn=os.setsid in start_app()/start_bringup() makes this safe for
    # anything this panel started itself. For a row this panel didn't start
    # (e.g. a bringup-managed node found via live_map()), killpg hits
    # whatever process group that pid actually belongs to -- if that's a
    # shared group (the whole `ros2 launch` tree), this stops more than just
    # this row. True today for ports 8102/8110 as well; nothing new here.
    log_event(f"[{port}] stopping pid {pid}...")
    try:
        os.killpg(pgid, signal.SIGTERM)
    except ProcessLookupError:
        pass

    def _force_kill_if_stuck():
        deadline = time.time() + KILL_GRACE_PERIOD_S
        while time.time() < deadline:
            if port not in live_map(force=True):
                return
            time.sleep(0.3)
        log_event(f"[{port}] did not stop gracefully, forcing SIGKILL", level="warn")
        try:
            os.killpg(pgid, signal.SIGKILL)
        except ProcessLookupError:
            pass

    threading.Thread(target=_force_kill_if_stuck, daemon=True).start()
    return True, f"Stopping {owner} (pid {pid})..."


def restart_app(port):
    if port not in APP_COMMANDS:
        return False, f"No start command configured for port {port}, cannot restart."

    if port in live_map(force=True):
        ok, message = stop_app(port)
        if not ok:
            return False, message

        # Wait for the port to actually come free; starting into a still-bound
        # port just fails with EADDRINUSE and leaves the service down.
        deadline = time.time() + KILL_GRACE_PERIOD_S + 2.0
        while time.time() < deadline:
            if port not in live_map(force=True):
                break
            time.sleep(0.3)
        else:
            return False, f"Port {port} never came free, not restarting."

    return start_app(port)

# System monitor (tegrastats) -- merged in from the standalone
# soc_monitoring.py so CPU/GPU/RAM/power/temp show up on this same panel
# instead of a separate port. Jetson-only, so it just stays "unavailable"
# on any machine without a tegrastats binary.
TEGRASTATS_AVAILABLE = shutil.which("tegrastats") is not None

soc_lock = threading.Lock()
soc_stats = {
    "cpu": [], "gpu": 0,
    "ram_used": 0, "ram_total": 0,
    "swap_used": 0, "swap_total": 0,
    "cpu_temp": 0.0, "soc_temp": 0.0,
    "power_gpu": 0, "power_cpu": 0, "power_system": 0,
}


def parse_tegrastats(line):
    stats = {
        "cpu": [], "gpu": 0,
        "ram_used": 0, "ram_total": 0,
        "swap_used": 0, "swap_total": 0,
        "cpu_temp": 0.0, "soc_temp": 0.0,
        "power_gpu": 0, "power_cpu": 0, "power_system": 0,
    }

    m = re.search(r"RAM\s+(\d+)/(\d+)MB", line)
    if m:
        stats["ram_used"] = int(m.group(1))
        stats["ram_total"] = int(m.group(2))

    m = re.search(r"SWAP\s+(\d+)/(\d+)MB", line)
    if m:
        stats["swap_used"] = int(m.group(1))
        stats["swap_total"] = int(m.group(2))

    m = re.search(r"CPU\s+\[(.*?)\]", line)
    if m:
        cores = []
        for item in m.group(1).split(","):
            item = item.strip()
            if item == "off":
                cores.append({"usage": 0, "freq": 0, "off": True})
            else:
                cm = re.search(r"(\d+)%@(\d+)", item)
                if cm:
                    cores.append({"usage": int(cm.group(1)), "freq": int(cm.group(2)), "off": False})
        stats["cpu"] = cores

    m = re.search(r"GR3D_FREQ\s+(\d+)%", line)
    if m:
        stats["gpu"] = int(m.group(1))

    m = re.search(r"cpu@([\d.]+)C", line)
    if m:
        stats["cpu_temp"] = float(m.group(1))

    m = re.search(r"soc0@([\d.]+)C", line)
    if m:
        stats["soc_temp"] = float(m.group(1))

    m = re.search(r"VDD_GPU_SOC\s+(\d+)mW", line)
    if m:
        stats["power_gpu"] = int(m.group(1))

    m = re.search(r"VDD_CPU_CV\s+(\d+)mW", line)
    if m:
        stats["power_cpu"] = int(m.group(1))

    m = re.search(r"VIN_SYS_5V0\s+(\d+)mW", line)
    if m:
        stats["power_system"] = int(m.group(1))

    return stats


def _soc_monitor_thread():
    global soc_stats
    while True:
        try:
            proc = subprocess.Popen(
                ["tegrastats", "--interval", "1000"],
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                text=True, bufsize=1,
            )
            for line in proc.stdout:
                parsed = parse_tegrastats(line)
                with soc_lock:
                    soc_stats = parsed
        except Exception as e:
            log_event(f"tegrastats error: {e}", level="error")
            time.sleep(2)


state_node = None  # set in main() if ROS 2 is available


# ── Parameter / service call helpers ──────────────────────────────────────
# These block on the future rather than spinning it: the executor spins in
# its own thread (see main()), and these run on Flask request threads, so
# waiting here never starves the spin that completes the call.

def _param_value_for(value):
    """An rcl_interfaces ParameterValue matching a Python value's type."""
    if isinstance(value, bool):
        return ParameterValue(type=ParameterType.PARAMETER_BOOL, bool_value=value)
    if isinstance(value, int):
        return ParameterValue(type=ParameterType.PARAMETER_INTEGER, integer_value=value)
    if isinstance(value, float):
        return ParameterValue(type=ParameterType.PARAMETER_DOUBLE, double_value=value)
    return ParameterValue(type=ParameterType.PARAMETER_STRING, string_value=str(value))


def _await(future, timeout_s):
    deadline = time.monotonic() + timeout_s
    while not future.done():
        if time.monotonic() > deadline:
            return None, "call timed out"
        time.sleep(0.01)
    if future.exception() is not None:
        return None, f"call raised: {future.exception()}"
    return future.result(), None


def _call_set_parameters(client, name, value, timeout_s=5.0):
    if client is None:
        return False, "ROS 2 is not available"
    if not client.service_is_ready() and not client.wait_for_service(timeout_sec=min(timeout_s, 2.0)):
        return False, "node is not running (set_parameters unavailable)"
    request = SetParameters.Request(
        parameters=[Parameter(name=name, value=_param_value_for(value))])
    result, err = _await(client.call_async(request), timeout_s)
    if err:
        return False, err
    results = result.results
    if not results or not results[0].successful:
        return False, f"rejected: {results[0].reason if results else 'no result'}"
    return True, None


def _call_get_parameters(client, name, timeout_s=1.5):
    """The parameter's value, or None if the node isn't up or isn't numeric."""
    if client is None:
        return None
    if not client.service_is_ready() and not client.wait_for_service(timeout_sec=min(timeout_s, 1.0)):
        return None
    result, err = _await(client.call_async(GetParameters.Request(names=[name])), timeout_s)
    if err or not result.values:
        return None
    value = result.values[0]
    if value.type == ParameterType.PARAMETER_DOUBLE:
        return value.double_value
    if value.type == ParameterType.PARAMETER_INTEGER:
        return float(value.integer_value)
    return None


def _call_get_parameters_batch(client, names, timeout_s=1.5):
    """{name: value} for every name that resolved to a number -- one
    GetParameters call for the whole list instead of one per name, same
    reasoning as _scan_listening_ports() batching the port table into a
    single `ss` call. A name missing from the result means the node isn't
    up or doesn't have that parameter."""
    if client is None:
        return {}
    if not client.service_is_ready() and not client.wait_for_service(timeout_sec=min(timeout_s, 1.0)):
        return {}
    result, err = _await(client.call_async(GetParameters.Request(names=names)), timeout_s)
    if err or not result.values:
        return {}
    out = {}
    for name, value in zip(names, result.values):
        if value.type == ParameterType.PARAMETER_DOUBLE:
            out[name] = value.double_value
        elif value.type == ParameterType.PARAMETER_INTEGER:
            out[name] = float(value.integer_value)
    return out


class RobotStateNode(Node):
    """Caches the latest motor status, recovery counts and joint positions so
    the web UI can poll them over HTTP without touching rclpy.

    Motor status needs hw_interface's custom message; joint states only need
    sensor_msgs, so the two sets of subscriptions are independent — the 3D
    view still animates on a machine where hw_interface isn't built."""

    def __init__(self):
        super().__init__("automation_robot_state")
        self._lock = threading.Lock()
        self._latest = {"left": [], "right": []}
        self._recovery_counts = {}
        self._joint_positions = {}
        self._joint_efforts = {}
        self._joint_stamp = 0.0
        self._battery = {"percent": None, "stamp": 0.0}

        self.create_subscription(Float32, BATTERY_TOPIC, self._battery_cb, 10)

        if MOTOR_STATUS_AVAILABLE:
            self.create_subscription(
                MotorStatusArray, LEFT_MOTOR_TOPIC,
                lambda msg: self._cb("left", msg), 10,
            )
            self.create_subscription(
                MotorStatusArray, RIGHT_MOTOR_TOPIC,
                lambda msg: self._cb("right", msg), 10,
            )
            self.create_subscription(
                JointState, RECOVERY_COUNT_TOPIC, self._recovery_cb, 10,
            )

        for topic in (LEFT_JOINT_STATE_TOPIC, RIGHT_JOINT_STATE_TOPIC):
            self.create_subscription(JointState, topic, self._joint_cb, 10)

        # ── Command side ───────────────────────────────────────────────
        # Both publishers are created up front but publish nothing until the
        # operator arms the matching control in the UI.
        self._joint_cmd_pub = self.create_publisher(JointState, JOINT_CMD_TOPIC, 10)

        self._teleop_lock = threading.Lock()
        self._teleop = {"enabled": False, "linear": 0.0, "angular": 0.0, "at": 0.0}
        self._cmd_vel_pub = None
        try:
            from geometry_msgs.msg import Twist
            self._Twist = Twist
            self._cmd_vel_pub = self.create_publisher(Twist, CMD_VEL_TOPIC, 10)
            self.create_timer(1.0 / TELEOP_PUBLISH_HZ, self._teleop_tick)
        except Exception as e:
            log_event(f"Navigation joystick disabled (no geometry_msgs: {e})", level="warn")

        # ── Shared gen2 nodes ──────────────────────────────────────────
        # Clients are cheap to create against a node that isn't up yet; each
        # call checks readiness, so these simply report "not running" until
        # bringup starts them.
        self.move_home_client = self.create_client(Trigger, MOVE_HOME_SERVICE)
        self.mode_set_client = self.create_client(
            SetParameters, f"{MODE_TOGGLER_NODE}/set_parameters")
        self.limiter_set_client = self.create_client(
            SetParameters, f"{LIMITER_NODE}/set_parameters")
        self.limiter_get_client = self.create_client(
            GetParameters, f"{LIMITER_NODE}/get_parameters")
        self.gain_set_client = self.create_client(
            SetParameters, f"{GAIN_NODE}/set_parameters")
        self.gain_get_client = self.create_client(
            GetParameters, f"{GAIN_NODE}/get_parameters")

        self._mode = "unknown"
        # Transient-local, to match mode_toggler's own status publisher: it
        # publishes only on a transition, so a subscriber that connects later
        # would otherwise wait indefinitely for a mode change that may never
        # come.
        self.create_subscription(
            String, MODE_STATUS_TOPIC, self._mode_cb,
            QoSProfile(depth=1,
                       reliability=QoSReliabilityPolicy.RELIABLE,
                       durability=QoSDurabilityPolicy.TRANSIENT_LOCAL,
                       history=QoSHistoryPolicy.KEEP_LAST),
        )

    def _mode_cb(self, msg):
        with self._lock:
            self._mode = str(msg.data)

    def get_mode(self):
        with self._lock:
            return self._mode

    def call_move_home(self, timeout_s=20.0, mode_timeout_s=10.0):
        """Trigger /move_home. The service itself refuses until it has seen
        both arms' joint states, so a 'not running' here means bringup is
        down, not that the pose was rejected.

        The service blocks for ~16.7s (500 steps @ 30Hz) before responding,
        so timeout_s must stay comfortably above that.

        In teach mode the arms run with zeroed gains, so a home trajectory
        commanded there wouldn't actually be followed. Force the robot into
        normal mode first and wait for mode_toggler to confirm the settled
        state (not just accept the parameter) before triggering the move."""
        client = self.move_home_client
        if not client.service_is_ready() and not client.wait_for_service(timeout_sec=2.0):
            return False, f"{MOVE_HOME_SERVICE} is not available (is bringup running?)"

        if self.get_mode() != "normal":
            ok, err = _call_set_parameters(self.mode_set_client, "mode", "normal")
            if not ok:
                return False, f"failed to switch to normal mode: {err}"
            deadline = time.monotonic() + mode_timeout_s
            while self.get_mode() != "normal":
                if time.monotonic() > deadline:
                    return False, "timed out waiting for normal mode before move home"
                time.sleep(0.05)
        result, err = _await(client.call_async(Trigger.Request()), timeout_s)
        if err:
            return False, err
        return bool(result.success), result.message or ""

    def _cb(self, side, msg):
        data = [{
            "arm_name": m.arm_name, "id": m.id, "error": m.error,
            "error_name": m.error_name,
            "mos_temp": round(float(m.mos_temp), 1),
            "rotor_temp": round(float(m.rotor_temp), 1),
        } for m in msg.motors]
        with self._lock:
            self._latest[side] = data

    def _recovery_cb(self, msg):
        counts = {name: int(pos) for name, pos in zip(msg.name, msg.position)}
        with self._lock:
            self._recovery_counts = counts

    def _battery_cb(self, msg):
        with self._lock:
            self._battery = {"percent": round(float(msg.data), 1), "stamp": time.time()}

    def _joint_cb(self, msg):
        # One dict for both arms: the two topics carry disjoint joint names,
        # so merging them is what gives the viewer a whole-robot pose.
        updates, efforts = {}, {}
        for i, (name, position) in enumerate(zip(msg.name, msg.position)):
            try:
                updates[str(name)] = round(float(position), 6)
            except (TypeError, ValueError):
                continue
            # effort[] is optional in JointState and hw_interface fills it
            # with the motor's measured torque, which the hover readout shows.
            if i < len(msg.effort):
                try:
                    efforts[str(name)] = round(float(msg.effort[i]), 4)
                except (TypeError, ValueError):
                    pass
        if not updates:
            return
        with self._lock:
            self._joint_positions.update(updates)
            self._joint_efforts.update(efforts)
            self._joint_stamp = time.time()

    def get_status(self):
        with self._lock:
            return {k: list(v) for k, v in self._latest.items()}

    def get_recovery_counts(self):
        with self._lock:
            return dict(self._recovery_counts)

    def get_battery(self):
        with self._lock:
            return dict(self._battery)

    def get_joint_positions(self):
        with self._lock:
            return dict(self._joint_positions), dict(self._joint_efforts), self._joint_stamp

    # ── Commands ───────────────────────────────────────────────────────
    def publish_joint_cmd(self, name, position):
        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.name = [name]
        msg.position = [float(position)]
        self._joint_cmd_pub.publish(msg)

    def set_teleop(self, linear=None, angular=None, enabled=None):
        with self._teleop_lock:
            if enabled is not None:
                self._teleop["enabled"] = bool(enabled)
                # Centre the stick on arm as well as disarm. Disarming alone
                # is not enough: a deflection POST already in flight lands
                # afterwards, and arming again inside the deadman window
                # would then drive the base with it.
                self._teleop["linear"] = self._teleop["angular"] = 0.0
            elif self._teleop["enabled"]:
                # Deflection sent while disarmed is dropped, not stored.
                if linear is not None:
                    self._teleop["linear"] = float(linear)
                if angular is not None:
                    self._teleop["angular"] = float(angular)
            self._teleop["at"] = time.time()
            return dict(self._teleop)

    def get_teleop(self):
        with self._teleop_lock:
            return dict(self._teleop)

    def _teleop_tick(self):
        """Republish the stick at a fixed rate while armed.

        A base that is driving needs a steady stream of /cmd_vel, and it must
        stop on its own if the browser goes away mid-drive — a dropped wifi
        link with the stick pushed forward is the failure that matters here.
        Anything older than TELEOP_DEADMAN_S publishes as a zero Twist.
        """
        if self._cmd_vel_pub is None:
            return
        with self._teleop_lock:
            state = dict(self._teleop)
        if not state["enabled"]:
            return

        msg = self._Twist()
        if time.time() - state["at"] <= TELEOP_DEADMAN_S:
            msg.linear.x = state["linear"]
            msg.angular.z = state["angular"]
        self._cmd_vel_pub.publish(msg)

_lock = threading.Lock()
_proc = None        # subprocess.Popen of `ros2 launch`, or None
_started_at = None  # time.time() when it was launched

_log_lock = threading.Lock()
_log_seq = 0
_log_entries = collections.deque(maxlen=1000)


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


def _reader_thread(proc):
    """Streams the launch process's combined stdout/stderr into the log,
    then reclaims _proc once it exits (whether we killed it or it died on
    its own) so status/launch reflect reality."""
    for line in iter(proc.stdout.readline, ""):
        if not line:
            break
        log_event(line.rstrip("\n"))
    proc.stdout.close()

    return_code = proc.wait()

    global _proc, _started_at
    with _lock:
        if _proc is proc:
            _proc = None
            _started_at = None

    log_event(
        f"{LAUNCH_PACKAGE} {LAUNCH_FILE} exited (code {return_code})",
        level="info" if return_code == 0 else "error",
    )


def start_bringup():
    global _proc, _started_at
    with _lock:
        if _proc is not None and _proc.poll() is None:
            return False, "bringup is already running."

        try:
            proc = subprocess.Popen(
                ["ros2", "launch", LAUNCH_PACKAGE, LAUNCH_FILE],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                # New process group/session: `ros2 launch` spawns one child
                # process per node it brings up, and killing just the
                # `ros2 launch` PID leaves all of those running. Putting it
                # in its own group lets kill_bringup() signal the whole
                # tree at once, the same way a terminal's Ctrl+C does.
                preexec_fn=os.setsid,
            )
        except Exception as e:
            log_event(f"failed to launch: {e}", level="error")
            return False, f"Failed to launch: {e}"

        _proc = proc
        _started_at = time.time()

    threading.Thread(target=_reader_thread, args=(proc,), daemon=True).start()
    log_event(f"Launching {LAUNCH_PACKAGE} {LAUNCH_FILE} (pid {proc.pid})")
    return True, f"Launched {LAUNCH_PACKAGE} {LAUNCH_FILE} (pid {proc.pid})."


def kill_bringup():
    with _lock:
        proc = _proc
        if proc is None or proc.poll() is not None:
            return False, "bringup is not running."
        pgid = os.getpgid(proc.pid)

    log_event(f"Stopping {LAUNCH_PACKAGE} {LAUNCH_FILE} (pid {proc.pid})...")
    try:
        # SIGINT, not SIGTERM/SIGKILL: this is what `ros2 launch` catches to
        # cleanly shut down every node it started, same as Ctrl+C.
        os.killpg(pgid, signal.SIGINT)
    except ProcessLookupError:
        pass

    def _force_kill_if_stuck():
        deadline = time.time() + KILL_GRACE_PERIOD_S
        while time.time() < deadline:
            if proc.poll() is not None:
                return
            time.sleep(0.2)
        if proc.poll() is None:
            log_event("bringup did not stop gracefully, forcing SIGKILL", level="warn")
            try:
                os.killpg(pgid, signal.SIGKILL)
            except ProcessLookupError:
                pass

    threading.Thread(target=_force_kill_if_stuck, daemon=True).start()
    return True, "Stopping bringup..."


def _bringup_already_running() -> bool:
    """True if a `ros2 launch <package> <launch_file>` process already
    exists on this machine, regardless of whether *this* Flask process is
    the one tracking it. Needed because the bringup child tree survives
    independently of this process (preexec_fn=os.setsid in start_bringup()):
    after a systemd restart of this panel (Restart=always), `_proc` resets
    to None even though an orphaned bringup may still be running from
    before the crash. Checking the OS instead of our own in-memory state is
    what lets auto-launch-on-startup below stay safe."""
    try:
        result = subprocess.run(
            ["pgrep", "-f", f"ros2 launch {LAUNCH_PACKAGE} {LAUNCH_FILE}"],
            capture_output=True, text=True, timeout=3.0,
        )
        return result.returncode == 0 and bool(result.stdout.strip())
    except Exception:
        return False


def get_status():
    with _lock:
        proc = _proc
        started_at = _started_at
    running = proc is not None and proc.poll() is None
    return {
        "running": running,
        "pid": proc.pid if running else None,
        "uptime_s": round(time.time() - started_at, 1) if running and started_at else 0.0,
        "package": LAUNCH_PACKAGE,
        "launch_file": LAUNCH_FILE,
    }


@atexit.register
def _cleanup_on_exit():
    """Don't leave an orphaned `ros2 launch` tree running if this Flask
    process itself is stopped while bringup is still up."""
    with _lock:
        proc = _proc
    if proc is not None and proc.poll() is None:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGINT)
        except ProcessLookupError:
            pass


@app.after_request
def _allow_cross_origin_api(resp):
    """Lets the E-STOP button on every other UI (each on its own port)
    call /api/kill on this one from the browser."""
    if request.path.startswith("/api/"):
        resp.headers["Access-Control-Allow-Origin"] = "*"
        resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return resp


@app.route("/")
def home():
    return render_template(
        "index.html",
        package=LAUNCH_PACKAGE,
        launch_file=LAUNCH_FILE,
        ports=PORT_TABLE,
        ros_distro=os.environ.get("ROS_DISTRO", "—").title(),
        self_port=SELF_PORT,
        kill_grace=KILL_GRACE_PERIOD_S,
        tegrastats=TEGRASTATS_AVAILABLE,
        motor_status=MOTOR_STATUS_AVAILABLE,
        robot_model=ROBOT_MODEL_AVAILABLE,
        desc_package=DESC_PACKAGE,
    )


@app.route("/ports")
def ports():
    return render_template("ports.html", ports=PORT_TABLE)


@app.route("/api/status")
def api_status():
    return jsonify(get_status())


@app.route("/api/launch", methods=["POST"])
def api_launch():
    ok, msg = start_bringup()
    return jsonify({"success": ok, "message": msg}), (200 if ok else 409)


@app.route("/api/kill", methods=["POST"])
def api_kill():
    ok, msg = kill_bringup()
    return jsonify({"success": ok, "message": msg}), (200 if ok else 409)


@app.route("/api/apps")
def api_apps():
    return jsonify({"apps": app_list()})


@app.route("/api/app/<int:port>/<action>", methods=["POST"])
def api_app_action(port, action):
    if port not in {entry["port"] for entry in PORT_TABLE}:
        return jsonify({"success": False, "message": f"Unknown port {port}."}), 404

    handler = {"start": start_app, "stop": stop_app, "restart": restart_app}.get(action)
    if handler is None:
        return jsonify({"success": False, "message": f"Unknown action '{action}'."}), 400

    ok, message = handler(port)
    return jsonify({"success": ok, "message": message}), (200 if ok else 409)


@app.route("/api/logs")
def api_logs():
    since = request.args.get("since", 0, type=int)
    with _log_lock:
        entries = [e for e in _log_entries if e["id"] > since]
    return jsonify({"logs": entries})


@app.route("/api/motor_status")
def api_motor_status():
    status = state_node.get_status() if state_node else {"left": [], "right": []}
    return jsonify({"status": status, "available": MOTOR_STATUS_AVAILABLE})


@app.route("/api/recovery_counts")
def api_recovery_counts():
    counts = state_node.get_recovery_counts() if state_node else {}
    return jsonify({"counts": counts, "available": MOTOR_STATUS_AVAILABLE})


@app.route("/api/battery")
def api_battery():
    """Latest reading off /battery_info (std_msgs/Float32, 0-100). `percent`
    is None until the first message arrives -- battery_info.py is one of
    bringup's currently-commented-out nodes, so that's the common case."""
    battery = state_node.get_battery() if state_node else {"percent": None, "stamp": 0.0}
    age_s = round(time.time() - battery["stamp"], 1) if battery["stamp"] else None
    return jsonify({"percent": battery["percent"], "age_s": age_s})


@app.route("/api/joint_states")
def api_joint_states():
    """Everything the 3D view needs each tick: measured joint positions
    (rad/m), measured torques, and the motor behind each joint.

    `age_s` lets the page tell a live pose from the last one a since-stopped
    bringup left behind, without having to track message arrival itself.
    The motor rows ride along here rather than on their own endpoint so the
    hover readout can never show one joint's angle beside another's
    temperature."""
    if state_node is None:
        return jsonify({
            "positions": {}, "efforts": {}, "motors": {},
            "available": False, "age_s": None,
        })

    positions, efforts, stamp = state_node.get_joint_positions()
    status = state_node.get_status()
    recoveries = state_node.get_recovery_counts()

    # (arm_name, id) -> motor row, to join against the URDF's own mapping.
    by_motor = {}
    for motors in status.values():
        for motor in motors:
            by_motor[(motor["arm_name"], motor["id"])] = motor

    motors = {}
    for joint, ref in robot_meta()["motors"].items():
        motor = by_motor.get((ref["arm"], ref["id"]))
        motors[joint] = {
            "arm": ref["arm"],
            "id": ref["id"],
            "error": motor["error"] if motor else None,
            "error_name": motor["error_name"] if motor else None,
            "mos_temp": motor["mos_temp"] if motor else None,
            "rotor_temp": motor["rotor_temp"] if motor else None,
            "recoveries": recoveries.get(f"{ref['arm']}_motor_{ref['id']}", 0),
        }

    return jsonify({
        "positions": positions,
        "efforts": efforts,
        "motors": motors,
        "available": True,
        "age_s": round(time.time() - stamp, 2) if stamp else None,
    })


@app.route("/api/robot_joints")
def api_robot_joints():
    """The commandable joints, with their URDF limits — what the joint-control
    sliders are built from. Mimic joints are left out: they follow their
    target rather than taking a command of their own."""
    meta = robot_meta()
    joints = [
        {
            "name": name,
            "type": limit["type"],
            "lower": limit["lower"],
            "upper": limit["upper"],
            "motor": meta["motors"].get(name),
        }
        for name, limit in meta["limits"].items()
        if not limit["mimic"]
    ]
    joints.sort(key=lambda j: j["name"])
    return jsonify({"joints": joints, "available": ROBOT_MODEL_AVAILABLE})


@app.route("/api/joint_cmd", methods=["POST"])
def api_joint_cmd():
    """Publish one joint-position command to /joint_cmd.

    The UI keeps its sliders disabled until the operator arms them, but the
    clamp below is what actually guarantees this panel cannot command a joint
    past its URDF limit — a caller that skips the UI is bounded too."""
    if state_node is None:
        return jsonify({"ok": False, "error": "ROS 2 is not available"}), 503

    data = request.get_json(silent=True) or {}
    name = data.get("name")
    if not isinstance(name, str) or not name:
        return jsonify({"ok": False, "error": "missing joint name"}), 400

    limits = robot_meta()["limits"].get(name)
    if limits is None:
        return jsonify({"ok": False, "error": f"unknown joint '{name}'"}), 400
    if limits["mimic"]:
        return jsonify({
            "ok": False,
            "error": f"'{name}' mimics {limits['mimic']} and is not commanded directly",
        }), 400

    try:
        position = float(data.get("position"))
    except (TypeError, ValueError):
        return jsonify({"ok": False, "error": "invalid position"}), 400
    if position != position or position in (float("inf"), float("-inf")):
        return jsonify({"ok": False, "error": "invalid position"}), 400

    clamped = max(limits["lower"], min(limits["upper"], position))
    try:
        state_node.publish_joint_cmd(name, clamped)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

    return jsonify({"ok": True, "name": name, "position": clamped,
                    "clamped": clamped != position})


@app.route("/api/move_home", methods=["POST"])
def api_move_home():
    """Send both arms to their home pose via gen2's /move_home service."""
    if state_node is None:
        return jsonify({"ok": False, "message": "ROS 2 is not available"}), 503

    log_event("Move Home requested from the dashboard")
    ok, message = state_node.call_move_home()
    log_event(f"Move Home: {message}", level="info" if ok else "error")
    return jsonify({"ok": ok, "message": message}), (200 if ok else 409)


@app.route("/api/mode", methods=["GET"])
def api_mode():
    """Whatever mode_toggler last reported on its status topic. This is the
    mode that actually landed on hardware — the `mode` parameter only says
    what was asked for, which is why the status topic is what's shown."""
    return jsonify({"mode": state_node.get_mode() if state_node else "unknown"})


@app.route("/api/mode/set", methods=["POST"])
def api_mode_set():
    """Switch mode_toggler between 'teach' (backdrivable) and 'normal'
    (holds trajectory)."""
    if state_node is None:
        return jsonify({"ok": False, "message": "ROS 2 is not available"}), 503

    mode = (request.get_json(silent=True) or {}).get("mode")
    if mode not in ("teach", "normal"):
        return jsonify({"ok": False, "message": "mode must be 'teach' or 'normal'"}), 400

    ok, err = _call_set_parameters(state_node.mode_set_client, "mode", mode)
    message = f"mode_toggler -> {mode}" if ok else f"mode_toggler set failed: {err}"
    log_event(message, level="info" if ok else "error")
    return jsonify({"ok": ok, "message": message, "mode": mode}), (200 if ok else 409)


@app.route("/api/speed_limits", methods=["GET", "POST"])
def api_speed_limits():
    """Read or set joint_command_limiter's max_velocity / max_acceleration —
    how fast anything commanding the arms, this panel's sliders included, is
    allowed to move them."""
    if request.method == "GET":
        client = state_node.limiter_get_client if state_node else None
        return jsonify({name: _call_get_parameters(client, name) for name in LIMITER_PARAMS})

    if state_node is None:
        return jsonify({"ok": False, "message": "ROS 2 is not available"}), 503

    data = request.get_json(silent=True) or {}
    results, all_ok = {}, True
    for name in LIMITER_PARAMS:
        if name not in data:
            continue
        try:
            value = float(data[name])
        except (TypeError, ValueError):
            results[name] = {"ok": False, "message": f"{name} must be a number"}
            all_ok = False
            continue
        if not (value > 0):
            # A zero or negative limit would either freeze every arm command
            # or be rejected downstream; refusing here gives a clearer answer.
            results[name] = {"ok": False, "message": f"{name} must be greater than 0"}
            all_ok = False
            continue

        ok, err = _call_set_parameters(state_node.limiter_set_client, name, value)
        message = f"{name} -> {value}" if ok else f"{name} set failed: {err}"
        results[name] = {"ok": ok, "message": message}
        all_ok = all_ok and ok
        log_event(f"joint_command_limiter {message}", level="info" if ok else "error")

    if not results:
        return jsonify({"ok": False, "message": "nothing to set"}), 400
    return jsonify({"ok": all_ok, "results": results}), (200 if all_ok else 409)


@app.route("/api/gains", methods=["GET", "POST"])
def api_gains():
    """Read or set teach_mode_node's per-motor stiffness (normal_kp_<n>) and
    damping (normal_kd_<n>) -- what the Motor Status panel's gains table
    edits. One value per motor id (1-GAIN_NUM_MOTORS): teach_mode_node
    applies the same kp/kd array to both arms, so there's nothing to pick
    between left/right here."""
    if request.method == "GET":
        client = state_node.gain_get_client if state_node else None
        names = [
            f"normal_{kind}_{i}" for kind in ("kp", "kd") for i in GAIN_MOTOR_IDS
        ]
        values = _call_get_parameters_batch(client, names)
        return jsonify({
            "kp": {i: values.get(f"normal_kp_{i}") for i in GAIN_MOTOR_IDS},
            "kd": {i: values.get(f"normal_kd_{i}") for i in GAIN_MOTOR_IDS},
            "available": bool(values),
        })

    if state_node is None:
        return jsonify({"ok": False, "message": "ROS 2 is not available"}), 503

    data = request.get_json(silent=True) or {}
    try:
        motor = int(data.get("motor"))
    except (TypeError, ValueError):
        return jsonify({"ok": False, "message": "invalid motor"}), 400
    if motor not in GAIN_MOTOR_IDS:
        return jsonify({"ok": False, "message": f"motor must be 1-{GAIN_NUM_MOTORS}"}), 400

    results, all_ok = {}, True
    for kind in ("kp", "kd"):
        if kind not in data:
            continue
        try:
            value = float(data[kind])
        except (TypeError, ValueError):
            results[kind] = {"ok": False, "message": f"{kind} must be a number"}
            all_ok = False
            continue
        if value < 0:
            # Negative stiffness/damping doesn't mean anything physically --
            # 0 is valid (that's what teach mode itself uses).
            results[kind] = {"ok": False, "message": f"{kind} must be >= 0"}
            all_ok = False
            continue

        name = f"normal_{kind}_{motor}"
        ok, err = _call_set_parameters(state_node.gain_set_client, name, value)
        message = f"{name} -> {value}" if ok else f"{name} set failed: {err}"
        results[kind] = {"ok": ok, "message": message}
        all_ok = all_ok and ok
        log_event(f"teach_mode_node {message}", level="info" if ok else "error")

    if not results:
        return jsonify({"ok": False, "message": "nothing to set"}), 400
    return jsonify({"ok": all_ok, "results": results, "motor": motor}), (200 if all_ok else 409)


@app.route("/api/teleop", methods=["POST"])
def api_teleop():
    """Latest joystick deflection, as normalized x/y in [-1, 1].

    Deflection is turned into a Twist here rather than in the browser so the
    speed limits are the server's, not something a page can talk its way
    past."""
    if state_node is None:
        return jsonify({"ok": False, "error": "ROS 2 is not available"}), 503

    data = request.get_json(silent=True) or {}
    try:
        x = max(-1.0, min(1.0, float(data.get("x", 0.0))))
        y = max(-1.0, min(1.0, float(data.get("y", 0.0))))
    except (TypeError, ValueError):
        return jsonify({"ok": False, "error": "invalid deflection"}), 400

    state = state_node.set_teleop(
        # Push forward drives forward; push right turns right, which is
        # negative yaw in REP-103's right-handed frame.
        linear=y * TELEOP_MAX_LINEAR,
        angular=-x * TELEOP_MAX_ANGULAR,
    )
    return jsonify({"ok": True, "enabled": state["enabled"],
                    "linear": state["linear"], "angular": state["angular"]})


@app.route("/api/teleop/enable", methods=["POST"])
def api_teleop_enable():
    """Arm or disarm /cmd_vel publishing. Nothing reaches the base until this
    is on, and disarming re-centres the stick."""
    if state_node is None:
        return jsonify({"ok": False, "error": "ROS 2 is not available"}), 503

    data = request.get_json(silent=True) or {}
    enabled = bool(data.get("enabled"))

    # Every page load disarms, to resync a browser that was refreshed while
    # armed. Only a real change is worth a log line.
    was = state_node.get_teleop()["enabled"]
    state = state_node.set_teleop(enabled=enabled)
    if was != state["enabled"]:
        log_event(f"Navigation joystick {'armed' if enabled else 'disarmed'}",
                  level="warn" if enabled else "info")
    return jsonify({"ok": True, "enabled": state["enabled"]})


@app.route("/api/urdf")
def api_urdf():
    """The robot description, with package:// URIs rewritten to /pkg/ so the
    browser can fetch the meshes it references."""
    if not ROBOT_MODEL_AVAILABLE:
        return Response(
            f"<!-- {DESC_PACKAGE} not found (looked in: {', '.join(_desc_candidates)}) -->",
            mimetype="application/xml", status=404,
        )
    with open(ROBOT_URDF) as f:
        content = f.read()
    content = content.replace(f"package://{DESC_PACKAGE}/", "/pkg/")
    return Response(content, mimetype="application/xml")


@app.route("/api/viewer_joint_overrides")
def api_viewer_joint_overrides():
    """Joint names whose rotation direction the 3D viewer should flip, read
    fresh from config/viewer_joint_overrides.yaml on every call so an edit
    takes effect on the next page reload."""
    return jsonify({"joints": _load_viewer_joint_overrides(VIEWER_JOINT_OVERRIDES_YAML)})


@app.route("/pkg/<path:subpath>")
def serve_pkg(subpath):
    """Serve mesh/texture files out of the description package."""
    if not DESC_PKG:
        abort(404)
    root = os.path.realpath(DESC_PKG)
    full = os.path.realpath(os.path.join(root, subpath))
    # realpath on both sides, then a separator-terminated prefix check: a
    # "../" in subpath (or a symlink pointing out of the package) must not
    # turn this into a read of any file on the robot.
    if full != root and not full.startswith(root + os.sep):
        abort(403)
    if not os.path.isfile(full):
        abort(404)
    mime = {
        ".stl": "model/stl",
        ".dae": "model/vnd.collada+xml",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
    }.get(os.path.splitext(full)[1].lower(), "application/octet-stream")
    return send_file(full, mimetype=mime)


@app.route("/api/soc_stats")
def api_soc_stats():
    with soc_lock:
        stats = dict(soc_stats)
    return jsonify({"stats": stats, "available": TEGRASTATS_AVAILABLE})


def main():
    global state_node
    print(
        f"Bringup Launch Control UI on http://{socket.gethostname().lower()}.local:8100 "
        f"({LAUNCH_PACKAGE} {LAUNCH_FILE})"
    )

    if ROS_AVAILABLE:
        rclpy.init()
        state_node = RobotStateNode()
        executor = SingleThreadedExecutor()
        executor.add_node(state_node)
        threading.Thread(target=executor.spin, daemon=True).start()
        log_event(
            f"Watching joint states: {LEFT_JOINT_STATE_TOPIC}, {RIGHT_JOINT_STATE_TOPIC}"
        )
        log_event(f"Watching battery: {BATTERY_TOPIC}")
    else:
        log_event(f"ROS 2 unavailable ({ROS_IMPORT_ERROR}) — no live robot state", level="warn")

    if MOTOR_STATUS_AVAILABLE:
        log_event(f"Watching motor status: {LEFT_MOTOR_TOPIC}, {RIGHT_MOTOR_TOPIC}")
    else:
        reason = ROS_IMPORT_ERROR or MOTOR_STATUS_IMPORT_ERROR or \
            "hw_interface motor_status message not available"
        log_event(f"Motor status disabled ({reason})", level="warn")

    if ROBOT_MODEL_AVAILABLE:
        log_event(f"3D view using {ROBOT_URDF}")
    else:
        log_event(f"3D view disabled ({DESC_PACKAGE} not found)", level="warn")

    if TEGRASTATS_AVAILABLE:
        threading.Thread(target=_soc_monitor_thread, daemon=True).start()
        log_event("Watching system stats (tegrastats)")
    else:
        log_event("System monitor disabled (tegrastats not found)", level="warn")

    # Auto-launch bringup on startup -- but only if nothing is running yet.
    # This process itself auto-starts on boot via gen2-robot.service with
    # Restart=always, and the bringup child tree survives independently of
    # it (preexec_fn=os.setsid in start_bringup()); blindly calling
    # start_bringup() on every startup would stack a *second* full bringup
    # on top of a still-running orphaned one after a crash+restart, with
    # both fighting over the same CAN adapter and vcan0/vcan1. Checking the
    # OS via _bringup_already_running() (rather than trusting _proc, which
    # resets to None on restart) avoids that while still auto-launching on
    # a genuine first start.
    if _bringup_already_running():
        log_event(
            f"{LAUNCH_PACKAGE} {LAUNCH_FILE} already running -- not auto-launching a duplicate. "
            "Use Kill in the web UI first if you want to restart it.",
            level="warn",
        )
    else:
        ok, msg = start_bringup()
        if not ok:
            log_event(f"Auto-launch failed: {msg}", level="error")

    log_event("launch-control panel ready")

    try:
        app.run(host="0.0.0.0", port=8100, threaded=True)
    finally:
        if state_node is not None:
            try:
                state_node.destroy_node()
                rclpy.shutdown()
            except Exception:
                pass


if __name__ == "__main__":
    main()
