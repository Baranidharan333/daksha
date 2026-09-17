#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, QoSDurabilityPolicy, QoSReliabilityPolicy, QoSHistoryPolicy
from std_msgs.msg import String
from flask import Flask, jsonify, render_template_string, request
import subprocess
import signal
import os
import re
import ipaddress
import socket
import threading
import time
import logging
from werkzeug.serving import WSGIRequestHandler

# Bare labels ("leader1") or dotted hostnames ("leader1.local"); no
# spaces/slashes/shell metacharacters, and must start with a letter or
# digit so a leading "-" can't be mistaken for a `ping` flag.
_HOSTNAME_RE = re.compile(
    r'^[A-Za-z0-9]([A-Za-z0-9-]{0,62})?(\.[A-Za-z0-9]([A-Za-z0-9-]{0,62})?)*$'
)


def normalize_host(raw):
    """Validate a user-supplied host and return the resolvable form, or
    None if it isn't a plausible hostname/IP. Bare labels default to
    mDNS (leader1 -> leader1.local) since that's how these robots are
    reached on the LAN."""
    host = (raw or "").strip()
    if not host:
        return None
    try:
        ipaddress.ip_address(host)
        return host
    except ValueError:
        pass
    if not _HOSTNAME_RE.match(host):
        return None
    if "." not in host:
        host += ".local"
    return host

# Must match mode_toggler's publisher QoS (transient-local) so this
# subscriber gets the last settled mode even if it connects after
# mode_toggler already published it, instead of waiting forever.
MODE_STATUS_QOS = QoSProfile(
    depth=1,
    reliability=QoSReliabilityPolicy.RELIABLE,
    durability=QoSDurabilityPolicy.TRANSIENT_LOCAL,
    history=QoSHistoryPolicy.KEEP_LAST,
)

# Flask app
app = Flask(__name__)

# Global state
process = None
last_mode = None
node_instance = None

HTML = """
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Gen2 Leader Control</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">

<style>

:root{
  --bg:#eef3fb; --panel:#ffffff; --panel-2:#f7faff; --line:#dbe5f1;
  --txt:#16263b; --muted:#5b6b80; --dim:#93a3b8;
  --blue:#1f6feb; --blue-deep:#0b53c4; --blue-soft:#eaf2ff;
  --rec:#e5484d; --play:#1f6feb; --ready:#16a34a; --amber:#c2750a;
  --shadow:0 1px 2px rgba(16,33,61,.05), 0 10px 26px rgba(16,33,61,.07);
  --shadow-sm:0 1px 2px rgba(16,33,61,.06);
}
*{box-sizing:border-box}
body{
  margin:0; color:var(--txt); min-height:100vh;
  background:
    radial-gradient(900px 480px at 88% -8%, rgba(31,111,235,.10), transparent 62%),
    linear-gradient(180deg,#f6f9ff,#eef3fb);
  font-family:"Space Grotesk",system-ui,sans-serif; -webkit-font-smoothing:antialiased;
}
.mono{font-family:"IBM Plex Mono",monospace}
.wrap{max-width:720px; margin:0 auto; padding:26px 22px 60px}

header{display:flex; align-items:center; justify-content:space-between; gap:18px; flex-wrap:wrap;
  padding-bottom:18px; border-bottom:1px solid var(--line); margin-bottom:20px;}
.brand{display:flex; align-items:center; gap:14px; flex-wrap:wrap}
.lamp{width:13px; height:13px; border-radius:50%; background:var(--dim);
  box-shadow:0 0 0 4px rgba(31,111,235,.07); transition:.25s}
.lamp.ready{background:var(--ready); box-shadow:0 0 9px rgba(22,163,74,.5)}
.lamp.rec{background:var(--rec); box-shadow:0 0 12px rgba(229,72,77,.6),0 0 0 4px rgba(229,72,77,.12); animation:pulse 1s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.3}}
h1{font-size:21px; font-weight:600; letter-spacing:.13em; text-transform:uppercase; margin:0; color:var(--blue-deep)}
h1 small{display:block; font-size:10.5px; letter-spacing:.3em; color:var(--muted); font-weight:500; margin-top:3px}
.state-badge{font-family:"IBM Plex Mono",monospace; font-size:11px; letter-spacing:.16em;
  color:var(--muted); background:var(--panel); border:1px solid var(--line); border-radius:8px;
  padding:7px 12px; text-transform:uppercase; box-shadow:var(--shadow-sm);
  display:inline-flex; align-items:center; gap:8px}
.state-badge b{color:var(--blue-deep); font-weight:600}

.card{background:var(--panel); border:1px solid var(--line); border-radius:14px;
  padding:20px; box-shadow:var(--shadow)}
.eyebrow{font-family:"IBM Plex Mono",monospace; font-size:10.5px; letter-spacing:.24em;
  text-transform:uppercase; color:var(--blue); display:flex; align-items:center; gap:8px; margin-bottom:16px}
.eyebrow::before{content:""; width:18px; height:2px; background:var(--blue); border-radius:2px; opacity:.5}

.btns{display:flex; gap:10px; flex-wrap:wrap}
button, a.b-primary{font-family:"Space Grotesk",sans-serif; font-weight:600; font-size:13px; letter-spacing:.03em;
  border:1px solid var(--line); background:#fff; color:var(--txt); padding:13px 18px;
  border-radius:9px; cursor:pointer; transition:.15s; display:inline-flex; align-items:center; gap:8px;
  box-shadow:var(--shadow-sm); flex:1 1 200px; justify-content:center}
button:hover, a.b-primary:hover{border-color:var(--dim); transform:scale(1.02)}
button:active, a.b-primary:active{transform:scale(0.98)}
.b-primary{background:var(--blue); border-color:var(--blue); color:#fff}
.b-primary:hover{background:var(--blue-deep); border-color:var(--blue-deep)}
a.b-primary{background:var(--blue); border-color:var(--blue); color:#fff}
a.b-primary:hover{background:var(--blue-deep); border-color:var(--blue-deep)}
.b-play{border-color:rgba(31,111,235,.45); color:var(--blue)}
.b-play:hover{background:var(--blue-soft)}
.b-rec{border-color:rgba(229,72,77,.45); color:var(--rec)}
.b-rec:hover{background:#fff0f0}
.dot{width:9px;height:9px;border-radius:50%;background:currentColor;display:inline-block}

.toggle{display:flex; gap:0; border:1px solid var(--line); border-radius:9px; overflow:hidden;
  box-shadow:var(--shadow-sm)}
.toggle button{flex:1; border:none; border-radius:0; box-shadow:none; background:#fff}
.toggle button:not(:last-child){border-right:1px solid var(--line)}
.toggle button.active{background:var(--blue); color:#fff}
.toggle button.active.teach{background:var(--amber)}
button:disabled{opacity:.5; cursor:not-allowed; transform:none}
.b-home{background:var(--ready); border-color:var(--ready); color:#fff}
.b-home:hover{background:#128a3e; border-color:#128a3e}

.readout{display:grid; grid-template-columns:repeat(3,1fr); gap:1px; background:var(--line);
  border:1px solid var(--line); border-radius:10px; overflow:hidden; margin-top:18px}
.readout div{background:var(--panel-2); padding:12px 14px}
.readout .k{font-size:10px; letter-spacing:.15em; text-transform:uppercase; color:var(--dim)}
.readout .v{font-family:"IBM Plex Mono",monospace; font-size:19px; color:var(--txt); margin-top:4px}
.readout .v.live{color:var(--ready)}
.readout .v.err{color:var(--rec)}

.field{margin-bottom:0}
label{display:block; font-size:11px; letter-spacing:.05em; color:var(--muted); margin:0 0 6px}
input{width:100%; background:#fbfdff; border:1px solid var(--line); color:var(--txt);
  font-family:"IBM Plex Mono",monospace; font-size:13px; padding:11px 12px; border-radius:9px; outline:none; transition:.15s}
input:focus{border-color:var(--blue); box-shadow:0 0 0 3px rgba(31,111,235,.12); background:#fff}
.row{display:flex; gap:10px}
.row input{flex:1}
.row button{flex:0 0 auto; width:auto; padding:11px 20px}
a.b-primary{text-decoration:none}

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
<div class="wrap">
  <header>
    <div class="brand">
      <span class="lamp" id="lamp"></span>
      <h1>Gen2 Leader Controller<small>Launch Control Console</small></h1>
    </div>
    <div style="display:flex; align-items:center; gap:12px">
      <div class="state-badge" id="stateBadge">STATUS · <b id="stateText">STOPPED</b></div>
      <button id="ihubEstop" onclick="ihubEmergencyStop()" title="Kill ROS 2 bringup" style="background:#d81f2f;color:#fff;border:2px solid rgba(255,255,255,.5);border-radius:8px;padding:8px 14px;font:700 12px/1.2 system-ui,-apple-system,sans-serif;letter-spacing:.04em;cursor:pointer;box-shadow:0 2px 10px rgba(216,31,47,.45);white-space:nowrap;">&#9211; E-STOP</button>
    </div>
  </header>

  <div class="card">
    <div class="eyebrow">Launch Controls</div>
    <div class="btns">
      <button class="b-primary" onclick="run('/normal')"><span class="dot"></span> Start Normal</button>
      <button class="b-play" onclick="run('/mirror')"><span class="dot"></span> Start Mirror</button>
      <button onclick="run('/restart')"><span class="dot"></span> Restart</button>
      <button class="b-rec" onclick="run('/kill')"><span class="dot"></span> Kill Launch</button>
    </div>

    <div class="readout">
      <div><div class="k">Status</div><div class="v" id="statusVal">—</div></div>
      <div><div class="k">Mode</div><div class="v" id="modeVal">None</div></div>
      <div><div class="k">Port</div><div class="v">8102</div></div>
    </div>
  </div>

  <div class="card" style="margin-top:18px">
    <div class="eyebrow">Robot Mode</div>
    <div class="toggle">
      <button id="btnTeach" class="teach" onclick="setRobotMode('teach')">Teach</button>
      <button id="btnNormal" onclick="setRobotMode('normal')">Normal</button>
    </div>
    <div class="readout" style="grid-template-columns:1fr">
      <div><div class="k">Robot Mode</div><div class="v" id="robotModeVal">unknown</div></div>
    </div>
    <div class="btns" style="margin-top:14px">
      <button class="b-home" id="btnGoHome" onclick="goHome()"><span class="dot"></span> Go Home</button>
    </div>
    <div class="readout" style="grid-template-columns:1fr; margin-top:10px">
      <div><div class="k">Go Home</div><div class="v" id="homeMsg">—</div></div>
    </div>
  </div>

  <div class="card" style="margin-top:18px">
    <div class="eyebrow">Speed Limits</div>
    <div class="field">
      <label>Max Velocity (rad/s)</label>
      <div class="row">
        <input id="velocityInput" type="number" step="0.1" min="0" placeholder="—">
        <button class="b-primary" onclick="setVelocity()">Set</button>
      </div>
    </div>
    <div class="field" style="margin-top:14px">
      <label>Max Acceleration (rad/s²)</label>
      <div class="row">
        <input id="accelInput" type="number" step="0.5" min="0" placeholder="—">
        <button class="b-primary" onclick="setAcceleration()">Set</button>
      </div>
    </div>
  </div>

  <div class="card" style="margin-top:18px">
    <div class="eyebrow">Leader Portal</div>
    <div class="field">
      <label>Leader hostname</label>
      <div class="row">
        <input id="leaderHost" placeholder="leader1 or leader1.local" value="leader1">
        <button class="b-primary" onclick="checkLeader()">Connect</button>
      </div>
    </div>

    <div class="readout" style="grid-template-columns:1fr; margin-top:14px">
      <div><div class="k">Reachability</div><div class="v" id="leaderStatusVal">not checked</div></div>
    </div>

    <div class="btns" style="margin-top:14px">
      <a id="leaderLink" class="b-primary" style="display:none; margin-bottom:4px" href="#" target="_blank" rel="noopener">
        <span class="dot"></span> <span id="leaderLinkText">Open Portal</span>
      </a>
    </div>
  </div>
</div>

<script>

function run(url)
{
    fetch(url)
    .then(r=>r.json())
    .then(updateStatus);
}

function setRobotMode(mode)
{
    fetch("/mode/" + mode)
    .then(r=>r.json())
    .then(updateStatus);
}

function goHome()
{
    const btn = document.getElementById("btnGoHome");
    const msgEl = document.getElementById("homeMsg");
    btn.disabled = true;
    msgEl.textContent = "switching to normal, moving…";
    msgEl.className = "v";

    fetch("/home")
    .then(r=>r.json())
    .then(data=>{
        msgEl.textContent = data.message || (data.ok ? "done" : "failed");
        msgEl.className = data.ok ? "v live" : "v err";
        btn.disabled = false;
        updateStatus();
    })
    .catch(()=>{
        msgEl.textContent = "request failed";
        msgEl.className = "v err";
        btn.disabled = false;
    });
}

function checkLeader()
{
    const host = document.getElementById("leaderHost").value.trim();
    const statusVal = document.getElementById("leaderStatusVal");
    const link = document.getElementById("leaderLink");

    if(!host)
    {
        statusVal.textContent = "enter a hostname";
        statusVal.className = "v err";
        link.style.display = "none";
        return;
    }

    statusVal.textContent = "checking…";
    statusVal.className = "v";
    link.style.display = "none";

    fetch("/check_leader?host=" + encodeURIComponent(host))
    .then(r=>r.json())
    .then(data=>{
        if(!data.valid)
        {
            statusVal.textContent = "invalid hostname";
            statusVal.className = "v err";
            link.style.display = "none";
            return;
        }
        if(data.available)
        {
            statusVal.textContent = "available (" + data.host + ")";
            statusVal.className = "v live";
            document.getElementById("leaderLinkText").textContent = "Open http://" + data.host + "/";
            link.href = "http://" + data.host + "/";
            link.style.display = "inline-flex";
        }
        else
        {
            statusVal.textContent = "unreachable (" + data.host + ")";
            statusVal.className = "v err";
            link.style.display = "none";
        }
    })
    .catch(()=>{
        statusVal.textContent = "check failed";
        statusVal.className = "v err";
        link.style.display = "none";
    });
}

function setVelocity()
{
    const val = parseFloat(document.getElementById("velocityInput").value);
    if(isNaN(val)) return;
    fetch("/velocity_set/" + val).then(r=>r.json());
}

function setAcceleration()
{
    const val = parseFloat(document.getElementById("accelInput").value);
    if(isNaN(val)) return;
    fetch("/acceleration_set/" + val).then(r=>r.json());
}

function pollVelocity()
{
    fetch("/velocity_status")
    .then(r=>r.json())
    .then(data=>{
        const el = document.getElementById("velocityInput");
        if(data.available && document.activeElement !== el)
        {
            el.value = data.value.toFixed(2);
        }
    })
    .finally(()=>setTimeout(pollVelocity, 3000));
}

function pollAcceleration()
{
    fetch("/acceleration_status")
    .then(r=>r.json())
    .then(data=>{
        const el = document.getElementById("accelInput");
        if(data.available && document.activeElement !== el)
        {
            el.value = data.value.toFixed(2);
        }
    })
    .finally(()=>setTimeout(pollAcceleration, 3000));
}

pollVelocity();
pollAcceleration();

function updateStatus()
{
    fetch("/status")
    .then(r=>r.json())
    .then(data=>{

        const lamp = document.getElementById("lamp");
        const stateText = document.getElementById("stateText");
        const statusVal = document.getElementById("statusVal");
        const modeVal = document.getElementById("modeVal");
        const robotModeVal = document.getElementById("robotModeVal");
        const btnTeach = document.getElementById("btnTeach");
        const btnNormal = document.getElementById("btnNormal");

        if(data.running)
        {
            lamp.className = "lamp ready";
            stateText.textContent = "RUNNING";
            statusVal.textContent = "RUNNING";
            statusVal.className = "v live";
        }
        else
        {
            lamp.className = "lamp";
            stateText.textContent = "STOPPED";
            statusVal.textContent = "STOPPED";
            statusVal.className = "v";
        }

        modeVal.textContent = data.mode == null ? "None" : data.mode;

        robotModeVal.textContent = data.robot_mode;
        btnTeach.className = data.robot_mode === "teach" ? "teach active" : "teach";
        btnNormal.className = data.robot_mode === "normal" ? "active" : "";
    });
}

setInterval(updateStatus, 1000);

updateStatus();

</script>

</body>
</html>
"""


class Gen2LeaderNode(Node):
    """ROS2 Node for Gen2 Leader Control"""
    
    def __init__(self):
        super().__init__('gen2_leader_controller')
        self.get_logger().info('Gen2 Leader Controller Node started')
        self.process = None
        self.last_mode = None

        self._robot_mode = "unknown"
        self.create_subscription(
            String, "/mode_toggler/status", self._robot_mode_cb, MODE_STATUS_QOS,
        )

    def _robot_mode_cb(self, msg):
        self._robot_mode = msg.data

    def get_robot_mode(self):
        return self._robot_mode

    def set_robot_mode(self, mode):
        """Best-effort `ros2 param set /mode_toggler mode <mode>`."""
        if mode not in ("teach", "normal"):
            return False
        try:
            subprocess.run(
                ["ros2", "param", "set", "/mode_toggler", "mode", mode],
                check=True, capture_output=True, text=True, timeout=5.0,
            )
            self.get_logger().info(f'Robot mode set to {mode}')
            return True
        except Exception as e:
            self.get_logger().error(f'Failed to set robot mode to {mode}: {str(e)}')
            return False

    def get_double_param(self, node_name, name):
        """Best-effort `ros2 param get <node_name> <name>`, e.g. 'Double value is: 3.0'."""
        try:
            result = subprocess.run(
                ["ros2", "param", "get", node_name, name],
                check=True, capture_output=True, text=True, timeout=1.5,
            )
            return float(result.stdout.strip().rsplit(":", 1)[-1].strip())
        except Exception as e:
            self.get_logger().error(f'Failed to get {node_name} {name}: {str(e)}')
            return None

    def set_double_param(self, node_name, name, value):
        """Best-effort `ros2 param set <node_name> <name> <value>`."""
        try:
            subprocess.run(
                ["ros2", "param", "set", node_name, name, str(value)],
                check=True, capture_output=True, text=True, timeout=5.0,
            )
            self.get_logger().info(f'{node_name} {name} set to {value}')
            return True
        except Exception as e:
            self.get_logger().error(f'Failed to set {node_name} {name} to {value}: {str(e)}')
            return False

    def get_max_velocity(self):
        return self.get_double_param("/joint_command_limiter", "max_velocity")

    def set_max_velocity(self, value):
        return self.set_double_param("/joint_command_limiter", "max_velocity", value)

    def get_max_acceleration(self):
        return self.get_double_param("/joint_command_limiter", "max_acceleration")

    def set_max_acceleration(self, value):
        return self.set_double_param("/joint_command_limiter", "max_acceleration", value)

    def wait_for_mode(self, target, timeout_s=6.0):
        """Blocks (bounded) until /mode_toggler/status reports `target`."""
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            if self._robot_mode == target:
                return True, f"mode_toggler settled at '{target}'"
            time.sleep(0.05)
        return False, (
            f"mode_toggler did not settle at '{target}' in {timeout_s:.1f}s "
            f"(last status: '{self._robot_mode}')"
        )

    def move_home(self):
        """Switch to normal mode (so the arm actually tracks a trajectory
        instead of sitting backdrivable in teach mode), wait for it to land
        on hardware, then trigger the home move: the /move_home service if
        it's available, otherwise a direct zero-position /joint_cmd publish."""
        if not self.set_robot_mode("normal"):
            return False, "Failed to switch to normal mode."
        settled, wmsg = self.wait_for_mode("normal")
        if not settled:
            return False, wmsg

        try:
            result = subprocess.run(
                ["ros2", "service", "call", "/move_home", "std_srvs/srv/Trigger", "{}"],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0:
                self.get_logger().info('Triggered /move_home service')
                return True, "Switched to normal mode and triggered /move_home."
        except Exception as e:
            self.get_logger().error(f'/move_home service call failed: {str(e)}')

        # Fallback: publish zero positions directly to /joint_cmd.
        joint_names = [
            "left_joint_1", "left_joint_2", "left_joint_3", "left_joint_4",
            "left_joint_5", "left_joint_6", "left_joint_7",
            "right_joint_1", "right_joint_2", "right_joint_3", "right_joint_4",
            "right_joint_5", "right_joint_6", "right_joint_7",
            "left_gripper_left_joint", "right_gripper_right_joint",
        ]
        names = "[" + ", ".join(joint_names) + "]"
        positions = "[" + ", ".join("0" for _ in joint_names) + "]"
        try:
            subprocess.Popen([
                "ros2", "topic", "pub", "--once", "/joint_cmd",
                "sensor_msgs/msg/JointState",
                f"{{name: {names}, position: {positions}}}",
            ])
            return True, "Switched to normal mode and published Home pose to /joint_cmd."
        except Exception as e:
            self.get_logger().error(f'Home fallback publish failed: {str(e)}')
            return False, f"Failed to trigger home move: {str(e)}"

    def kill_process(self):
        """Kill the running process"""
        global process, last_mode
        
        if self.process is not None:
            if self.process.poll() is None:
                try:
                    os.killpg(os.getpgid(self.process.pid), signal.SIGINT)
                    self.process.wait(timeout=5)
                except:
                    try:
                        self.process.kill()
                    except:
                        pass
        
        self.process = None
        process = None
        last_mode = None
    
    def start_launch(self, mode):
        """Start a launch (normal or mirror)"""
        global process, last_mode
        
        self.get_logger().info(f'Starting {mode} launch...')
        
        self.kill_process()
        
        if mode == "normal":
            cmd = """
            source /opt/ros/humble/setup.bash
            source ~/.barani/gen2_full/install/setup.bash
            ros2 launch gen2_leader gen2_leader.launch.py
            """
        elif mode == "mirror":
            cmd = """
            source /opt/ros/humble/setup.bash
            source ~/.barani/gen2_full/install/setup.bash
            ros2 launch gen2_leader gen2_leader_mirror.launch.py
            """
        else:
            return False
        
        try:
            self.process = subprocess.Popen(
                ["bash", "-c", cmd],
                preexec_fn=os.setsid
            )
            process = self.process
            last_mode = mode
            self.last_mode = mode
            
            self.get_logger().info(f'{mode} launch started (PID: {self.process.pid})')
            return True
        except Exception as e:
            self.get_logger().error(f'Failed to start {mode} launch: {str(e)}')
            return False
    
    def is_running(self):
        """Check if process is running"""
        if self.process is None:
            return False
        return self.process.poll() is None


# ============================================================================
# Flask Routes
# ============================================================================

@app.route("/")
def index():
    return render_template_string(HTML)


@app.route("/normal")
def normal():
    if node_instance:
        node_instance.start_launch("normal")
    return jsonify(ok=True)


@app.route("/mirror")
def mirror():
    if node_instance:
        node_instance.start_launch("mirror")
    return jsonify(ok=True)


@app.route("/kill")
def kill():
    global process, last_mode
    if node_instance:
        node_instance.kill_process()
    process = None
    last_mode = None
    return jsonify(ok=True)


@app.route("/restart")
def restart():
    if node_instance and node_instance.last_mode:
        node_instance.start_launch(node_instance.last_mode)
    return jsonify(ok=True)


@app.route("/home")
def go_home():
    ok, msg = False, "Node not ready."
    if node_instance:
        ok, msg = node_instance.move_home()
    return jsonify(ok=ok, message=msg)


@app.route("/mode/<mode>")
def set_mode(mode):
    ok = False
    if node_instance:
        ok = node_instance.set_robot_mode(mode)
    return jsonify(ok=ok)


@app.route("/velocity_status")
def velocity_status():
    value = node_instance.get_max_velocity() if node_instance else None
    return jsonify(available=value is not None, value=value)


@app.route("/velocity_set/<value>")
def velocity_set(value):
    ok = False
    if node_instance:
        try:
            ok = node_instance.set_max_velocity(float(value))
        except ValueError:
            ok = False
    return jsonify(ok=ok)


@app.route("/acceleration_status")
def acceleration_status():
    value = node_instance.get_max_acceleration() if node_instance else None
    return jsonify(available=value is not None, value=value)


@app.route("/acceleration_set/<value>")
def acceleration_set(value):
    ok = False
    if node_instance:
        try:
            ok = node_instance.set_max_acceleration(float(value))
        except ValueError:
            ok = False
    return jsonify(ok=ok)


@app.route("/check_leader")
def check_leader():
    host = normalize_host(request.args.get("host", ""))
    if host is None:
        return jsonify(valid=False, available=False, host=None)

    try:
        result = subprocess.run(
            ["ping", "-c", "1", "-W", "2", host],
            capture_output=True, text=True, timeout=5.0,
        )
        available = result.returncode == 0
    except Exception:
        available = False

    return jsonify(valid=True, available=available, host=host)


@app.route("/status")
def status():
    running = False
    mode = None
    robot_mode = "unknown"

    if node_instance:
        running = node_instance.is_running()
        mode = node_instance.last_mode
        robot_mode = node_instance.get_robot_mode()

    return jsonify(
        running=running,
        mode=mode,
        robot_mode=robot_mode
    )


# ============================================================================
# Main
# ============================================================================

def run_flask():
    """Run Flask server in separate thread"""
    print("Web server starting on http://0.0.0.0:8102")

    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)

    app.run(host="0.0.0.0", port=8102, debug=False, use_reloader=False, threaded=True)


def main():
    """Main entry point"""
    global node_instance
    
    # Initialize ROS2
    rclpy.init()
    
    # Create ROS2 node
    node = Gen2LeaderNode()
    node_instance = node
    
    print("="*60)
    print(" Gen2 Leader Web Controller (ROS2 Node)")
    print("="*60)
    print("Open your browser:")
    print(f"  http://{socket.gethostname().lower()}.local:8102")
    print("  or")
    print("  http://<ROBOT_IP>:8102")
    print("="*60)
    print()
    
    # Start Flask in separate thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Spin ROS2 node
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Shutting down...')
        node.kill_process()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
