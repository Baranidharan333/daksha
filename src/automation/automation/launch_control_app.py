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

from flask import Flask, jsonify, render_template, request

logging.getLogger("werkzeug").setLevel(logging.WARNING)

# ROS 2 is optional at import time so this file still runs (in a degraded,
# no-motor-status mode) if launched outside a sourced ROS 2 environment.
ROS_IMPORT_ERROR = None
MOTOR_STATUS_IMPORT_ERROR = None
try:
    import rclpy
    from rclpy.node import Node
    from rclpy.executors import SingleThreadedExecutor
    from sensor_msgs.msg import JointState
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
# project.config.yaml's motor_topics section) — this panel isn't a generic
# topic picker, just a live view of the two arms while bringup is running.
LEFT_MOTOR_TOPIC = "/LeftArmSystem/motor_status"
RIGHT_MOTOR_TOPIC = "/RightArmSystem/motor_status"
# Published by gen2/arm_recovery_watchdog.py: a JointState whose name[]/
# position[] pairs are "<ArmName>_motor_<id>" -> how many times recovery
# has been triggered for that motor.
RECOVERY_COUNT_TOPIC = "/arm_recovery/recovery_counts"

# Reference data for the /ports page — the workspace's 8100-8199 port
# consolidation (see port_report.pdf in this same directory). "kind" drives
# whether the UI renders a clickable link: "http" gets one, "tcp"/"udp"
# sockets and "reserved" (declared in config but not actually bound by any
# script yet) are shown as plain badges instead, since a link there would
# just fail to load.
PORT_TABLE = [
    {"port": 8100, "service": "Bringup Launch Control", "file": "automation/automation/launch_control_app.py", "kind": "http"},
    {"port": 8101, "service": "VR Management UI", "file": "tele/vr_teleop/vr_teleop/main_scripts/vr_management_ui.py", "kind": "http"},
    {"port": 8102, "service": "gen2 leader controller UI", "file": "gen2/gen2/leader_controller_ui.py", "kind": "http"},
    {"port": 8103, "service": "ROS-TCP-Endpoint (Unity bridge)", "file": "tele/ROS-TCP-Endpoint/ros_tcp_endpoint/server.py", "kind": "tcp"},
    {"port": 5005, "service": "Raw leader-controller socket listener", "file": "tele/gen2_leader/gen2_leader/Gen2Leader_raw.py", "kind": "udp"},
    {"port": 8110, "service": "gesture_management — Teach & Replay Console", "file": "gesture_management/gesture_management/gesture_management_app.py", "kind": "http"},
    {"port": 7071, "service": "Daksha Dashboard", "file": "ui/Clients_UI/daksha_ui/daksha_ui/dashboard_app.py", "kind": "http"},
    {"port": 7001, "service": "Daksha sub-UI", "file": "ui/Clients_UI/daksha_ui/daksha_ui/subui_app.py", "kind": "http"},
    {"port": 7002, "service": "Daksha Viveka camera-stream UI", "file": "ui/Clients_UI/daksha_ui/daksha_ui/viveka_camera_ui.py", "kind": "http"},
    {"port": 8130, "service": "joint_analyzer server", "file": "ui/analyzer/joint_analyzer/server.py", "kind": "http"},
    {"port": 8131, "service": "joint_analyzer plot server", "file": "ui/analyzer/joint_analyzer/plot_server.py", "kind": "http"},
    {"port": 8141, "service": "Daksha API bridge camera streamer", "file": "global/daksha_api_bridge_leader/daksha_api_bridge_leader/camera_streamer.py", "kind": "http"},
    {"port": 8888, "service": "Data Collection Terminal", "file": "ui/Clients_UI/daksha_data_collection/daksha_data_collection/web_data_management_ui.py", "kind": "http"},
]

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


motor_node = None  # set in main() if ROS/hw_interface are available


class MotorStatusNode(Node):
    """Subscribes to both arms' motor_status topics and caches the latest
    reading of each so the web UI can poll it without touching rclpy."""

    def __init__(self):
        super().__init__("automation_motor_status")
        self._lock = threading.Lock()
        self._latest = {"left": [], "right": []}
        self._recovery_counts = {}
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

    def get_status(self):
        with self._lock:
            return {k: list(v) for k, v in self._latest.items()}

    def get_recovery_counts(self):
        with self._lock:
            return dict(self._recovery_counts)

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
    return render_template("index.html", package=LAUNCH_PACKAGE, launch_file=LAUNCH_FILE)


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


@app.route("/api/logs")
def api_logs():
    since = request.args.get("since", 0, type=int)
    with _log_lock:
        entries = [e for e in _log_entries if e["id"] > since]
    return jsonify({"logs": entries})


@app.route("/api/motor_status")
def api_motor_status():
    status = motor_node.get_status() if motor_node else {"left": [], "right": []}
    return jsonify({"status": status, "available": MOTOR_STATUS_AVAILABLE})


@app.route("/api/recovery_counts")
def api_recovery_counts():
    counts = motor_node.get_recovery_counts() if motor_node else {}
    return jsonify({"counts": counts, "available": MOTOR_STATUS_AVAILABLE})


@app.route("/api/soc_stats")
def api_soc_stats():
    with soc_lock:
        stats = dict(soc_stats)
    return jsonify({"stats": stats, "available": TEGRASTATS_AVAILABLE})


def main():
    global motor_node
    print(
        f"Bringup Launch Control UI on http://{socket.gethostname().lower()}.local:8100 "
        f"({LAUNCH_PACKAGE} {LAUNCH_FILE})"
    )

    if MOTOR_STATUS_AVAILABLE:
        rclpy.init()
        motor_node = MotorStatusNode()
        executor = SingleThreadedExecutor()
        executor.add_node(motor_node)
        threading.Thread(target=executor.spin, daemon=True).start()
        log_event(f"Watching motor status: {LEFT_MOTOR_TOPIC}, {RIGHT_MOTOR_TOPIC}")
    else:
        reason = ROS_IMPORT_ERROR or MOTOR_STATUS_IMPORT_ERROR or \
            "hw_interface motor_status message not available"
        log_event(f"Motor status disabled ({reason})", level="warn")

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
        if MOTOR_STATUS_AVAILABLE and motor_node is not None:
            try:
                motor_node.destroy_node()
                rclpy.shutdown()
            except Exception:
                pass


if __name__ == "__main__":
    main()
