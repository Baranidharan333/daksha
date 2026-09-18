#!/usr/bin/env python3
"""
Starts/stops the `vr_teleop` bridge (default_server_endpoint, quest_tf_switch,
quest_tf_to_pose) and `kinematics ik_node`, and serves a Flask page
(http://localhost:8101) showing their live stdout in two panels, kept
separate from the VR/gesture management UI.

vr_teleop replaces Unity's ROS-TCP-Endpoint: default_server_endpoint still
terminates the Quest's TCP connection and publishes /quest/{left,right}/pose
and /quest/{left,right}/joy, but the controller poses now reach ik_node via
TF (quest_tf_switch broadcasts world -> quest_left/quest_right; quest_tf_to_pose
looks that up and republishes it as the /left/pose, /right/pose topics
ik_node subscribes to) instead of a direct PoseStamped relay.

Toggle with:
    ros2 param set /vr_management_ui enabled true|false
"""

import os
import signal
import socket
import subprocess
import threading
import time
import collections
import logging

import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
from rclpy.executors import MultiThreadedExecutor
from rcl_interfaces.msg import (
    SetParametersResult,
    Parameter as ParameterMsg,
    ParameterValue,
    ParameterType,
)
from rcl_interfaces.srv import SetParameters, GetParameters
from std_msgs.msg import String
from flask import Flask, jsonify, Response, request

logging.getLogger("werkzeug").setLevel(logging.WARNING)

app = Flask(__name__)

_node = None

_lock = threading.Lock()
_streams = {
    "tcp": {"seq": 0, "entries": collections.deque(maxlen=500)},
    "ik": {"seq": 0, "entries": collections.deque(maxlen=500)},
}


def _append(stream, line):
    with _lock:
        s = _streams[stream]
        s["seq"] += 1
        s["entries"].append({"id": s["seq"], "line": line})


PAGE = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>TCP / IK Node Logs</title>
  <style>
    :root {
      --blue-900: #0b3d91;
      --blue-700: #1257c2;
      --blue-600: #1565c0;
      --blue-100: #e8f1fd;
      --blue-50:  #f4f8fe;
      --border:   #d7e3f5;
      --gray-50:  #f6f8fb;
      --text:     #1c2b3a;
      --text-dim: #6b7c93;
    }
    * { box-sizing: border-box; }
    body {
      background: var(--gray-50);
      color: var(--text);
      font-family: -apple-system, "Segoe UI", Roboto, Arial, sans-serif;
      margin: 0;
      height: 100vh;
      display: flex;
      flex-direction: column;
    }

    header {
      background: #fff;
      border-bottom: 1px solid var(--border);
      box-shadow: 0 1px 3px rgba(11,61,145,0.06);
      padding: 12px 20px;
      display: flex;
      align-items: center;
      gap: 20px;
      flex-wrap: wrap;
    }
    header .title {
      font-size: 16px;
      font-weight: 600;
      color: var(--blue-900);
      flex: 1;
      min-width: 160px;
    }

    .control {
      display: flex;
      align-items: center;
      gap: 10px;
      background: var(--blue-50);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 6px 10px 6px 14px;
    }
    .control .label { font-size: 11px; color: var(--text-dim); text-transform: uppercase; letter-spacing: .04em; }
    .control .state { font-size: 13px; font-weight: 600; color: var(--text); min-width: 64px; }

    .control input[type="number"] {
      width: 56px;
      font-family: inherit;
      font-size: 13px;
      font-weight: 600;
      color: var(--text);
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 4px 6px;
    }
    .control input[type="number"]:disabled { opacity: .45; }

    .dot { width: 9px; height: 9px; border-radius: 50%; background: #b8c4d6; flex-shrink: 0; }
    .dot.on  { background: var(--blue-600); box-shadow: 0 0 0 3px var(--blue-100); }
    .dot.off { background: #b8c4d6; }

    button.hmi-btn {
      font-family: inherit;
      font-size: 12px;
      font-weight: 600;
      padding: 7px 16px;
      border-radius: 7px;
      border: 1px solid var(--blue-600);
      cursor: pointer;
      background: #fff;
      color: var(--blue-600);
      transition: background .15s ease, color .15s ease, transform .1s ease;
    }
    button.hmi-btn:hover:not(:disabled) { background: var(--blue-100); }
    button.hmi-btn:active:not(:disabled) { transform: scale(0.97); }
    button.hmi-btn.active {
      background: var(--blue-600);
      color: #fff;
    }
    button.hmi-btn.active:hover:not(:disabled) { background: var(--blue-700); }
    button.hmi-btn:disabled { opacity: .45; cursor: default; }

    .cols {
      flex: 1;
      display: flex;
      gap: 16px;
      padding: 16px 20px;
      min-height: 0;
    }
    .col {
      flex: 1;
      display: flex;
      flex-direction: column;
      min-width: 0;
      background: #fff;
      border: 1px solid var(--border);
      border-radius: 12px;
      overflow: hidden;
      box-shadow: 0 1px 3px rgba(11,61,145,0.05);
    }
    .col .col-head {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 10px 14px;
      background: var(--blue-50);
      border-bottom: 1px solid var(--border);
    }
    .col .col-head h2 {
      font-size: 13px;
      font-weight: 600;
      margin: 0;
      color: var(--blue-900);
      flex: 1;
    }
    .col .col-head button {
      font-family: inherit;
      font-size: 11px;
      padding: 4px 10px;
      border-radius: 6px;
      border: 1px solid var(--border);
      background: #fff;
      color: var(--text-dim);
      cursor: pointer;
    }
    .col .col-head button:hover { background: var(--blue-100); color: var(--blue-700); }

    .log {
      flex: 1;
      overflow-y: auto;
      padding: 10px 14px;
      white-space: pre-wrap;
      word-break: break-all;
      font-family: "SFMono-Regular", Consolas, Menlo, monospace;
      font-size: 12px;
      line-height: 1.5;
      color: #2a3a4d;
    }
    .log::-webkit-scrollbar { width: 8px; }
    .log::-webkit-scrollbar-thumb { background: var(--border); border-radius: 4px; }
  </style>
</head>
<body>
<script>
async function ihubEmergencyStop(){
  if(!confirm('EMERGENCY STOP\n\nKill the ROS 2 bringup now?')) return;
  var btn=document.getElementById('ihubEstop');
  var prev=btn.textContent; btn.disabled=true; btn.textContent='STOPPING…';
  try{
    var res=await fetch('http://'+location.hostname+':8100/api/kill',{method:'POST'});
    var data={}; try{ data=await res.json(); }catch(e){}
    alert(data.message || (res.ok?'Bringup stopped.':'E-STOP request failed.'));
  }catch(e){
    alert('E-STOP request failed: '+e);
  }finally{
    btn.disabled=false; btn.textContent=prev;
  }
}
</script>
  <header>
    <span class="title">TCP / IK Node Logs</span>

    <div class="control">
      <span class="dot" id="statusDot"></span>
      <span class="label">Endpoint</span>
      <span class="state" id="statusText">...</span>
      <button class="hmi-btn" id="toggleBtn" disabled>...</button>
    </div>

    <div class="control">
      <span class="dot" id="modeDot"></span>
      <span class="label">Mode</span>
      <span class="state" id="modeText">...</span>
      <button class="hmi-btn" id="modeBtn" disabled>...</button>
    </div>

    <div class="control">
      <span class="dot" id="postureDot"></span>
      <span class="label">Posture</span>
      <span class="state" id="postureText">...</span>
      <button class="hmi-btn" id="postureBtn" disabled>...</button>
    </div>

    <div class="control">
      <span class="dot" id="collisionDot"></span>
      <span class="label">Collision</span>
      <span class="state" id="collisionText">...</span>
      <button class="hmi-btn" id="collisionBtn" disabled>...</button>
    </div>

    <div class="control">
      <span class="dot" id="gripperPubDot"></span>
      <span class="label">Gripper Publish</span>
      <span class="state" id="gripperPubText">...</span>
      <button class="hmi-btn" id="gripperPubBtn" disabled>...</button>
    </div>

    <div class="control">
      <span class="dot" id="velocityDot"></span>
      <span class="label">Max Vel (rad/s)</span>
      <input type="number" id="velocityInput" step="0.1" min="0" disabled>
      <button class="hmi-btn" id="velocityBtn" disabled>Set</button>
    </div>

    <div class="control">
      <span class="dot" id="accelDot"></span>
      <span class="label">Max Acc (rad/s²)</span>
      <input type="number" id="accelInput" step="0.5" min="0" disabled>
      <button class="hmi-btn" id="accelBtn" disabled>Set</button>
    </div>

    <button id="ihubEstop" onclick="ihubEmergencyStop()" title="Kill ROS 2 bringup" style="margin-left:auto;background:#d81f2f;color:#fff;border:2px solid rgba(255,255,255,.5);border-radius:8px;padding:8px 14px;font:700 12px/1.2 system-ui,-apple-system,sans-serif;letter-spacing:.04em;cursor:pointer;box-shadow:0 2px 10px rgba(216,31,47,.45);white-space:nowrap;">&#9211; E-STOP</button>
  </header>

  <div class="cols">
    <div class="col">
      <div class="col-head">
        <h2>vr_teleop</h2>
        <button id="clearTcp">Clear</button>
      </div>
      <div class="log" id="tcp"></div>
    </div>
    <div class="col">
      <div class="col-head">
        <h2>kinematics ik_node</h2>
        <button id="clearIk">Clear</button>
      </div>
      <div class="log" id="ik"></div>
    </div>
  </div>

  <script>
    const since = { tcp: 0, ik: 0 };

    const toggleBtn = document.getElementById('toggleBtn');
    const statusDot = document.getElementById('statusDot');
    const statusText = document.getElementById('statusText');

    function renderStatus(data) {
      toggleBtn.disabled = false;
      if (data.enabled) {
        statusDot.className = 'dot on';
        statusText.textContent = data.tcp_running ? 'Running' : 'Starting…';
        toggleBtn.textContent = 'Stop';
        toggleBtn.className = 'hmi-btn active';
      } else {
        statusDot.className = 'dot off';
        statusText.textContent = 'Stopped';
        toggleBtn.textContent = 'Start';
        toggleBtn.className = 'hmi-btn';
      }
    }

    function pollStatus() {
      fetch('/api/status')
        .then(r => r.json())
        .then(renderStatus)
        .finally(() => setTimeout(pollStatus, 2000));
    }
    pollStatus();

    toggleBtn.addEventListener('click', () => {
      toggleBtn.disabled = true;
      fetch('/api/toggle', { method: 'POST' })
        .then(r => r.json())
        .then(renderStatus);
    });

    const modeBtn = document.getElementById('modeBtn');
    const modeDot = document.getElementById('modeDot');
    const modeText = document.getElementById('modeText');

    function renderMode(data) {
      if (!data.available) {
        modeBtn.disabled = true;
        modeDot.className = 'dot';
        modeText.textContent = 'N/A';
        modeBtn.textContent = 'Mode';
        modeBtn.className = 'hmi-btn';
        return;
      }
      modeBtn.disabled = false;
      if (data.mode === 'teach') {
        modeDot.className = 'dot on';
        modeText.textContent = 'Teach';
        modeBtn.textContent = 'Switch to Normal';
        modeBtn.className = 'hmi-btn active';
      } else {
        modeDot.className = 'dot off';
        modeText.textContent = 'Normal';
        modeBtn.textContent = 'Switch to Teach';
        modeBtn.className = 'hmi-btn';
      }
    }

    function pollMode() {
      fetch('/api/mode_status')
        .then(r => r.json())
        .then(renderMode)
        .finally(() => setTimeout(pollMode, 2000));
    }
    pollMode();

    modeBtn.addEventListener('click', () => {
      modeBtn.disabled = true;
      fetch('/api/mode_toggle', { method: 'POST' })
        .then(r => r.json())
        .then(renderMode);
    });

    const postureBtn = document.getElementById('postureBtn');
    const postureDot = document.getElementById('postureDot');
    const postureText = document.getElementById('postureText');

    function renderPosture(data) {
      if (!data.available) {
        postureBtn.disabled = true;
        postureDot.className = 'dot';
        postureText.textContent = 'N/A';
        postureBtn.textContent = 'Posture';
        postureBtn.className = 'hmi-btn';
        return;
      }
      postureBtn.disabled = false;
      if (data.enabled) {
        postureDot.className = 'dot on';
        postureText.textContent = 'Enabled';
        postureBtn.textContent = 'Disable';
        postureBtn.className = 'hmi-btn active';
      } else {
        postureDot.className = 'dot off';
        postureText.textContent = 'Disabled';
        postureBtn.textContent = 'Enable';
        postureBtn.className = 'hmi-btn';
      }
    }

    function pollPosture() {
      fetch('/api/posture_status')
        .then(r => r.json())
        .then(renderPosture)
        .finally(() => setTimeout(pollPosture, 2000));
    }
    pollPosture();

    postureBtn.addEventListener('click', () => {
      postureBtn.disabled = true;
      fetch('/api/posture_toggle', { method: 'POST' })
        .then(r => r.json())
        .then(renderPosture);
    });

    const collisionBtn = document.getElementById('collisionBtn');
    const collisionDot = document.getElementById('collisionDot');
    const collisionText = document.getElementById('collisionText');

    function renderCollision(data) {
      if (!data.available) {
        collisionBtn.disabled = true;
        collisionDot.className = 'dot';
        collisionText.textContent = 'N/A';
        collisionBtn.textContent = 'Collision';
        collisionBtn.className = 'hmi-btn';
        return;
      }
      collisionBtn.disabled = false;
      if (data.enabled) {
        collisionDot.className = 'dot on';
        collisionText.textContent = 'Enabled';
        collisionBtn.textContent = 'Disable';
        collisionBtn.className = 'hmi-btn active';
      } else {
        collisionDot.className = 'dot off';
        collisionText.textContent = 'Disabled';
        collisionBtn.textContent = 'Enable';
        collisionBtn.className = 'hmi-btn';
      }
    }

    function pollCollision() {
      fetch('/api/collision_status')
        .then(r => r.json())
        .then(renderCollision)
        .finally(() => setTimeout(pollCollision, 2000));
    }
    pollCollision();

    collisionBtn.addEventListener('click', () => {
      collisionBtn.disabled = true;
      fetch('/api/collision_toggle', { method: 'POST' })
        .then(r => r.json())
        .then(renderCollision);
    });

    const gripperPubBtn = document.getElementById('gripperPubBtn');
    const gripperPubDot = document.getElementById('gripperPubDot');
    const gripperPubText = document.getElementById('gripperPubText');

    function renderGripperPub(data) {
      if (!data.available) {
        gripperPubBtn.disabled = true;
        gripperPubDot.className = 'dot';
        gripperPubText.textContent = 'N/A';
        gripperPubBtn.textContent = 'Gripper';
        gripperPubBtn.className = 'hmi-btn';
        return;
      }
      gripperPubBtn.disabled = false;
      if (data.enabled) {
        gripperPubDot.className = 'dot on';
        gripperPubText.textContent = 'Enabled';
        gripperPubBtn.textContent = 'Disable';
        gripperPubBtn.className = 'hmi-btn active';
      } else {
        gripperPubDot.className = 'dot off';
        gripperPubText.textContent = 'Disabled';
        gripperPubBtn.textContent = 'Enable';
        gripperPubBtn.className = 'hmi-btn';
      }
    }

    function pollGripperPub() {
      fetch('/api/gripper_publish_status')
        .then(r => r.json())
        .then(renderGripperPub)
        .finally(() => setTimeout(pollGripperPub, 2000));
    }
    pollGripperPub();

    gripperPubBtn.addEventListener('click', () => {
      gripperPubBtn.disabled = true;
      fetch('/api/gripper_publish_toggle', { method: 'POST' })
        .then(r => r.json())
        .then(renderGripperPub);
    });

    function setupNumberControl(inputId, dotId, btnId, statusUrl, setUrl) {
      const input = document.getElementById(inputId);
      const dot = document.getElementById(dotId);
      const btn = document.getElementById(btnId);

      function render(data) {
        if (!data.available) {
          input.disabled = true;
          btn.disabled = true;
          dot.className = 'dot';
          return;
        }
        input.disabled = false;
        btn.disabled = false;
        dot.className = 'dot on';
        if (document.activeElement !== input && data.value !== null) {
          input.value = data.value.toFixed(2);
        }
      }

      function poll() {
        fetch(statusUrl)
          .then(r => r.json())
          .then(render)
          .finally(() => setTimeout(poll, 2000));
      }
      poll();

      btn.addEventListener('click', () => {
        btn.disabled = true;
        fetch(setUrl, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ value: parseFloat(input.value) }),
        })
          .then(r => r.json())
          .then(render);
      });
    }

    setupNumberControl('velocityInput', 'velocityDot', 'velocityBtn',
      '/api/velocity_status', '/api/velocity_set');
    setupNumberControl('accelInput', 'accelDot', 'accelBtn',
      '/api/acceleration_status', '/api/acceleration_set');

    document.getElementById('clearTcp').addEventListener('click', () => {
      document.getElementById('tcp').textContent = '';
    });
    document.getElementById('clearIk').addEventListener('click', () => {
      document.getElementById('ik').textContent = '';
    });

    function poll() {
      fetch(`/api/logs?tcp_since=${since.tcp}&ik_since=${since.ik}`)
        .then(r => r.json())
        .then(data => {
          for (const key of ["tcp", "ik"]) {
            const el = document.getElementById(key);
            const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 30;
            for (const entry of data[key]) {
              el.textContent += entry.line + "\\n";
              since[key] = entry.id;
            }
            if (atBottom) el.scrollTop = el.scrollHeight;
          }
        })
        .finally(() => setTimeout(poll, 1000));
    }
    poll();
  </script>
</body>
</html>
"""


@app.route("/")
def index():
    return Response(PAGE, mimetype="text/html")


@app.route("/api/logs")
def api_logs():

    tcp_since = int(request.args.get("tcp_since", 0))
    ik_since = int(request.args.get("ik_since", 0))

    with _lock:
        tcp = [e for e in _streams["tcp"]["entries"] if e["id"] > tcp_since]
        ik = [e for e in _streams["ik"]["entries"] if e["id"] > ik_since]

    return jsonify({"tcp": tcp, "ik": ik})


@app.route("/api/status")
def api_status():

    if _node is None:
        return jsonify({"enabled": False, "tcp_running": False, "ik_running": False})

    return jsonify({
        "enabled": bool(_node.get_parameter("enabled").value),
        "tcp_running": (
            _node.process is not None
            and _node.tf_process is not None
            and _node.pose_bridge_process is not None
        ),
        "ik_running": _node.ik_process is not None,
    })


@app.route("/api/toggle", methods=["POST"])
def api_toggle():

    if _node is None:
        return jsonify({"success": False}), 503

    new_value = not bool(_node.get_parameter("enabled").value)

    _node.set_parameters([
        Parameter("enabled", Parameter.Type.BOOL, new_value),
    ])

    return api_status()


@app.route("/api/mode_status")
def api_mode_status():

    if _node is None:
        return jsonify({"mode": None, "available": False})

    mode = _node.get_mode()

    return jsonify({"mode": mode, "available": mode is not None})


@app.route("/api/mode_toggle", methods=["POST"])
def api_mode_toggle():

    if _node is None:
        return jsonify({"success": False}), 503

    current = _node.get_mode()

    if current is None:
        return jsonify({"mode": None, "available": False})

    new_mode = "normal" if current == "teach" else "teach"

    result = _node.set_mode(new_mode)

    if result is None or not result.results or not result.results[0].successful:
        return jsonify({"mode": current, "available": True, "success": False}), 502

    return jsonify({"mode": new_mode, "available": True, "success": True})


@app.route("/api/posture_status")
def api_posture_status():

    if _node is None:
        return jsonify({"available": False, "enabled": False})

    return jsonify({
        "available": _node.ik_process is not None,
        "enabled": _node.posture_enabled,
    })


@app.route("/api/posture_toggle", methods=["POST"])
def api_posture_toggle():

    if _node is None or _node.ik_process is None:
        return jsonify({"success": False, "available": False}), 503

    new_value = not _node.posture_enabled

    if not _node.set_posture(new_value):
        return jsonify({
            "success": False,
            "available": True,
            "enabled": _node.posture_enabled,
        }), 502

    return jsonify({
        "success": True,
        "available": True,
        "enabled": _node.posture_enabled,
    })


@app.route("/api/collision_status")
def api_collision_status():

    if _node is None:
        return jsonify({"available": False, "enabled": False})

    return jsonify({
        "available": _node.ik_process is not None,
        "enabled": _node.collision_enabled,
    })


@app.route("/api/collision_toggle", methods=["POST"])
def api_collision_toggle():

    if _node is None or _node.ik_process is None:
        return jsonify({"success": False, "available": False}), 503

    new_value = not _node.collision_enabled

    if not _node.set_collision(new_value):
        return jsonify({
            "success": False,
            "available": True,
            "enabled": _node.collision_enabled,
        }), 502

    return jsonify({
        "success": True,
        "available": True,
        "enabled": _node.collision_enabled,
    })


@app.route("/api/gripper_publish_status")
def api_gripper_publish_status():

    if _node is None:
        return jsonify({"available": False, "enabled": False})

    return jsonify({
        "available": _node.gripper_set_params_client.service_is_ready(),
        "enabled": _node.gripper_publish_enabled,
    })


@app.route("/api/gripper_publish_toggle", methods=["POST"])
def api_gripper_publish_toggle():

    if _node is None or not _node.gripper_set_params_client.service_is_ready():
        return jsonify({"success": False, "available": False}), 503

    new_value = not _node.gripper_publish_enabled

    if not _node.set_gripper_publish(new_value):
        return jsonify({
            "success": False,
            "available": True,
            "enabled": _node.gripper_publish_enabled,
        }), 502

    return jsonify({
        "success": True,
        "available": True,
        "enabled": _node.gripper_publish_enabled,
    })


@app.route("/api/velocity_status")
def api_velocity_status():

    if _node is None:
        return jsonify({"available": False, "value": None})

    value = _node.get_max_velocity()

    return jsonify({"available": value is not None, "value": value})


@app.route("/api/velocity_set", methods=["POST"])
def api_velocity_set():

    if _node is None:
        return jsonify({"success": False, "available": False}), 503

    value = (request.get_json(silent=True) or {}).get("value")

    if value is None:
        return jsonify({"success": False, "available": True}), 400

    if not _node.set_max_velocity(float(value)):
        return jsonify({"success": False, "available": True}), 502

    return jsonify({"success": True, "available": True, "value": float(value)})


@app.route("/api/acceleration_status")
def api_acceleration_status():

    if _node is None:
        return jsonify({"available": False, "value": None})

    value = _node.get_max_acceleration()

    return jsonify({"available": value is not None, "value": value})


@app.route("/api/acceleration_set", methods=["POST"])
def api_acceleration_set():

    if _node is None:
        return jsonify({"success": False, "available": False}), 503

    value = (request.get_json(silent=True) or {}).get("value")

    if value is None:
        return jsonify({"success": False, "available": True}), 400

    if not _node.set_max_acceleration(float(value)):
        return jsonify({"success": False, "available": True}), 502

    return jsonify({"success": True, "available": True, "value": float(value)})


class VRManagementUI(Node):

    def __init__(self):
        super().__init__("vr_management_ui")

        self.declare_parameter("enabled", False)

        self.process = None
        self.tf_process = None
        self.pose_bridge_process = None
        self.ik_process = None

        self.log_pub = self.create_publisher(
            String,
            "/vr_teleop/log",
            100,
        )

        self.ik_log_pub = self.create_publisher(
            String,
            "/ik_node/log",
            100,
        )

        self.mode_get_client = self.create_client(
            GetParameters,
            "/mode_toggler/get_parameters",
        )

        self.mode_set_client = self.create_client(
            SetParameters,
            "/mode_toggler/set_parameters",
        )

        self.posture_enabled = True
        self.collision_enabled = True
        self.ik_set_params_client = self.create_client(
            SetParameters,
            "/dual_arm_ik/set_parameters",
        )

        self.gripper_publish_enabled = False
        self.gripper_set_params_client = self.create_client(
            SetParameters,
            "/vr_gripper_servo/set_parameters",
        )

        self.joint_limiter_get_client = self.create_client(
            GetParameters,
            "/joint_command_limiter/get_parameters",
        )

        self.joint_limiter_set_client = self.create_client(
            SetParameters,
            "/joint_command_limiter/set_parameters",
        )

        self.add_on_set_parameters_callback(
            self.parameter_callback
        )

        if self.get_parameter("enabled").value:
            self.start_node()

    # --------------------------------

    def parameter_callback(self, params):

        for p in params:

            if p.name == "enabled":

                if p.value:
                    self.start_node()
                else:
                    self.stop_node()

        return SetParametersResult(successful=True)

    # --------------------------------

    def free_port(self, port):

        try:
            output = subprocess.check_output(
                ["lsof", "-ti", f":{port}"],
                text=True,
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            return

        for pid in output.split():

            self.get_logger().info(
                f"Port {port} occupied by pid {pid}, killing it"
            )

            try:
                os.kill(int(pid), signal.SIGKILL)
            except ProcessLookupError:
                pass

    # --------------------------------

    def start_node(self):

        if self.process is not None:
            return

        # default_server_endpoint's ROS_TCP_PORT default is 10000 (see
        # bridge_nodes/server.py) and nothing overrides it in the run below
        # -- freeing 8103 (unrelated to anything else in this file, likely
        # a stale/copy-paste port) left a stale listener on 10000 uncleared,
        # so bind() failed silently and the UI reported "Running" with the
        # bridge actually accepting no connections.
        self.free_port(8103)

        self.get_logger().info("Starting vr_teleop default_server_endpoint")

        self.process = subprocess.Popen(
            [
                "ros2",
                "run",
                "vr_teleop",
                "default_server_endpoint",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            preexec_fn=os.setsid,
        )

        threading.Thread(
            target=self.read_logs,
            args=(self.process, self.log_pub, "tcp"),
            daemon=True,
        ).start()

        self.get_logger().info("Starting vr_teleop quest_tf_switch")

        self.tf_process = subprocess.Popen(
            [
                "ros2",
                "run",
                "vr_teleop",
                "quest_tf_switch",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            preexec_fn=os.setsid,
        )

        threading.Thread(
            target=self.read_logs,
            args=(self.tf_process, self.log_pub, "tcp"),
            daemon=True,
        ).start()

        self.get_logger().info("Starting vr_teleop quest_tf_to_pose")

        self.pose_bridge_process = subprocess.Popen(
            [
                "ros2",
                "run",
                "vr_teleop",
                "quest_tf_to_pose",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            preexec_fn=os.setsid,
        )

        threading.Thread(
            target=self.read_logs,
            args=(self.pose_bridge_process, self.log_pub, "tcp"),
            daemon=True,
        ).start()

        threading.Thread(
            target=self.start_ik_node_delayed,
            daemon=True,
        ).start()

    # --------------------------------

    def start_ik_node_delayed(self):

        time.sleep(5.0)

        if self.process is None or self.ik_process is not None:
            return

        self.get_logger().info("Starting kinematics ik_node")
        self.posture_enabled = True
        self.collision_enabled = True

        self.ik_process = subprocess.Popen(
            [
                "ros2",
                "run",
                "kinematics",
                "ik_node",
                "--ros-args",
                "-p", "arms:=['left','right']",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            preexec_fn=os.setsid,
        )

        threading.Thread(
            target=self.read_logs,
            args=(self.ik_process, self.ik_log_pub, "ik"),
            daemon=True,
        ).start()

    # --------------------------------

    def stop_node(self):

        if self.process is None:
            return

        self.get_logger().info("Stopping vr_teleop default_server_endpoint")

        self.terminate_process(self.process)
        self.process = None

        if self.tf_process is not None:
            self.get_logger().info("Stopping vr_teleop quest_tf_switch")
            self.terminate_process(self.tf_process)
            self.tf_process = None

        if self.pose_bridge_process is not None:
            self.get_logger().info("Stopping vr_teleop quest_tf_to_pose")
            self.terminate_process(self.pose_bridge_process)
            self.pose_bridge_process = None

        if self.ik_process is not None:
            self.get_logger().info("Stopping kinematics ik_node")
            self.terminate_process(self.ik_process)
            self.ik_process = None

    # --------------------------------

    def terminate_process(self, process):

        try:
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            process.wait(timeout=5)
        except ProcessLookupError:
            pass
        except subprocess.TimeoutExpired:
            os.killpg(os.getpgid(process.pid), signal.SIGKILL)
            process.wait()

    # --------------------------------

    def call_sync(self, client, req, timeout=2.0):

        if not client.wait_for_service(timeout_sec=0.5):
            return None

        future = client.call_async(req)

        start = time.monotonic()

        while not future.done():

            if time.monotonic() - start > timeout:
                return None

            time.sleep(0.01)

        return future.result()

    # --------------------------------

    def get_mode(self):

        req = GetParameters.Request()
        req.names = ["mode"]

        result = self.call_sync(self.mode_get_client, req)

        if result is None or not result.values:
            return None

        return result.values[0].string_value

    # --------------------------------

    def set_mode(self, mode):

        req = SetParameters.Request()

        p = ParameterMsg()
        p.name = "mode"
        p.value = ParameterValue(
            type=ParameterType.PARAMETER_STRING,
            string_value=mode,
        )
        req.parameters.append(p)

        self.get_logger().info(f"Requesting /mode_toggler mode = {mode}")

        # mode_toggler's own confirm budget (DOWNSTREAM_CONFIRM_TIMEOUT_S) is
        # 3.0s - it can legitimately take that long waiting on teach_mode_node's
        # hardware gain confirm. call_sync()'s 2.0s default would then give up
        # here before mode_toggler ever replies, misreporting a real (if slow)
        # success as a timeout.
        return self.call_sync(self.mode_set_client, req, timeout=4.0)

    # --------------------------------

    def set_bool_param(self, client, node_name, name, enabled):

        req = SetParameters.Request()

        p = ParameterMsg()
        p.name = name
        p.value = ParameterValue(
            type=ParameterType.PARAMETER_BOOL,
            bool_value=enabled,
        )
        req.parameters.append(p)

        self.get_logger().info(f"Requesting {node_name} {name} = {enabled}")

        result = self.call_sync(client, req)

        if result is None or not result.results or not result.results[0].successful:
            return False

        return True

    # --------------------------------

    def set_posture(self, enabled):

        if not self.set_bool_param(
                self.ik_set_params_client, "/dual_arm_ik", "posture_enabled", enabled):
            return False

        self.posture_enabled = enabled
        return True

    # --------------------------------

    def set_collision(self, enabled):

        if not self.set_bool_param(
                self.ik_set_params_client, "/dual_arm_ik", "collision_enabled", enabled):
            return False

        self.collision_enabled = enabled
        return True

    # --------------------------------

    def set_gripper_publish(self, enabled):

        if not self.set_bool_param(
                self.gripper_set_params_client, "/vr_gripper_servo", "publish_enabled", enabled):
            return False

        self.gripper_publish_enabled = enabled
        return True

    # --------------------------------

    def get_double_param(self, client, name):

        req = GetParameters.Request()
        req.names = [name]

        result = self.call_sync(client, req)

        if result is None or not result.values:
            return None

        return result.values[0].double_value

    # --------------------------------

    def set_double_param(self, client, node_name, name, value):

        req = SetParameters.Request()

        p = ParameterMsg()
        p.name = name
        p.value = ParameterValue(
            type=ParameterType.PARAMETER_DOUBLE,
            double_value=value,
        )
        req.parameters.append(p)

        self.get_logger().info(f"Requesting {node_name} {name} = {value}")

        result = self.call_sync(client, req)

        if result is None or not result.results or not result.results[0].successful:
            return False

        return True

    # --------------------------------

    def get_max_velocity(self):
        return self.get_double_param(self.joint_limiter_get_client, "max_velocity")

    def set_max_velocity(self, value):
        return self.set_double_param(
            self.joint_limiter_set_client, "/joint_command_limiter", "max_velocity", value)

    # --------------------------------

    def get_max_acceleration(self):
        return self.get_double_param(self.joint_limiter_get_client, "max_acceleration")

    def set_max_acceleration(self, value):
        return self.set_double_param(
            self.joint_limiter_set_client, "/joint_command_limiter", "max_acceleration", value)

    # --------------------------------

    def read_logs(self, process, publisher, stream):

        while process and process.stdout:

            line = process.stdout.readline()

            if not line:
                break

            msg = String()
            msg.data = line.rstrip()

            publisher.publish(msg)
            _append(stream, msg.data)

            self.get_logger().info(line.rstrip())


def main():

    global _node

    rclpy.init()

    node = VRManagementUI()
    _node = node

    executor = MultiThreadedExecutor()
    executor.add_node(node)
    threading.Thread(target=executor.spin, daemon=True).start()

    node.get_logger().info(f"TCP/IK log viewer on http://{socket.gethostname().lower()}.local:8101")

    try:
        app.run(host="0.0.0.0", port=8101, threaded=True)
    finally:
        node.stop_node()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
