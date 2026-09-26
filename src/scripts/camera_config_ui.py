#!/usr/bin/env python3
"""
camera_config_ui.py
--------------------
Small standalone web UI for finding which USB port/serial each connected
Intel RealSense camera is actually on, and assigning those serials to the
world/left/right roles in camera_launch's config/cameras.yaml -- the file
start_all_cameras.launch.py reads at launch time.

This exists because serial numbers alone (the only thing rs-enumerate-devices
normally prints in its short form) don't tell you which physical camera you're
holding; matching by USB port position, model and firmware while looking at
the device list is much easier than typing serials into a text editor by hand.

Doesn't touch any ROS process itself -- it only reads/writes cameras.yaml (via
a targeted text edit that leaves every comment in that file untouched, since
those comments carry real operational context) and shells out to
rs-enumerate-devices for detection. Run camera_launch's start_all_cameras
launch again (or restart bringup) to pick up a saved change.

Run (no ROS sourcing required, just Flask + PyYAML, both already used by the
automation package):
    python3 camera_config_ui.py            # open http://<hostname>:8150
    python3 camera_config_ui.py --config /path/to/cameras.yaml --port 8150
"""

import argparse
import os
import re
import socket
import subprocess

import yaml
from flask import Flask, jsonify, request

APP_DIR = os.path.dirname(os.path.realpath(__file__))
# .../src/scripts/../camera/camera_launch/config/cameras.yaml
DEFAULT_CONFIG_PATH = os.path.normpath(
    os.path.join(APP_DIR, "..", "camera", "camera_launch", "config", "cameras.yaml")
)

app = Flask(__name__)
CONFIG_PATH = DEFAULT_CONFIG_PATH  # overridden by --config in main()

# realsense2_camera's serial_no parameter strips a single leading "_" before
# use (see realsense_node_factory.cpp) -- it's there only so a purely numeric
# serial survives YAML/ROS param parsing as a string instead of being read as
# an integer. cameras.yaml stores it that way, so every value written back
# here must carry the same prefix.
SERIAL_PREFIX = "_"


# ── Detection ────────────────────────────────────────────────────────────

def detect_cameras(timeout_s=8.0):
    """[{serial, name, firmware, usb_port, usb_speed, video_device}, ...]
    parsed from `rs-enumerate-devices`'s full (non -s) output, which is the
    only form that includes the physical USB port and video4linux device --
    or (None, error_message) if the tool isn't available or fails."""
    try:
        result = subprocess.run(
            ["rs-enumerate-devices"], capture_output=True, text=True, timeout=timeout_s,
        )
    except FileNotFoundError:
        return None, "rs-enumerate-devices not found -- is librealsense installed and on PATH?"
    except Exception as e:
        return None, f"rs-enumerate-devices failed: {e}"

    devices = []
    current = None
    for line in result.stdout.splitlines():
        if line.strip() == "Device info:":
            if current:
                devices.append(current)
            current = {}
            continue
        if current is None:
            continue
        stripped = line.strip()
        if stripped == "" or stripped.startswith("Stream Profiles"):
            devices.append(current)
            current = None
            continue
        m = re.match(r"\s*([^:]+?)\s*:\s*\t?(.*)", line)
        if m:
            current[m.group(1).strip()] = m.group(2).strip()
    if current:
        devices.append(current)

    out = []
    for d in devices:
        serial = d.get("Serial Number", "")
        if not serial:
            continue
        physical_port = d.get("Physical Port", "")
        # ".../usb1/1-4/1-4.1/1-4.1:1.0/video4linux/video0" -> "1-4.1"
        port_match = re.search(r"/(\d+-[\d.]+):\d+\.\d+/", physical_port)
        video_match = re.search(r"(video\d+)$", physical_port)
        out.append({
            "serial": serial,
            "name": d.get("Name", "?"),
            "firmware": d.get("Firmware Version", "?"),
            "usb_port": port_match.group(1) if port_match else None,
            "usb_speed": d.get("Usb Type Descriptor", "?"),
            "video_device": f"/dev/{video_match.group(1)}" if video_match else None,
        })
    return out, None


# ── cameras.yaml: read (parsed) + write (surgical, comment-preserving) ────

# Matches a top-level role block header, e.g. "  right:" -- two-space indent,
# matching cameras.yaml's actual layout (see that file's `cameras:` map).
ROLE_HEADER_RE = re.compile(r"^  (\w+):\s*$")


def load_config():
    with open(CONFIG_PATH) as f:
        text = f.read()
    doc = yaml.safe_load(text) or {}
    roles = {}
    for role, cam in (doc.get("cameras") or {}).items():
        serial = str(cam.get("serial_no", ""))
        if serial.startswith(SERIAL_PREFIX):
            serial = serial[len(SERIAL_PREFIX):]
        roles[role] = {
            "enabled": bool(cam.get("enabled", True)),
            "serial_no": serial,
            "namespace": cam.get("namespace", role),
            "name": cam.get("name", "camera"),
            "color_resolution": cam.get("color_resolution", "640x480"),
            "color_fps": cam.get("color_fps", 30),
        }
    return roles


def _role_block_ranges(lines):
    """{role_name: (start_line, end_line)} -- end_line exclusive."""
    ranges = {}
    current, start = None, None
    for i, line in enumerate(lines):
        m = ROLE_HEADER_RE.match(line)
        if m:
            if current is not None:
                ranges[current] = (start, i)
            current, start = m.group(1), i
    if current is not None:
        ranges[current] = (start, len(lines))
    return ranges


def save_config(updates):
    """updates: {role: {"serial_no": "<digits, no prefix>", "enabled": bool}}.

    Rewrites only the serial_no/enabled *values* inside each named role's
    block, in place, via plain text substitution -- every comment and every
    other field in cameras.yaml is left byte-for-byte untouched. A full
    yaml.safe_load()+dump() round-trip would silently drop all of that
    file's documentation, which is most of its value.
    """
    with open(CONFIG_PATH) as f:
        text = f.read()
    lines = text.splitlines(keepends=True)
    ranges = _role_block_ranges(lines)

    for role, fields in updates.items():
        if role not in ranges:
            raise ValueError(f"no '{role}:' block found in {CONFIG_PATH}")
        start, end = ranges[role]
        for field, value in fields.items():
            if field == "serial_no":
                value_str = f'"{SERIAL_PREFIX}{value}"'
            elif isinstance(value, bool):
                value_str = "true" if value else "false"
            else:
                value_str = str(value)
            pattern = re.compile(r"^(\s*" + re.escape(field) + r"\s*:\s*).*$")
            for i in range(start, end):
                m = pattern.match(lines[i])
                if m:
                    lines[i] = f"{m.group(1)}{value_str}\n"
                    break
            else:
                raise ValueError(f"field '{field}' not found in '{role}:' block")

    tmp_path = CONFIG_PATH + ".tmp"
    with open(tmp_path, "w") as f:
        f.write("".join(lines))
    os.replace(tmp_path, CONFIG_PATH)


# ── Routes ─────────────────────────────────────────────────────────────

@app.route("/")
def home():
    return PAGE


@app.route("/api/detect")
def api_detect():
    devices, error = detect_cameras()
    return jsonify({"devices": devices or [], "error": error})


@app.route("/api/config")
def api_config():
    try:
        return jsonify({"ok": True, "roles": load_config(), "path": CONFIG_PATH})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/save", methods=["POST"])
def api_save():
    data = request.get_json(silent=True) or {}
    roles = data.get("roles")
    if not isinstance(roles, dict) or not roles:
        return jsonify({"ok": False, "error": "no roles given"}), 400

    updates = {}
    for role, fields in roles.items():
        if not isinstance(fields, dict):
            return jsonify({"ok": False, "error": f"bad payload for role '{role}'"}), 400
        entry = {}
        if "serial_no" in fields:
            serial = re.sub(r"\D", "", str(fields["serial_no"]))
            if not serial:
                return jsonify({"ok": False, "error": f"'{role}': serial_no must be numeric"}), 400
            entry["serial_no"] = serial
        if "enabled" in fields:
            entry["enabled"] = bool(fields["enabled"])
        if entry:
            updates[role] = entry

    try:
        save_config(updates)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
    return jsonify({"ok": True, "roles": load_config()})


PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Camera Config</title>
<style>
  :root { color-scheme: light dark; }
  body { font-family: -apple-system, Segoe UI, Roboto, sans-serif; margin: 0;
         background: #0f1420; color: #e6e9ef; }
  header { padding: 20px 24px 8px; }
  h1 { font-size: 20px; margin: 0 0 4px; }
  .sub { color: #8b93a7; font-size: 13px; }
  main { padding: 8px 24px 40px; max-width: 980px; }
  .card { background: #161c2c; border: 1px solid #262e44; border-radius: 10px;
          padding: 16px 18px; margin-top: 18px; }
  .card h2 { font-size: 15px; margin: 0 0 12px; display: flex; align-items: center;
             justify-content: space-between; }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th, td { text-align: left; padding: 7px 8px; border-bottom: 1px solid #22293c; }
  th { color: #8b93a7; font-weight: 600; font-size: 11px; text-transform: uppercase;
       letter-spacing: .04em; }
  .mono { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
  select, input[type=text] { background: #0f1420; color: #e6e9ef; border: 1px solid #2e3652;
         border-radius: 6px; padding: 5px 8px; font-size: 13px; }
  button { background: #3461ff; color: #fff; border: none; border-radius: 6px;
           padding: 6px 14px; font-size: 13px; cursor: pointer; }
  button.ghost { background: transparent; border: 1px solid #2e3652; color: #cdd3e0; }
  button:disabled { opacity: .5; cursor: default; }
  .role-row td { vertical-align: middle; }
  .pill { display: inline-block; padding: 2px 8px; border-radius: 999px; font-size: 11px; }
  .pill.on { background: rgba(52,209,122,.15); color: #34d17a; }
  .pill.off { background: rgba(255,255,255,.08); color: #8b93a7; }
  .empty { color: #8b93a7; font-size: 13px; padding: 6px 0; }
  .err { color: #ff6b6b; font-size: 13px; }
  #toast { position: fixed; bottom: 20px; right: 20px; background: #1c2338; border: 1px solid #2e3652;
           padding: 10px 16px; border-radius: 8px; font-size: 13px; opacity: 0; transition: opacity .2s; }
  #toast.show { opacity: 1; }
  #toast.err { border-color: #6e2a2a; color: #ff9b9b; }
</style>
</head>
<body>
<header>
  <h1>Intel RealSense Camera Config</h1>
  <div class="sub" id="configPath">cameras.yaml</div>
</header>
<main>
  <div class="card">
    <h2>Detected Cameras <button class="ghost" onclick="loadDetected()">Refresh</button></h2>
    <table id="detectedTable"><thead>
      <tr><th>Model</th><th>Serial</th><th>USB Port</th><th>Speed</th><th>Video Device</th></tr>
    </thead><tbody><tr><td colspan="5" class="empty">Loading…</td></tr></tbody></table>
  </div>

  <div class="card">
    <h2>Camera Roles</h2>
    <table id="rolesTable"><thead>
      <tr><th>Role</th><th>Enabled</th><th>Assigned Camera</th><th>Namespace / Topic</th></tr>
    </thead><tbody><tr><td colspan="4" class="empty">Loading…</td></tr></tbody></table>
    <div style="margin-top:14px; display:flex; gap:10px; align-items:center;">
      <button onclick="save()">Save to cameras.yaml</button>
      <span id="saveNote" class="sub"></span>
    </div>
  </div>
</main>
<div id="toast"></div>
<script>
let detected = [];
let roles = {};

function toast(msg, err){
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.className = 'show' + (err ? ' err' : '');
  clearTimeout(t._t);
  t._t = setTimeout(() => t.className = '', 3000);
}

async function loadDetected(){
  const tbody = document.querySelector('#detectedTable tbody');
  tbody.innerHTML = '<tr><td colspan="5" class="empty">Scanning USB…</td></tr>';
  try{
    const r = await fetch('/api/detect');
    const d = await r.json();
    if(d.error){
      tbody.innerHTML = `<tr><td colspan="5" class="err">${d.error}</td></tr>`;
      return;
    }
    detected = d.devices;
    if(!detected.length){
      tbody.innerHTML = '<tr><td colspan="5" class="empty">No RealSense cameras detected on USB right now.</td></tr>';
    } else {
      tbody.innerHTML = detected.map(c => `<tr>
        <td>${c.name}</td>
        <td class="mono">${c.serial}</td>
        <td class="mono">${c.usb_port || '—'}</td>
        <td>${c.usb_speed || '—'}</td>
        <td class="mono">${c.video_device || '—'}</td>
      </tr>`).join('');
    }
  }catch(e){
    tbody.innerHTML = `<tr><td colspan="5" class="err">${e}</td></tr>`;
  }
  renderRoles(); // dropdown options depend on the detected list too
}

function serialOptionsHtml(currentSerial){
  const known = new Set(detected.map(c => c.serial));
  let opts = detected.map(c =>
    `<option value="${c.serial}" ${c.serial === currentSerial ? 'selected' : ''}>${c.serial} (${c.name}${c.usb_port ? ', port ' + c.usb_port : ''})</option>`
  ).join('');
  if(currentSerial && !known.has(currentSerial)){
    opts += `<option value="${currentSerial}" selected>${currentSerial} (not currently detected)</option>`;
  }
  if(!currentSerial){
    opts = '<option value="">— none —</option>' + opts;
  }
  return opts;
}

async function loadRoles(){
  const r = await fetch('/api/config');
  const d = await r.json();
  if(!d.ok){ toast(d.error, true); return; }
  roles = d.roles;
  document.getElementById('configPath').textContent = d.path;
  renderRoles();
}

function renderRoles(){
  const tbody = document.querySelector('#rolesTable tbody');
  const names = Object.keys(roles);
  if(!names.length){
    tbody.innerHTML = '<tr><td colspan="4" class="empty">No camera roles found.</td></tr>';
    return;
  }
  tbody.innerHTML = names.map(role => {
    const c = roles[role];
    return `<tr class="role-row" data-role="${role}">
      <td><b>${role}</b></td>
      <td><input type="checkbox" ${c.enabled ? 'checked' : ''} onchange="roles['${role}'].enabled = this.checked; renderPill('${role}')">
          <span class="pill ${c.enabled ? 'on' : 'off'}" id="pill-${role}">${c.enabled ? 'ENABLED' : 'DISABLED'}</span></td>
      <td><select onchange="roles['${role}'].serial_no = this.value">
            ${serialOptionsHtml(c.serial_no)}
          </select></td>
      <td class="mono sub">/${c.namespace}/${c.name}</td>
    </tr>`;
  }).join('');
}

function renderPill(role){
  const pill = document.getElementById('pill-' + role);
  const on = roles[role].enabled;
  pill.className = 'pill ' + (on ? 'on' : 'off');
  pill.textContent = on ? 'ENABLED' : 'DISABLED';
}

async function save(){
  const payload = {roles: {}};
  for(const role in roles){
    payload.roles[role] = {serial_no: roles[role].serial_no, enabled: roles[role].enabled};
  }
  document.getElementById('saveNote').textContent = 'Saving…';
  try{
    const r = await fetch('/api/save', {
      method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload),
    });
    const d = await r.json();
    if(!d.ok){ toast(d.error, true); document.getElementById('saveNote').textContent = ''; return; }
    roles = d.roles;
    renderRoles();
    toast('Saved. Re-launch camera_launch (or bringup) to pick it up.');
    document.getElementById('saveNote').textContent = '';
  }catch(e){
    toast(String(e), true);
    document.getElementById('saveNote').textContent = '';
  }
}

loadRoles().then(loadDetected);
</script>
</body>
</html>"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=DEFAULT_CONFIG_PATH,
                         help="Path to cameras.yaml (default: %(default)s)")
    parser.add_argument("--port", type=int, default=8150)
    args = parser.parse_args()

    global CONFIG_PATH
    CONFIG_PATH = os.path.normpath(args.config)
    if not os.path.isfile(CONFIG_PATH):
        raise SystemExit(f"cameras.yaml not found: {CONFIG_PATH}")

    print(f"Camera Config UI on http://{socket.gethostname().lower()}.local:{args.port} "
          f"(editing {CONFIG_PATH})")
    app.run(host="0.0.0.0", port=args.port, threaded=True)


if __name__ == "__main__":
    main()
