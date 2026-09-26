const $ = id => document.getElementById(id);

function toast(msg, err=false){
  const t = $("toast"); t.textContent = msg;
  t.className = "toast show" + (err ? " err" : "");
  clearTimeout(t._t); t._t = setTimeout(()=> t.className = "toast", 3600);
}

async function post(url){
  const r = await fetch(url, {method:"POST"});
  return {ok:r.ok, data: await r.json()};
}

let launching = false;
let killing = false;
let bringupRunning = false;

// Camera-grid state -- declared here (not down by the camera code itself)
// because showView() calls stopCameraStreaming() on the very first paint
// (see the initial showView(...) call below), which reads camPollInterval.
// A `let` further down the file would still be in its temporal dead zone
// at that point and throw "Cannot access before initialization", which
// aborts all remaining top-level script execution -- including every
// poll()/pollApps()/pollLogs()/... call -- leaving the whole dashboard
// stuck on its static placeholder text forever.
let camPollInterval = null;
let camLastFrameAt = {};
let cameraRegistry = [];    // [{id, display_name, topic}, ...] -- every known camera
let selectedCameraIds = []; // ordered ids currently displayed in the grid
let camDragId = null;

async function doLaunch(){
  launching = true;
  $("btnLaunch").disabled = true;
  const {data} = await post("/api/launch");
  toast(data.message, !data.success);
  launching = false;
  poll();
}

async function doKill(){
  killing = true;
  $("btnKill").disabled = true;
  const {data} = await post("/api/kill");
  toast(data.message, !data.success);
  killing = false;
  poll();
}

async function poll(){
  try{
    const r = await fetch("/api/status");
    const s = await r.json();

    $("pid").textContent = s.pid ?? "—";
    $("sidePid").textContent = s.pid ?? "—";
    const up = (s.uptime_s || 0).toFixed(1) + "s";
    $("uptime").textContent = up;
    $("sideUptime").textContent = up;

    $("btnLaunch").disabled = launching || s.running;
    $("btnKill").disabled = killing || !s.running;

    $("statePill").className = "state-pill" + (s.running ? "" : " stopped");
    $("stateText").textContent = s.running ? "RUNNING" : "STOPPED";
    $("sysDot").className = "dot-live" + (s.running ? "" : " off");
    $("sysState").textContent = s.running ? "System Online" : "System Offline";
    $("sysState").style.color = s.running ? "" : "var(--dim)";
    $("motorNote").textContent = s.running ? "" : "Waiting for bringup…";

    bringupRunning = s.running;
  }catch(e){}
}

/* ------------------------------------------------------------- clock */
function tickClock(){
  const d = new Date();
  const date = d.toLocaleDateString("en-US", {month:"short", day:"numeric", year:"numeric"});
  const time = d.toLocaleTimeString("en-GB", {hour12:false});
  $("clock").textContent = `${date}  ${time}`;
}

/* ------------------------------------------------------- applications */
let appFilter = "";

const ICON = {
  open:    `<svg viewBox="0 0 24 24"><path d="M14 4h6v6M20 4l-8.5 8.5"/><path d="M18 14v5a1 1 0 01-1 1H5a1 1 0 01-1-1V7a1 1 0 011-1h5"/></svg>`,
  restart: `<svg viewBox="0 0 24 24"><path d="M3 12a9 9 0 1015-6.7M3 4v5h5"/></svg>`,
  stop:    `<svg viewBox="0 0 24 24"><rect x="7" y="7" width="10" height="10" rx="1.5" fill="currentColor" stroke="none"/></svg>`,
  start:   `<svg viewBox="0 0 24 24"><path d="M8 5l11 7-11 7z" fill="currentColor" stroke="none"/></svg>`,
};

function appRowHtml(a){
  const url = `${location.protocol}//${location.hostname}:${a.port}/`;

  let open;
  if(a.kind === "http"){
    open = `<a class="act open" href="${url}">Open ${ICON.open}</a>`;
  } else {
    open = `<span class="act-badge">${a.kind.toUpperCase()}</span>`;
  }

  // Restart needs a configured start command; Stop only needs the PID that
  // holds the port, so it works for anything already running.
  const restartTitle = a.is_self ? "This is the panel itself"
    : a.startable ? "Restart" : `No start command configured for port ${a.port}`;
  const restart = `<button class="act icon" title="${restartTitle}"
      ${(a.startable && !a.is_self) ? "" : "disabled"}
      onclick="appAction(${a.port},'restart')">${ICON.restart}</button>`;

  let toggle;
  if(a.is_self){
    toggle = `<button class="act icon" disabled title="Refusing to stop this panel">${ICON.stop}</button>`;
  } else if(a.running){
    toggle = `<button class="act stop" title="Stop (pid ${a.pid ?? "?"})"
        onclick="appAction(${a.port},'stop')">${ICON.stop}</button>`;
  } else {
    toggle = `<button class="act start" ${a.startable ? "" : "disabled"}
        title="${a.startable ? "Start" : `No start command configured for port ${a.port}`}"
        onclick="appAction(${a.port},'start')">${ICON.start}</button>`;
  }

  const status = a.running
    ? `<span class="status up"><span class="bulb"></span>Running</span>`
    : `<span class="status down"><span class="bulb"></span>Not Running</span>`;

  return `<tr>
    <td class="c-idx">${a.index}</td>
    <td class="c-port"><span class="port-pill">${a.port}</span></td>
    <td>${a.service}</td>
    <td class="c-status">${status}</td>
    <td class="c-act"><div class="acts">${open}${restart}${toggle}</div></td>
  </tr>`;
}

function renderApps(apps){
  const q = appFilter.trim().toLowerCase();
  const shown = q
    ? apps.filter(a => `${a.port} ${a.service} ${a.file}`.toLowerCase().includes(q))
    : apps;

  $("appRows").innerHTML = shown.length
    ? shown.map(appRowHtml).join("")
    : `<tr><td colspan="5" class="empty">No application matches “${appFilter}”.</td></tr>`;

  const up = apps.filter(a => a.running).length;
  const unmanaged = apps.filter(a => !a.startable && !a.is_self).length;
  $("setStartable").textContent = `${apps.filter(a => a.startable).length} of ${apps.length}`;
  $("appsFoot").textContent =
    `${up} of ${apps.length} running` +
    (q ? ` · showing ${shown.length}` : "") +
    (unmanaged ? ` · ${unmanaged} without a start command (see APP_COMMANDS in launch_control_app.py)` : "");
}

async function pollApps(){
  try{
    const r = await fetch("/api/apps");
    const d = await r.json();
    renderApps(d.apps || []);
  }catch(e){}
}

async function appAction(port, action){
  const {data} = await post(`/api/app/${port}/${action}`);
  toast(data.message, !data.success);
  setTimeout(pollApps, 600);
}

/* --------------------------------------------------------------- logs */
let lastLogId = 0;
async function pollLogs(){
  try{
    const r = await fetch(`/api/logs?since=${lastLogId}`);
    const d = await r.json();
    // The panel's log ids reset to 0 whenever its process restarts. If the
    // server's latest id is behind what this tab last saw, `since` is stale
    // from a previous process and would filter out every entry the new one
    // has logged -- resync to the start instead of going silent forever.
    if(typeof d.latest === "number" && d.latest < lastLogId){
      lastLogId = 0;
      return pollLogs();
    }
    if(!d.logs.length) return;
    const box = $("logBody");
    const atBottom = box.scrollTop + box.clientHeight >= box.scrollHeight - 4;
    for(const e of d.logs){
      lastLogId = Math.max(lastLogId, e.id);
      const line = document.createElement("div");
      line.className = "logline " + (e.level || "info");
      const t = document.createElement("span");
      t.className = "t";
      t.textContent = e.ts;
      line.appendChild(t);
      line.appendChild(document.createTextNode(e.message));
      box.appendChild(line);
    }
    while(box.children.length > 800) box.removeChild(box.firstChild);
    if(atBottom && $("autoScroll").checked) box.scrollTop = box.scrollHeight;
  }catch(e){}
}

function clearLog(){
  $("logBody").innerHTML = "";
}

/* -------------------------------------------------------- motor status */
// error codes per hw_interface's decode_error(): 0=Disabled, 1=Enabled,
// 8-14=real fault conditions (Overvoltage, Overtemp, Comm Lost, etc).
function isFault(m){ return !(m.error === 0 || m.error === 1); }

function renderMotorSide(side, motors, available, recoveryCounts){
  const body = $("motorBody_" + side);
  if(!body) return;
  if(!available){
    body.innerHTML = `<div class="empty">Motor status not available.</div>`;
    return;
  }
  if(!motors || !motors.length){
    body.innerHTML = `<div class="empty">Waiting for data…</div>`;
    return;
  }
  const rows = motors.map(m => {
    const recoveries = (recoveryCounts || {})[`${m.arm_name}_motor_${m.id}`] || 0;
    return `<tr class="${isFault(m) ? 'motor-row-fault' : ''}">
      <td class="num"><b>${m.id}</b></td>
      <td>${m.error_name}</td>
      <td class="num">${m.mos_temp}°C</td>
      <td class="num">${m.rotor_temp}°C</td>
      <td class="num">${recoveries}</td>
    </tr>`;
  }).join("");
  body.innerHTML = `<table class="motor-table">
    <thead><tr><th>ID</th><th>Status</th><th>MOS</th><th>Rotor</th><th>Rec</th></tr></thead>
    <tbody>${rows}</tbody>
  </table>`;
}

function renderSummary(left, right, recoveryCounts){
  const all = [...(left||[]), ...(right||[])];
  if(!all.length){
    for(const id of ["sumTotal","sumEnabled","sumDisabled","sumFaults","sumMaxTemp","sumRecoveries"]) $(id).textContent = "—";
    return;
  }
  const enabled = all.filter(m => m.error === 1).length;
  const disabled = all.filter(m => m.error === 0).length;
  const faults = all.filter(isFault).length;
  const maxTemp = Math.max(...all.map(m => Math.max(m.mos_temp, m.rotor_temp)));
  const totalRecoveries = Object.values(recoveryCounts || {}).reduce((a, b) => a + b, 0);
  $("sumTotal").textContent = all.length;
  $("sumEnabled").textContent = enabled;
  $("sumDisabled").textContent = disabled;
  $("sumFaults").textContent = faults;
  $("sumMaxTemp").textContent = maxTemp.toFixed(1) + "°C";
  $("sumRecoveries").textContent = totalRecoveries;
}

async function pollMotorStatus(){
  if(!bringupRunning) return;
  try{
    const [statusRes, recoveryRes] = await Promise.all([
      fetch("/api/motor_status"),
      fetch("/api/recovery_counts"),
    ]);
    const d = await statusRes.json();
    const recovery = await recoveryRes.json();
    const left = d.status.left, right = d.status.right;
    const counts = recovery.counts || {};
    renderMotorSide("left", left, d.available, counts);
    renderMotorSide("right", right, d.available, counts);
    renderSummary(left, right, counts);
  }catch(e){}
}

/* --------------------------------------------------- stiffness/damping */
// Shared by both arms (one Kp/Kd per motor id, not per arm -- see
// teach_mode_node.py's send_gains()). A field the operator is mid-editing
// is marked "dirty" and pollGains() leaves it alone until Apply (or a page
// reload) clears that, so a 1s poll can't wipe out a half-typed value.
const GAIN_MOTORS = [1, 2, 3, 4, 5, 6, 7, 8];
const gainsDirty = new Set();

function gainInputId(motor, kind){ return `gain_${kind}_${motor}`; }

function markGainDirty(motor, kind){
  gainsDirty.add(gainInputId(motor, kind));
  $(gainInputId(motor, kind)).classList.add("dirty");
}

function gainsRowHtml(motor){
  const kp = gainInputId(motor, "kp"), kd = gainInputId(motor, "kd");
  return `<tr>
    <td class="num"><b>${motor}</b></td>
    <td><input type="number" step="0.1" min="0" class="gain-input" id="${kp}"
        oninput="markGainDirty(${motor},'kp')"></td>
    <td><input type="number" step="0.1" min="0" class="gain-input" id="${kd}"
        oninput="markGainDirty(${motor},'kd')"></td>
    <td><button class="gain-apply" title="Apply to motor ${motor}" onclick="applyGain(${motor})">${ICON.restart}</button></td>
  </tr>`;
}

function initGainsTable(){
  const body = $("gainsRows");
  if(!body) return;
  body.innerHTML = GAIN_MOTORS.map(gainsRowHtml).join("");
}

async function pollGains(){
  if(!bringupRunning) return;
  try{
    const r = await fetch("/api/gains");
    const d = await r.json();
    $("gainsNote").textContent = d.available ? "" : "teach_mode_node not running";
    for(const motor of GAIN_MOTORS){
      for(const kind of ["kp", "kd"]){
        const id = gainInputId(motor, kind);
        if(gainsDirty.has(id)) continue;
        const value = d[kind][motor];
        $(id).value = (value === null || value === undefined) ? "" : value;
      }
    }
  }catch(e){}
}

async function applyGain(motor){
  const kpEl = $(gainInputId(motor, "kp")), kdEl = $(gainInputId(motor, "kd"));
  const body = {motor};
  const kp = parseFloat(kpEl.value), kd = parseFloat(kdEl.value);
  if(Number.isFinite(kp)) body.kp = kp;
  if(Number.isFinite(kd)) body.kd = kd;
  if(!("kp" in body) && !("kd" in body)){
    toast("Enter a Kp or Kd value first", true);
    return;
  }
  try{
    const r = await fetch("/api/gains", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(body),
    });
    const d = await r.json();
    const msgs = Object.values(d.results || {}).map(x => x.message);
    toast(msgs.join(" · ") || d.message || `Motor ${motor} gains updated`, !d.ok);
    if(d.ok){
      gainsDirty.delete(gainInputId(motor, "kp"));
      gainsDirty.delete(gainInputId(motor, "kd"));
      kpEl.classList.remove("dirty");
      kdEl.classList.remove("dirty");
    }
  }catch(e){
    toast("Could not set gains: " + e.message, true);
  }
}

/* ---------------------------------------------------------- soc stats */
// One rolling history per tile, drawn as the sparkline behind the value.
const HISTORY = 40;
const history = {cpu:[], gpu:[], ram:[], cputemp:[], soctemp:[], power:[]};

function drawSpark(id, values){
  const el = $(id);
  if(!el) return;
  if(values.length < 2){ el.innerHTML = ""; return; }

  const max = Math.max(...values, 1);
  const min = Math.min(...values, 0);
  const span = (max - min) || 1;
  const step = 100 / (values.length - 1);
  const pts = values.map((v, i) => [i * step, 32 - ((v - min) / span) * 28]);

  const line = pts.map(([x, y], i) => `${i ? "L" : "M"}${x.toFixed(1)} ${y.toFixed(1)}`).join(" ");
  const area = `${line} L100 34 L0 34 Z`;
  el.innerHTML = `<path class="area" d="${area}"/><path class="line" d="${line}"/>`;
}

function renderSocStats(stats, available){
  if(!available){
    for(const id of ["socCpu","socGpu","socRam","socCpuTemp","socSocTemp","socPower"]) $(id).textContent = "n/a";
    $("socCores").innerHTML = "";
    return;
  }
  const cores = stats.cpu || [];
  const active = cores.filter(c => !c.off);
  const cpuAvg = active.length ? Math.round(active.reduce((a,c)=>a+c.usage,0)/active.length) : 0;
  const ramPct = stats.ram_total ? (stats.ram_used / stats.ram_total) * 100 : 0;
  const watts = (stats.power_system || 0) / 1000;

  $("socCpu").textContent = cpuAvg + "%";
  $("socGpu").textContent = (stats.gpu || 0) + "%";
  $("socRam").textContent = `${stats.ram_used}/${stats.ram_total}MB`;
  $("socCpuTemp").textContent = (stats.cpu_temp || 0).toFixed(1) + "°C";
  $("socSocTemp").textContent = (stats.soc_temp || 0).toFixed(1) + "°C";
  $("socPower").textContent = watts.toFixed(2) + "W";

  const sample = {
    cpu: cpuAvg, gpu: stats.gpu || 0, ram: ramPct,
    cputemp: stats.cpu_temp || 0, soctemp: stats.soc_temp || 0, power: watts,
  };
  for(const key of Object.keys(history)){
    history[key].push(sample[key]);
    if(history[key].length > HISTORY) history[key].shift();
  }
  drawSpark("sparkCpu", history.cpu);
  drawSpark("sparkGpu", history.gpu);
  drawSpark("sparkRam", history.ram);
  drawSpark("sparkCpuTemp", history.cputemp);
  drawSpark("sparkSocTemp", history.soctemp);
  drawSpark("sparkPower", history.power);

  $("socCores").innerHTML = cores.map((c, i) =>
    c.off
      ? `<span class="core-chip off">C${i} off</span>`
      : `<span class="core-chip">C${i} ${c.usage}%</span>`
  ).join("");
}

async function pollSocStats(){
  try{
    const r = await fetch("/api/soc_stats");
    const d = await r.json();
    renderSocStats(d.stats, d.available);
  }catch(e){}
}

/* --------------------------------------------------------------- battery */
// Stale after this long with no new /battery_info message -- battery_info.py
// isn't started by bringup by default, so "no data yet" is the common case
// and must read differently from "was reporting, then stopped".
const BATTERY_STALE_AFTER_S = 5.0;

function renderBattery(percent, ageS){
  const pill = $("batteryPill");
  const fill = pill.querySelector(".battery-fill");
  const stale = percent === null || ageS === null || ageS > BATTERY_STALE_AFTER_S;

  $("batteryText").textContent = stale ? "— %" : `${percent.toFixed(0)} %`;
  fill.setAttribute("width", stale ? 0 : Math.max(0, Math.min(100, percent)) / 100 * 14);
  pill.classList.toggle("low", !stale && percent <= 15);
  pill.classList.toggle("mid", !stale && percent > 15 && percent <= 30);
  pill.title = stale ? "Battery (/battery_info) — no data" : `Battery (/battery_info) — ${percent.toFixed(0)}%`;
}

async function pollBattery(){
  try{
    const r = await fetch("/api/battery");
    const d = await r.json();
    renderBattery(d.percent, d.age_s);
  }catch(e){
    renderBattery(null, null);
  }
}

/* ------------------------------------------------------------- 3D view */
// The viewer pulls ~11MB of meshes, so it is built the first time Dashboard
// (the only view its card belongs to) is rendered rather than at page load.
// Dashboard is the default view, so in practice that is still "as soon as the
// page is open" — but a user who lands on #logs or #applications never pays
// for it.
let robotViewer = null;
let robotInitStarted = false;
// A pose only counts as live while joint states keep arriving: bringup can go
// down with the last pose still on screen, and a stale robot that looks live
// is worse than one that says so.
const JOINT_STALE_AFTER_S = 3.0;

function robotSetOverlay(text, failed=false){
  const overlay = $("robotOverlay");
  if(!overlay) return;
  overlay.classList.toggle("done", text === null);
  overlay.classList.toggle("failed", !!failed);
  if(text !== null) $("robotOverlayText").textContent = text;
}

function initRobotViewer(){
  if(robotInitStarted) return;
  const stage = $("robotStage");
  if(!stage) return;

  robotInitStarted = true;
  if(stage.dataset.available !== "yes"){
    robotSetOverlay("Robot description not found on this machine — build and source daksha_description_full_body to see the 3D view.", true);
    return;
  }
  if(typeof THREE === "undefined" || typeof RobotViewer === "undefined"){
    robotSetOverlay("3D libraries failed to load (see static/js/vendor/).", true);
    return;
  }

  try{
    robotViewer = new RobotViewer($("robotCanvas"), stage,
      text => robotSetOverlay(text, false));
    robotViewer.onHover(onJointHover);
  }catch(e){
    robotSetOverlay(`Could not start the 3D view — ${e.message}`, true);
    return;
  }
  // The viewer has already written the reason through onStatus; this only
  // swaps the spinner for a resting error state.
  robotViewer.load("/api/urdf").then(ok => {
    if(!ok) $("robotOverlay").classList.add("failed");
  });
}

function robotResetCamera(){ if(robotViewer) robotViewer.resetCamera(); }
function robotToggleGrid(){ if(robotViewer) robotViewer.toggleGrid(); }

/* ------------------------------------------------- hover motor readout */
// Latest /api/joint_states payload, so the tooltip can be refreshed in place
// while the cursor sits still on a part and the numbers keep arriving.
let latestJoints = {positions:{}, efforts:{}, motors:{}};
let hoveredJoint = null;

// hw_interface's own bands: 8-14 are real faults, 0/1 are disabled/enabled.
const MOTOR_TEMP_WARN = 60;
const MOTOR_TEMP_ALERT = 65;

function prettyJoint(name){
  return name.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());
}

function onJointHover(jointName, at){
  const tip = $("jointTip");
  if(!tip) return;

  if(!jointName){
    hoveredJoint = null;
    tip.classList.remove("visible");
    return;
  }
  hoveredJoint = jointName;
  renderJointTip(jointName);
  tip.classList.add("visible");

  if(!at) return;  // a refresh from new data, not a pointer move
  // Offset from the cursor, flipped near an edge so the readout never hangs
  // off the stage.
  const rect = $("robotStage").getBoundingClientRect();
  let x = at.clientX - rect.left + 18;
  let y = at.clientY - rect.top + 18;
  if(x + tip.offsetWidth > rect.width - 8) x = at.clientX - rect.left - tip.offsetWidth - 18;
  if(y + tip.offsetHeight > rect.height - 8) y = at.clientY - rect.top - tip.offsetHeight - 18;
  tip.style.left = Math.max(8, x) + "px";
  tip.style.top = Math.max(8, y) + "px";
}

function renderJointTip(jointName){
  const tip = $("jointTip");
  const motor = latestJoints.motors[jointName] || {};
  const pos = latestJoints.positions[jointName];
  const effort = latestJoints.efforts[jointName];
  const num = v => Number.isFinite(Number(v)) ? Number(v) : null;

  $("jtName").textContent = prettyJoint(jointName);
  $("jtMotor").textContent = motor.id ? `${motor.arm} · #${motor.id}` : "no motor";
  $("jtStatus").textContent = motor.error_name || "—";

  const p = num(pos);
  // Prismatic gripper joints are metres; everything else is an angle.
  $("jtPos").textContent = p === null ? "—"
    : (jointName.includes("gripper") ? `${(p * 1000).toFixed(1)} mm`
                                     : `${(p * 180 / Math.PI).toFixed(1)}°`);

  const t = num(effort);
  $("jtTorque").textContent = t === null ? "—" : `${t.toFixed(2)} N·m`;

  const mos = num(motor.mos_temp), rotor = num(motor.rotor_temp);
  $("jtMos").textContent = mos === null ? "—" : `${mos.toFixed(1)} °C`;
  $("jtRotor").textContent = rotor === null ? "—" : `${rotor.toFixed(1)} °C`;
  $("jtRec").textContent = motor.recoveries ?? "—";

  const hottest = Math.max(mos ?? -Infinity, rotor ?? -Infinity);
  tip.classList.remove("warn", "critical", "fault");
  if(Number.isFinite(hottest)){
    if(hottest >= MOTOR_TEMP_ALERT) tip.classList.add("critical");
    else if(hottest >= MOTOR_TEMP_WARN) tip.classList.add("warn");
  }
  if(motor.error !== null && motor.error !== undefined && motor.error !== 0 && motor.error !== 1){
    tip.classList.add("fault");
  }
}

function setRobotLive(state, label){
  const pill = $("robotLive");
  if(!pill) return;
  pill.className = "robot-live" + (state ? " " + state : "");
  pill.querySelector("b").textContent = label;
}

async function pollJointStates(){
  // Nothing to drive until the model is in the scene.
  if(!robotViewer || !robotViewer.rootObj) return;
  try{
    const r = await fetch("/api/joint_states");
    const d = await r.json();
    if(!d.available){
      setRobotLive("", "NO ROS");
      return;
    }
    latestJoints = {
      positions: d.positions || {},
      efforts: d.efforts || {},
      motors: d.motors || {},
    };
    // Keep a tooltip that is already open in step with the incoming data,
    // without moving it out from under the cursor.
    if(hoveredJoint) renderJointTip(hoveredJoint);
    syncJointSliders(latestJoints.positions);

    if(d.age_s === null){
      setRobotLive("", "NO DATA");
      return;
    }
    robotViewer.setJointPositions(d.positions);
    if(d.age_s > JOINT_STALE_AFTER_S) setRobotLive("stale", `STALE ${d.age_s.toFixed(0)}s`);
    else setRobotLive("live", "LIVE");
  }catch(e){}
}

/* ------------------------------------------------------- joint control */
// Sliders publish to /joint_cmd, so they stay inert until explicitly armed
// and snap back to following the measured pose the moment they are disarmed.
let jointArmed = false;
let jointDragging = null;   // joint whose slider the operator is holding
let jointsMeta = [];

function jointUnits(j){
  return j.type === "prismatic"
    ? {toUi: v => v * 1000, fromUi: v => v / 1000, step: 0.5, fmt: v => v.toFixed(1) + " mm"}
    : {toUi: v => v * 180 / Math.PI, fromUi: v => v * Math.PI / 180, step: 0.5, fmt: v => v.toFixed(1) + "°"};
}

function renderJointSliders(joints){
  jointsMeta = joints;
  const box = $("jointCols");
  if(!box) return;
  if(!joints.length){
    box.innerHTML = `<div class="empty">No commandable joints found in the robot description.</div>`;
    return;
  }

  const sides = [["left", "Left arm"], ["right", "Right arm"]];
  box.innerHTML = sides.map(([prefix, title]) => {
    const rows = joints.filter(j => j.name.startsWith(prefix + "_")).map(j => {
      const u = jointUnits(j);
      return `<div class="jrow">
        <span class="jrow-name">${j.name.replace(prefix + "_", "")}</span>
        <input type="range" id="js_${j.name}" data-joint="${j.name}" disabled
               min="${u.toUi(j.lower).toFixed(2)}" max="${u.toUi(j.upper).toFixed(2)}"
               step="${u.step}" value="0">
        <span class="jrow-val" id="jv_${j.name}">—</span>
      </div>`;
    }).join("");
    return `<div><div class="jgroup-head">${title}</div>${rows}</div>`;
  }).join("");

  box.querySelectorAll("input[type=range]").forEach(el => {
    el.addEventListener("pointerdown", () => { jointDragging = el.dataset.joint; });
    el.addEventListener("input", () => sendJointCmd(el));
    const release = () => { if(jointDragging === el.dataset.joint) jointDragging = null; };
    el.addEventListener("pointerup", release);
    el.addEventListener("pointercancel", release);
    el.addEventListener("blur", release);
  });
}

async function sendJointCmd(el){
  const name = el.dataset.joint;
  const meta = jointsMeta.find(j => j.name === name);
  if(!meta || !jointArmed) return;

  const u = jointUnits(meta);
  const ui = parseFloat(el.value);
  $("jv_" + name).textContent = u.fmt(ui);
  try{
    const r = await fetch("/api/joint_cmd", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({name, position: u.fromUi(ui)}),
    });
    const d = await r.json();
    if(!d.ok) toast(d.error || "Joint command failed", true);
  }catch(e){}
}

// While disarmed (or while another joint is being dragged) the sliders track
// the measured pose, so arming never jumps the arm to a stale slider value.
function syncJointSliders(positions){
  for(const j of jointsMeta){
    if(jointDragging === j.name) continue;
    const v = positions[j.name];
    if(!Number.isFinite(Number(v))) continue;
    const u = jointUnits(j);
    const el = $("js_" + j.name);
    if(!el) continue;
    el.value = u.toUi(Number(v));
    $("jv_" + j.name).textContent = u.fmt(u.toUi(Number(v)));
  }
}

function setJointArmed(on){
  jointArmed = on;
  document.querySelectorAll("#jointCols input[type=range]").forEach(el => { el.disabled = !on; });
  // Keep the switch itself in sync with the actual armed state — a page
  // reload must never show Enabled while sliders are still inert, which is
  // what a browser restoring the checkbox's last-checked state would do.
  const arm = $("jointArm");
  if(arm) arm.checked = on;
  const note = $("jointNote");
  note.classList.toggle("armed", on);
  note.textContent = on
    ? "You can now move the joints."
    : "Disabled — sliders publish to /joint_cmd once enabled.";
}

// Arm joints only — the gripper isn't part of the home pose comparison and
// mimic joints (e.g. the driven gripper finger) don't take a command anyway.
const HOME_JOINT_RE = /_joint_[1-7]$/;
const HOME_TOLERANCE_RAD = 0.05;

async function armIsHome(){
  const armJoints = jointsMeta.filter(j => HOME_JOINT_RE.test(j.name));
  if(!armJoints.length) return false;
  try{
    const r = await fetch("/api/joint_states");
    const d = await r.json();
    const positions = d.positions || {};
    return armJoints.every(j => {
      const v = Number(positions[j.name]);
      return Number.isFinite(v) && Math.abs(v) <= HOME_TOLERANCE_RAD;
    });
  }catch(e){
    return false;
  }
}

async function waitForHome(timeoutMs = 20000, pollMs = 300){
  const deadline = Date.now() + timeoutMs;
  while(Date.now() < deadline){
    if(await armIsHome()) return true;
    await new Promise(res => setTimeout(res, pollMs));
  }
  return false;
}

// Enabling Joint Control must never let a slider jump the arms from wherever
// they currently sit — so this always drives them through /move_home first,
// confirms the measured joint states actually landed there, and only then
// arms the sliders. Any failure at either step leaves control disabled.
async function armJointControlAfterHome(checkbox){
  checkbox.disabled = true;
  const note = $("jointNote");
  const fail = (msg) => {
    toast(msg, true);
    checkbox.checked = false;
    checkbox.disabled = false;
    setJointArmed(false);
  };

  note.textContent = "Homing…";
  let d;
  try{
    const r = await fetch("/api/move_home", {method: "POST"});
    d = await r.json();
  }catch(e){
    fail("Move Home request failed");
    return;
  }
  if(!d.ok){
    fail(d.message || "Move Home failed");
    return;
  }

  note.textContent = "Homing… verifying home position from joint states.";
  const reached = await waitForHome();
  if(!reached){
    fail("Could not confirm the arms reached home — joint control stays disabled");
    return;
  }

  checkbox.disabled = false;
  setJointArmed(true);
}

async function loadJoints(){
  try{
    const r = await fetch("/api/robot_joints");
    const d = await r.json();
    renderJointSliders(d.joints || []);
    setJointArmed(false);
  }catch(e){}
}

/* ------------------------------------------------------- robot actions */
async function doMoveHome(){
  const btn = $("btnHome");
  btn.disabled = true;
  try{
    // /move_home drives the arms through a trajectory, so this call is slow
    // by nature — the button stays disabled until the service answers rather
    // than letting a second press stack another motion on the first.
    const r = await fetch("/api/move_home", {method: "POST"});
    const d = await r.json();
    toast(d.message || (d.ok ? "Moving home…" : "Move Home failed"), !d.ok);
  }catch(e){
    toast("Move Home failed: " + e.message, true);
  }finally{
    btn.disabled = false;
  }
}

async function setRobotMode(mode){
  try{
    const r = await fetch("/api/mode/set", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({mode}),
    });
    const d = await r.json();
    toast(d.message, !d.ok);
    // The pill is not set from the reply: mode_toggler's status topic is the
    // only thing that says the switch actually landed on hardware, and the
    // transition takes a moment. pollMode() picks it up.
  }catch(e){
    toast("Mode change failed: " + e.message, true);
  }
}

function renderMode(mode){
  const pill = $("modePill");
  if(!pill) return;
  pill.textContent = "MODE " + (mode || "—").toUpperCase();
  pill.className = "ch-note";
  if(mode === "teach" || mode === "normal") pill.classList.add(mode);
  else if(mode && mode !== "unknown") pill.classList.add("busy");

  document.querySelectorAll("#modeSeg button").forEach(b =>
    b.classList.toggle("active", b.dataset.mode === mode));
}

async function pollMode(){
  try{
    const r = await fetch("/api/mode");
    renderMode((await r.json()).mode);
  }catch(e){}
}

async function loadSpeedLimits(){
  try{
    const r = await fetch("/api/speed_limits");
    const d = await r.json();
    // null means the limiter node isn't up; leave the box empty rather than
    // showing a number that isn't the robot's.
    if(d.max_velocity !== null) $("limVel").value = d.max_velocity;
    if(d.max_acceleration !== null) $("limAcc").value = d.max_acceleration;
  }catch(e){}
}

async function setSpeedLimits(){
  const body = {};
  const vel = parseFloat($("limVel").value);
  const acc = parseFloat($("limAcc").value);
  if(Number.isFinite(vel)) body.max_velocity = vel;
  if(Number.isFinite(acc)) body.max_acceleration = acc;
  if(!Object.keys(body).length){
    toast("Enter a velocity or acceleration first", true);
    return;
  }
  try{
    const r = await fetch("/api/speed_limits", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(body),
    });
    const d = await r.json();
    const msgs = Object.values(d.results || {}).map(x => x.message);
    toast(msgs.join(" · ") || d.message || "Speed limits updated", !d.ok);
  }catch(e){
    toast("Could not set speed limits: " + e.message, true);
  }
}

/* --------------------------------------------------- navigation joystick */
let navArmed = false;
let navPointer = null;
let navX = 0, navY = 0;       // normalized deflection, [-1, 1]
const NAV_MAX_LINEAR = 0.5;   // must match TELEOP_MAX_* in launch_control_app.py
const NAV_MAX_ANGULAR = 1.0;

function navSetStick(x, y){
  navX = x; navY = y;
  const pad = $("navPad");
  const r = (pad.clientWidth / 2) - 26;   // keep the knob inside the ring
  $("navStick").style.transform = `translate(${x * r}px, ${-y * r}px)`;
  $("navLinear").textContent = (y * NAV_MAX_LINEAR).toFixed(2) + " m/s";
  $("navAngular").textContent = (-x * NAV_MAX_ANGULAR).toFixed(2) + " rad/s";
}

function navFromEvent(e){
  const pad = $("navPad");
  const rect = pad.getBoundingClientRect();
  let x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
  let y = -(((e.clientY - rect.top) / rect.height) * 2 - 1);
  // Clamp to the circle, not the square: a corner drag should not exceed
  // full speed on both axes at once.
  const mag = Math.hypot(x, y);
  if(mag > 1){ x /= mag; y /= mag; }
  navSetStick(x, y);
}

async function navSend(){
  if(!navArmed) return;
  try{
    await fetch("/api/teleop", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({x: navX, y: navY}),
    });
  }catch(e){}
}

function setNavArmed(on){
  navArmed = on;
  $("navPad").classList.toggle("disarmed", !on);
  const note = $("navNote");
  note.classList.toggle("armed", on);
  note.textContent = on
    ? "Armed — the base is driven from this pad while you hold it."
    : "Disabled — nothing is published to /cmd_vel.";
  navSetStick(0, 0);
  fetch("/api/teleop/enable", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({enabled: on}),
  }).then(r => r.json()).then(d => {
    if(!d.ok) toast(d.error || "Could not change teleop state", true);
  }).catch(() => {});
}

function initNavPad(){
  const pad = $("navPad");
  if(!pad) return;

  pad.addEventListener("pointerdown", e => {
    if(!navArmed) return;
    navPointer = e.pointerId;
    pad.setPointerCapture(e.pointerId);
    navFromEvent(e);
  });
  pad.addEventListener("pointermove", e => {
    if(navPointer !== e.pointerId) return;
    navFromEvent(e);
  });
  // Releasing, leaving the pad, or losing the pointer all recentre: the stick
  // is held, never left parked at speed.
  const release = e => {
    if(navPointer !== e.pointerId) return;
    navPointer = null;
    navSetStick(0, 0);
    navSend();
  };
  pad.addEventListener("pointerup", release);
  pad.addEventListener("pointercancel", release);
  pad.addEventListener("lostpointercapture", release);

  $("navArm").addEventListener("change", e => setNavArmed(e.target.checked));
  $("jointArm").addEventListener("change", e => {
    if(e.target.checked) armJointControlAfterHome(e.target);
    else setJointArmed(false);
  });
  setNavArmed(false);
}

/* --------------------------------------------------------------- wiring */
$("appSearch").addEventListener("input", e => {
  appFilter = e.target.value;
  pollApps();
});

/* --------------------------------------------------------------- views */
// The sidebar switches between views instead of scrolling one long page.
// A block lists the views it belongs to in data-views, so Dashboard can
// reuse the same markup as the single-topic views rather than duplicating
// it (duplicate markup would mean duplicate element ids, and every poll
// above looks elements up by id).
const VIEWS = {
  dashboard:    ["Dashboard",   "3D View",    "Live pose of the robot, driven by the arms' measured joint states"],
  applications: ["Application", "Management", "Start, stop and monitor all ROS and web applications"],
  monitor:      ["System",      "Monitor",    "CPU, GPU, memory, temperature and power from tegrastats"],
  motor:        ["Motor",       "Status",     "Per-motor state, temperature and recovery counts for both arms"],
  cameras:      ["Live",        "Cameras",    "Multi-camera vision monitor, streamed live from the robot's camera topics"],
  control:      ["Bringup",     "Control",    "Launch and stop the ROS 2 bringup for this robot"],
  logs:         ["Launch",      "Log",        "Combined output from the bringup and any app started here"],
  settings:     ["Panel",       "Settings",   "How this launch-control panel is configured"],
};

function showView(view){
  if(!VIEWS[view]) view = "dashboard";

  for(const el of document.querySelectorAll("[data-views]")){
    el.classList.toggle("is-hidden", !el.dataset.views.split(/\s+/).includes(view));
  }
  // A row whose children are all hidden would still take up its own gap.
  for(const group of document.querySelectorAll("[data-group]")){
    const anyVisible = [...group.children].some(c => !c.classList.contains("is-hidden"));
    group.classList.toggle("is-hidden", !anyVisible);
  }

  const [lead, tail, sub] = VIEWS[view];
  $("pageTitle").innerHTML = `${lead} <span>${tail}</span>`;
  $("pageSub").textContent = sub;

  document.querySelectorAll(".nav-item").forEach(n =>
    n.classList.toggle("active", n.dataset.target === view));

  document.querySelector(".main").scrollTop = 0;

  // Build the viewer the first time its card is actually on screen, and
  // re-measure on every later switch back: the canvas was display:none while
  // Dashboard was hidden, so its client size was 0 and the renderer would
  // otherwise keep the aspect ratio it had when it last drew.
  const robotCard = $("robotCard");
  if(robotCard && !robotCard.classList.contains("is-hidden")){
    initRobotViewer();
    if(robotViewer) robotViewer.resize();
  }

  // Cameras only stream while their card is on screen — polling from a
  // hidden view would waste bandwidth decoding frames nobody sees.
  const camerasCard = $("cameras");
  if(camerasCard && !camerasCard.classList.contains("is-hidden")){
    loadCameraConfig().then(startCameraStreaming);
  } else {
    stopCameraStreaming();
  }
}

document.querySelectorAll(".nav-item").forEach(item => {
  item.addEventListener("click", e => {
    e.preventDefault();
    const view = item.dataset.target;
    // Keep the hash in step so a view survives a refresh and the browser's
    // back button moves between views.
    if(location.hash.slice(1) !== view) location.hash = view;
    showView(view);
  });
});
window.addEventListener("hashchange", () => showView(location.hash.slice(1)));
showView(location.hash.slice(1) || "dashboard");

tickClock(); setInterval(tickClock, 1000);
poll(); setInterval(poll, 1000);
pollApps(); setInterval(pollApps, 3000);
pollLogs(); setInterval(pollLogs, 1000);
pollMotorStatus(); setInterval(pollMotorStatus, 1000);
initGainsTable();
pollGains(); setInterval(pollGains, 1000);
pollSocStats(); setInterval(pollSocStats, 1000);
pollBattery(); setInterval(pollBattery, 1000);
// 10 Hz: fast enough that an arm moving at teleop speed looks continuous,
// and the payload is ~16 floats.
pollJointStates(); setInterval(pollJointStates, 100);

initNavPad();
loadJoints();
// Mode transitions take a couple of seconds to land and the limiter's values
// can be changed by any other UI, so both are polled rather than assumed.
pollMode(); setInterval(pollMode, 2000);
loadSpeedLimits(); setInterval(loadSpeedLimits, 15000);
// The deadman on the server zeroes the base after 500ms of silence, so the
// stick has to keep talking while it is held down.
setInterval(() => { if(navArmed && navPointer !== null) navSend(); }, 100);

/* --------------------------------------------------------- camera grid */
// Cameras are discovered from the backend (CAMERA_REGISTRY in
// launch_control_app.py), not hardcoded here — the operator picks which
// ones to display via the drag-and-drop config panel and can save that
// layout (persisted server-side to config/camera_layout.json).
// (camPollInterval/camLastFrameAt/cameraRegistry/selectedCameraIds/camDragId
// are declared near the top of this file -- see the comment there.)

function escHtml(str){
  return String(str)
    .replace(/&/g,"&amp;").replace(/</g,"&lt;")
    .replace(/>/g,"&gt;").replace(/"/g,"&quot;");
}

function camById(id){
  return cameraRegistry.find(c => c.id === id);
}

function toggleCameraConfigPanel(){
  const panel = $("camConfigPanel");
  if(!panel) return;
  const show = panel.style.display === "none";
  panel.style.display = show ? "block" : "none";
  $("camConfigToggleBtn")?.classList.toggle("active", show);
}

async function loadCameraConfig(){
  try{
    const res = await fetch("/api/camera_config");
    const data = await res.json();
    if(data && data.ok){
      cameraRegistry = data.available || [];
      selectedCameraIds = data.selected || cameraRegistry.map(c => c.id);
    }
  }catch(e){
    console.warn("[Camera Config] load failed", e);
  }
  renderCameraConfigLists();
  renderCameraGrid();
  initCameraCards();
}

async function saveCameraConfig(){
  try{
    const res = await fetch("/api/camera_config", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({selected: selectedCameraIds}),
    });
    const data = await res.json();
    toast(data.ok ? "Camera layout saved" : (data.error || "Failed to save camera layout"), !data.ok);
  }catch(e){
    toast("Failed to reach server to save camera layout", true);
  }
}

function renderCameraConfigLists(){
  const availableList = $("camAvailableList");
  const selectedList = $("camSelectedList");
  if(!availableList || !selectedList) return;

  const availableIds = cameraRegistry.map(c => c.id).filter(id => !selectedCameraIds.includes(id));

  const chip = cam => `
    <div class="cam-drop-item" draggable="true" ondragstart="camDragStart(event, '${cam.id}')" ondragend="camDragEnd(event)">
      <div>
        <span class="cam-drop-item-name">${escHtml(cam.display_name)}</span>
        <span class="cam-drop-item-topic">${escHtml(cam.topic)}</span>
      </div>
      <span class="cam-drop-item-handle">⠿</span>
    </div>`;

  availableList.innerHTML = availableIds.length
    ? availableIds.map(id => camById(id)).filter(Boolean).map(chip).join("")
    : '<span class="cam-config-hint">All known cameras are displayed.</span>';

  selectedList.innerHTML = selectedCameraIds.length
    ? selectedCameraIds.map(id => camById(id)).filter(Boolean).map(chip).join("")
    : '<span class="cam-config-hint">Drag a camera here to display it.</span>';
}

function camDragStart(event, id){
  camDragId = id;
  event.dataTransfer.effectAllowed = "move";
  event.target.classList.add("dragging");
}

function camDragEnd(event){
  event.target.classList.remove("dragging");
  document.querySelectorAll(".cam-drop-list").forEach(el => el.classList.remove("cam-drag-over"));
}

function camDragOver(event){
  event.preventDefault();
  event.currentTarget.classList.add("cam-drag-over");
}

function camDrop(event, target){
  event.preventDefault();
  event.currentTarget.classList.remove("cam-drag-over");
  if(!camDragId) return;

  selectedCameraIds = selectedCameraIds.filter(id => id !== camDragId);
  if(target === "selected") selectedCameraIds.push(camDragId);
  camDragId = null;

  renderCameraConfigLists();
  renderCameraGrid();
  initCameraCards();
  fetchCameraFrames();
}

function renderCameraGrid(){
  const grid = $("camDynamicGrid");
  if(!grid) return;
  const cams = selectedCameraIds.map(id => camById(id)).filter(Boolean);
  // World is the operator's main situational-awareness view, so it always
  // takes the full top row regardless of where it sits in the saved
  // display order -- the wrist cameras are close-up detail underneath it.
  const ordered = [...cams].sort((a, b) =>
    (a.id === "world" ? -1 : 0) - (b.id === "world" ? -1 : 0));
  grid.innerHTML = ordered.map((cam, i) => `
    <div class="cam-card${cam.id === "world" ? " cam-card-wide" : ""}">
      <div class="cam-card-header">
        <span>CAM ${i + 1}: ${escHtml(cam.display_name)}</span>
        <span class="cam-status-tag" id="cam-tag-${cam.id}">OFFLINE</span>
      </div>
      <img class="cam-img-viewport" id="cam-img-${cam.id}" style="display:none;">
      <div class="cam-offline-placeholder" id="cam-off-${cam.id}">
        <span>${escHtml(cam.display_name)} Offline</span>
        <span style="font-size:0.75rem;">${escHtml(cam.topic)}</span>
      </div>
    </div>`).join("");
}

function refreshCameraStreams(){
  const btn = document.querySelector(".cam-action-btn[onclick=\"refreshCameraStreams()\"]");
  const icon = btn ? btn.querySelector("svg") : null;
  if(icon) icon.classList.add("spin");

  toast("Re-syncing camera vision streams…");
  stopCameraStreaming();
  initCameraCards();

  setTimeout(() => {
    startCameraStreaming();
    if(icon) icon.classList.remove("spin");
    toast("Camera streams re-synced");
  }, 200);
}

function stopCameraStreaming(){
  if(camPollInterval){
    clearInterval(camPollInterval);
    camPollInterval = null;
  }
}

function startCameraStreaming(){
  stopCameraStreaming();
  initCameraCards();
  // Poll camera frames at ~15 FPS.
  camPollInterval = setInterval(fetchCameraFrames, 70);
  fetchCameraFrames();
}

async function fetchCameraFrames(){
  const camerasCard = $("cameras");
  if(!camerasCard || camerasCard.classList.contains("is-hidden")){
    stopCameraStreaming();
    return;
  }

  try{
    const res = await fetch("/api/camera_frames");
    const data = await res.json();
    const now = Date.now();

    if(data && data.ok && data.frames){
      selectedCameraIds.map(id => camById(id)).filter(Boolean).forEach(cfg => {
        const frameData = data.frames[cfg.id];
        const img = $(`cam-img-${cfg.id}`);
        const off = $(`cam-off-${cfg.id}`);
        const tag = $(`cam-tag-${cfg.id}`);

        if(frameData){
          camLastFrameAt[cfg.id] = now;
          if(img){ img.src = frameData; img.style.display = "block"; }
          if(off) off.style.display = "none";
          if(tag){
            tag.textContent = "LIVE";
            tag.style.background = "rgba(34, 197, 94, 0.18)";
            tag.style.color = "#4ade80";
            tag.style.borderColor = "rgba(34, 197, 94, 0.3)";
          }
        } else if(now - (camLastFrameAt[cfg.id] || 0) > 2500){
          if(img) img.style.display = "none";
          if(off) off.style.display = "flex";
          if(tag){
            tag.textContent = "OFFLINE";
            tag.style.background = "";
            tag.style.color = "";
            tag.style.borderColor = "";
          }
        }
      });
    }
  }catch(err){
    console.warn("[Camera Stream] Poll error:", err);
  }
}

function initCameraCards(){
  selectedCameraIds.map(id => camById(id)).filter(Boolean).forEach(cfg => {
    const img = $(`cam-img-${cfg.id}`);
    const off = $(`cam-off-${cfg.id}`);
    const tag = $(`cam-tag-${cfg.id}`);
    if(img){ img.removeAttribute("src"); img.style.display = "none"; }
    if(off) off.style.display = "flex";
    if(tag){
      tag.textContent = "OFFLINE";
      tag.style.background = "";
      tag.style.color = "";
      tag.style.borderColor = "";
    }
  });
}
