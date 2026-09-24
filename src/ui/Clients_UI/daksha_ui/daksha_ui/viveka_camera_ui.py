#!/usr/bin/env python3
"""
VIVEKA  -  Multi-Camera Web Monitor  (ROS 2 + Flask)
====================================================
Subscribes to the robot's ROS 2 camera topics and serves them as a single
web page (2x2 layout) on the device's IP, with the VIVEKA control-room theme
and the scanning/lock overlay. Open the printed URL from any device on the
same network.

    TRIVIEW GATEWAY:      python3 viveka_camera_ui.py
    ROBOT (with ROS 2):   python3 viveka_camera_ui.py --ros
    ANY LAPTOP (no ROS):  python3 viveka_camera_ui.py --demo

Then browse to   http://<device-ip>:7002

By default this page displays only the three WebRTC camera feeds from
http://192.168.11.200:8090, served by
/home/s1/.ihub/camera/build/triview. The local gateway starts automatically
when needed and stops with this UI if this UI started it.
Override its address with --gateway-url or VIVEKA_GATEWAY_URL.

This script supports BOTH Raw (`sensor_msgs/Image`) and Compressed 
(`sensor_msgs/CompressedImage`) topics automatically. If your topic name ends with
'compressed', it will use CompressedImage, otherwise it will use raw Image.

Requires:  flask, opencv-python, numpy   (+ rclpy on the robot)
    pip install flask opencv-python numpy
"""

import sys
import os
import subprocess
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import build_opener, ProxyHandler
import json
import logging
import time
import socket
import argparse
import threading
from collections import deque

import numpy as np
import cv2
from flask import Flask, Response
from werkzeug.serving import make_server

# --------------------------------------------------------------- cameras ---
# (display name, ROS 2 topic)   <-- edit to match your robot
# If the topic ends in 'compressed', it subscribes to CompressedImage, else raw Image
CAMERAS = [
    ("WORLD · ZED RIGHT", "/zed/zed_node/right/color/rect/image/compressed"),
    ("WORLD · ZED LEFT", "/zed/zed_node/left/color/rect/image/compressed"),
    ("RIGHT ARM", "/right/camera/color/image_raw/compressed"),
    ("LEFT ARM", "/left/camera/color/image_raw/compressed"),
]
PORT = 7002
JPEG_QUALITY = 80


# --------------------------------------------------------------- store -----
class Cam:
    def __init__(self, idx, name, topic):
        self.idx, self.name, self.topic = idx, name, topic
        self._jpeg = None
        self._lock = threading.Lock()
        self._t = deque(maxlen=30)
        self.w = self.h = 0
        self.count = 0

    def update(self, jpeg, w=0, h=0):
        with self._lock:
            self._jpeg = jpeg
            self.count += 1
            self._t.append(time.time())
            if w:
                self.w, self.h = w, h

    def jpeg(self):
        with self._lock:
            return self._jpeg

    def fps(self):
        with self._lock:
            if len(self._t) < 2:
                return 0.0
            dt = self._t[-1] - self._t[0]
            return (len(self._t) - 1) / dt if dt > 0 else 0.0

    def online(self):
        with self._lock:
            return bool(self._t) and (time.time() - self._t[-1] < 2.0)


CAMS = [Cam(i, n, t) for i, (n, t) in enumerate(CAMERAS)]


def _placeholder(text="NO SIGNAL"):
    img = np.full((360, 640, 3), 18, np.uint8)
    cv2.putText(img, text, (230, 188), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                (90, 90, 96), 2, cv2.LINE_AA)
    ok, buf = cv2.imencode(".jpg", img)
    return buf.tobytes()


NO_SIGNAL = _placeholder()


# ------------------------------------------------------------- ROS 2 -------
def start_ros():
    """Bring up the ROS node and return the settings it read as parameters.

    Camera tiles, JPEG quality and the serving port come from
    Clients_UI/config/daksha_ui.yaml, handed over as a ROS parameter file by
    daksha_ui/launch/client_ui.launch.py. The module-level CAMERAS/PORT/
    JPEG_QUALITY constants stay as the fallback for --demo and the TriView
    gateway mode, which run without ROS at all.
    """
    global CAMS, JPEG_QUALITY

    import rclpy
    from rclpy.exceptions import ParameterNotDeclaredException
    from rclpy.node import Node
    from rclpy.qos import qos_profile_sensor_data
    from sensor_msgs.msg import CompressedImage, Image

    rclpy.init()
    node = Node(
        "viveka_web_monitor",
        automatically_declare_parameters_from_overrides=True,
    )

    def param(name, default):
        """Parameter value, or `default` when no params file supplied it."""
        try:
            return node.get_parameter(name).value
        except ParameterNotDeclaredException:
            return default

    names = list(param("daksha_ui.viveka_camera.camera_names", [n for n, _ in CAMERAS]))
    topics = list(param("daksha_ui.viveka_camera.camera_topics", [t for _, t in CAMERAS]))
    if len(names) != len(topics):
        # Parallel lists are the only way a parameter file can carry a list of
        # pairs, so a mismatched edit is a real possibility; pair what we can
        # rather than dying or silently showing the wrong label on a tile.
        node.get_logger().warn(
            f"camera_names ({len(names)}) and camera_topics ({len(topics)}) "
            f"differ in length - using the first {min(len(names), len(topics))}"
        )

    CAMS = [Cam(i, n, t) for i, (n, t) in enumerate(zip(names, topics))]
    JPEG_QUALITY = int(param("daksha_ui.viveka_camera.jpeg_quality", JPEG_QUALITY))

    def make_cb(cam):
        def cb(msg):
            # Check if it's a CompressedImage
            if isinstance(msg, CompressedImage):
                data = bytes(msg.data)
                fmt = (getattr(msg, "format", "") or "").lower()
                if "jpeg" in fmt or "jpg" in fmt:
                    jpeg = data
                    if cam.w == 0:                      # learn size once, cheaply
                        im = cv2.imdecode(np.frombuffer(data, np.uint8),
                                          cv2.IMREAD_COLOR)
                        if im is not None:
                            cam.update(jpeg, im.shape[1], im.shape[0]); return
                    cam.update(jpeg)
                else:                                    # png or other -> re-encode
                    im = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
                    if im is None:
                        return
                    ok, buf = cv2.imencode(".jpg", im,
                                           [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
                    cam.update(buf.tobytes(), im.shape[1], im.shape[0])
            else: 
                # Handle raw Image
                data = bytes(msg.data)
                channels = 4 if msg.encoding in ("bgra8", "rgba8") else (1 if msg.encoding in ("mono8", "mono16") else 3)
                
                # Reshape raw bytes to numpy array
                try:
                    if msg.encoding in ("rgb8", "bgr8", "bgra8", "rgba8"):
                        im = np.frombuffer(data, dtype=np.uint8).reshape((msg.height, msg.width, channels))
                        # OpenCV expects BGR format
                        if msg.encoding == "rgb8":
                            im = cv2.cvtColor(im, cv2.COLOR_RGB2BGR)
                        elif msg.encoding == "rgba8":
                            im = cv2.cvtColor(im, cv2.COLOR_RGBA2BGR)
                        elif msg.encoding == "bgra8":
                            im = cv2.cvtColor(im, cv2.COLOR_BGRA2BGR)
                    elif msg.encoding == "mono8":
                        im = np.frombuffer(data, dtype=np.uint8).reshape((msg.height, msg.width))
                    else:
                        # Fallback for other encodings
                        im = np.frombuffer(data, dtype=np.uint8).reshape((msg.height, msg.width, -1))
                except Exception as e:
                    node.get_logger().error(f"Error decoding raw image: {e}")
                    return

                ok, buf = cv2.imencode(".jpg", im, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
                cam.update(buf.tobytes(), im.shape[1], im.shape[0])
                
        return cb

    for cam in CAMS:
        if cam.topic.endswith('compressed'):
            node.create_subscription(CompressedImage, cam.topic,
                                     make_cb(cam), qos_profile_sensor_data)
        else:
            node.create_subscription(Image, cam.topic,
                                     make_cb(cam), qos_profile_sensor_data)
        node.get_logger().info(f"subscribed: {cam.topic}")

    threading.Thread(target=rclpy.spin, args=(node,), daemon=True).start()

    return {
        "host": param("daksha_ui.viveka_camera.host", "0.0.0.0"),
        "port": param("daksha_ui.viveka_camera.port", None),
    }


# ------------------------------------------------------------- demo --------
def start_demo():
    stop = threading.Event()

    def loop(cam, base_hue):
        w, h = 640, 360
        t0 = time.time()
        ramp = np.linspace(0, 1, h)[:, None, None]
        while not stop.is_set():
            t = time.time() - t0
            top = np.array([base_hue, 70, 55], np.float32)
            img = (top * (1 - ramp) + np.array([14, 12, 16]) * ramp).astype(np.uint8)
            cx = int(w * 0.5 + 120 * np.sin(t * 0.7))
            cy = int(h * 0.55 + 40 * np.sin(t * 1.1))
            cv2.rectangle(img, (cx - 70, cy - 50), (cx + 70, cy + 50),
                          (200, 170, 90), -1)
            cv2.putText(img, cam.name, (16, 30), cv2.FONT_HERSHEY_SIMPLEX,
                        0.6, (240, 240, 240), 1, cv2.LINE_AA)
            cv2.putText(img, "DEMO FEED", (16, h - 16), cv2.FONT_HERSHEY_SIMPLEX,
                        0.5, (180, 180, 188), 1, cv2.LINE_AA)
            ok, buf = cv2.imencode(".jpg", img,
                                   [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
            cam.update(buf.tobytes(), w, h)
            time.sleep(1 / 20)

    hues = [110, 18, 145, 40]
    for cam, hue in zip(CAMS, hues):
        threading.Thread(target=loop, args=(cam, hue), daemon=True).start()
    return stop


# ------------------------------------------------------------- web ---------
logging.getLogger("werkzeug").setLevel(logging.WARNING)

app = Flask(__name__)
app.config["GATEWAY_URL"] = os.environ.get(
    "VIVEKA_GATEWAY_URL", "http://192.168.11.200:8090"
)

GATEWAY_PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Cameras</title>
<style>
*{box-sizing:border-box}html,body{margin:0;width:100%;height:100%;background:#000}
main{height:100dvh;display:grid;grid-template-columns:1fr 1fr;
grid-template-rows:1fr 1fr;gap:4px;padding:4px}
.feed{position:relative;min-width:0;min-height:0;background:#080808}
.feed{overflow:hidden;container-type:size}
/* The gateway letterboxes the side-by-side ZED image into 16:9.
   Enlarge each half and crop the top/bottom padding from that stream. */
.stereo-view{height:100%;width:min(100%,calc(100cqh * var(--stereo-ratio,1.777778)));margin:auto;overflow:hidden}
.stereo-view video{position:relative;top:-50%;width:200%;height:200%;max-width:none}
.stereo-right video{transform:translateX(-50%)}
video{display:block;width:100%;height:100%;object-fit:contain}
.state{position:absolute;inset:0;display:grid;place-items:center;
color:#aaa;font:14px sans-serif;pointer-events:none}
.state:empty{display:none}

</style></head><body><main aria-label="Live cameras">
<section class="feed stereo-left"><div class="stereo-view"><video autoplay muted playsinline aria-label="Stereo left"></video></div><span class="state"></span></section>
<section class="feed stereo-right"><div class="stereo-view"><video autoplay muted playsinline aria-label="Stereo right"></video></div><span class="state"></span></section>
<section class="feed"><video autoplay muted playsinline aria-label="Camera 2"></video><span class="state"></span></section>
<section class="feed"><video autoplay muted playsinline aria-label="Camera 3"></video><span class="state"></span></section>
</main><script>
const gateway = %%GATEWAY_JSON%%;
let stopped = false;
const cleanups = [];
document.querySelectorAll('.feed:not(.stereo-right)').forEach((feed, id) => {
  // Both stereo views share one gateway stream and signaling connection.
  const feeds = id === 0 ? [feed, document.querySelector('.stereo-right')] : [feed];
  const videos = feeds.map(panel => panel.querySelector('video'));
  const setState = text => feeds.forEach(panel => panel.querySelector('.state').textContent = text);
  let current, retry;
  feeds.forEach(panel => panel.addEventListener('dblclick', () => panel.requestFullscreen?.().catch(() => {})));
  if (id === 0) videos.forEach(video => video.addEventListener('loadedmetadata', () => {
    feeds.forEach(panel => panel.style.setProperty('--stereo-ratio', video.videoWidth / video.videoHeight));
  }));
  function close() {
    if (!current) return;
    const old = current;
    current = null;
    clearTimeout(old.timeout);
    old.ws.onclose = old.ws.onerror = old.ws.onmessage = null;
    old.pc.onconnectionstatechange = old.pc.onicecandidate = old.pc.ontrack = null;
    old.ws.close(); old.pc.close();
    videos.forEach(video => {video.srcObject = null;});
  }
  function connect() {
    if (stopped) return;
    setState('Connecting…');
    const url = new URL(gateway);
    url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:';
    url.pathname = url.pathname.replace(/\/$/, '') + '/ws/' + id;
    url.search = ''; url.hash = '';
    const pc = new RTCPeerConnection({iceServers: []});
    const ws = new WebSocket(url);
    const connection = {pc, ws, pending: [], chain: Promise.resolve()};
    current = connection;
    const active = () => current === connection && !stopped;
    function fail() {
      if (!active()) return;
      close();
      setState('Reconnecting…');
      clearTimeout(retry);
      retry = setTimeout(connect, 2500);
    }
    connection.timeout = setTimeout(fail, 15000);
    videos.forEach(video => {
    video.onplaying = () => {
      if (active()) {clearTimeout(connection.timeout); setState('');}
    };
    video.onwaiting = () => {if (active()) setState('Connecting…');};
    video.onerror = fail;
    });
    pc.ontrack = ({streams, track, receiver}) => {
      if (!active()) return;
      try {
        if ('jitterBufferTarget' in receiver) receiver.jitterBufferTarget = 0;
        else if ('playoutDelayHint' in receiver) receiver.playoutDelayHint = 0;
      } catch (_) {}
      const stream = streams[0] || new MediaStream([track]);
      videos.forEach(video => {video.srcObject = stream; video.play().catch(fail);});
    };
    pc.onicecandidate = ({candidate}) => {
      if (active() && candidate && ws.readyState === WebSocket.OPEN)
        ws.send(JSON.stringify({type:'ice', ...candidate.toJSON()}));
    };
    pc.onconnectionstatechange = () => {
      if (['failed','closed','disconnected'].includes(pc.connectionState)) fail();
    };
    ws.onmessage = ({data}) => {
      connection.chain = connection.chain.then(async () => {
        if (!active()) return;
        const message = JSON.parse(data);
        if (message.type === 'offer') {
          await pc.setRemoteDescription({type:'offer', sdp:message.sdp});
          if (!active()) return;
          while (connection.pending.length) {
            await pc.addIceCandidate(connection.pending.shift());
            if (!active()) return;
          }
          const answer = await pc.createAnswer();
          if (!active()) return;
          await pc.setLocalDescription(answer);
          if (active() && ws.readyState === WebSocket.OPEN)
            ws.send(JSON.stringify({type:'answer', sdp:answer.sdp}));
        } else if (message.type === 'ice') {
          const candidate = {candidate:message.candidate, sdpMLineIndex:message.sdpMLineIndex};
          if (pc.remoteDescription) await pc.addIceCandidate(candidate);
          else connection.pending.push(candidate);
        } else if (message.type === 'error') fail();
      }).catch(fail);
    };
    ws.onerror = ws.onclose = fail;
  }
  cleanups.push(() => {clearTimeout(retry); close();});
  connect();
});
window.addEventListener('pagehide', () => {stopped = true; cleanups.forEach(close => close());});
window.addEventListener('pageshow', event => {if (event.persisted) location.reload();});
</script></body></html>"""


@app.route("/")
def index():
    if app.config["GATEWAY_URL"]:
        return Response(GATEWAY_PAGE.replace(
            "%%GATEWAY_JSON%%", json.dumps(app.config["GATEWAY_URL"]).replace("<", "\\u003c")
        ), mimetype="text/html")
    cams = [{"n": c.idx, "name": c.name, "topic": c.topic,
             "src": f"/stream/{c.idx}"} for c in CAMS]
    html = PAGE.replace("%%CAMS%%", json.dumps(cams)).replace("%%MODE%%", "live")
    return Response(html, mimetype="text/html")


@app.route("/stream/<int:cam>")
def stream(cam):
    def gen():
        boundary = b"--frame\r\nContent-Type: image/jpeg\r\n\r\n"
        while True:
            jpeg = CAMS[cam].jpeg() if 0 <= cam < len(CAMS) else None
            if jpeg is None:
                jpeg = NO_SIGNAL
            yield boundary + jpeg + b"\r\n"
            time.sleep(1 / 30)
    return Response(gen(),
                    mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/stats")
def stats():
    return Response(json.dumps({
        "cams": [{"n": c.idx, "fps": round(c.fps(), 1),
                  "res": (f"{c.w}x{c.h}" if c.w else "--"),
                  "frames": c.count, "online": c.online()} for c in CAMS],
    }), mimetype="application/json")


def lan_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


# ------------------------------------------------------------- page --------
PAGE = r"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>VIVEKA · Camera Array</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap');
:root{
  --bg:#eef1f7; --bg2:#fbfcff; --card:#ffffff; --ink:#0d1b33; --ink2:#3b4a63;
  --muted:#7c8aa3; --line:#e3e7ef; --accent:#2563eb; --accent2:#1e51d6;
  --ok:#16a34a; --shadow:0 14px 38px -18px rgba(16,32,64,.45);
}
*{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%}
body{
  font-family:'Sora','Segoe UI',system-ui,sans-serif;color:var(--ink);
  background:
    radial-gradient(circle at 1px 1px, rgba(37,99,235,.06) 1px, transparent 0) 0 0/24px 24px,
    linear-gradient(180deg,var(--bg2),var(--bg));
  background-attachment:fixed;min-height:100vh;
}
.mono{font-family:'IBM Plex Mono',ui-monospace,Menlo,monospace}

/* ---- top bar ---- */
.topbar{position:sticky;top:0;z-index:10;display:flex;align-items:center;
  justify-content:space-between;gap:18px;padding:14px 26px;
  background:rgba(255,255,255,.72);backdrop-filter:blur(12px) saturate(1.4);
  border-bottom:1px solid var(--line)}
.brand{display:flex;align-items:center;gap:13px}
.mark{width:30px;height:30px;border-radius:50%;background:
  radial-gradient(circle at 35% 30%,#5b8bff,var(--accent) 60%,#1740b8);
  position:relative;box-shadow:0 4px 14px -4px rgba(37,99,235,.7)}
.mark::after{content:"";position:absolute;inset:0;margin:auto;width:8px;height:8px;
  border-radius:50%;background:#fff}
.brand h1{font-size:20px;font-weight:700;letter-spacing:.06em}
.brand .sub{font-size:10.5px;letter-spacing:.34em;color:var(--muted);margin-top:2px}
.status{display:flex;align-items:center;gap:14px}
.chip{display:flex;align-items:center;gap:8px;padding:7px 13px;border-radius:999px;
  background:#fff;border:1px solid var(--line);box-shadow:var(--shadow);
  font-size:12px;font-weight:600;letter-spacing:.04em}
.chip .dot{width:8px;height:8px;border-radius:50%;background:var(--accent);
  box-shadow:0 0 0 4px rgba(37,99,235,.16);animation:pulse 2.4s ease-in-out infinite}
.sysrow{display:flex;gap:7px}
.sys{display:flex;align-items:center;gap:6px;padding:6px 10px;border-radius:8px;
  background:#fff;border:1px solid var(--line);font-size:11px;font-weight:600;color:var(--ink2)}
.sys i{width:6px;height:6px;border-radius:50%;background:var(--accent);display:inline-block;
  animation:pulse 2.4s ease-in-out infinite}
.sys:nth-child(2) i{animation-delay:.5s}
.sys:nth-child(3) i{animation-delay:1s}
.tele{display:flex;flex-direction:column;align-items:flex-end;line-height:1.25}
.tele .big{font-size:15px;font-weight:600}
.tele .lbl{font-size:10px;letter-spacing:.22em;color:var(--muted)}

/* ---- sub strip ---- */
.strip{display:flex;align-items:center;justify-content:space-between;
  padding:12px 28px 0;max-width:1500px;margin:0 auto}
.strip h2{font-size:12px;letter-spacing:.32em;color:var(--muted);font-weight:600}
.strip .feeds{font-size:12px;color:var(--ink2)}

/* ---- grid ---- */
.grid{display:grid;grid-template-columns:1fr 1fr;gap:20px;
  padding:18px 28px 34px;max-width:1500px;margin:0 auto}
@media(max-width:900px){.grid{grid-template-columns:1fr}}

.card{background:var(--card);border:1px solid var(--line);border-radius:16px;
  box-shadow:var(--shadow);overflow:hidden;opacity:0;transform:translateY(16px);
  animation:rise .75s cubic-bezier(.2,.8,.2,1) forwards}
.chead{display:flex;align-items:center;gap:11px;padding:12px 15px}
.idx{width:24px;height:24px;border-radius:7px;background:var(--accent);color:#fff;
  display:grid;place-items:center;font-size:12px;font-weight:700;flex:none}
.cmeta{min-width:0;flex:1}
.cmeta .nm{font-size:14px;font-weight:600;letter-spacing:.03em}
.cmeta .tp{font-size:11px;color:var(--muted);white-space:nowrap;overflow:hidden;
  text-overflow:ellipsis}
.cstat{display:flex;align-items:center;gap:7px;flex:none}
.cstat .lv{width:7px;height:7px;border-radius:50%;background:var(--ok);
  box-shadow:0 0 0 3px rgba(22,163,74,.16)}
.cstat .lv.off{background:#c2c8d2;box-shadow:0 0 0 3px rgba(0,0,0,.04)}
.cstat .fps{font-size:11.5px;color:var(--ink2);min-width:54px;text-align:right}

.media{position:relative;aspect-ratio:16/9;background:#0a0e16;overflow:hidden}
.media img{width:100%;height:100%;object-fit:cover;display:block}
.media::after{content:"";position:absolute;inset:0;pointer-events:none;
  box-shadow:inset 0 0 60px rgba(0,0,0,.35)}
.ovl{position:absolute;inset:0;width:100%;height:100%;pointer-events:none}
.ovl .ln{stroke:var(--accent);stroke-width:1;opacity:.42;
  transition:opacity .2s}
.ovl.lk .ln{opacity:.62}
.ovl .brk{stroke:var(--accent);stroke-width:1.4;fill:none;stroke-linecap:round}
.ovl.lk .brk{stroke-width:2.4}
.ovl .bore{stroke:#fff;opacity:.4;stroke-width:1}
.ovl .ring{stroke:var(--accent);fill:none;stroke-width:2;opacity:0}
/* static white corner frame */
.cnr{position:absolute;width:18px;height:18px;border:2px solid rgba(255,255,255,.85);
  pointer-events:none}
.cnr.tl{top:9px;left:9px;border-right:0;border-bottom:0}
.cnr.tr{top:9px;right:9px;border-left:0;border-bottom:0}
.cnr.bl{bottom:9px;left:9px;border-right:0;border-top:0}
.cnr.br{bottom:9px;right:9px;border-left:0;border-top:0}

@keyframes rise{to{opacity:1;transform:none}}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}
.foot{text-align:center;color:var(--muted);font-size:11px;letter-spacing:.18em;
  padding:0 0 24px}
</style></head>
<body>
  <div class="topbar">
    <div class="brand">
      <div class="mark"></div>
      <div><h1>VIVEKA</h1><div class="sub">3-SYSTEM VLA RUNTIME</div></div>
    </div>
    <div class="status">
      <div class="chip"><span class="dot"></span>POLICY LOADED</div>
      <div class="sysrow">
        <div class="sys"><i></i>S1</div>
        <div class="sys"><i></i>S2</div>
        <div class="sys"><i></i>S3</div>
      </div>
      <div class="tele">
        <div class="big mono" id="clock">--:--:--</div>
        <div class="lbl"><span id="agg">0.0</span> FPS · <span id="feeds">0/0</span> FEEDS</div>
      </div>
    </div>
  </div>

  <div class="strip">
    <h2>CAMERA ARRAY</h2>
    <div class="feeds mono" id="conn">ESTABLISHING LINK…</div>
  </div>
  <div class="grid" id="grid"></div>
  <div class="foot">VIVEKA PERCEPTION · LIVE CAMERA ARRAY</div>

<script>
const CAMS = %%CAMS%%;
const MODE = "%%MODE%%";

const grid = document.getElementById('grid');
const SVGNS = 'http://www.w3.org/2000/svg';
function el(tag, attrs){const e=document.createElementNS(SVGNS,tag);
  for(const k in attrs) e.setAttribute(k, attrs[k]); return e;}

class Tracker{
  constructor(svg, phase){
    this.svg=svg; this.phase=phase; this.w=0; this.h=0;
    this.vy=el('line',{class:'ln'}); this.hx=el('line',{class:'ln'});
    this.bx=el('path',{class:'brk'}); this.cr1=el('line',{class:'ln'});
    this.cr2=el('line',{class:'ln'}); this.ring=el('circle',{class:'ring'});
    this.bv=el('line',{class:'bore'}); this.bh=el('line',{class:'bore'});
    [this.vy,this.hx,this.ring,this.bx,this.cr1,this.cr2,this.bv,this.bh]
      .forEach(n=>svg.appendChild(n));
    new ResizeObserver(()=>this.measure()).observe(svg); this.measure();
  }
  measure(){const r=this.svg.getBoundingClientRect(); this.w=r.width; this.h=r.height;
    const cx=this.w/2, cy=this.h/2;
    this.bv.setAttribute('x1',cx); this.bv.setAttribute('x2',cx);
    this.bv.setAttribute('y1',cy-8); this.bv.setAttribute('y2',cy+8);
    this.bh.setAttribute('y1',cy); this.bh.setAttribute('y2',cy);
    this.bh.setAttribute('x1',cx-8); this.bh.setAttribute('x2',cx+8);}
  update(t){
    const W=this.w,H=this.h; if(!W) return;
    const cx=W/2, cy=H/2, CYCLE=4.0, SCAN=3.0, tt=t+this.phase;
    const cpos=tt%CYCLE, sc=Math.floor(tt/CYCLE)*SCAN+Math.min(cpos,SCAN);
    const tx=cx+0.30*W*Math.sin(2*Math.PI/5.0*sc);
    const ty=cy+0.20*H*Math.sin(2*Math.PI/3.1*sc+1.0);
    const locked=cpos>=SCAN, lp=locked?(cpos-SCAN)/(CYCLE-SCAN):0;
    this.svg.classList.toggle('lk',locked);
    this.vy.setAttribute('x1',tx);this.vy.setAttribute('x2',tx);
    this.vy.setAttribute('y1',6);this.vy.setAttribute('y2',H-6);
    this.hx.setAttribute('y1',ty);this.hx.setAttribute('y2',ty);
    this.hx.setAttribute('x1',6);this.hx.setAttribute('x2',W-6);
    let bw,bh,bl;
    if(locked){const e=Math.min(1,lp/0.25);bw=92-34*e;bh=70-26*e;bl=14;}
    else{bw=92;bh=70;bl=11;}
    const x1=tx-bw/2,y1=ty-bh/2,x2=tx+bw/2,y2=ty+bh/2;
    this.bx.setAttribute('d',
      `M ${x1} ${y1+bl} L ${x1} ${y1} L ${x1+bl} ${y1}
       M ${x2-bl} ${y1} L ${x2} ${y1} L ${x2} ${y1+bl}
       M ${x1} ${y2-bl} L ${x1} ${y2} L ${x1+bl} ${y2}
       M ${x2-bl} ${y2} L ${x2} ${y2} L ${x2} ${y2-bl}`);
    this.cr1.setAttribute('x1',tx-8);this.cr1.setAttribute('x2',tx+8);
    this.cr1.setAttribute('y1',ty);this.cr1.setAttribute('y2',ty);
    this.cr2.setAttribute('x1',tx);this.cr2.setAttribute('x2',tx);
    this.cr2.setAttribute('y1',ty-8);this.cr2.setAttribute('y2',ty+8);
    if(locked&&lp<0.4){this.ring.setAttribute('cx',tx);this.ring.setAttribute('cy',ty);
      this.ring.setAttribute('r',18+58*(lp/0.4));
      this.ring.style.opacity=(1-lp/0.4)*0.6;}
    else this.ring.style.opacity=0;
  }
}

const trackers=[];
CAMS.forEach((c,i)=>{
  const card=document.createElement('div'); card.className='card';
  card.style.animationDelay=(i*0.09)+'s';
  card.innerHTML=`
    <div class="chead">
      <div class="idx">${i+1}</div>
      <div class="cmeta"><div class="nm">${c.name}</div>
        <div class="tp mono">${c.topic}</div></div>
      <div class="cstat"><span class="lv off" id="lv${i}"></span>
        <span class="fps mono" id="fps${i}">— fps</span></div>
    </div>
    <div class="media">
      <img src="${c.src}" alt="${c.name}"
           onerror="this.style.opacity=.25">
      <svg class="ovl" id="ovl${i}" preserveAspectRatio="none"></svg>
      <span class="cnr tl"></span><span class="cnr tr"></span>
      <span class="cnr bl"></span><span class="cnr br"></span>
    </div>`;
  grid.appendChild(card);
  trackers.push(new Tracker(card.querySelector('#ovl'+i), i*0.9));
});

function loop(){const t=performance.now()/1000;
  trackers.forEach(tr=>tr.update(t)); requestAnimationFrame(loop);}
requestAnimationFrame(loop);

function clock(){const d=new Date();
  document.getElementById('clock').textContent=d.toTimeString().slice(0,8);}
setInterval(clock,1000); clock();

async function poll(){
  if(MODE!=='live') return;
  try{
    const r=await fetch('/stats'); const s=await r.json();
    let agg=0, on=0;
    s.cams.forEach(c=>{
      agg+=c.fps; if(c.online) on++;
      const f=document.getElementById('fps'+c.n);
      const lv=document.getElementById('lv'+c.n);
      if(f) f.textContent=c.fps.toFixed(0)+' fps';
      if(lv) lv.classList.toggle('off',!c.online);
    });
    document.getElementById('agg').textContent=agg.toFixed(1);
    document.getElementById('feeds').textContent=on+'/'+s.cams.length;
    document.getElementById('conn').textContent=
      on?('LINK ACTIVE · '+on+' STREAMS'):'WAITING FOR STREAMS…';
  }catch(e){
    document.getElementById('conn').textContent='SERVER OFFLINE';
  }
}
if(MODE==='live'){setInterval(poll,1000); poll();}
else{ // static preview
  document.getElementById('conn').textContent='PREVIEW MODE';
  CAMS.forEach((c,i)=>{const f=document.getElementById('fps'+i);
    const lv=document.getElementById('lv'+i);
    if(f)f.textContent='30 fps'; if(lv)lv.classList.remove('off');});
  document.getElementById('agg').textContent='120.0';
  document.getElementById('feeds').textContent=CAMS.length+'/'+CAMS.length;
}
</script>
</body></html>"""


# ------------------------------------------------------------- main --------
def gateway_running(url):
    try:
        opener = build_opener(ProxyHandler({}))
        with opener.open(url.rstrip("/") + "/api/status", timeout=2) as response:
            status = json.load(response)
        return isinstance(status.get("cameras"), list) and "gateway" in status
    except (OSError, ValueError):
        return False


def stop_gateway(process):
    if process is not None and process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=8)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


def ensure_gateway(url, binary):
    if gateway_running(url):
        print(f"Using running TriView gateway: {url}", flush=True)
        return None
    address = urlsplit(url)
    # Only start a process when the requested gateway belongs to this machine.
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.bind((socket.gethostbyname(address.hostname), 0))
    except OSError as error:
        raise RuntimeError(f"Gateway is unreachable: {url}. Start it on its host.") from error
    if address.scheme != "http" or address.path not in ("", "/"):
        raise RuntimeError("Automatic gateway startup requires a local http://host:port URL.")
    binary = Path(binary).expanduser().resolve()
    if not binary.is_file():
        raise RuntimeError(f"TriView executable not found: {binary}")
    env = dict(os.environ, STREAM_HOST="0.0.0.0", STREAM_PORT=str(address.port or 80))
    print(f"Starting TriView: {binary}", flush=True)
    process = subprocess.Popen([str(binary)], cwd=binary.parent.parent,
                               env=env, start_new_session=True)
    try:
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise RuntimeError(f"TriView exited with code {process.returncode}.")
            if gateway_running(url):
                return process
            time.sleep(0.25)
        raise RuntimeError(f"TriView did not become available at {url} within 30 seconds.")
    except BaseException:
        stop_gateway(process)
        raise


def main():
    ap = argparse.ArgumentParser(description="VIVEKA multi-camera web monitor")
    modes = ap.add_mutually_exclusive_group()
    modes.add_argument("--demo", action="store_true",
                    help="run without ROS using synthetic feeds")
    modes.add_argument("--ros", action="store_true",
                       help="subscribe to ROS camera topics instead of TriView")
    ap.add_argument("--gateway-url", default=app.config["GATEWAY_URL"],
                    help="TriView gateway URL (default: %(default)s)")
    # Default None, not PORT: in --ros mode the port comes from the parameter
    # file, and this has to be able to tell "user passed --port" apart from
    # "user said nothing" so an explicit flag still wins over the config.
    ap.add_argument("--port", type=int, default=None)
    ap.add_argument("--triview-bin", default="/home/s1/.ihub/camera/build/triview",
                    help="local TriView executable to start when the gateway is unavailable")
    # `ros2 launch`/`ros2 run` append --ros-args -r __node:=... etc. to argv;
    # strip those before argparse sees them, or it errors out on launch.
    try:
        from rclpy.utilities import remove_ros_args
        argv = remove_ros_args(sys.argv)[1:]
    except Exception:
        argv = sys.argv[1:]
    args = ap.parse_args(argv)
    if args.demo or args.ros:
        app.config["GATEWAY_URL"] = None
    else:
        gateway = urlsplit(args.gateway_url)
        if gateway.scheme not in ("http", "https") or not gateway.hostname:
            ap.error("--gateway-url must be an http:// or https:// URL")
        app.config["GATEWAY_URL"] = args.gateway_url

    serve_host = "0.0.0.0"

    if args.demo:
        start_demo()
        print("VIVEKA web monitor  [DEMO MODE]")
    elif args.ros:
        try:
            ros_cfg = start_ros()
            print("VIVEKA web monitor  [ROS 2]")
        except Exception as e:
            print("Could not start ROS 2 (", e, ")")
            print("Tip: source your ROS 2 setup, or run with --demo.")
            return
        # An explicit --port beats the parameter file; otherwise the config wins.
        serve_host = ros_cfg["host"]
        if args.port is None and ros_cfg["port"] is not None:
            args.port = int(ros_cfg["port"])
    else:
        print(f"VIVEKA web monitor  [TRIVIEW: {args.gateway_url}]")

    if args.port is None:
        args.port = PORT

    # Reserve the UI port before starting a gateway or opening camera devices.
    try:
        server = make_server(serve_host, args.port, app, threaded=True)
    except SystemExit:
        print(f"VIVEKA port {args.port} is already in use. If VIVEKA is already running, "
              f"open http://{lan_ip()}:{args.port} instead of starting another copy.")
        return 1
    process = None
    try:
        if not args.demo and not args.ros:
            process = ensure_gateway(args.gateway_url, args.triview_bin)
        ip = lan_ip()
        print(f"  open: http://{ip}:{args.port} (or http://localhost:{args.port})", flush=True)
        if not args.demo and not args.ros:
            print(f"  camera LAN: http://{urlsplit(args.gateway_url).hostname}:{args.port}", flush=True)
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    except (OSError, RuntimeError, ValueError) as error:
        print(f"Could not start VIVEKA: {error}", file=sys.stderr)
        return 1
    finally:
        server.server_close()
        stop_gateway(process)
    return 0


if __name__ == "__main__":
    sys.exit(main())
