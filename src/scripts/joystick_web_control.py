#!/usr/bin/env python3

import logging
import threading
import time

from flask import Flask, request, jsonify, render_template_string

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist

logging.getLogger("werkzeug").setLevel(logging.WARNING)

# =====================================================
# CONFIG
# =====================================================

MAX_LINEAR = 0.5      # m/s at full forward/back deflection
MAX_ANGULAR = 1.0      # rad/s at full left/right deflection
PUBLISH_RATE_HZ = 20.0
DEADMAN_TIMEOUT = 0.5  # zero cmd_vel if no joystick update received within this long
WEB_PORT = 8120

# =====================================================
# SHARED JOYSTICK STATE
# =====================================================

_state_lock = threading.Lock()
_joy_x = 0.0
_joy_y = 0.0
_last_update = 0.0


class JoystickCmdVelPublisher(Node):

    def __init__(self):
        super().__init__("joystick_web_control")

        self.publisher = self.create_publisher(Twist, "/cmd_vel", 10)
        self.timer = self.create_timer(1.0 / PUBLISH_RATE_HZ, self._publish_cmd_vel)

        print("JOYSTICK WEB CONTROL STARTED")

    # -----------------------------------------------------
    # TIMER CALLBACK
    # -----------------------------------------------------

    def _publish_cmd_vel(self):

        with _state_lock:
            x, y, last = _joy_x, _joy_y, _last_update

        msg = Twist()

        if (time.time() - last) > DEADMAN_TIMEOUT:
            msg.linear.x = 0.0
            msg.angular.z = 0.0
        else:
            msg.linear.x = y * MAX_LINEAR
            msg.angular.z = -x * MAX_ANGULAR

        self.publisher.publish(msg)


def _ros_spin(node):
    rclpy.spin(node)


# =====================================================
# FLASK APP
# =====================================================

app = Flask(__name__)

PAGE = """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Joystick Control</title>
<style>
  :root {
    --accent: #10b981;
    --accent-glow: rgba(16,185,129,.55);
    --bg-1: #0b0d12;
    --bg-2: #151823;
    --card: rgba(255,255,255,.04);
    --border: rgba(255,255,255,.08);
    --text: #e5e7eb;
    --muted: #7b8394;
  }
  * { box-sizing: border-box; }
  html, body {
    margin: 0; min-height: 100%; color: var(--text);
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    background:
      radial-gradient(circle at 15% 10%, rgba(16,185,129,.10), transparent 40%),
      radial-gradient(circle at 85% 90%, rgba(59,130,246,.10), transparent 45%),
      linear-gradient(160deg, var(--bg-1), var(--bg-2));
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    gap: 22px; touch-action: none; padding: 24px;
  }

  #pad {
    width: 260px; height: 260px; border-radius: 50%;
    background:
      repeating-radial-gradient(circle, transparent 0 38px, rgba(255,255,255,.025) 39px 40px),
      radial-gradient(circle at 50% 50%, #1b2030, #0c0e14);
    border: 1px solid var(--border);
    box-shadow: inset 0 0 40px rgba(0,0,0,.6), 0 0 0 1px rgba(255,255,255,.02);
    position: relative; touch-action: none;
  }
  #pad::before, #pad::after {
    content: ''; position: absolute; background: rgba(255,255,255,.12);
  }
  #pad::before { left: 50%; top: 8px; bottom: 8px; width: 1px; transform: translateX(-50%); }
  #pad::after { top: 50%; left: 8px; right: 8px; height: 1px; transform: translateY(-50%); }
  #crosshair {
    position: absolute; left: 50%; top: 50%; width: 6px; height: 6px;
    border-radius: 50%; background: rgba(255,255,255,.25);
    transform: translate(-50%, -50%);
  }
  #stick {
    width: 74px; height: 74px; border-radius: 50%;
    background: radial-gradient(circle at 35% 30%, #34e3a1, var(--accent) 70%);
    box-shadow: 0 0 22px var(--accent-glow), 0 4px 10px rgba(0,0,0,.4), inset 0 2px 4px rgba(255,255,255,.35);
    position: absolute; left: 50%; top: 50%;
    transform: translate(-50%, -50%);
    transition: box-shadow .15s ease;
    cursor: grab;
  }
  #stick.active { cursor: grabbing; box-shadow: 0 0 34px var(--accent-glow), 0 4px 10px rgba(0,0,0,.4); }
</style>
</head>
<body>
  <div id="pad"><div id="crosshair"></div><div id="stick"></div></div>

<script>
const pad = document.getElementById('pad');
const stick = document.getElementById('stick');
const radius = pad.clientWidth / 2;
let dragging = false;
let sendTimer = null;

function setStick(x, y) {
  stick.style.left = (50 + x * 50) + '%';
  stick.style.top = (50 - y * 50) + '%';
}

function sendJoystick(x, y) {
  fetch('/api/joystick', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({x: x, y: y})
  }).catch(() => {});
}

function startSending(getXY) {
  if (sendTimer) clearInterval(sendTimer);
  sendTimer = setInterval(() => {
    const [x, y] = getXY();
    sendJoystick(x, y);
  }, 100);
}

function stopSending() {
  if (sendTimer) { clearInterval(sendTimer); sendTimer = null; }
}

let curX = 0, curY = 0;

function updateFromEvent(evt) {
  const rect = pad.getBoundingClientRect();
  const cx = rect.left + rect.width / 2;
  const cy = rect.top + rect.height / 2;
  const px = (evt.clientX !== undefined ? evt.clientX : evt.touches[0].clientX) - cx;
  const py = (evt.clientY !== undefined ? evt.clientY : evt.touches[0].clientY) - cy;

  let x = px / radius;
  let y = -py / radius;

  const mag = Math.hypot(x, y);
  if (mag > 1) { x /= mag; y /= mag; }

  curX = x; curY = y;
  setStick(x, y);
}

function onDown(evt) {
  dragging = true;
  stick.classList.add('active');
  updateFromEvent(evt);
  startSending(() => [curX, curY]);
}

function onMove(evt) {
  if (!dragging) return;
  evt.preventDefault();
  updateFromEvent(evt);
}

function onUp() {
  if (!dragging) return;
  dragging = false;
  stick.classList.remove('active');
  curX = 0; curY = 0;
  setStick(0, 0);
  sendJoystick(0, 0);
  stopSending();
}

pad.addEventListener('mousedown', onDown);
window.addEventListener('mousemove', onMove);
window.addEventListener('mouseup', onUp);

pad.addEventListener('touchstart', onDown, {passive: false});
window.addEventListener('touchmove', onMove, {passive: false});
window.addEventListener('touchend', onUp);
</script>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(PAGE)


@app.route("/api/joystick", methods=["POST"])
def api_joystick():
    global _joy_x, _joy_y, _last_update

    data = request.get_json(force=True, silent=True) or {}

    try:
        x = max(-1.0, min(1.0, float(data.get("x", 0.0))))
        y = max(-1.0, min(1.0, float(data.get("y", 0.0))))
    except (TypeError, ValueError):
        return jsonify(ok=False, error="invalid x/y"), 400

    with _state_lock:
        _joy_x = x
        _joy_y = y
        _last_update = time.time()

    return jsonify(ok=True)


# =====================================================
# MAIN
# =====================================================

def main():
    rclpy.init()
    node = JoystickCmdVelPublisher()

    ros_thread = threading.Thread(target=_ros_spin, args=(node,), daemon=True)
    ros_thread.start()

    try:
        app.run(host="0.0.0.0", port=WEB_PORT, debug=False, use_reloader=False)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
