import os
os.environ['ROS_DOMAIN_ID'] = os.environ.get('ROS_DOMAIN_ID', '33')
import json
import threading
import time
import subprocess
import uuid
import yaml
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

import rclpy
from rclpy.node import Node
import rclpy.executors
from rclpy.qos import QoSProfile, QoSDurabilityPolicy, QoSReliabilityPolicy, QoSHistoryPolicy
from std_srvs.srv import Trigger
from std_msgs.msg import String
from hw_interface.msg import MotorStatusArray
from daksha_msgs.srv import StartRecord, StartReplay
import cv2
import glob
from pathlib import Path

try:
    from .camera_ui_display import CameraDisplayNode
except ImportError:
    from camera_ui_display import CameraDisplayNode

# Must match mode_toggler's publisher QoS (transient-local) so a subscriber
# gets the last status even if it connects after mode_toggler already
# settled into its startup mode, instead of waiting forever.
MODE_STATUS_QOS = QoSProfile(
    depth=1,
    reliability=QoSReliabilityPolicy.RELIABLE,
    durability=QoSDurabilityPolicy.TRANSIENT_LOCAL,
    history=QoSHistoryPolicy.KEEP_LAST,
)


def set_toggler_mode(mode_name):
    """Best-effort `ros2 param set /mode_toggler mode <mode_name>` — same
    mechanism gesture_management and the Daksha dashboard use (mode_toggler
    is a shared gen2 node, not specific to any one UI)."""
    try:
        result = subprocess.run(
            ["ros2", "param", "set", "/mode_toggler", "mode", mode_name],
            capture_output=True, text=True, timeout=5.0,
        )
        if result.returncode != 0:
            return False, f"mode_toggler set failed: {result.stderr.strip()}"
        return True, f"mode_toggler -> {mode_name}"
    except Exception as e:
        return False, f"mode_toggler set failed: {e}"


# --- Configuration Path Settings ---
# Fallback dataset directory (used only if config.yaml root_dir is missing) —
# package-relative rather than CWD-relative, so it doesn't depend on where
# the process happens to be launched from.
DATASET_BASE_DIR = str(Path(__file__).resolve().parent.parent / "datasets")

# ── Per-Session State ─────────────────────────────────────────────────────────
SESSION_TIMEOUT = 3600  # seconds of inactivity before a session is discarded

_DEFAULT_DOMAIN_ID = None

def _resolve_default_domain_id() -> int:
    """Read ros.domain_id from config.yaml (the single source of truth also
    used by the Daksha dashboard) once and cache it, falling back to this
    process's own ROS_DOMAIN_ID env var. A new browser session with no
    explicit domain selection binds its camera node to this value, so it
    MUST match the domain the robot's cameras/arms actually bring up on
    (see ~/.bashrc / start_robot.sh) or every fresh session sees no frames."""
    global _DEFAULT_DOMAIN_ID
    if _DEFAULT_DOMAIN_ID is not None:
        return _DEFAULT_DOMAIN_ID
    try:
        with open(_get_default_config_path()) as f:
            cfg = yaml.safe_load(f) or {}
        _DEFAULT_DOMAIN_ID = int(cfg.get('domain_id', cfg.get('recording', {}).get('domain_id', 0)))
    except Exception:
        _DEFAULT_DOMAIN_ID = int(os.environ.get('ROS_DOMAIN_ID', 33))
    return _DEFAULT_DOMAIN_ID

class SessionState:
    """Lightweight per-browser-session state container."""
    def __init__(self, session_id: str):
        self.session_id   = session_id
        self.domain_id    = _resolve_default_domain_id()  # ROS Domain ID (matches this robot's actual bringup)

        self.loaded_topics: list = []
        # camera_names maps camera-label -> ros-topic for THIS session
        self.camera_names: dict = {
            "Left Wrist Camera": "/left/camera/color/image_raw",
            "Right Wrist Camera": "/right/camera/color/image_raw",
            "Primary Binocular Vision (Left)": "/zed/zed_node/left/color/rect/image",
            "Primary Binocular Vision (Right)": "/zed/zed_node/right/color/rect/image"
        }
        self.last_active  = time.time()



    def touch(self):
        self.last_active = time.time()

# Global session store
_session_store: dict = {}          # session_id → SessionState
_session_lock  = threading.Lock()

# Reference-count per ROS topic: how many sessions are subscribed to it.
# The actual ROS subscription is created when count goes 0→1 and
# destroyed when count goes 1→0.
_topic_refcount: dict = {}         # topic_string → int
_topic_ref_lock = threading.Lock()

def _session_cleanup_loop():
    """Background thread that evicts sessions idle for more than SESSION_TIMEOUT."""
    while True:
        time.sleep(300)
        now = time.time()
        with _session_lock:
            expired = [sid for sid, s in _session_store.items()
                       if now - s.last_active > SESSION_TIMEOUT]
            for sid in expired:
                _session_store.pop(sid, None)

threading.Thread(target=_session_cleanup_loop, daemon=True).start()

def _get_or_create_session(session_id=None) -> SessionState:
    """Return existing session or create a fresh one with default domain 0."""
    with _session_lock:
        if session_id and session_id in _session_store:
            s = _session_store[session_id]
            s.touch()
            return s
        new_id = session_id if session_id else str(uuid.uuid4())
        s = SessionState(new_id)
        _session_store[new_id] = s
        return s

def _active_session_count() -> int:
    with _session_lock:
        return len(_session_store)

# ── Per-Domain Camera Node Pool ────────────────────────────────────────────
# Each unique domain ID gets its own rclpy Context, CameraDisplayNode, and
# executor thread. This means cameras work on ANY domain without a server restart.
# The reference-count key is (domain_id, topic_string) to avoid cross-domain conflicts.

_domain_cam_pool: dict = {}       # domain_id -> CameraDisplayNode
_domain_cam_pool_lock = threading.Lock()

def _get_or_create_domain_cam_node(domain_id: int) -> 'CameraDisplayNode':
    """Return a CameraDisplayNode bound to `domain_id`, creating one if needed."""
    with _domain_cam_pool_lock:
        if domain_id in _domain_cam_pool:
            return _domain_cam_pool[domain_id]

        # Create a dedicated rclpy context for this domain.
        # rclpy.init(domain_id=X, context=ctx) is supported in ROS 2 Humble.
        ctx = rclpy.Context()
        try:
            rclpy.init(context=ctx, domain_id=domain_id)
        except Exception as e:
            # Fallback: init without domain_id (uses ROS_DOMAIN_ID env var)
            try:
                ctx = rclpy.Context()
                rclpy.init(context=ctx)
            except Exception:
                pass

        cam_node = CameraDisplayNode({}, context=ctx)

        # Auto-register default 4 cameras on node startup so feeds are subscribed immediately
        default_cams = [
            ("Left Wrist Camera", "/left/camera/color/image_raw/compressed"),
            ("Right Wrist Camera", "/right/camera/color/image_raw/compressed"),
            ("Primary Binocular Vision (Left)", "/zed/zed_node/left/color/rect/image/compressed"),
            ("Primary Binocular Vision (Right)", "/zed/zed_node/right/color/rect/image/compressed")
        ]
        for name, topic in default_cams:
            cam_node._subscription_queue.put({'action': 'register', 'name': name, 'topic': topic})

        executor = rclpy.executors.SingleThreadedExecutor(context=ctx)
        executor.add_node(cam_node)

        t = threading.Thread(
            target=executor.spin,
            name=f'cam_exec_d{domain_id}',
            daemon=True
        )
        t.start()


        _domain_cam_pool[domain_id] = cam_node
        return cam_node

HTML_TEMPLATE = """<!doctype html>
<html lang="en">

<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>iHub Robotics — Data Collection Terminal</title>
  <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
  <script>
    (function() {
      const urlParams = new URLSearchParams(window.location.search);
      const urlTheme = urlParams.get('theme');
      const savedTheme = urlTheme || localStorage.getItem('theme') || localStorage.getItem('daksha_theme');
      if (savedTheme === 'light') {
        document.documentElement.classList.add('light-mode');
      }
    })();
  </script>
  <style>
    /* Dark Cyber Theme for Operator Terminal */
    :root {
      --bg-color: #000000;
      --panel-bg: #0a0a0a;
      --panel-border: rgba(255, 255, 255, 0.14);
      --text-main: #ffffff;
      --text-muted: #a1a1aa;
      --primary: #ffffff;
      --primary-hover: #ededed;
      --danger: #ef4444;
      --danger-hover: #dc2626;
      --success: #10b981;
      --border: rgba(255, 255, 255, 0.14);
      --radius: 12px;
      --shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.9);
      --shadow-lg: 0 20px 30px -10px rgba(0, 0, 0, 0.95);
    }
    :root.light-mode, html.light-mode, body.light-mode {
      --bg-color: #f8fafc;
      --panel-bg: #ffffff;
      --panel-border: rgba(203, 213, 225, 0.8);
      --text-main: #1e293b;
      --text-muted: #475569;
      --primary: #0284c7;
      --primary-hover: #0369a1;
      --danger: #dc2626;
      --danger-hover: #b91c1c;
      --success: #059669;
      --border: rgba(203, 213, 225, 0.8);
      --radius: 12px;
      --shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.04);
      --shadow-lg: 0 20px 30px -10px rgba(15, 23, 42, 0.06);
    }
    .light-mode body {
      background-color: #f8fafc !important;
      color: #1e293b !important;
    }
    .light-mode .header-panel, .light-mode .panel {
      background: #ffffff !important;
      border-color: #cbd5e1 !important;
      box-shadow: 0 4px 20px -2px rgba(15, 23, 42, 0.04) !important;
    }
    .light-mode .header-panel {
      border-left: 4px solid #0284c7 !important;
    }
    .light-mode h1, .light-mode h2 {
      color: #0f766e !important;
    }
    .light-mode label {
      color: #475569 !important;
    }
    .light-mode input, .light-mode select {
      background: #f8fafc !important;
      color: #1e293b !important;
      border: 1px solid #cbd5e1 !important;
    }
    .light-mode input:focus, .light-mode select:focus {
      border-color: #0284c7 !important;
      box-shadow: 0 0 0 3px rgba(2, 132, 199, 0.15) !important;
      background: #ffffff !important;
    }
    .light-mode button {
      background: linear-gradient(135deg, #0284c7, #0369a1) !important;
      color: #ffffff !important;
      border: 1px solid #0284c7 !important;
      box-shadow: 0 2px 8px rgba(2, 132, 199, 0.2) !important;
      border-radius: 9999px !important;
    }
    .light-mode button:hover {
      background: linear-gradient(135deg, #0369a1, #075985) !important;
      border-color: #0369a1 !important;
      box-shadow: 0 4px 12px rgba(2, 132, 199, 0.3) !important;
    }
    .light-mode .btn-success {
      background: linear-gradient(135deg, #059669, #047857) !important;
      color: #ffffff !important;
      border: 1px solid #047857 !important;
      box-shadow: 0 2px 8px rgba(5, 150, 105, 0.2) !important;
    }
    .light-mode .btn-success:hover {
      background: linear-gradient(135deg, #047857, #065f46) !important;
      box-shadow: 0 4px 12px rgba(5, 150, 105, 0.3) !important;
    }
    .light-mode .btn-danger {
      background: linear-gradient(135deg, #dc2626, #b91c1c) !important;
      color: #ffffff !important;
      border: 1px solid #b91c1c !important;
      box-shadow: 0 2px 8px rgba(220, 38, 38, 0.2) !important;
    }
    .light-mode .btn-danger:hover {
      background: linear-gradient(135deg, #b91c1c, #991b1b) !important;
      box-shadow: 0 4px 12px rgba(220, 38, 38, 0.3) !important;
    }
    .light-mode .btn-outline {
      background: #ffffff !important;
      border: 1px solid #e2e8f0 !important;
      color: #0f172a !important;
      box-shadow: 0 1px 3px rgba(0,0,0,0.05) !important;
    }
    .light-mode .btn-outline:hover {
      background: #f8fafc !important;
      border-color: #cbd5e1 !important;
      color: #0284c7 !important;
    }
    .light-mode .camera-box {
      background: #f1f5f9 !important;
      border-color: #e2e8f0 !important;
      color: #0f172a !important;
    }
    .light-mode .camera-box .cam-label {
      background: linear-gradient(transparent, rgba(241, 245, 249, 0.95)) !important;
      color: #0f172a !important;
    }
    .light-mode .motor-stat {
      background: #f8fafc !important;
      border-color: #e2e8f0 !important;
      color: #0f172a !important;
    }
    .light-mode details.dev-drawer {
      background: #f8fafc !important;
      border-color: #e2e8f0 !important;
    }
    .light-mode details.dev-drawer summary {
      color: #0284c7 !important;
    }
    .light-mode div[style*="background: rgba(56, 189, 248"] {
      background: #f0f9ff !important;
      border-color: #bae6fd !important;
    }
    .light-mode div[style*="background: rgba(15, 23, 42"] {
      background: #f8fafc !important;
      border-color: #e2e8f0 !important;
    }
    *, *::before, *::after {
      box-sizing: border-box !important;
    }
    body {
      font-family: 'Outfit', sans-serif;
      background: var(--bg-color);
      color: var(--text-main);
      margin: 0; padding: 18px;
      display: flex; flex-direction: column; height: 100vh;
      overflow: hidden;
    }

    /* Grid layout */
    .app-container {
      display: grid;
      grid-template-areas:
        "header header header"
        "left center right"
        "bottom bottom bottom";
      grid-template-columns: 340px 1fr 340px;
      grid-template-rows: auto 1fr auto;
      gap: 16px; flex: 1; min-height: 0;
    }

    /* Top Bar */
    .header-panel {
      grid-area: header;
      display: flex; justify-content: space-between; align-items: center;
      background: var(--panel-bg); padding: 14px 22px;
      border-radius: var(--radius); border: 1px solid var(--border);
      border-left: 4px solid var(--primary);
    }
    .header-panel h1 { margin: 0; color: #f8fafc; font-size: 1.4rem; font-weight: 700; display: flex; align-items: center; gap: 10px; }
    .domain-loader { display: flex; gap: 10px; align-items: center; }

    /* Panels */
    .panel {
      background: var(--panel-bg); padding: 20px;
      border-radius: var(--radius); border: 1px solid var(--border);
      display: flex; flex-direction: column; overflow-y: auto;
      box-shadow: var(--shadow);
    }
    .panel h2 {
      margin-top: 0; font-size: 1.05rem; color: var(--primary);
      border-bottom: 1px solid var(--border); padding-bottom: 10px; margin-bottom: 16px;
      text-transform: uppercase; letter-spacing: 1px; font-weight: 700;
    }

    .left-panel { grid-area: left; }
    .center-panel { grid-area: center; }
    .right-panel { grid-area: right; }
    .bottom-panel { grid-area: bottom; }

    /* Forms & Inputs */
    .form-group { margin-bottom: 14px; }
    .form-group label { display: block; font-size: 0.78rem; font-weight: 600; margin-bottom: 6px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; }
    input, select {
      width: 100%; padding: 10px 12px;
      border: 1px solid var(--border); border-radius: 8px;
      font-family: 'Outfit', sans-serif; font-size: 0.9rem;
      background: rgba(15, 23, 42, 0.8); color: #f8fafc; transition: all 0.2s;
    }
    input:focus, select:focus { outline: none; border-color: var(--primary); box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.2); background: #0f172a;}

    /* Buttons */
    button {
      padding: 10px 18px; border: 1px solid rgba(255, 255, 255, 0.16); border-radius: 9999px; font-weight: 600; cursor: pointer; transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
      background: #18181b; color: #ffffff; font-family: 'Outfit', sans-serif; font-size: 0.88rem; letter-spacing: 0.02em;
      display: inline-flex; align-items: center; justify-content: center; gap: 8px;
      box-shadow: 0 2px 6px rgba(0,0,0,0.4);
    }
    button:hover { background: #27272a; border-color: rgba(255, 255, 255, 0.3); color: #ffffff; transform: translateY(-1px); box-shadow: 0 4px 12px rgba(0,0,0,0.6); }
    button:active { transform: translateY(0); }
    
    .btn-success {
      background: linear-gradient(135deg, rgba(6, 95, 70, 0.7), rgba(4, 120, 87, 0.8));
      color: #ffffff; border: 1px solid rgba(16, 185, 129, 0.4);
      box-shadow: 0 2px 8px rgba(5, 150, 105, 0.2);
    }
    .btn-success:hover {
      background: linear-gradient(135deg, rgba(4, 120, 87, 0.95), rgba(5, 150, 105, 1));
      color: #ffffff; border-color: rgba(52, 211, 153, 0.6);
      box-shadow: 0 4px 14px rgba(5, 150, 105, 0.4);
    }
    
    .btn-danger {
      background: linear-gradient(135deg, rgba(153, 27, 27, 0.7), rgba(185, 28, 28, 0.8));
      color: #ffffff; border: 1px solid rgba(239, 68, 68, 0.4);
      box-shadow: 0 2px 8px rgba(220, 38, 38, 0.2);
    }
    .btn-danger:hover {
      background: linear-gradient(135deg, rgba(185, 28, 28, 0.95), rgba(220, 38, 38, 1));
      color: #ffffff; border-color: rgba(248, 113, 113, 0.6);
      box-shadow: 0 4px 14px rgba(220, 38, 38, 0.4);
    }
    
    .btn-outline { background: rgba(255, 255, 255, 0.04); border: 1px solid rgba(255, 255, 255, 0.16); color: #e4e4e7; }
    .btn-outline:hover { background: rgba(255, 255, 255, 0.12); border-color: rgba(255, 255, 255, 0.3); color: #ffffff; }

    /* Topic Selectors */
    .topics-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 16px;}

    /* Cameras */
    .camera-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-top: 10px; }

    .camera-box { background: #070b14; aspect-ratio: 16/9; width: 100%; height: auto; border-radius: 10px; position: relative; overflow: hidden; display: flex; align-items: center; justify-content: center; color: white; font-size: 0.85rem; border: 1px solid var(--border); }
    .camera-box img { width: 100%; height: 100%; object-fit: cover; display: block; }
    .camera-box .cam-label { position: absolute; bottom: 0; left: 0; right: 0; background: linear-gradient(transparent, rgba(0,0,0,0.85)); padding: 10px 8px 6px; text-align: center; font-weight: 600; font-size: 0.8rem;}
    .camera-box .cam-waiting { position: absolute; top: 0; left: 0; right: 0; bottom: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; color: #64748b; font-size: 0.75rem; gap: 6px; pointer-events: none; }
    .cam-waiting-dot { width: 8px; height: 8px; border-radius: 50%; background: #38bdf8; animation: camPulse 1.5s infinite; }
    @keyframes camPulse { 0%,100% { opacity: 0.4; } 50% { opacity: 1; } }

    /* Motor Stats */
    .motor-stat { display: flex; justify-content: space-between; padding: 8px 12px; background: rgba(15, 23, 42, 0.6); border-radius: 6px; margin-bottom: 6px; border: 1px solid var(--border); font-size: 0.82rem; }
    .motor-stat .temp { font-weight: 700; color: var(--primary); font-family: 'JetBrains Mono', monospace; }
    .motor-stat .temp.high { color: var(--danger); }

    /* Toast Notification */
    .toast-container { position: fixed; bottom: 24px; right: 24px; z-index: 50; display: flex; flex-direction: column; gap: 10px; pointer-events: none; }
    .toast { background: var(--panel-bg); border-left: 4px solid var(--success); padding: 14px 20px; border-radius: var(--radius); box-shadow: var(--shadow-lg); color: var(--text-main); font-weight: 600; font-size: 0.9rem; transform: translateX(120%); opacity: 0; transition: all 0.3s ease; pointer-events: auto; }
    .toast.show { transform: translateX(0); opacity: 1; }
    .toast.error { border-left-color: var(--danger); }

    /* Custom Collapsible Drawer */
    details.dev-drawer {
      background: rgba(15, 23, 42, 0.4);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 10px 14px;
      margin-top: 10px;
      transition: all 0.2s ease;
    }
    details.dev-drawer[open] {
      background: rgba(15, 23, 42, 0.7);
    }
    details.dev-drawer summary {
      cursor: pointer;
      font-weight: 700;
      color: var(--primary);
      font-size: 0.82rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      user-select: none;
      display: flex !important;
      align-items: center !important;
      justify-content: space-between !important;
      gap: 8px !important;
      list-style: none !important;
      width: 100% !important;
    }
    details.dev-drawer summary > span:first-child {
      flex: 1;
      min-width: 0;
      line-height: 1.3;
    }
    details.dev-drawer summary::-webkit-details-marker {
      display: none !important;
    }
    details.dev-drawer summary .drawer-arrow {
      width: 22px;
      height: 22px;
      border-radius: 50%;
      background: rgba(255, 255, 255, 0.08);
      display: inline-flex;
      align-items: center;
      justify-content: center;
      transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1), background 0.2s;
    }
    details.dev-drawer[open] summary .drawer-arrow {
      transform: rotate(180deg);
      background: rgba(56, 189, 248, 0.25);
    }
    .light-mode details.dev-drawer summary .drawer-arrow {
      background: rgba(2, 132, 199, 0.1);
      color: #0284c7;
    }
    @keyframes estopPulse {
      0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7); }
      70% { box-shadow: 0 0 0 10px rgba(239, 68, 68, 0); }
      100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
    }
  </style>
</head>
<body>
  <div class="app-container">
    <div class="header-panel">
      <h1>
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color: var(--primary);"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect><line x1="8" y1="21" x2="16" y2="21"></line><line x1="12" y1="17" x2="12" y2="21"></line></svg>
        Data Collection Operator Terminal
      </h1>
      <div style="display: flex; align-items: center; gap: 14px;">
        <input type="hidden" id="domain_id" value="33" />
        <div id="mode-toggle-badge" onclick="toggleRobotMode()" title="Click to switch between Teach (backdrivable) and Normal (holds trajectory) mode" style="cursor: pointer; font-size: 0.78rem; background: rgba(16, 185, 129, 0.1); color: var(--success); border: 1px solid rgba(16, 185, 129, 0.25); padding: 5px 14px; border-radius: 20px; font-weight: 700; letter-spacing: 0.05em; display: inline-flex; align-items: center; gap: 8px;">
          <span id="mode-dot" style="width: 8px; height: 8px; border-radius: 50%; background: #10b981; display: inline-block; box-shadow: 0 0 8px #10b981;"></span>
          <span id="mode-badge-text">MODE: —</span>
        </div>
        <div id="sys-active-badge" style="font-size: 0.78rem; background: rgba(16, 185, 129, 0.1); color: var(--success); border: 1px solid rgba(16, 185, 129, 0.25); padding: 5px 14px; border-radius: 20px; font-weight: 700; letter-spacing: 0.05em; display: inline-flex; align-items: center; gap: 8px;">
          <span style="width: 8px; height: 8px; border-radius: 50%; background: #10b981; display: inline-block; box-shadow: 0 0 8px #10b981;"></span>
          SYSTEM ACTIVE
        </div>
      </div>
    </div>

    
    <!-- LEFT PANEL: Operator Controls & Prompts -->
    <div class="panel left-panel">
      <h2>1. Task & Recording Setup</h2>
      <div class="form-group">
        <label>Dataset Identifier</label>
        <input type="text" id="dataset_name" placeholder="e.g. box_pick_and_place" oninput="syncDatasetNames()" />
      </div>

      <div class="form-group">
        <label>Task 1 Name</label>
        <input type="text" id="task1_name" placeholder="e.g. pick_object" oninput="updateTaskLabels()" />
      </div>
      <div class="form-group">
        <label>Prompt 1 Instruction</label>
        <input type="text" id="prompt1_used" placeholder="e.g. Pick up the targeted block" />
      </div>

      <div class="form-group">
        <label>Task 2 Name</label>
        <input type="text" id="task2_name" placeholder="e.g. place_object" oninput="updateTaskLabels()" />
      </div>
      <div class="form-group">
        <label>Prompt 2 Instruction</label>
        <input type="text" id="prompt2_used" placeholder="e.g. Place the block into destination bin" />
      </div>

      <div style="margin-top: 10px; padding: 14px; background: rgba(56, 189, 248, 0.05); border: 1px solid rgba(56, 189, 248, 0.2); border-radius: 10px;">
        <label style="font-size:0.8rem; font-weight:700; color:var(--primary); display:block; margin-bottom:8px;">ACTIVE RECORD CONTROL</label>
        <div style="display:flex; gap:8px; margin-bottom: 10px;">
          <select id="active_record_task" style="flex:1;">
            <option value="1">Task 1: pick_object</option>
            <option value="2">Task 2: place_object</option>
          </select>
        </div>
        <div style="display:flex; gap:10px;">
          <button class="btn-success" onclick="startRecord()" style="flex:1; display: inline-flex; align-items: center; justify-content: center; gap: 6px;">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><circle cx="12" cy="12" r="9"/></svg>
            Start Record
          </button>
          <button class="btn-danger" onclick="stopRecord()" style="flex:1; display: inline-flex; align-items: center; justify-content: center; gap: 6px;">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><rect x="5" y="5" width="14" height="14" rx="2"/></svg>
            Stop Record
          </button>
        </div>
        <div style="margin-top: 10px; text-align: center; font-size: 1.05rem; font-weight: bold; color: var(--primary); font-family: 'JetBrains Mono', monospace;" id="live_steps_display">
          Steps: 0 / 0
        </div>
        <div id="validation-blocked-panel" style="display:none; margin-top: 10px; padding: 10px; border: 1px solid var(--danger, #ef4444); border-radius: 8px; background: rgba(239,68,68,0.08);">
          <div id="validation-blocked-message" style="font-size: 0.9rem; margin-bottom: 8px;"></div>
          <button class="btn-danger" onclick="acknowledgeValidation()" style="width:100%;">Acknowledge & Resume</button>
        </div>
      </div>

      <!-- LIVE HARDWARE & SAFETY TELEMETRY CARD -->
      <div style="margin-top: 14px; padding: 14px; background: var(--panel-bg); border: 1px solid var(--border); border-radius: 12px; box-shadow: var(--shadow);">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
          <div style="display: flex; align-items: center; gap: 8px;">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--primary)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
            </svg>
            <span style="font-size: 0.8rem; font-weight: 800; letter-spacing: 0.05em; color: var(--text-main);">HARDWARE & SAFETY TELEMETRY</span>
          </div>
          <span id="data-safety-badge" style="font-size:0.7rem; font-weight:800; background:rgba(16, 185, 129, 0.12); color:#059669; padding:3px 10px; border-radius:12px; border:1px solid rgba(16, 185, 129, 0.3);">SAFE</span>
        </div>

        <!-- Battery Health -->
        <div style="margin-bottom: 12px; padding: 10px 12px; background: rgba(2, 132, 199, 0.04); border: 1px solid rgba(2, 132, 199, 0.15); border-radius: 8px;">
          <div style="display: flex; justify-content: space-between; align-items: center; font-size: 0.78rem; margin-bottom: 6px;">
            <span style="color: var(--text-muted); font-weight: 600; display: flex; align-items: center; gap: 6px;">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="1" y="6" width="18" height="12" rx="2"/><line x1="23" y1="11" x2="23" y2="13"/></svg>
              Battery Level
            </span>
            <span id="data-battery-val" style="font-weight: 800; font-family: 'JetBrains Mono', monospace; font-size: 0.95rem; color: var(--primary);">87.0%</span>
          </div>
          <div style="width: 100%; height: 8px; background: rgba(100, 116, 139, 0.2); border-radius: 4px; overflow: hidden;">
            <div id="data-battery-fill" style="width: 87%; height: 100%; background: linear-gradient(90deg, #059669, #10b981); transition: width 0.3s ease;"></div>
          </div>
        </div>

        <!-- Urgent Safety Warning Banner -->
        <div id="data-warning-banner" style="display: none; font-size: 0.78rem; font-weight: 700; background: rgba(239, 68, 68, 0.12); color: #dc2626; padding: 8px 10px; border-radius: 8px; border: 1px solid rgba(239, 68, 68, 0.3); margin-bottom: 10px; text-align: center;">
        </div>

        <!-- Live Motor Temperatures -->
        <div style="font-size: 0.75rem; font-weight: 700; letter-spacing: 0.04em; color: var(--text-muted); margin-bottom: 8px; display: flex; align-items: center; gap: 6px;">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 4v10.54a4 4 0 1 1-4 0V4a2 2 0 0 1 4 0z"/></svg>
          Live Motor Temperatures
        </div>
        <div id="data-motor-temp-list" style="display: grid; grid-template-columns: 1fr 1fr; gap: 6px; max-height: 150px; overflow-y: auto;">
          <div style="font-size:0.75rem; color:#64748b;">Initializing motor telemetry…</div>
        </div>
      </div>
    </div>
    
    <!-- CENTER PANEL: Live Camera Feeds (4-Camera Grid) -->
    <div class="panel center-panel">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
        <h2 style="margin: 0; border: none; padding: 0;">Live Robot Vision Streams (4-Camera Grid)</h2>
      </div>
      
      <div class="camera-grid" id="camera-grid">
        <!-- 4 Fixed Camera Feeds rendered automatically on launch -->
      </div>
    </div>

    
    <!-- RIGHT PANEL: Dataset Stats & Replay / Delete Operations -->
    <div class="panel right-panel">
      <h2>2. Dataset & Episode Operations</h2>
      
      <!-- PROMINENT DATASET STATS CARD (IN DIRECT EYE-SIGHT) -->
      <div style="margin-bottom: 16px; padding: 14px; background: var(--panel-bg); border: 1px solid var(--border); border-radius: 12px; box-shadow: var(--shadow);">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
          <label style="font-size:0.8rem; font-weight:800; color:var(--primary); display:flex; align-items:center; gap:6px; margin:0;">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>
            DATASET METRICS & STATS
          </label>
          <button class="btn-outline" onclick="loadDatasetStats()" style="padding: 3px 10px; font-size: 0.72rem; border-radius: 9999px;">Sync Stats</button>
        </div>
        <div style="display:flex; gap:8px; margin-bottom:10px;">
          <input type="text" id="stats_query_dataset" placeholder="e.g. box_pick_and_place" style="flex:1; font-weight:700;" oninput="syncDatasetNames()" />
        </div>
        <div id="dataset-stats-display" style="font-size: 0.8rem; color: var(--text-muted);">
          <div style="display:grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 8px;">
            <div style="background: rgba(2, 132, 199, 0.08); padding: 8px 12px; border-radius: 8px; border: 1px solid rgba(2, 132, 199, 0.2); text-align: center;">
              <div style="font-size: 0.68rem; color: var(--text-muted); text-transform: uppercase; font-weight: 700;">Total Episodes</div>
              <div style="font-size: 1.25rem; font-weight: 800; color: var(--primary); font-family: 'JetBrains Mono', monospace; margin-top: 2px;">0</div>
            </div>
            <div style="background: rgba(2, 132, 199, 0.08); padding: 8px 12px; border-radius: 8px; border: 1px solid rgba(2, 132, 199, 0.2); text-align: center;">
              <div style="font-size: 0.68rem; color: var(--text-muted); text-transform: uppercase; font-weight: 700;">Total Frames</div>
              <div style="font-size: 1.25rem; font-weight: 800; color: var(--primary); font-family: 'JetBrains Mono', monospace; margin-top: 2px;">0</div>
            </div>
          </div>
          <div style="font-size: 0.75rem; color: var(--text-muted);">Tasks (0): None</div>
        </div>
      </div>

      <!-- REPLAY CONTROL -->
      <div style="margin-bottom: 16px; padding: 14px; background: rgba(2, 132, 199, 0.03); border: 1px solid var(--border); border-radius: 10px;">
        <label style="font-size:0.8rem; font-weight:700; color:var(--primary); display:block; margin-bottom:8px;">REPLAY CONTROL</label>
        <div style="display:flex; gap:8px; margin-bottom:8px;">
          <input type="text" id="replay_dataset" placeholder="e.g. box_pick_and_place" style="flex:1;" />
          <select id="replay_task" style="width: 100px;">
            <option value="1">Task 1</option>
            <option value="2">Task 2</option>
          </select>
        </div>
        <div style="display:flex; gap:8px; margin-bottom:10px;">
          <input type="number" id="replay_episode" min="1" placeholder="e.g. 1" style="flex:1;" />
          <input type="number" id="replay_speed" step="0.1" placeholder="e.g. 1.0" style="width: 80px;" />
        </div>
        <div style="display:flex; gap:8px;">
          <button onclick="startReplay()" style="flex:1; display: inline-flex; align-items: center; justify-content: center; gap: 6px;">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"/></svg>
            Start Replay
          </button>
          <button class="btn-danger" onclick="stopReplay()" style="flex:1; display: inline-flex; align-items: center; justify-content: center; gap: 6px;">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><rect x="5" y="5" width="14" height="14" rx="2"/></svg>
            Stop Replay
          </button>
        </div>
      </div>

      <!-- DELETE EPISODE -->
      <div style="padding: 14px; background: rgba(239, 68, 68, 0.04); border: 1px solid rgba(239, 68, 68, 0.2); border-radius: 10px;">
        <label style="font-size:0.8rem; font-weight:700; color:var(--danger); display:block; margin-bottom:8px;">DELETE EPISODE</label>
        <div style="display:flex; gap:8px; margin-bottom:8px;">
          <input type="text" id="delete_dataset" placeholder="e.g. box_pick_and_place" style="flex:1;" />
          <input type="number" id="delete_episode" min="1" placeholder="Episode #" style="width: 80px;" />
        </div>
        <button class="btn-danger" onclick="deleteEpisode()" style="width: 100%; display: inline-flex; align-items: center; justify-content: center; gap: 6px;">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
          Delete Episode
        </button>
      </div>
    </div>
    
    <!-- BOTTOM PANEL: Collapsible Developer & ROS Configuration Drawer -->
    <div class="panel bottom-panel" style="padding: 12px 18px;">
      <details class="dev-drawer" style="margin: 0; background: transparent; border: none; padding: 0;">
        <summary>
          <span style="display: inline-flex; align-items: center; gap: 8px;">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="4" y1="21" x2="4" y2="14"></line><line x1="4" y1="10" x2="4" y2="3"></line><line x1="12" y1="21" x2="12" y2="12"></line><line x1="12" y1="8" x2="12" y2="3"></line><line x1="20" y1="21" x2="20" y2="16"></line><line x1="20" y1="12" x2="20" y2="3"></line><line x1="1" y1="14" x2="7" y2="14"></line><line x1="9" y1="8" x2="15" y2="8"></line><line x1="17" y1="16" x2="23" y2="16"></line></svg>
            Advanced Developer Configurations (Recording Hz, Episode Len, Max Episodes)
          </span>
          <span class="drawer-arrow">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M6 9l6 6 6-6"/></svg>
          </span>
        </summary>
        
        <div style="display:grid; grid-template-columns: repeat(5, 1fr); gap: 12px; margin-top: 14px;">
          <div><label style="font-size:0.75rem; color:var(--text-muted);">Recording Hz</label><input type="number" id="record_hz" value="30" /></div>
          <div><label style="font-size:0.75rem; color:var(--text-muted);">Max Episodes</label><input type="number" id="max_episodes" value="1" /></div>
          <div><label style="font-size:0.75rem; color:var(--text-muted);">Episode Length</label><input type="number" id="episode_len" value="500" /></div>
          <div><label style="font-size:0.75rem; color:var(--text-muted);">Interdelay (s)</label><input type="number" id="interdelay" value="2.0" step="0.1" /></div>
          <div><label style="font-size:0.75rem; color:var(--text-muted);">Video FPS</label><input type="number" id="fps" value="30" min="1" step="1" /></div>
        </div>
      </details>

    </div>
  </div>

  <!-- Custom Confirmation Dialog Modal -->
  <div id="custom-confirm-modal" class="modal-overlay" style="display: none;">

    <div class="modal-content">
      <div class="modal-icon" id="modal-icon">
        <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
      </div>
      <h3 id="modal-title">Confirm Action</h3>
      <p id="modal-message">Are you sure you want to proceed?</p>
      <div class="modal-buttons">
        <button class="btn-outline" id="modal-cancel-btn" onclick="closeConfirmModal(false)">Cancel</button>
        <button class="btn-danger" id="modal-confirm-btn" onclick="closeConfirmModal(true)">Confirm</button>
      </div>
    </div>
  </div>

  <div class="toast-container" id="toast-container"></div>

  <script>
    function updateTaskLabels() {
        const t1 = document.getElementById('task1_name').value || 'Task 1';
        const t2 = document.getElementById('task2_name').value || 'Task 2';
        
        const recSel = document.getElementById('active_record_task');
        if(recSel) {
            recSel.options[0].text = 'Task: ' + t1;
            recSel.options[1].text = 'Task: ' + t2;
        }
        
        const repSel = document.getElementById('replay_task');
        if(repSel) {
            repSel.options[0].text = 'Task: ' + t1;
            repSel.options[1].text = 'Task: ' + t2;
        }
    }

    function showToast(message, isError=false) {
      const container = document.getElementById('toast-container');
      const toast = document.createElement('div');
      toast.className = 'toast' + (isError ? ' error' : '');
      toast.innerText = message;
      container.appendChild(toast);
      void toast.offsetWidth;
      toast.classList.add('show');
      setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 400);
      }, 3500);
    }

    let loadedDomainId = 33;
    
    function validateDomainId(checkLoaded = false, silent = true) {
      return true;
    }


    let confirmResolver = null;
    function showConfirmModal(title, message, icon = '⚠️', confirmText = 'Confirm', showCancel = true) {
      document.getElementById('modal-title').innerText = title;
      document.getElementById('modal-message').innerText = message;
      document.getElementById('modal-icon').innerText = icon;
      
      const confirmBtn = document.getElementById('modal-confirm-btn');
      if (confirmBtn) {
        confirmBtn.innerText = confirmText;
      }
      
      const cancelBtn = document.getElementById('modal-cancel-btn');
      if (cancelBtn) {
        cancelBtn.style.display = showCancel ? 'inline-flex' : 'none';
      }
      
      const overlay = document.getElementById('custom-confirm-modal');
      overlay.style.display = 'flex';
      // Force reflow
      overlay.offsetHeight;
      overlay.classList.add('show');
      return new Promise((resolve) => {
        confirmResolver = resolve;
      });
    }

    function closeConfirmModal(result) {
      const overlay = document.getElementById('custom-confirm-modal');
      overlay.classList.remove('show');
      setTimeout(() => {
        overlay.style.display = 'none';
      }, 200);
      if (confirmResolver) {
        confirmResolver(result);
        confirmResolver = null;
      }
    }

    let isRestarting = false;
    let availableTopics = [];
    
    async function loadTopics(silent = false) {
      if (!validateDomainId(false, silent)) return;
      const domainId = parseInt(document.getElementById('domain_id').value);
      try {
        const res = await fetch('/api/topics/load', {
          method: 'POST', body: JSON.stringify({ domain_id: domainId })
        });
        const data = await res.json();
        if (data.ok) {
          // No restarts — topics are always listed via subprocess per-session.
          // If the requested domain differs from the server's running domain, show a warning.
          if (data.domain_mismatch) {
            showToast(`⚠️ Topics listed from Domain ${domainId}. Server runs on Domain ${data.server_domain}. Cameras & recording use Domain ${data.server_domain}.`, true);
          }
          availableTopics = data.topics;
          loadedDomainId = domainId;
          if (!silent) showToast('Topics loaded successfully!');
          populateDropdowns();
        } else {
          loadedDomainId = null;
          if (!silent) showConfirmModal('Failed to Load Topics', 'Could not retrieve ROS topics. Please verify that your ROS environment is active and running.', '❌', 'OK', false);
        }
      } catch (e) {
        loadedDomainId = null;
        if (!silent) showConfirmModal('Network Error', 'A connection error occurred while requesting topics from the server.', '❌', 'OK', false);
      }
    }
    
    function populateDropdowns() {
      const jointSelects = [
        'topic_leader_left', 'topic_leader_right',
        'topic_follower_left', 'topic_follower_right',
        'topic_cmd_left', 'topic_cmd_right',
        'topic_leader_cmd_left', 'topic_leader_cmd_right'
      ];
      jointSelects.forEach(selId => {
        const sel = document.getElementById(selId);
        if (!sel) return;
        const currentVal = sel.value;
        sel.innerHTML = '<option value="">-- Select Topic --</option>';
        let foundCurrent = false;
        availableTopics.forEach(t => {
          const opt = document.createElement('option');
          opt.value = t; opt.innerText = t;
          if (t === currentVal) { opt.selected = true; foundCurrent = true; }
          sel.appendChild(opt);
        });
        if (currentVal && !foundCurrent) {
          const opt = document.createElement('option');
          opt.value = currentVal; opt.innerText = currentVal;
          opt.selected = true;
          sel.appendChild(opt);
        }
      });
      document.querySelectorAll('[id$="_topic"]').forEach(sel => {
        if (jointSelects.some(j => sel.id === j)) return;
        if (sel.tagName !== 'SELECT') return;
        populateCameraDropdown(sel.id);
      });
    }

    function populateCameraDropdown(selectId) {
      const sel = document.getElementById(selectId);
      if (!sel) return;
      const currentVal = sel.value;
      sel.innerHTML = '<option value="">-- Select Camera Topic --</option>';
      const imgTopics = availableTopics.filter(t => t.includes('image') || t.includes('compressed') || t.includes('camera'));
      const otherTopics = availableTopics.filter(t => !imgTopics.includes(t));
      const sorted = [...imgTopics, ...otherTopics];
      let foundCurrent = false;
      sorted.forEach(t => {
        const opt = document.createElement('option');
        opt.value = t; opt.innerText = t;
        if (t === currentVal) { opt.selected = true; foundCurrent = true; }
        sel.appendChild(opt);
      });
      if (currentVal && !foundCurrent) {
        const opt = document.createElement('option');
        opt.value = currentVal; opt.innerText = currentVal;
        opt.selected = true;
        sel.appendChild(opt);
      }
    }

    let currentRobotMode = null;

    function updateModeIndicator(mode) {
      currentRobotMode = mode;
      const badge = document.getElementById('mode-toggle-badge');
      const dot = document.getElementById('mode-dot');
      const txt = document.getElementById('mode-badge-text');
      if (!badge || !dot || !txt) return;
      if (mode === 'teach') {
        badge.style.background = 'rgba(245, 158, 11, 0.1)';
        badge.style.color = '#f59e0b';
        badge.style.borderColor = 'rgba(245, 158, 11, 0.25)';
        dot.style.background = '#f59e0b';
        dot.style.boxShadow = '0 0 8px #f59e0b';
        txt.textContent = 'MODE: TEACH';
      } else if (mode === 'normal') {
        badge.style.background = 'rgba(16, 185, 129, 0.1)';
        badge.style.color = 'var(--success)';
        badge.style.borderColor = 'rgba(16, 185, 129, 0.25)';
        dot.style.background = '#10b981';
        dot.style.boxShadow = '0 0 8px #10b981';
        txt.textContent = 'MODE: NORMAL';
      } else {
        badge.style.background = 'rgba(239, 68, 68, 0.1)';
        badge.style.color = '#ef4444';
        badge.style.borderColor = 'rgba(239, 68, 68, 0.25)';
        dot.style.background = '#ef4444';
        dot.style.boxShadow = '0 0 8px #ef4444';
        txt.textContent = `MODE: ${(mode || 'unknown').toUpperCase()}`;
      }
    }

    async function toggleRobotMode() {
      const target = currentRobotMode === 'teach' ? 'normal' : 'teach';
      try {
        const res = await fetch('/api/mode/set', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ mode: target })
        });
        const data = await res.json();
        showToast(data.message || data.error || (data.ok ? 'Mode changed' : 'Mode change failed'), !data.ok);
      } catch (e) {
        showToast('Mode change request failed', true);
      }
    }

    async function updateMotorStats() {
      try {
        const res = await fetch('/api/motor-status');
        const data = await res.json();

        updateModeIndicator(data.mode);

        // 1. Update Battery Display & Warnings
        const battery = Number(data.battery) || 87.0;
        const batVal = document.getElementById('data-battery-val');
        const batFill = document.getElementById('data-battery-fill');
        const warnBanner = document.getElementById('data-warning-banner');
        const safetyBadge = document.getElementById('data-safety-badge');

        if (batVal) batVal.textContent = battery.toFixed(1) + '%';
        if (batFill) {
          batFill.style.width = Math.min(100, Math.max(0, battery)) + '%';
          if (battery <= 30) {
            batFill.style.background = 'linear-gradient(90deg, #ef4444, #dc2626)';
          } else if (battery <= 35) {
            batFill.style.background = 'linear-gradient(90deg, #f59e0b, #eab308)';
          } else {
            batFill.style.background = 'linear-gradient(90deg, #10b981, #34d399)';
          }
        }

        let hasWarning = false;
        let warningText = '';

        if (battery <= 35) {
          hasWarning = true;
          warningText = `⚠️ LOW BATTERY WARNING: Battery level at ${battery.toFixed(1)}% (below 35% threshold)`;
        }

        // 2. Update Motor Temperatures & Thermal Warnings
        const motors = data.motors || [];
        const container = document.getElementById('motor-stats-container');
        const listEl = document.getElementById('data-motor-temp-list');

        if (container) {
          if (!motors.length) {
            container.innerHTML = '<div style="color:#aaa;font-size:0.8rem;padding:8px;">Waiting for motor data...</div>';
          } else {
            container.innerHTML = motors.map(m => {
              const temp = m.temperature !== undefined ? parseFloat(m.temperature).toFixed(1) : '?';
              const highClass = temp > 45 ? 'high' : '';
              return `<div class="motor-stat"><span>${m.name}</span><span class="temp ${highClass}">${temp} °C</span></div>`;
            }).join('');
          }
        }

        if (listEl) {
          if (!motors.length) {
            listEl.innerHTML = '<div style="font-size:0.75rem; color:#64748b; grid-column: 1/-1;">Waiting for motor topics…</div>';
          } else {
            listEl.innerHTML = motors.map(m => {
              const temp = m.temperature !== undefined ? parseFloat(m.temperature) : 38.0;
              const name = m.name || 'Motor';
              
              if (temp > 80) {
                hasWarning = true;
                warningText = `🚨 CRITICAL: Motor [${name}] at ${temp.toFixed(1)}°C (>80°C) — hardware damage risk!`;
              } else if (temp >= 65) {
                hasWarning = true;
                warningText = `🚨 HIGH THERMAL ALERT: Motor [${name}] at ${temp.toFixed(1)}°C (65°C - 80°C)`;
              } else if (temp >= 60 && !hasWarning) {
                hasWarning = true;
                warningText = `⚠️ MOTOR OVERHEAT WARNING: Motor [${name}] elevated at ${temp.toFixed(1)}°C (60°C - 65°C)`;
              }

              let badgeStyle = 'background: rgba(34, 197, 94, 0.1); color: #22c55e; border: 1px solid rgba(34, 197, 94, 0.3);';
              if (temp >= 65) badgeStyle = 'background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.5); font-weight: bold; animation: estopPulse 1.5s infinite;';
              else if (temp >= 60) badgeStyle = 'background: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.5); font-weight: bold;';

              return `<div style="padding: 5px 8px; border-radius: 6px; font-size: 0.72rem; display: flex; justify-content: space-between; align-items: center; ${badgeStyle}">
                <span style="font-weight: 600; text-overflow: ellipsis; overflow: hidden; white-space: nowrap;">${name}</span>
                <span style="font-family: monospace;">${temp.toFixed(1)}°C</span>
              </div>`;
            }).join('');
          }
        }

        // 3. Update Warning Banner & Safety Badge State
        if (warnBanner) {
          if (hasWarning) {
            warnBanner.textContent = warningText;
            warnBanner.style.display = 'block';
          } else {
            warnBanner.style.display = 'none';
          }
        }

        if (safetyBadge) {
          if (hasWarning) {
            safetyBadge.textContent = 'WARNING';
            safetyBadge.style.background = 'rgba(245, 158, 11, 0.2)';
            safetyBadge.style.color = '#f59e0b';
            safetyBadge.style.borderColor = 'rgba(245, 158, 11, 0.4)';
          } else {
            safetyBadge.textContent = 'SAFE';
            safetyBadge.style.background = 'rgba(34, 197, 94, 0.15)';
            safetyBadge.style.color = '#22c55e';
            safetyBadge.style.borderColor = 'rgba(34, 197, 94, 0.3)';
          }
        }

      } catch(e) {
        console.error('updateMotorStats failed', e);
      }
    }
    updateMotorStats();
    setInterval(updateMotorStats, 1500);


      let cameraCount = 0;

    function reindexCameras() {
      const container = document.getElementById('camera-topic-selectors');
      if (!container) return;
      const divs = Array.from(container.children);
      cameraCount = divs.length;

      divs.forEach((div, idx) => {
        const num = idx + 1;
        div.id = 'cam_container_' + num;

        const label = div.querySelector('.cam-number-label');
        if (label) label.innerText = `CAM ${num}`;

        const nameInput = div.querySelector('input');
        if (nameInput) {
          nameInput.id = `cam_${num}_name`;
          nameInput.onchange = () => registerCamera(num);
        }

        const topicSelect = div.querySelector('select');
        if (topicSelect) {
          topicSelect.id = `cam_${num}_topic`;
          topicSelect.onchange = () => registerCamera(num);
        }

        const deleteBtn = div.querySelector('button');
        if (deleteBtn) {
          deleteBtn.onclick = () => removeCamera(num);
        }
      });
    }

    function addCameraTopic(initialName = '', initialTopic = '') {
      const container = document.getElementById('camera-topic-selectors');


      const div = document.createElement('div');
      div.style.cssText = 'display:flex;gap:10px;align-items:center;margin-bottom:8px;';
      div.innerHTML = `
        <label class="cam-number-label" style="width: 80px; font-size:0.8rem; color:var(--text-muted); font-weight:600;">CAM</label>
        <input type="text" placeholder="Name (e.g. wrist_left)" style="flex:1;">
        <select style="flex:2;"></select>
        <button class="btn-danger" style="padding: 6px 10px; font-size: 0.8rem;">X</button>
      `;
      container.appendChild(div);

      reindexCameras();

      const num = cameraCount;
      populateCameraDropdown(`cam_${num}_topic`);

      const nameInput = document.getElementById(`cam_${num}_name`);
      const topicSelect = document.getElementById(`cam_${num}_topic`);

      if (initialTopic) {
        // Ensure the initial topic exists as an option (even before Load Topics is clicked)
        let found = false;
        for (const opt of topicSelect.options) {
          if (opt.value === initialTopic) { found = true; break; }
        }
        if (!found) {
          const opt = document.createElement('option');
          opt.value = initialTopic;
          opt.innerText = initialTopic;
          topicSelect.appendChild(opt);
        }
        topicSelect.value = initialTopic;
      }
      if (initialName) {
        nameInput.value = initialName;
        nameInput.dataset.registeredName = initialName;
      }
    }

    // autoAddDefaultCameras() — call this manually from the browser console if needed.
    // Cameras are intentionally NOT auto-added on startup; user adds them manually.
    async function autoAddDefaultCameras() {
      const defaultCams = {
        'left_wrist': '/left_arm/left/color/image_raw/compressed',
        'right_wrist': '/right_arm/right/color/image_raw/compressed',
        'zed_left': '/zed/zed_node/left/color/raw/image/compressed',
        'zed_right': '/zed/zed_node/right/color/raw/image/compressed'
      };

      const domainId = loadedDomainId;

      for (const [name, topic] of Object.entries(defaultCams)) {
        addCameraTopic(name, topic);
        await fetch('/api/cameras/register', {
          method: 'POST',
          body: JSON.stringify({ name, topic, domain_id: parseInt(domainId) })
        });
        createCameraBoxInUI(name);
      }
    }

    async function removeCamera(num) {
      const nameInput = document.getElementById(`cam_${num}_name`);
      const oldName = nameInput ? nameInput.dataset.registeredName || nameInput.value : '';
      if (oldName) {
        recentlyUnregistered.add(oldName);
        await fetch('/api/cameras/unregister', {
          method: 'POST',
          body: JSON.stringify({ name: oldName })
        });
        const box = document.getElementById('cam-box-' + oldName);
        if (box) box.remove();
        stopCamPoller(oldName);
      }
      const container = document.getElementById('cam_container_' + num);
      if (container) container.remove();

      reindexCameras();
    }

    async function registerCamera(num) {
      const nameInput = document.getElementById(`cam_${num}_name`);
      const topicSelect = document.getElementById(`cam_${num}_topic`);
      if (!nameInput || !topicSelect) return;

      let name = nameInput.value.trim();
      const topic = topicSelect.value;

      if (!topic) return;

      if (!name) {
        if (topic === '/left_arm/left/color/image_raw/compressed') {
          name = 'left_wrist';
        } else if (topic === '/right_arm/right/color/image_raw/compressed') {
          name = 'right_wrist';
        } else if (topic === '/zed/zed_node/left/color/raw/image/compressed') {
          name = 'zed_left';
        } else if (topic === '/zed/zed_node/right/color/raw/image/compressed') {
          name = 'zed_right';
        } else {
          const parts = topic.split('/').filter(Boolean);
          // Skip common non-descriptive ROS topic path words
          const skip = new Set(['compressed', 'image_raw', 'image', 'color', 'raw', 'rect', 'theora', 'ffmpeg']);
          const meaningful = parts.filter(p => {
            const lp = p.toLowerCase();
            return !skip.has(lp) && !lp.includes('node');
          });
          if (meaningful.length >= 2) {
            name = meaningful[0] + '_' + meaningful[1];
          } else if (meaningful.length === 1) {
            name = meaningful[0];
          } else {
            name = `cam_${num}`;
          }
        }
      }

      // Avoid name collisions between different camera inputs
      let isDuplicate = false;
      document.querySelectorAll('[id^="cam_"][id$="_name"]').forEach(input => {
        if (input.id !== `cam_${num}_name` && input.value.trim() === name) {
          isDuplicate = true;
        }
      });
      if (isDuplicate) {
        name = name + '_' + num;
      }
      nameInput.value = name;

      const oldName = nameInput.dataset.registeredName;
      if (oldName && oldName !== name) {
        await fetch('/api/cameras/unregister', {
          method: 'POST',
          body: JSON.stringify({ name: oldName })
        });
        const box = document.getElementById('cam-box-' + oldName);
        if (box) box.remove();
        stopCamPoller(oldName);
      }

      nameInput.dataset.registeredName = name;
      const domainId = loadedDomainId;

      await fetch('/api/cameras/register', {
        method: 'POST',
        body: JSON.stringify({ name, topic, domain_id: parseInt(domainId) })
      });

      // Clear from recentlyUnregistered since we are adding it back
      recentlyUnregistered.delete(name);

      // Create the camera grid box now (only when user explicitly adds)
      createCameraBoxInUI(name);
    }

    function createCameraBoxInUI(name) {
      const grid = document.getElementById('camera-grid');
      if (!grid) return;
      let box = document.getElementById('cam-box-' + name);
      if (!box) {
        box = document.createElement('div');
        box.id = 'cam-box-' + name;
        box.className = 'camera-box';
        box.innerHTML = `
          <img id="cam-img-${name}" src="" style="display:none; width:100%; height:100%; object-fit:cover;"/>
          <div class="cam-waiting" id="cam-wait-${name}">
            <div class="cam-waiting-dot"></div>
            <span>Waiting for feed...</span>
          </div>
          <div class="cam-label" style="display: flex; align-items: center; justify-content: center; gap: 8px;">
            <span class="cam-status-dot" id="cam-status-dot-${name}" style="display: inline-block; width: 8px; height: 8px; border-radius: 50%; background-color: #ef4444; transition: background-color 0.3s;"></span>
            <span class="cam-status-text" id="cam-status-text-${name}" style="font-size: 0.7rem; font-weight: 700; color: #ef4444; transition: color 0.3s;">OFFLINE</span>
            <span style="font-weight: 600;">${name}</span>
          </div>`;
        grid.appendChild(box);
      }
      startCamPoller(name);
    }
    
    let globalPollerActive = false;
    const activeCamerasList = new Set();
    const recentlyUnregistered = new Set();

    function startCamPoller(cam) {
      activeCamerasList.add(cam);
      if (!globalPollerActive) {
        globalPollerActive = true;
        runGlobalPoller();
      }
    }

    function stopCamPoller(cam) {
      activeCamerasList.delete(cam);
      const img = document.getElementById('cam-img-' + cam);
      const waitDiv = document.getElementById('cam-wait-' + cam);
      if (img) { img.style.display = 'none'; img.src = ''; }
      if (waitDiv) waitDiv.style.display = 'flex';
      if (activeCamerasList.size === 0) {
        globalPollerActive = false;
      }
    }

    async function runGlobalPoller() {
      if (!globalPollerActive) return;
      try {
        const res = await fetch('/api/cameras/all-frames');
        const data = await res.json();
        if (data.ok && data.frames) {
          activeCamerasList.forEach(cam => {
            const frame = data.frames[cam];
            const img = document.getElementById('cam-img-' + cam);
            const waitDiv = document.getElementById('cam-wait-' + cam);
            const dot = document.getElementById('cam-status-dot-' + cam);
            const text = document.getElementById('cam-status-text-' + cam);
            if (frame) {
              if (img) {
                if (img.src !== frame) {
                  img.src = frame;
                }
                img.style.display = 'block';
              }
              if (waitDiv) waitDiv.style.display = 'none';
              if (dot) dot.style.backgroundColor = '#10b981'; // Green
              if (text) {
                text.innerText = 'LIVE';
                text.style.color = '#10b981';
              }
            } else {
              if (img) img.style.display = 'none';
              if (waitDiv) waitDiv.style.display = 'flex';
              if (dot) dot.style.backgroundColor = '#ef4444'; // Red
              if (text) {
                text.innerText = 'OFFLINE';
                text.style.color = '#ef4444';
              }
            }
          });
        }
        setTimeout(runGlobalPoller, 100);
      } catch (err) {
        console.error("Poller error:", err);
        setTimeout(runGlobalPoller, 500);
      }
    }
    
    // NOTE: updateCameras() has been intentionally removed.
    // Camera state is now fully per-session (cookie-isolated on the server).
    // Each browser manages its own cameras — the server never pushes cameras
    // from one user's session into another user's browser.

    let liveStepTimer = null;
    function startLiveSteps(hz, maxSteps) {
        clearInterval(liveStepTimer);
        let currentStep = 0;
        const display = document.getElementById('live_steps_display');
        display.innerText = `Steps: 0 / ${maxSteps}`;
        if (hz <= 0) return;
        const intervalMs = 1000 / hz;
        liveStepTimer = setInterval(() => {
            currentStep++;
            display.innerText = `Steps: ${currentStep} / ${maxSteps}`;
            if (currentStep >= maxSteps) {
                clearInterval(liveStepTimer);
            }
        }, intervalMs);
    }
    function stopLiveSteps() {
        clearInterval(liveStepTimer);
        document.getElementById('live_steps_display').innerText = `Steps: Stopped`;
    }

    async function startRecord() {
      if (!validateDomainId(true)) return;
      const activeTaskIdx = document.getElementById('active_record_task').value;
      const taskName = document.getElementById('task' + activeTaskIdx + '_name').value;
      const promptUsed = document.getElementById('prompt' + activeTaskIdx + '_used').value;
      const datasetName = document.getElementById('dataset_name').value;

      if (!datasetName) { showToast('Please provide a dataset identifier', true); return; }
      if (!taskName) { showToast('Please provide a task name', true); return; }
      if (!promptUsed) { showToast('Please provide a prompt instruction', true); return; }

      const getVal = (id) => { const el = document.getElementById(id); return el ? el.value : ''; };
      const topics = {
        leader_topic_left: getVal('topic_leader_left'),
        leader_topic_right: getVal('topic_leader_right'),
        follower_topic_left: getVal('topic_follower_left'),
        follower_topic_right: getVal('topic_follower_right'),
        follower_cmd_topic_left: getVal('topic_cmd_left'),
        follower_cmd_topic_right: getVal('topic_cmd_right'),
        leader_cmd_topic_left: "",
        leader_cmd_topic_right: "",
        camera_topics: {}
      };


      for(let i=1; i<=cameraCount; i++) {
         const nameEl = document.getElementById('cam_' + i + '_name');
         const topicEl = document.getElementById('cam_' + i + '_topic_input') || document.getElementById('cam_' + i + '_topic');
         if(nameEl && topicEl && nameEl.value && topicEl.value) {
             topics.camera_topics[nameEl.value] = topicEl.value;
         }
      }

      const payload = {
        dataset_name: datasetName,
        task: taskName,
        prompt: promptUsed,
        record_hz: parseFloat(getVal('record_hz') || "30"),
        episode_length: parseInt(getVal('episode_len') || "500"),
        max_episodes: parseInt(getVal('max_episodes') || "1"),
        domain_id: parseInt(getVal('domain_id') || "0"),
        interdelay: parseFloat(getVal('interdelay') || "2.0"),
        fps: parseInt(getVal('fps') || "30"),
        topics: topics
      };
      showToast('Starting recording...');
      try {
        const res = await fetch('/api/record/start', { method: 'POST', body: JSON.stringify(payload) });
        const data = await res.json();
        if(data.ok) {
            showToast('Recording request sent — waiting for topics...');
            _statusPollerActive = true;
        } else {
            showToast('Start failed: ' + (data.error || 'Unknown'), true);
        }
      } catch(e) { showToast('Network error: ' + e, true); }
    }
    
    async function stopRecord() {
      try {
        const res = await fetch('/api/record/stop', { method: 'POST' });
        const data = await res.json();
        if(data.ok) {
            showToast('Recording stopped');
            _statusPollerActive = false;
            _statusRecordingStarted = false;
            stopLiveSteps();
            hideRecStatusPanel();
            loadDatasetStats();
        } else {
            showToast('Error: ' + data.error, true);
        }
      } catch(e) { showToast('Network error', true); }
    }
    
    let currentDatasetEpisodes = 0;

    async function startReplay() {
      if (!validateDomainId(true)) return;
      const activeTaskIdx = document.getElementById('replay_task').value;
      const taskName = document.getElementById('task' + activeTaskIdx + '_name').value;
      const promptUsed = document.getElementById('prompt' + activeTaskIdx + '_used').value;

      if (!document.getElementById('replay_dataset').value) {
        showToast('Please provide a dataset name', true);
        return;
      }
      // User enters Episode 1, 2, 3... We convert to 0-based index for the backend
      const episodeDisplay = parseInt(document.getElementById('replay_episode').value);
      const episode = episodeDisplay - 1;  // convert to 0-based

      if (isNaN(episodeDisplay) || episodeDisplay < 1) {
         showToast('Please enter a valid episode number (starting from 1)', true);
         return;
      }
      if (currentDatasetEpisodes > 0 && episodeDisplay > currentDatasetEpisodes) {
         showToast(`Episode ${episodeDisplay} does not exist! You have Episodes 1 to ${currentDatasetEpisodes}`, true);
         return;
      }

      const payload = {
          speed: parseFloat(document.getElementById('replay_speed').value || "1.0"),
          dataset_name: document.getElementById('replay_dataset').value,
          episode_index: episode,
          record_hz: parseFloat(document.getElementById('record_hz').value),
          episode_length: parseInt(document.getElementById('episode_len').value),
          domain_id: parseInt(document.getElementById('domain_id').value || "0"),
          task: taskName,
          prompt: promptUsed
      };
      try {
        const res = await fetch('/api/replay/start', { method: 'POST', body: JSON.stringify(payload) });
        const data = await res.json();
        if(data.ok) {
            showToast(`Replaying Episode ${episodeDisplay}...`);
            const hz = payload.record_hz * payload.speed;
            startLiveSteps(hz, payload.episode_length);
        } else {
            showToast('Error: ' + data.error, true);
        }
      } catch(e) { showToast('Network error', true); }
    }
    
    async function stopReplay() {
      try {
        const res = await fetch('/api/replay/stop', { method: 'POST' });
        const data = await res.json();
        if(data.ok) {
            showToast('Replay stopped');
            stopLiveSteps();
        } else {
            showToast('Error: ' + data.error, true);
        }
      } catch(e) { showToast('Network error', true); }
    }

    async function deleteEpisode() {
      const dataset = document.getElementById('delete_dataset').value;
      // User enters Episode 1, 2, 3... We convert to 0-based index for the backend
      const episodeDisplay = parseInt(document.getElementById('delete_episode').value);
      const episode = episodeDisplay - 1;  // convert to 0-based

      if (!dataset) {
        showToast('Please provide a dataset name', true);
        return;
      }
      if (isNaN(episodeDisplay) || episodeDisplay < 1) {
        showToast('Please enter a valid episode number (starting from 1)', true);
        return;
      }
      if (currentDatasetEpisodes > 0 && episodeDisplay > currentDatasetEpisodes) {
         showToast(`Episode ${episodeDisplay} does not exist! You have Episodes 1 to ${currentDatasetEpisodes}`, true);
         return;
      }

      const confirmed = await showConfirmModal(
        'Delete Episode',
        `Are you sure you want to delete Episode ${episodeDisplay} from dataset "${dataset}"?\nThis action cannot be undone.`,
        '',
        'Delete'
      );
      if (!confirmed) return;

      showToast('Deleting episode...');
      try {
        const res = await fetch('/api/dataset/delete-episode', {
          method: 'POST',
          body: JSON.stringify({ dataset_name: dataset, episode: episode })
        });
        const data = await res.json();
        if(data.ok) {
          showToast(`Episode ${episodeDisplay} deleted successfully`);
          loadDatasetStats();
        } else {
          showToast('Delete failed: ' + (data.error || 'Unknown'), true);
        }
      } catch(e) {
        showToast('Network error: ' + e, true);
      }
    }

    function syncDatasetNames() {
      const sourceName = document.getElementById('dataset_name').value.trim();
      const fallbackName = sourceName || 'box_pick_and_place';
      const ids = ['stats_query_dataset', 'replay_dataset', 'delete_dataset'];

      ids.forEach(id => {
        const el = document.getElementById(id);
        if (!el) return;
        el.value = sourceName || el.value || '';
        el.placeholder = `e.g. ${fallbackName}`;
      });

      // Do NOT auto-load dataset stats here — only load when explicitly requested
      // or after a recording completes. This prevents cross-session data leakage.
    }

    async function loadDatasetStats() {
      const datasetName = document.getElementById('stats_query_dataset').value.trim()
        || document.getElementById('dataset_name').value.trim();
      if (!datasetName) {
        showToast('Please specify a dataset to query', true);
        return;
      }
      const display = document.getElementById('dataset-stats-display');
      display.innerHTML = '<span style="color:#aaa;">Loading...</span>';
      try {
        const res = await fetch(`/api/dataset/info?dataset_name=${encodeURIComponent(datasetName)}`);
        const data = await res.json();
        if (data.ok) {
          currentDatasetEpisodes = data.episode_count;
          // Show episode range as 1-based (Episode 1 to N) — no confusing index talk
          let helperText = data.episode_count > 0
            ? `(Episode 1 to ${data.episode_count})`
            : '(No episodes yet)';

          let cleanedTasks = [];
          if (data.task_names) {
            data.task_names.forEach(t => {
              if (t.includes('^C') || t.includes('\x03')) return;
              let clean = t.trim();
              if (clean === 'pick_object') {
                clean = 'Pick Object';
              } else if (clean.includes('_') && !clean.includes(' ')) {
                clean = clean.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
              }
              if (clean) {
                clean = clean.charAt(0).toUpperCase() + clean.slice(1);
                if (!cleanedTasks.includes(clean)) {
                  cleanedTasks.push(clean);
                }
              }
            });
          }

          let tasksHtml = '';
          if (cleanedTasks.length > 0) {
            tasksHtml = `<div style="margin-top: 4px; padding-left: 10px; font-size: 0.8rem; color: var(--text-muted); display: flex; flex-direction: column; gap: 4px;">` + 
                         cleanedTasks.map(t => `<div style="display: flex; gap: 6px; align-items: flex-start;"><span>•</span><span>${t}</span></div>`).join('') + 
                        `</div>`;
          } else {
            tasksHtml = ' <span style="color:#aaa;">None</span>';
          }

          display.innerHTML = `
            <div style="display:grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 10px;">
              <div style="background: rgba(2, 132, 199, 0.08); padding: 8px 12px; border-radius: 8px; border: 1px solid rgba(2, 132, 199, 0.2); text-align: center;">
                <div style="font-size: 0.68rem; color: var(--text-muted); text-transform: uppercase; font-weight: 700; letter-spacing: 0.04em;">Total Episodes</div>
                <div style="font-size: 1.3rem; font-weight: 800; color: var(--primary); font-family: 'JetBrains Mono', monospace; margin-top: 2px;">${data.episode_count}</div>
              </div>
              <div style="background: rgba(2, 132, 199, 0.08); padding: 8px 12px; border-radius: 8px; border: 1px solid rgba(2, 132, 199, 0.2); text-align: center;">
                <div style="font-size: 0.68rem; color: var(--text-muted); text-transform: uppercase; font-weight: 700; letter-spacing: 0.04em;">Total Frames</div>
                <div style="font-size: 1.3rem; font-weight: 800; color: var(--primary); font-family: 'JetBrains Mono', monospace; margin-top: 2px;">${data.total_frames}</div>
              </div>
            </div>
            <div style="padding: 8px 10px; background: rgba(0, 0, 0, 0.03); border-radius: 6px; border: 1px solid var(--border);">
              <b style="color: var(--text-main); font-size: 0.78rem;">Tasks (${cleanedTasks.length}):</b>${tasksHtml}
            </div>
          `;

          const replayHelper = document.getElementById('replay-episode-helper');
          if (replayHelper) replayHelper.innerText = helperText;
          const deleteHelper = document.getElementById('delete-episode-helper');
          if (deleteHelper) deleteHelper.innerText = helperText;
          
          showToast('Stats loaded successfully');
        } else {
          display.innerHTML = `<span style="color:var(--danger);">${data.error || 'Failed to load'}</span>`;
          showToast('Stats load failed', true);
        }
      } catch (e) {
        display.innerHTML = '<span style="color:var(--danger);">Error fetching stats</span>';
        showToast('Network error loading stats', true);
      }
    }
    
    // ── Recorder status polling ────────────────────────────────────────────
    let _statusPollerActive = false;
    let _statusRecordingStarted = false;

    async function checkBackgroundStatus() {
      // Only process recording status if the user has loaded topics AND their
      // domain matches the server's running domain. This prevents User B (on domain 0
      // or domain 2) from seeing recording activity that belongs to User A (domain 18).
      if (!loadedDomainId) return;
      try {
        const res = await fetch('/api/recorder/status');
        const data = await res.json();
        if (!data.ok) return;

        // If the server is running on a different domain than this session, hide status.
        if (data.server_domain !== undefined && data.server_domain !== loadedDomainId) return;

        if (data.replay_active) {
          const overlays = document.querySelectorAll('.replay-mode-overlay');
          overlays.forEach(overlay => overlay.style.display = 'none');
        }

        if (data.recording) {
          if (!_statusRecordingStarted) {
            _statusRecordingStarted = true;
            showToast('Recording active');
            hideRecStatusPanel();
          }
          
          if (data.dataset_name) {
            const ids = ['dataset_name', 'stats_query_dataset', 'replay_dataset', 'delete_dataset'];
            ids.forEach(id => {
              const el = document.getElementById(id);
              if (el && el.value !== data.dataset_name) {
                el.value = data.dataset_name;
              }
            });
          }
          
          const display = document.getElementById('live_steps_display');
          if (display) {
            display.innerText = `Steps: ${data.step_count} / ${data.max_steps}`;
          }

          updateValidationPanel(data);
        } else {
          updateValidationPanel(data);
          if (_statusRecordingStarted) {
            _statusRecordingStarted = false;
            _statusPollerActive = false;
            stopLiveSteps();
            hideRecStatusPanel();
            showToast('Recording stopped and saved successfully');
            loadDatasetStats();
          } else {
            if (_statusPollerActive) {
              showRecStatusPanel(data.missing || []);
            }
          }
        }
      } catch (e) {}
    }

    function updateValidationPanel(data) {
      const panel = document.getElementById('validation-blocked-panel');
      const msgEl = document.getElementById('validation-blocked-message');
      if (!panel || !msgEl) return;
      if (data.validation_blocked) {
        const info = data.last_episode_validation;
        const issues = (info && info.issues) ? info.issues.map(i => i.message || i.code).join('; ') : '';
        msgEl.innerText = `⚠️ Episode ${info ? info.episode : ''} failed validation${issues ? ': ' + issues : ''}. Recording is paused.`;
        panel.style.display = 'block';
      } else {
        panel.style.display = 'none';
      }
    }

    async function acknowledgeValidation() {
      try {
        const res = await fetch('/api/record/acknowledge_validation', { method: 'POST', body: JSON.stringify({}) });
        const data = await res.json();
        if (data.ok) {
          showToast(data.message || 'Acknowledged. Resuming.');
          document.getElementById('validation-blocked-panel').style.display = 'none';
        } else {
          showToast('Acknowledge failed: ' + (data.error || 'Unknown'), true);
        }
      } catch (e) { showToast('Network error: ' + e, true); }
    }

    // Run this continuous checker every 100ms for high responsiveness
    setInterval(checkBackgroundStatus, 100);

    function showRecStatusPanel(missingList) {
      const panel = document.getElementById('rec-status-panel');
      const list = document.getElementById('rec-status-list');
      if (!panel || !list) return;
      if (missingList.length === 0) {
        list.innerHTML = '<span style="color:#166534;">All topics delivering data ✓</span>';
      } else {
        list.innerHTML = missingList.map(t =>
          `<div>⚠️ <b>${t.role || t}</b>: ${t.topic || ''} — ${t.status || 'MISSING'} (${t.publishers || 0} pub${(t.publishers||0)!==1?'s':''})</div>`
        ).join('');
      }
      panel.style.display = 'block';
    }

    function hideRecStatusPanel() {
      const panel = document.getElementById('rec-status-panel');
      if (panel) panel.style.display = 'none';
    }

    async function loadConfig() {
      updateTaskLabels();
      try {
        const res = await fetch('/api/config');
        const data = await res.json();
        if (!data.ok) { console.warn('Config load failed:', data.error); return; }

        const topics = data.topics || {};
        const recording = data.recording || {};

        if (recording.record_hz && document.getElementById('record_hz')) document.getElementById('record_hz').value = recording.record_hz;
        if (recording.episode_len && document.getElementById('episode_len')) document.getElementById('episode_len').value = recording.episode_len;
        if (recording.inter_episode_delay && document.getElementById('interdelay')) document.getElementById('interdelay').value = recording.inter_episode_delay;
        if (recording.fps && document.getElementById('fps')) document.getElementById('fps').value = recording.fps;
        if (recording.max_episodes && document.getElementById('max_episodes')) document.getElementById('max_episodes').value = recording.max_episodes;
        
        setSelectValue('topic_leader_cmd_right', topics.leader_cmd_topic_right);
      } catch(e) {
        console.error('loadConfig error:', e);
      }
    }

    function initFixed4CameraGrid() {
      const fixedCameras = [
        { name: "Primary Binocular Vision (Left)",    topic: "/zed/zed_node/left/color/rect/image/compressed" },
        { name: "Primary Binocular Vision (Right)",   topic: "/zed/zed_node/right/color/rect/image/compressed" },
        { name: "Left Wrist Camera",                  topic: "/left/camera/color/image_raw/compressed" },
        { name: "Right Wrist Camera",                 topic: "/right/camera/color/image_raw/compressed" }
      ];

      const domainId = parseInt(loadedDomainId) || 33;

      fixedCameras.forEach(cam => {
        fetch('/api/cameras/register', {
          method: 'POST',
          body: JSON.stringify({ name: cam.name, topic: cam.topic, domain_id: domainId })
        }).catch(e => {});
        createCameraBoxInUI(cam.name);
      });
    }

    loadConfig();
    // Auto-load topics for domain 33 on startup so cameras connect immediately
    loadTopics(true).then(() => initFixed4CameraGrid());
    // Also init camera grid immediately (before topics finish loading) for UI display
    initFixed4CameraGrid();

    // Real-time Theme Sync with Main Dashboard UI (app.py)
    async function syncThemeWithMainApp() {
      const host = window.location.hostname || 'localhost';
      try {
        const res = await fetch(`http://${host}:7070/api/theme`);
        if (res.ok) {
          const data = await res.json();
          if (data.theme === 'light') {
            document.documentElement.classList.add('light-mode');
            document.body.classList.add('light-mode');
            localStorage.setItem('theme', 'light');
            return;
          } else if (data.theme === 'dark') {
            document.documentElement.classList.remove('light-mode');
            document.body.classList.remove('light-mode');
            localStorage.setItem('theme', 'dark');
            return;
          }
        }
      } catch(e) {}

      const urlParams = new URLSearchParams(window.location.search);
      const urlTheme = urlParams.get('theme');
      const activeTheme = urlTheme || localStorage.getItem('theme') || localStorage.getItem('daksha_theme');
      if (activeTheme === 'light') {
        document.documentElement.classList.add('light-mode');
        document.body.classList.add('light-mode');
      } else {
        document.documentElement.classList.remove('light-mode');
        document.body.classList.remove('light-mode');
      }
    }

    syncThemeWithMainApp();
    setInterval(syncThemeWithMainApp, 300);
    window.addEventListener('storage', syncThemeWithMainApp);
    window.addEventListener('focus', syncThemeWithMainApp);
    document.addEventListener('visibilitychange', () => {
      if (!document.hidden) {
        syncThemeWithMainApp();
      }
    });
    try {
      const themeBc = new BroadcastChannel('ihub_theme_channel');
      themeBc.onmessage = (e) => {
        if (e.data && e.data.theme) {
          if (e.data.theme === 'light') {
            document.documentElement.classList.add('light-mode');
            document.body.classList.add('light-mode');
          } else {
            document.documentElement.classList.remove('light-mode');
            document.body.classList.remove('light-mode');
          }
        }
      };
    } catch(err) {}

  </script>
</body>
</html>
"""

def _get_default_config_path():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.abspath(os.path.join(base_dir, '..', 'config', 'config.yaml')),
        os.path.abspath(os.path.join(base_dir, 'config', 'config.yaml')),
    ]
    try:
        from ament_index_python.packages import get_package_share_directory
        candidates.append(os.path.join(
            get_package_share_directory("daksha_data_collection"), "config", "config.yaml"))
    except Exception:
        pass
    for c in candidates:
        if os.path.exists(c):
            return c
    return candidates[0]

class DataManagementUINode(Node):
    CONFIG_PATH = _get_default_config_path()

    def get_dataset_base_dir(self):
        try:
            with open(self.CONFIG_PATH, 'r') as f:
                cfg = yaml.safe_load(f) or {}
            root_dir = cfg.get('dataset', {}).get('root_dir')
            if root_dir:
                return os.path.expanduser(root_dir)
        except Exception:
            pass
        return DATASET_BASE_DIR

    def __init__(self, camera_node: CameraDisplayNode):
        super().__init__('data_management_ui_controller')
        self.camera_node = camera_node
        self.get_logger().info('Initializing DataManagementUINode...')
        
        # Native service clients
        self.cli_rec_start = self.create_client(StartRecord, '/recorder/start')
        self.cli_rec_stop = self.create_client(Trigger, '/recorder/stop')
        self.cli_rec_ack_validation = self.create_client(Trigger, '/recorder/acknowledge_validation')
        self.cli_rep_start = self.create_client(StartReplay, '/replay/start')
        self.cli_rep_stop = self.create_client(Trigger, '/replay/stop')

        # Self-healing: this UI is meant to run alongside ros2_topic_recorder
        # and ros2_topic_replay (see launch/data_collection.launch.py), but
        # in practice it keeps getting started alone via a bare
        # `ros2 run daksha_data_collection web_data_management_ui` --
        # leaving /recorder/start (and /replay/start) with no server behind
        # them, so every Start Record/Replay click fails with "service is
        # not available" until someone notices and manually launches the
        # missing node. Checking here and auto-launching whatever's missing
        # makes this UI self-sufficient regardless of how it was started.
        # Delayed (not checked immediately): service discovery needs a few
        # spin cycles to populate after this node is added to an executor,
        # and that hasn't happened yet at __init__ time.
        self._dep_check_timer = self.create_timer(3.0, self._ensure_dependent_nodes)

        self._rec_state = False  # False = idle/waiting, True = recording
        self._rec_missing: list = []
        self._rec_step = 0
        self._rec_max_steps = 0
        self._configured_topics: dict = {}   # role→topic for status checks
        self._replay_active = False
        self._record_active = False
        
        # Guards the read-modify-write of CONFIG_PATH in start_record(): the
        # HTTP server is threaded, so two near-simultaneous Start Record
        # requests (double-click, slow retry) could otherwise race and let
        # one request's dataset/task/topic selection silently clobber the
        # other's before the recorder ever reads the file.
        self._config_lock = threading.Lock()

        # Motor status from real ROS topics
        self._motor_data = {}   # {'left': [...], 'right': [...]}
        self._motor_lock = threading.Lock()
        self.create_subscription(
            MotorStatusArray,
            '/LeftArmSystem/motor_status',
            lambda msg: self._motor_cb(msg, 'left'),
            10
        )
        self.create_subscription(
            MotorStatusArray,
            '/RightArmSystem/motor_status',
            lambda msg: self._motor_cb(msg, 'right'),
            10
        )
        self.get_logger().info('Subscribed to /LeftArmSystem/motor_status and /RightArmSystem/motor_status')

        # Current mode_toggler status ("teach" / "normal" / "transitioning" / ...)
        self._mode_status = "unknown"
        self._mode_status_lock = threading.Lock()
        self.create_subscription(
            String, "/mode_toggler/status", self._mode_status_cb, MODE_STATUS_QOS,
        )

        # Subscribe to recorder's UI status (allows UI sync even when started via terminal)
        self._last_recorder_status = {}
        self.create_subscription(
            String,
            '/recorder/ui_status',
            self._recorder_status_callback,
            10
        )

        # Subscribe to replay's UI status (allows UI sync even when started via terminal)
        self._last_replay_status = {}
        self._replay_video_thread_running = False
        self.create_subscription(
            String,
            '/replay/ui_status',
            self._replay_status_callback,
            10
        )

        # teleop_mux removed: UI is data-collection only, no robot control

    def _recorder_status_callback(self, msg: String):
        try:
            self._last_recorder_status = json.loads(msg.data)
            self._rec_state = self._last_recorder_status.get('recording', False)
            if self._rec_state:
                cam_topics = self._last_recorder_status.get('camera_topics', {})
                for name, topic in cam_topics.items():
                    if name not in self.camera_node.ui_active_cameras:
                        self.camera_node._subscription_queue.put({'action': 'register', 'name': name, 'topic': topic})
        except Exception as e:
            pass

    def _replay_status_callback(self, msg: String):
        try:
            status = json.loads(msg.data)
            self._last_replay_status = status
            is_playing = status.get('is_playing', False)
            self._replay_active = is_playing
            
            if is_playing and not self._replay_video_thread_running:
                dataset_name = status.get('dataset_name', '')
                episode_index = status.get('episode_index', 0)
                speed = status.get('speed', 1.0)
                total_steps = status.get('total_steps', 0)
                
                if dataset_name and total_steps > 0:
                    record_hz = 30.0
                    try:
                        record_hz = float(self.get_config().get('recording', {}).get('record_hz', 30.0))
                    except Exception:
                        pass
                    hz = record_hz * speed
                    threading.Thread(
                        target=self._replay_video_thread,
                        args=(dataset_name, episode_index, hz, total_steps),
                        daemon=True
                    ).start()
        except Exception as e:
            self.get_logger().error(f"Error in replay status callback: {e}")

    def _ensure_dependent_nodes(self) -> None:
        """One-shot check (see the timer in __init__): launch
        ros2_topic_recorder / ros2_topic_replay ourselves if their services
        aren't up yet, so this UI works whether it was started via the
        proper launch file or standalone."""
        self._dep_check_timer.cancel()
        try:
            if not self.cli_rec_start.service_is_ready():
                self.get_logger().warn(
                    "/recorder/start not available -- launching ros2_topic_recorder"
                )
                subprocess.Popen(
                    ["ros2", "run", "daksha_data_collection", "ros2_topic_recorder"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    preexec_fn=os.setsid,
                )
            if not self.cli_rep_start.service_is_ready():
                self.get_logger().warn(
                    "/replay/start not available -- launching ros2_topic_replay"
                )
                subprocess.Popen(
                    ["ros2", "run", "daksha_data_collection", "ros2_topic_replay"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    preexec_fn=os.setsid,
                )
        except Exception as e:
            self.get_logger().error(f"Dependent-node self-check failed: {e}")

    def _motor_cb(self, msg: MotorStatusArray, side: str):
        """Cache latest per-motor status (id/error/error_name/mos_temp/rotor_temp)."""
        motors = []
        for m in msg.motors:
            motors.append({
                'name': f'motor_{m.id}',
                'error_name': m.error_name,
                'mos_temp': float(m.mos_temp),
                'rotor_temp': float(m.rotor_temp),
            })
        with self._motor_lock:
            self._motor_data[side] = motors

    def _mode_status_cb(self, msg):
        with self._mode_status_lock:
            self._mode_status = msg.data

    def get_mode_status(self):
        with self._mode_status_lock:
            return self._mode_status

    def get_motor_status(self):
        """Return combined left + right motor data as list, plus live battery telemetry."""
        with self._motor_lock:
            all_motors = (
                self._motor_data.get('left', []) +
                self._motor_data.get('right', [])
            )
        
        battery = 87.0
        try:
            import urllib.request
            req = urllib.request.Request("http://localhost:7070/api/telemetry", headers={"User-Agent": "DataUI"})
            with urllib.request.urlopen(req, timeout=0.5) as resp:
                tel = json.loads(resp.read().decode())
                if "battery" in tel:
                    battery = float(tel["battery"])
                if not all_motors:
                    # Map Daksha motor telemetry format if active
                    left_m = tel.get("motors_left", [])
                    right_m = tel.get("motors_right", [])
                    formatted = []
                    for m in left_m:
                        formatted.append({"name": f"Left Joint {m.get('id','?')}", "temperature": m.get('rotor_temp', 38.0), "status": m.get('error_name', 'Enabled')})
                    for m in right_m:
                        formatted.append({"name": f"Right Joint {m.get('id','?')}", "temperature": m.get('rotor_temp', 38.0), "status": m.get('error_name', 'Enabled')})
                    all_motors = formatted
        except Exception:
            pass

        return {
            'ok': True,
            'motors': all_motors,
            'battery': battery,
            'mode': self.get_mode_status(),
        }

    def get_recorder_status(self):
        """Return recording state + per-topic status using native fast rclpy checks."""
        server_domain = 0
        try:
            server_domain = int(os.environ.get('ROS_DOMAIN_ID', '0'))
        except Exception:
            pass

        recorder_alive = False
        try:
            if self.count_publishers('/recorder/ui_status') > 0:
                recorder_alive = True
        except Exception:
            pass

        if not recorder_alive:
            self._rec_state = False
            self._last_recorder_status = {}

        recording = self._rec_state
        step_count = 0
        max_steps = 500
        dataset_name = ""
        validation_blocked = False
        last_episode_validation = None

        if recorder_alive and self._last_recorder_status:
            recording = self._last_recorder_status.get('recording', False)
            step_count = self._last_recorder_status.get('step_count', 0)
            max_steps = self._last_recorder_status.get('max_steps', 500)
            dataset_name = self._last_recorder_status.get('dataset_name', "")
            validation_blocked = self._last_recorder_status.get('validation_blocked', False)
            last_episode_validation = self._last_recorder_status.get('last_episode_validation')

        if not self._configured_topics:
            return {
                'ok': True,
                'recording': recording,
                'step_count': step_count,
                'max_steps': max_steps,
                'dataset_name': dataset_name,
                'replay_active': self._replay_active,
                'missing': [],
                'server_domain': server_domain,
                'validation_blocked': validation_blocked,
                'last_episode_validation': last_episode_validation
            }

        missing = []
        for role, topic in self._configured_topics.items():
            if not topic:
                continue
            try:
                pubs = self.count_publishers(topic)
                if pubs == 0:
                    missing.append({'role': role, 'topic': topic,
                                    'status': 'NO_PUB', 'publishers': 0})
            except Exception:
                missing.append({'role': role, 'topic': topic,
                                'status': 'ERROR', 'publishers': 0})

        return {
            'ok': True,
            'recording': recording,
            'step_count': step_count,
            'max_steps': max_steps,
            'dataset_name': dataset_name,
            'replay_active': self._replay_active,
            'missing': missing,
            'server_domain': server_domain,
            'validation_blocked': validation_blocked,
            'last_episode_validation': last_episode_validation
        }

    def get_config(self):
        """Read config.yaml and return a JSON-safe dict for the UI."""
        try:
            with open(self.CONFIG_PATH, 'r') as f:
                cfg = yaml.safe_load(f) or {}
            topics_cfg  = cfg.get('topics', {})
            recording_cfg = cfg.get('recording', {})
            dataset_cfg = cfg.get('dataset', {})
            camera_topics = topics_cfg.pop('camera_topics', {}) or {}
            domain_id = cfg.get('domain_id')
            if domain_id is None:
                domain_id = recording_cfg.get('domain_id', 0)
            return {
                'ok': True,
                'topics': topics_cfg,
                'camera_topics': camera_topics,
                'recording': recording_cfg,
                'dataset_name': dataset_cfg.get('dataset_name', 'my_dataset'),
                'domain_id': domain_id
            }
        except Exception as e:
            return {'ok': False, 'error': str(e)}
        
    def _log_steps_thread(self, hz, max_steps, action_name):
        if hz <= 0: return
        interval = 1.0 / hz
        for step in range(1, max_steps + 1):
            if not getattr(self, f'_{action_name}_active', False):
                break
            self.get_logger().info(f"Live {action_name} step: {step} / {max_steps}")
            time.sleep(interval)
        self.get_logger().info(f"{action_name.capitalize()} completed.")
        setattr(self, f'_{action_name}_active', False)
        
    def _replay_video_thread(self, dataset_name, episode_index, hz, max_steps):
        self.get_logger().info(f"Replay video thread started for episode {episode_index} at {hz} Hz")
        self._replay_video_thread_running = True
        self.camera_node.set_replay_mode(True)
        
        base_dir = self.get_dataset_base_dir()
        
        # Load camera keys
        camera_keys = []
        base = Path(base_dir) / dataset_name
        info_file = base / "info.json"
        if not info_file.exists():
            info_file = base / "ros2_topics.json"
        if info_file.exists():
            try:
                with open(info_file, 'r') as f:
                    raw_info = json.load(f)
                if "params" in raw_info and "camera_topics" in raw_info["params"].get("topics", {}):
                    camera_keys = list(raw_info["params"]["topics"]["camera_topics"].keys())
                elif "topics" in raw_info and "camera_topics" in raw_info["topics"]:
                    camera_keys = list(raw_info["topics"]["camera_topics"].keys())
                elif "camera_topics" in raw_info:
                    camera_keys = list(raw_info["camera_topics"].keys())
                elif "camera_keys" in raw_info:
                    camera_keys = list(raw_info["camera_keys"])
            except Exception:
                pass
        
        caps = {}
        for key in camera_keys:
            video_glob = os.path.join(base_dir, dataset_name, "videos", key, "chunk-*", f"episode_{episode_index:06d}.mp4")
            matches = glob.glob(video_glob)
            if matches:
                cap = cv2.VideoCapture(matches[0])
                if cap.isOpened():
                    caps[key] = cap
                    self.get_logger().info(f"Opened video for camera {key}: {matches[0]}")
        
        if not caps:
            # Fallback auto-detect
            videos_dir = os.path.join(base_dir, dataset_name, "videos")
            if os.path.isdir(videos_dir):
                for key in os.listdir(videos_dir):
                    video_glob = os.path.join(videos_dir, key, "chunk-*", f"episode_{episode_index:06d}.mp4")
                    matches = glob.glob(video_glob)
                    if matches:
                        cap = cv2.VideoCapture(matches[0])
                        if cap.isOpened():
                            caps[key] = cap
                            self.get_logger().info(f"Opened auto-detected video for camera {key}: {matches[0]}")

        interval = 1.0 / hz if hz > 0 else 0.033
        
        ui_cams = self.camera_node.get_camera_names()
        def get_ui_name(video_key):
            if video_key in ui_cams:
                return video_key
            stripped = video_key.replace("observation.images.", "")
            if stripped in ui_cams:
                return stripped
            for ui_cam in ui_cams:
                if ui_cam in video_key:
                    return ui_cam
            return video_key

        try:
            for step in range(1, max_steps + 1):
                if not self._replay_active:
                    break
                
                start_time = time.time()
                
                # Read and process frames
                for camera_key, cap in caps.items():
                    ret, frame = cap.read()
                    if ret:
                        ui_name = get_ui_name(camera_key)
                        
                        # Draw professional overlay (Clean Replay HUD)
                        h, w, c = frame.shape
                        # Small, elegant semi-transparent box in top left for the blinking badge
                        cv2.rectangle(frame, (10, 10), (145, 38), (0, 0, 0), -1)
                        
                        show_blink = int(time.time() * 2) % 2 == 0
                        if show_blink:
                            cv2.circle(frame, (25, 24), 6, (0, 0, 255), -1)
                            cv2.putText(frame, "REPLAY", (42, 29), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
                        else:
                            cv2.circle(frame, (25, 24), 6, (0, 0, 50), -1)
                            cv2.putText(frame, "REPLAY", (42, 29), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 2)

                        # Progress step in bottom left
                        step_str = f"STEP: {step}/{max_steps}"
                        cv2.rectangle(frame, (10, h - 35), (150, h - 10), (0, 0, 0), -1)
                        cv2.putText(frame, step_str, (20, h - 18), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1)
                        
                        # Full frame red border for active replay highlight
                        cv2.rectangle(frame, (0, 0), (w-1, h-1), (0, 0, 255), 2)
                        
                        _, buffer = cv2.imencode('.jpg', frame)
                        jpeg_bytes = buffer.tobytes()
                        self.camera_node.inject_frame(ui_name, jpeg_bytes)
                
                elapsed = time.time() - start_time
                sleep_time = max(0.0, interval - elapsed)
                time.sleep(sleep_time)
        except Exception as e:
            self.get_logger().error(f"Error in replay video thread: {e}")
        finally:
            for cap in caps.values():
                cap.release()
            self.camera_node.set_replay_mode(False)
            self._replay_active = False
            self._replay_video_thread_running = False
            self.get_logger().info("Replay video thread terminated.")

    def get_topics_for_domain(self, domain_id, calling_session=None):
        """List ROS topics for the requested domain_id.

        This method NEVER restarts the server. Topics are always listed via a
        subprocess call with the requested domain ID as an env variable, so any
        domain can be queried without disrupting other users.

        If the requested domain differs from the server's running domain, a
        'domain_mismatch' flag is returned so the UI can display a clear warning.
        Camera subscriptions and recording always use the server's running domain.
        """
        try:
            try:
                domain_id_int = int(domain_id)
                if domain_id_int < 0 or domain_id_int > 232:
                    return {"ok": False, "error": f"Invalid Domain ID {domain_id}. Must be between 0 and 232."}
            except (ValueError, TypeError):
                return {"ok": False, "error": f"Invalid Domain ID {domain_id}. Must be an integer."}

            current_domain_str = os.environ.get('ROS_DOMAIN_ID', '0')
            try:
                current_domain = int(current_domain_str)
            except ValueError:
                current_domain = 0

            # Always list topics via subprocess with the requested domain.
            # This never requires a restart and never affects other users.
            env = os.environ.copy()
            env['ROS_DOMAIN_ID'] = str(domain_id_int)
            cmd = ['ros2', 'topic', 'list']
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=5.0, env=env)
                topics = [t for t in result.stdout.split('\n') if t] if result.returncode == 0 else []
            except Exception:
                topics = []

            if domain_id_int != current_domain:
                # Different domain — inform the UI about recording limitation, but do NOT restart.
                # Cameras now work on any domain via per-domain rclpy contexts.
                # Only the recorder/replay ROS services are bound to the server's startup domain.
                self.get_logger().info(
                    f"Session queried domain {domain_id_int} (server recorder domain: {current_domain}). "
                    "Topics listed and cameras will work. Recording uses the server's domain."
                )
                return {
                    "ok": True,
                    "topics": topics,
                    "server_domain": current_domain,
                    "domain_mismatch": domain_id_int != current_domain,
                    "warning": (
                        f"Recording & replay services run on Domain {current_domain} "
                        f"(the server's startup domain). "
                        f"Your cameras on Domain {domain_id_int} will work normally."
                    )
                }

            return {"ok": True, "topics": topics, "server_domain": current_domain}

        except Exception as e:
            return {"ok": False, "error": str(e)}

    def start_record(self, params):
        try:
            dataset_name = str(params.get('dataset_name', '')).strip()
            episode_length = int(params.get('episode_length', 500))
            record_hz = float(params.get('record_hz', 30.0))
            max_episodes = int(params.get('max_episodes', 1))
            domain_id = int(params.get('domain_id', 0))
            task = str(params.get('task', '')).strip()
            prompt = str(params.get('prompt', '')).strip()
            topics_data = params.get('topics', {})
            interdelay = float(params.get('interdelay', 5.0))
            fps = int(params.get('fps', 10))

            if not dataset_name or not task or not prompt:
                return {
                    "ok": False,
                    "error": "Dataset name, task name, and prompt are required before recording."
                }

            # Store configured topics for status polling
            self._configured_topics = {
                'leader_left':   topics_data.get('leader_topic_left', ''),
                'leader_right':  topics_data.get('leader_topic_right', ''),
                'follower_left': topics_data.get('follower_topic_left', ''),
                'follower_right':topics_data.get('follower_topic_right', ''),
                'f_cmd_left':    topics_data.get('follower_cmd_topic_left', ''),
                'f_cmd_right':   topics_data.get('follower_cmd_topic_right', ''),
                'l_cmd_left':    topics_data.get('leader_cmd_topic_left', ''),
                'l_cmd_right':   topics_data.get('leader_cmd_topic_right', ''),
            }
            self._configured_topics = {k: v for k, v in self._configured_topics.items() if v}
            self._rec_state = False

            # Update configuration YAML file
            try:
                with self._config_lock:
                    with open(self.CONFIG_PATH, 'r') as f:
                        cfg = yaml.safe_load(f) or {}

                    cfg.setdefault('dataset', {})['dataset_name'] = dataset_name
                    cfg['dataset']['task'] = task
                    cfg['dataset']['prompt'] = prompt

                    cfg.setdefault('recording', {})['record_hz'] = record_hz
                    cfg['recording']['episode_len'] = episode_length
                    cfg['recording']['max_episodes'] = max_episodes
                    cfg['recording']['domain_id'] = domain_id
                    cfg['recording']['inter_episode_delay'] = interdelay
                    cfg['recording']['fps'] = fps
                    cfg['domain_id'] = domain_id

                    if topics_data:
                        # Merge only non-empty values: the browser sends a full
                        # topics object shaped like the config on every request,
                        # so a session that starts recording before "Load
                        # Topics" has populated the pickers (or before the
                        # camera list has loaded) sends blank strings / an empty
                        # camera_topics dict for everything -- a blind .update()
                        # would silently blank out a previously-good config
                        # (including all camera topics) and let recording start
                        # with nothing actually wired up. Keep whatever's
                        # already configured for any key the browser left empty.
                        def _merge_nonempty(dst: dict, src: dict) -> None:
                            for k, v in src.items():
                                if v:
                                    dst[k] = v

                        _merge_nonempty(cfg.setdefault('topics', {}), topics_data)
                        _merge_nonempty(cfg.setdefault('recording_topics', {}), topics_data)

                    with open(self.CONFIG_PATH, 'w') as f:
                        yaml.dump(cfg, f, default_flow_style=False, sort_keys=False)
                    self.get_logger().info("Updated config.yaml with new recording parameters and topics.")
            except Exception as e:
                self.get_logger().error(f"Failed to update config.yaml: {e}")

            # Persist metadata alongside the dataset
            base_dir = self.get_dataset_base_dir()
            dataset_dir = os.path.join(base_dir, dataset_name)
            os.makedirs(dataset_dir, exist_ok=True)

            topics_file = os.path.join(dataset_dir, "ros2_topics.json")
            topics_map = {}
            if topics_data:
                topics_map.update(topics_data)
            
            joint_cmd = topics_map.get('joint_cmd_topic') or '/joint_cmd'
            topics_map.setdefault('follower_cmd_topic_left', joint_cmd)
            topics_map.setdefault('follower_cmd_topic_right', joint_cmd)

            saved = {
                'task': task,
                'prompt': prompt,
                'params': params,
                'topics': topics_map,
            }
            with open(topics_file, "w") as f:
                json.dump(saved, f, indent=2)

            # Native ROS 2 Service Call
            if not self.cli_rec_start.service_is_ready():
                return {"ok": False, "error": "/recorder/start service is not available. Is dataset_launch.py running?"}

            req = StartRecord.Request()
            
            # Dynamic attributes setup
            def safe_set(obj, attr, val):
                if hasattr(obj, attr):
                    try:
                        setattr(obj, attr, val)
                    except Exception as e:
                        self.get_logger().warn(f"Failed to set request attribute {attr}: {e}")

            safe_set(req, 'dataset_name', dataset_name)
            safe_set(req, 'episode_length', episode_length)
            safe_set(req, 'record_hz', record_hz)
            safe_set(req, 'max_episodes', max_episodes)
            safe_set(req, 'task', task)
            safe_set(req, 'prompt', prompt)
            safe_set(req, 'domain_id', domain_id)
            
            if topics_data:
                safe_set(req, 'leader_topic_left', topics_data.get('leader_topic_left', ''))
                safe_set(req, 'leader_topic_right', topics_data.get('leader_topic_right', ''))
                safe_set(req, 'follower_topic_left', topics_data.get('follower_topic_left', ''))
                safe_set(req, 'follower_topic_right', topics_data.get('follower_topic_right', ''))
                safe_set(req, 'follower_cmd_topic_left', topics_data.get('follower_cmd_topic_left', joint_cmd))
                safe_set(req, 'follower_cmd_topic_right', topics_data.get('follower_cmd_topic_right', joint_cmd))
                safe_set(req, 'leader_cmd_topic_left', topics_data.get('leader_cmd_topic_left', ''))
                safe_set(req, 'leader_cmd_topic_right', topics_data.get('leader_cmd_topic_right', ''))
                
                cam_topics = topics_data.get('camera_topics', {})
                safe_set(req, 'camera_keys', list(cam_topics.keys()))
                safe_set(req, 'camera_topic_values', list(cam_topics.values()))

            future = self.cli_rec_start.call_async(req)
            
            start_time = time.time()
            timeout = 10.0
            while not future.done():
                if time.time() - start_time > timeout:
                    return {"ok": False, "error": "Recorder start service call timed out"}
                time.sleep(0.05)

            response = future.result()
            success = getattr(response, 'success', True)
            msg = getattr(response, 'message', 'Recording started')
            
            if success:
                self._record_active = True
                threading.Thread(
                    target=self._log_steps_thread,
                    args=(record_hz, episode_length, 'record'),
                    daemon=True
                ).start()
                return {"ok": True, "message": msg}
            else:
                return {"ok": False, "error": f"Start failed: {msg}"}
        except Exception as e:
            return {"ok": False, "error": f"Exception: {str(e)}"}
            
    def stop_record(self):
        try:
            self._record_active = False
            if not self.cli_rec_stop.service_is_ready():
                return {"ok": False, "error": "/recorder/stop service is not available."}
            
            req = Trigger.Request()
            future = self.cli_rec_stop.call_async(req)
            
            start_time = time.time()
            timeout = 5.0
            while not future.done():
                if time.time() - start_time > timeout:
                    return {"ok": False, "error": "Stop service call timed out"}
                time.sleep(0.05)
                
            response = future.result()
            success = getattr(response, 'success', True)
            msg = getattr(response, 'message', 'Recording stopped')
            if success:
                return {"ok": True, "message": msg}
            else:
                return {"ok": False, "error": msg}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def acknowledge_validation(self):
        """Operator confirms a validation-failed episode (shown in the
        recording panel) has been reviewed; tells the recorder to resume
        auto-restarting the next episode."""
        try:
            if not self.cli_rec_ack_validation.service_is_ready():
                return {"ok": False, "error": "/recorder/acknowledge_validation service is not available."}

            req = Trigger.Request()
            future = self.cli_rec_ack_validation.call_async(req)

            start_time = time.time()
            timeout = 5.0
            while not future.done():
                if time.time() - start_time > timeout:
                    return {"ok": False, "error": "Acknowledge service call timed out"}
                time.sleep(0.05)

            response = future.result()
            success = getattr(response, 'success', True)
            msg = getattr(response, 'message', 'Acknowledged')
            if success:
                return {"ok": True, "message": msg}
            else:
                return {"ok": False, "error": msg}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def start_replay(self, params):
        try:
            dataset_name = params.get('dataset_name', 'new_dataset')
            episode_index = int(params.get('episode_index', 0))
            speed = float(params.get('speed', 1.0))
            record_hz = float(params.get('record_hz', 30.0))
            episode_length = int(params.get('episode_length', 500))
            domain_id = int(params.get('domain_id', 0))
            
            if not self.cli_rep_start.service_is_ready():
                return {"ok": False, "error": "/replay/start service is not available."}
            
            req = StartReplay.Request()
            req.dataset_name = dataset_name
            req.episode_index = episode_index
            req.speed = speed
            
            if hasattr(req, 'domain_id'):
                try:
                    req.domain_id = domain_id
                except Exception:
                    pass
            
            future = self.cli_rep_start.call_async(req)
            start_time = time.time()
            timeout = 10.0
            while not future.done():
                if time.time() - start_time > timeout:
                    return {"ok": False, "error": "Replay start service call timed out"}
                time.sleep(0.05)
                
            response = future.result()
            success = getattr(response, 'success', True)
            msg = getattr(response, 'message', 'Replay started')
            
            if success:
                self._replay_active = True
                hz = record_hz * speed
                threading.Thread(
                    target=self._replay_video_thread,
                    args=(dataset_name, episode_index, hz, episode_length),
                    daemon=True
                ).start()
                return {"ok": True, "message": msg}
            else:
                return {"ok": False, "error": msg}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def stop_replay(self):
        try:
            self._replay_active = False
            if not self.cli_rep_stop.service_is_ready():
                return {"ok": False, "error": "/replay/stop service is not available."}
            
            req = Trigger.Request()
            future = self.cli_rep_stop.call_async(req)
            start_time = time.time()
            timeout = 5.0
            while not future.done():
                if time.time() - start_time > timeout:
                    return {"ok": False, "error": "Replay stop service call timed out"}
                time.sleep(0.05)
                
            response = future.result()
            success = getattr(response, 'success', True)
            msg = getattr(response, 'message', 'Replay stopped')
            if success:
                return {"ok": True, "message": msg}
            else:
                return {"ok": False, "error": msg}
        except Exception as e:
            return {"ok": False, "error": str(e)}

class UIRequestHandler(BaseHTTPRequestHandler):
    ros_node: DataManagementUINode

    def log_message(self, format, *args): pass

    # ── Session helpers ───────────────────────────────────────────────────────
    def _extract_session_id(self) -> str | None:
        """Parse the session_id cookie from the request, or return None."""
        cookie_header = self.headers.get('Cookie', '')
        for part in cookie_header.split(';'):
            part = part.strip()
            if part.startswith('session_id='):
                return part[len('session_id='):].strip()
        return None

    def _get_session(self) -> SessionState:
        """Return the SessionState for this request (creating one if needed)."""
        return _get_or_create_session(self._extract_session_id())

    def _set_session_cookie(self, resp_session: SessionState):
        """Emit a Set-Cookie header so the browser remembers its session ID."""
        self.send_header(
            'Set-Cookie',
            f'session_id={resp_session.session_id}; Path=/; SameSite=Lax; HttpOnly; Max-Age=3600'
        )

    def _send_json(self, data: dict, status: int = 200):
        body = json.dumps(data).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        session = self._get_session()
        if parsed.path == '/':
            data = HTML_TEMPLATE.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(data)))
            self._set_session_cookie(session)   # ensure browser has its unique cookie
            self.end_headers()
            self.wfile.write(data)
        elif parsed.path == '/api/recorder/status':
            result = self.server.ros_node.get_recorder_status()
            self._send_json(result)
        elif parsed.path == '/api/motor-status':
            result = self.server.ros_node.get_motor_status()
            self._send_json(result)
        elif parsed.path == '/api/cameras/all-frames':
            # Return ONLY the cameras registered by this session,
            # fetched from the camera node that runs on the session's domain.
            all_frames = {}
            if session.camera_names:
                cam_node = _get_or_create_domain_cam_node(session.domain_id)
                for camera_name, _topic in session.camera_names.items():
                    frame_data = cam_node.get_camera_frame_base64(camera_name)
                    all_frames[camera_name] = frame_data
            result = {"ok": True, "frames": all_frames}
            self._send_json(result)
        elif parsed.path == '/api/cameras/active':
            # Return ONLY the cameras registered by this session.
            active = {}
            if session.camera_names:
                cam_node = _get_or_create_domain_cam_node(session.domain_id)
                for name, topic in session.camera_names.items():
                    entry = cam_node.camera_frames.get(name)
                    active[name] = {"topic": topic, "has_frame": entry is not None}
            self._send_json({"ok": True, "active": active})
        elif parsed.path.startswith('/api/cameras/stream/'):
            camera_name = parsed.path.split('/')[-1]
            self.send_response(200)
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=frame')
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.end_headers()

            cam_node_stream = _get_or_create_domain_cam_node(session.domain_id)
            last_frame = None
            try:
                while camera_name in cam_node_stream.camera_topics:
                    frame = cam_node_stream.get_camera_frame_jpeg_bytes(camera_name)
                    if frame is not None and frame != last_frame:
                        last_frame = frame
                        try:
                            self.wfile.write(b'--frame\r\n')
                            self.wfile.write(b'Content-Type: image/jpeg\r\n')
                            self.wfile.write(f'Content-Length: {len(frame)}\r\n\r\n'.encode('utf-8'))
                            self.wfile.write(frame)
                            self.wfile.write(b'\r\n')
                        except (BrokenPipeError, ConnectionResetError):
                            break
                    time.sleep(0.03)
            except Exception:
                pass
            return
        elif parsed.path.startswith('/api/cameras/frame/'):
            camera_name = parsed.path.split('/')[-1].split('?')[0]
            cam_node_frame = _get_or_create_domain_cam_node(session.domain_id)
            frame = None
            try:
                frame = cam_node_frame.get_camera_frame_jpeg_bytes(camera_name)
            except Exception:
                pass
            
            if frame:
                self.send_response(200)
                self.send_header('Content-Type', 'image/jpeg')
                self.end_headers()
                self.wfile.write(frame)
            else:
                self.send_response(404)
                self.end_headers()
            return
        elif parsed.path == '/api/config':
            result = self.server.ros_node.get_config()
            self._send_json(result)
        elif parsed.path == '/api/dataset/info':
            query_params = parse_qs(parsed.query)
            dataset_name = query_params.get('dataset_name', [''])[0]
            if not dataset_name:
                self._send_json({"ok": False, "error": "Missing dataset_name parameter"})
                return
            
            try:
                import pandas as pd
                from pathlib import Path
                base = Path(self.server.ros_node.get_dataset_base_dir()) / dataset_name
                
                info = {}
                info_file = base / "info.json"
                if not info_file.exists():
                    # Fallback to checking ros2_topics.json
                    info_file = base / "ros2_topics.json"
                
                if info_file.exists():
                    try:
                        with open(info_file, 'r') as f:
                            raw_info = json.load(f)
                            # Handle structure variations
                            if "params" in raw_info:
                                info.update(raw_info["params"])
                            info.update(raw_info)
                    except Exception:
                        pass
                
                episodes = []
                episodes_df = pd.DataFrame()
                ep_file = base / "meta" / "episodes" / "chunk-000" / "episodes.parquet"
                if ep_file.exists():
                    try:
                        episodes_df = pd.read_parquet(ep_file)
                        episodes = episodes_df.to_dict(orient='records')
                    except Exception as e:
                        if hasattr(self.server, 'ros_node') and self.server.ros_node:
                            self.server.ros_node.get_logger().error(f"Failed to read episodes parquet: {e}")
                
                tasks_df = pd.DataFrame()
                tasks_file = base / "meta" / "tasks" / "chunk-000" / "tasks.parquet"
                if tasks_file.exists():
                    try:
                        tasks_df = pd.read_parquet(tasks_file)
                    except Exception:
                        pass
                
                total_frames = 0
                if not episodes_df.empty and "length" in episodes_df.columns:
                    total_frames = int(episodes_df["length"].sum())
                elif "total_frames" in info:
                    total_frames = int(info["total_frames"])
                
                total_tasks = 0
                if not tasks_df.empty:
                    total_tasks = int(len(tasks_df))
                elif not episodes_df.empty and "task" in episodes_df.columns:
                    total_tasks = int(episodes_df["task"].astype(str).nunique())
                
                task_names = []
                if not tasks_df.empty and "task" in tasks_df.columns:
                    task_names = tasks_df["task"].astype(str).tolist()
                elif not episodes_df.empty and "task" in episodes_df.columns:
                    task_names = episodes_df["task"].astype(str).unique().tolist()
                
                topic_config = {}
                topics_file = base / "ros2_topics.json"
                if topics_file.exists():
                    try:
                        with open(topics_file, 'r') as f:
                            raw_topics = json.load(f)
                            if "topics" in raw_topics:
                                topic_config = raw_topics["topics"]
                            else:
                                topic_config = raw_topics
                    except Exception:
                        pass
                
                result = {
                    "ok": True,
                    "info": info,
                    "episodes": episodes,
                    "episode_count": int(len(episodes_df)) if not episodes_df.empty else 0,
                    "total_frames": total_frames,
                    "total_tasks": total_tasks,
                    "task_names": task_names,
                    "camera_keys": list(info.get("camera_keys", info.get("topics", {}).get("camera_topics", {}).keys())),
                    "video_keys": list(info.get("video_keys", [])),
                    "topic_config": topic_config
                }
            except Exception as e:
                result = {"ok": False, "error": str(e)}
            self._send_json(result)
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        parsed = urlparse(self.path)
        session = self._get_session()
        length = int(self.headers.get('Content-Length', '0'))
        raw = self.rfile.read(length) if length else b'{}'
        payload = json.loads(raw.decode('utf-8'))

        result = {"ok": False, "error": "Unknown endpoint"}
        try:
            if parsed.path == '/api/mode/set':
                mode = payload.get('mode')
                if mode not in ('teach', 'normal'):
                    result = {"ok": False, "error": "mode must be 'teach' or 'normal'"}
                else:
                    ok, msg = set_toggler_mode(mode)
                    result = {"ok": ok, "message": msg}
            elif parsed.path == '/api/topics/load':
                requested_domain = int(payload.get('domain_id', 0))
                # Store chosen domain in this session (does NOT affect other sessions)
                session.domain_id = requested_domain
                result = self.server.ros_node.get_topics_for_domain(
                    requested_domain, calling_session=session
                )
                if result.get('ok') and 'topics' in result:
                    session.loaded_topics = result['topics']
            elif parsed.path == '/api/record/start':
                result = self.server.ros_node.start_record(payload)
            elif parsed.path == '/api/record/stop':
                result = self.server.ros_node.stop_record()
            elif parsed.path == '/api/record/acknowledge_validation':
                result = self.server.ros_node.acknowledge_validation()
            elif parsed.path == '/api/replay/start':
                result = self.server.ros_node.start_replay(payload)
            elif parsed.path == '/api/replay/stop':
                result = self.server.ros_node.stop_replay()
            elif parsed.path == '/api/dataset/delete-episode':
                dataset_name = payload.get('dataset_name')
                episode = payload.get('episode')
                try:
                    from daksha_data_collection.delete_episode import delete_episode
                    from pathlib import Path
                    base = Path(self.server.ros_node.get_dataset_base_dir()) / dataset_name
                    delete_episode(base, episode)
                    result = {"ok": True}
                except Exception as e:
                    result = {"ok": False, "error": str(e)}
            elif parsed.path == '/api/cameras/register':
                name = payload.get('name')
                topic = payload.get('topic')
                if name and topic:
                    # Use the camera node for this session's domain
                    domain_id = session.domain_id if session.domain_id is not None else 0
                    cam_node = _get_or_create_domain_cam_node(domain_id)

                    # Unregister old topic for this camera name if it changed
                    old_topic = session.camera_names.get(name)
                    if old_topic and old_topic != topic:
                        with _topic_ref_lock:
                            ref_key = (domain_id, old_topic)
                            _topic_refcount[ref_key] = max(0, _topic_refcount.get(ref_key, 1) - 1)
                            if _topic_refcount[ref_key] == 0:
                                cam_node._subscription_queue.put({'action': 'unregister', 'name': name})

                    # Register the new topic in this session
                    session.camera_names[name] = topic
                    with _topic_ref_lock:
                        ref_key = (domain_id, topic)
                        prev = _topic_refcount.get(ref_key, 0)
                        _topic_refcount[ref_key] = prev + 1
                        if prev == 0:
                            # First session on this domain to need this topic
                            cam_node._subscription_queue.put({'action': 'register', 'name': name, 'topic': topic})
                    result = {"ok": True}
            elif parsed.path == '/api/cameras/unregister':
                name = payload.get('name')
                if name and name in session.camera_names:
                    topic = session.camera_names.pop(name)
                    domain_id = session.domain_id if session.domain_id is not None else 0
                    cam_node = _get_or_create_domain_cam_node(domain_id)
                    with _topic_ref_lock:
                        ref_key = (domain_id, topic)
                        _topic_refcount[ref_key] = max(0, _topic_refcount.get(ref_key, 1) - 1)
                        if _topic_refcount[ref_key] == 0:
                            cam_node._subscription_queue.put({'action': 'unregister', 'name': name})
                    result = {"ok": True}
                elif name:
                    result = {"ok": True}  # already unregistered, no-op
        except Exception as e:
            result = {"ok": False, "error": str(e)}

        self._send_json(result)
        
    def _send_json(self, data):
        json_data = json.dumps(data).encode('utf-8')
        self.send_response(200 if data.get("ok", True) else 400)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(json_data)))
        self.end_headers()
        try:
            self.wfile.write(json_data)
        except (BrokenPipeError, ConnectionResetError):
            try:
                if hasattr(self.server, 'ros_node') and self.server.ros_node:
                    self.server.ros_node.get_logger().warning('Client closed connection while sending JSON response')
            except Exception:
                pass

def load_camera_topics():
    import yaml
    config_path = _get_default_config_path()
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            cams = {}
            t_cams = config.get('recording_topics', {}).get('camera_topics') or {}
            
            # Map YAML dot-notation names to friendly UI camera names
            for k, v in t_cams.items():
                if not v:
                    continue
                name = k.split('.')[-1] if '.' in k else k
                if name in ('wrist_left', 'left_wrist'):
                    cams['left_wrist'] = v
                elif name in ('wrist_right', 'right_wrist'):
                    cams['right_wrist'] = v
                elif name in ('world_left', 'zed_left'):
                    cams['zed_left'] = v
                elif name in ('world_right', 'zed_right'):
                    cams['zed_right'] = v
                else:
                    cams[name] = v
            
            return cams
    except Exception as e:
        print(f"Failed to load camera topics: {e}")
        return {}


def get_local_ips():
    import subprocess
    ips = []
    try:
        # Run ip -o -4 addr show to get interfaces and their IPs
        output = subprocess.check_output(["ip", "-o", "-4", "addr", "show"], stderr=subprocess.DEVNULL).decode("utf-8").strip()
        for line in output.split('\n'):
            parts = line.split()
            if len(parts) >= 4:
                ifname = parts[1]
                ip_with_mask = parts[3]
                ip = ip_with_mask.split('/')[0]
                # Filter out loopback and virtual/docker/bridge interfaces
                if ifname.startswith(('lo', 'docker', 'virbr', 'vbox', 'br-', 'veth')):
                    continue
                if ip.startswith('127.'):
                    continue
                ips.append(ip)
    except Exception:
        # Fallback to hostname -I if ip command fails
        try:
            output = subprocess.check_output(["hostname", "-I"], stderr=subprocess.DEVNULL).decode("utf-8").strip()
            for ip in output.split():
                if ":" not in ip and not ip.startswith("127."):
                    # Exclude typical docker/virtual network ranges if parsed via hostname -I
                    if ip.startswith(('172.17.', '172.18.', '172.19.', '172.20.', '172.21.', '172.22.', '172.23.', '172.24.', '172.25.', '172.26.', '172.27.', '172.28.', '172.29.', '172.30.', '172.31.')):
                        continue
                    ips.append(ip)
        except Exception:
            pass
    return ips

def main(args=None):
    try:
        if not rclpy.ok():
            rclpy.init(args=args)
    except Exception:
        pass

    
    default_cams = {}
    camera_node = CameraDisplayNode(default_cams)
    ui_node = DataManagementUINode(camera_node)

    cfg_port = 8888
    try:
        with open(ui_node.CONFIG_PATH, 'r') as f:
            c = yaml.safe_load(f) or {}
            cfg_port = int(c.get('network', {}).get('data_collection_port', 8888))
    except Exception:
        pass

    server = ThreadingHTTPServer(('0.0.0.0', cfg_port), UIRequestHandler)
    server.ros_node = ui_node

    ips = get_local_ips()
    pref_ip = "localhost"
    for ip in ips:
        if ip.startswith("192.168.200."):
            pref_ip = ip
            break
    else:
        if ips:
            pref_ip = ips[0]

    ui_node.get_logger().info(f'Data Management UI listening on http://{pref_ip}:{cfg_port}')

    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()


    
    # Run each node in its own dedicated executor in a background thread.
    # Using separate SingleThreadedExecutors means each node's wait-set is rebuilt
    # independently every spin cycle, so dynamically added subscriptions are always picked up.
    cam_executor = rclpy.executors.SingleThreadedExecutor()
    cam_executor.add_node(camera_node)
    def run_cam_spin():
        try:
            cam_executor.spin()
        except Exception:
            pass
    cam_thread = threading.Thread(target=run_cam_spin, daemon=True)
    cam_thread.start()

    ui_executor = rclpy.executors.SingleThreadedExecutor()
    ui_executor.add_node(ui_node)

    try:
        ui_executor.spin()
    except (KeyboardInterrupt, rclpy.executors.ExternalShutdownException):
        pass
    finally:
        try:
            server.shutdown()
        except Exception:
            pass
        try:
            cam_executor.shutdown()
        except Exception:
            pass
        try:
            ui_executor.shutdown()
        except Exception:
            pass
        try:
            ui_node.destroy_node()
            camera_node.destroy_node()
        except Exception:
            pass
        try:
            rclpy.shutdown()
        except Exception:
            pass

if __name__ == '__main__':
    main()

