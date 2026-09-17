const $ = id => document.getElementById(id);
let playingName = null;

function toast(msg, err=false){
  const t = $("toast"); t.textContent = msg;
  t.className = "toast show" + (err ? " err" : "");
  clearTimeout(t._t); t._t = setTimeout(()=> t.className = "toast", 3200);
}
async function post(url, body){
  const r = await fetch(url, {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(body||{})});
  return {ok:r.ok, data: await r.json()};
}

async function startRec(){
  const name = $("recName").value.trim();
  if(!name){ toast("Name the gesture first.", true); return; }
  const {data} = await post("/api/record/start", {recording_name:name, topic_name:$("srcTopic").value.trim()});
  toast(data.message, !data.success);
}
async function stopRec(){
  const {data} = await post("/api/record/stop", {});
  toast(data.message, !data.success);
  refreshLibrary();
}
function toggleRepeatCount(){
  $("repeatCountWrap").style.display = ($("repeatMode").value === "count") ? "" : "none";
}
async function replay(name){
  const {data} = await post("/api/replay", {
    recording_name:name,
    output_topic:$("outTopic").value.trim(),
    replay_speed:$("speed").value,
    repeat_mode:$("repeatMode").value,
    repeat_count:parseInt($("repeatCount").value) || 1,
    interval_s:parseFloat($("intervalS").value) || 0,
  });
  toast(data.message, !data.success);
}
async function stopPlay(){
  const {data} = await post("/api/replay/stop", {});
  toast(data.message, !data.success);
}
async function goHome(){
  const {data} = await post("/api/home", {
    output_topic:$("outTopic").value.trim(),
    replay_speed:$("speed").value,
  });
  toast(data.message, !data.success);
}
let modeStatus = "unknown";
let modeSwitching = false;

async function toggleMode(){
  if(modeSwitching) return;
  const target = modeStatus === "normal" ? "teach" : "normal";
  modeSwitching = true;
  $("btnModeToggle").disabled = true;
  const {data} = await post("/api/mode/set", {mode: target});
  toast(data.message, !data.success);
  modeSwitching = false;
}

async function setRampVelocity(){
  const v = parseFloat($("rampVel").value);
  if(isNaN(v)){ toast("Enter a valid number.", true); return; }
  const {data} = await post("/api/set_ramp_velocity", {velocity:v});
  if(data.success) $("rampVel").value = data.velocity;
  toast(data.success ? `Ramp velocity set to ${data.velocity} rad/s` : data.message, !data.success);
}

async function setRampTolerance(){
  const v = parseFloat($("rampTol").value);
  if(isNaN(v)){ toast("Enter a valid number.", true); return; }
  const {data} = await post("/api/set_ramp_tolerance", {tolerance_deg:v});
  if(data.success) $("rampTol").value = data.tolerance_deg;
  toast(data.success ? `Ramp tolerance set to ${data.tolerance_deg}°` : data.message, !data.success);
}

async function setMaxVelocity(){
  const v = parseFloat($("maxVel").value);
  if(isNaN(v)){ toast("Enter a valid number.", true); return; }
  const {data} = await post("/api/speed_limits", {max_velocity:v});
  const r = data.max_velocity || {};
  toast(r.success ? `Max velocity set to ${v} rad/s` : (r.message || "Failed"), !r.success);
}

async function setMaxAcceleration(){
  const v = parseFloat($("maxAcc").value);
  if(isNaN(v)){ toast("Enter a valid number.", true); return; }
  const {data} = await post("/api/speed_limits", {max_acceleration:v});
  const r = data.max_acceleration || {};
  toast(r.success ? `Max acceleration set to ${v} rad/s²` : (r.message || "Failed"), !r.success);
}

async function pollSpeedLimits(){
  try {
    const r = await fetch("/api/speed_limits");
    const data = await r.json();
    const velEl = $("maxVel"), accEl = $("maxAcc");
    if(velEl && document.activeElement !== velEl && data.max_velocity !== null){
      velEl.value = Number(data.max_velocity).toFixed(2);
    }
    if(accEl && document.activeElement !== accEl && data.max_acceleration !== null){
      accEl.value = Number(data.max_acceleration).toFixed(2);
    }
  } catch(e) { /* joint_command_limiter not up yet */ }
}
async function del(name){
  if(!confirm(`Delete gesture "${name}"? This removes the .parquet file.`)) return;
  const {data} = await post("/api/recordings/delete", {recording_name:name});
  toast(data.message, !data.success);
  refreshLibrary();
}

async function renameRecording(name){
  const newName = prompt(`Rename "${name}" to:`, name);
  if(newName === null) return;
  const trimmed = newName.trim();
  if(!trimmed || trimmed === name) return;
  const {data} = await post("/api/recordings/rename", {old_name:name, new_name:trimmed});
  toast(data.message, !data.success);
  if(data.success){
    const i = sequenceQueue.indexOf(name);
    if(i !== -1){ sequenceQueue[i] = trimmed; renderQueue(); }
    refreshSequenceLibrary();
  }
  refreshLibrary();
}

// ----- play-sequence queue ----- //
let sequenceQueue = [];

function toggleQueue(name, checked){
  if(checked){
    if(!sequenceQueue.includes(name)) sequenceQueue.push(name);
  } else {
    sequenceQueue = sequenceQueue.filter(n => n !== name);
  }
  renderQueue();
}

function removeFromQueue(name){
  sequenceQueue = sequenceQueue.filter(n => n !== name);
  renderQueue();
  refreshLibrary();
}

function moveQueueItem(idx, dir){
  const newIdx = idx + dir;
  if(newIdx < 0 || newIdx >= sequenceQueue.length) return;
  [sequenceQueue[idx], sequenceQueue[newIdx]] = [sequenceQueue[newIdx], sequenceQueue[idx]];
  renderQueue();
}

function renderQueue(){
  const box = $("seqQueue");
  if(!sequenceQueue.length){
    box.innerHTML = `<div class="empty">Check gestures in the library below to build a play sequence.</div>`;
    $("btnPlaySeq").disabled = true;
    return;
  }
  box.innerHTML = sequenceQueue.map((n, i) => `
    <div class="seq-item">
      <span class="seq-idx">${i+1}</span>
      <span class="seq-name">${n}</span>
      <button class="icon-btn" onclick="moveQueueItem(${i},-1)" ${i===0?'disabled':''}>&uarr;</button>
      <button class="icon-btn" onclick="moveQueueItem(${i},1)" ${i===sequenceQueue.length-1?'disabled':''}>&darr;</button>
      <button class="icon-btn b-del" onclick="removeFromQueue('${n}')">Remove</button>
    </div>`).join("");
  $("btnPlaySeq").disabled = false;
}

async function playSequence(){
  if(!sequenceQueue.length) return;
  const {data} = await post("/api/replay_sequence", {
    recording_names: sequenceQueue,
    output_topic:$("outTopic").value.trim(),
    replay_speed:$("speed").value,
    repeat_mode:$("repeatMode").value,
    repeat_count:parseInt($("repeatCount").value) || 1,
    interval_s:parseFloat($("intervalS").value) || 0,
  });
  toast(data.message, !data.success);
}

// ----- sequence library (saved, named queues) ----- //
let savedSequences = [];

async function saveSequence(){
  if(!sequenceQueue.length){ toast("Queue is empty — check some gestures first.", true); return; }
  const name = prompt("Save this sequence as:");
  if(!name || !name.trim()) return;
  const {data} = await post("/api/sequences/save", {name:name.trim(), recording_names:sequenceQueue});
  toast(data.message, !data.success);
  if(data.success) refreshSequenceLibrary();
}

async function refreshSequenceLibrary(){
  const r = await fetch("/api/sequences"); const d = await r.json();
  savedSequences = d.sequences || [];
  $("seqLibCount").textContent = d.count;
  const body = $("seqLibBody");
  if(!savedSequences.length){
    body.innerHTML = `<div class="empty">No saved sequences yet. Check gestures above, then "Save as…".</div>`;
    return;
  }
  let rows = savedSequences.map(s => `
    <tr>
      <td class="gname">${s.name}</td>
      <td class="num"><b>${(s.recording_names||[]).length}</b></td>
      <td class="mono">${(s.recording_names||[]).join(" &rarr; ")}</td>
      <td class="num">${(s.created_at||'').replace('T',' ')||'—'}</td>
      <td>
        <button class="b-play icon-btn" onclick="playSavedSequence('${s.name}')"><span class="dot"></span>Play</button>
        <button class="icon-btn" onclick="loadSequence('${s.name}')">Load</button>
        <button class="b-del icon-btn" onclick="deleteSequence('${s.name}')">Delete</button>
      </td></tr>`).join("");
  body.innerHTML = `<table>
    <thead><tr><th>Sequence</th><th>Gestures</th><th>Order</th><th>Saved</th><th></th></tr></thead>
    <tbody>${rows}</tbody></table>`;
}

function loadSequence(name){
  const seq = savedSequences.find(s => s.name === name);
  if(!seq) return;
  sequenceQueue = [...(seq.recording_names || [])];
  renderQueue();
  refreshLibrary();
  toast(`Loaded '${name}' into the queue.`);
}

async function playSavedSequence(name){
  const {data} = await post("/api/sequences/play", {
    name,
    output_topic:$("outTopic").value.trim(),
    replay_speed:$("speed").value,
    repeat_mode:$("repeatMode").value,
    repeat_count:parseInt($("repeatCount").value) || 1,
    interval_s:parseFloat($("intervalS").value) || 0,
  });
  toast(data.message, !data.success);
}

async function deleteSequence(name){
  if(!confirm(`Delete saved sequence "${name}"?`)) return;
  const {data} = await post("/api/sequences/delete", {name});
  toast(data.message, !data.success);
  refreshSequenceLibrary();
}

async function refreshLibrary(){
  const r = await fetch("/api/recordings"); const d = await r.json();
  $("libCount").textContent = d.count;
  const body = $("libBody");
  if(!d.recordings.length){
    body.innerHTML = `<div class="empty">No gestures captured yet. Record one from the panel above to get started.</div>`;
    return;
  }
  let rows = d.recordings.map(g => {
    const playing = (g.name === playingName);
    const checked = sequenceQueue.includes(g.name) ? "checked" : "";
    return `<tr class="${playing?'playing-row':''}">
      <td class="checkcell"><input type="checkbox" ${checked} onchange="toggleQueue('${g.name}', this.checked)"></td>
      <td class="gname">${g.name}</td>
      <td class="num"><b>${(g.duration_s||0).toFixed(2)}</b>s</td>
      <td class="num">${(g.created_at||'').replace('T',' ')||'—'}</td>
      <td>
        <button class="b-play icon-btn" onclick="replay('${g.name}')"><span class="dot"></span>Play</button>
        <button class="icon-btn" onclick="renameRecording('${g.name}')">Rename</button>
        <button class="b-del icon-btn" onclick="del('${g.name}')">Delete</button>
      </td></tr>`;
  }).join("");
  body.innerHTML = `<table>
    <thead><tr><th></th><th>Gesture</th><th>Duration</th><th>Captured</th><th></th></tr></thead>
    <tbody>${rows}</tbody></table>`;
}

async function poll(){
  try{
    const r = await fetch("/api/state"); const s = await r.json();
    const rec = s.recording, rep = s.replay;
    $("recFrames").textContent = rec.frames||0;
    $("recJoints").textContent = rec.joints||0;
    $("recElapsed").textContent = (rec.elapsed_s||0).toFixed(1)+"s";
    $("recFrames").className = "v" + (rec.active?" live":"");
    $("btnRec").disabled = rec.active;
    $("btnStop").disabled = !rec.active;

    const pct = rep.percent||0;
    $("pfill").style.width = pct+"%";
    $("playPct").textContent = pct.toFixed(1)+"%";
    $("playFrame").textContent = (rep.frame||0)+" / "+(rep.total||0);
    $("playMsg").textContent = rep.message||"idle";
    $("playName").textContent = rep.active
      ? ((rep.playlist_total||0) > 1
          ? `Playing ${(rep.playlist_index||0)+1}/${rep.playlist_total} · ${rep.name}`
          : "Playing · "+rep.name)
      : "No gesture playing";
    $("btnStopPlay").disabled = !rep.active;
    $("btnGoHome").disabled = rec.active || rep.active;
    $("playLoop").textContent = (rep.active && rep.repeat_mode && rep.repeat_mode !== "once")
      ? (rep.repeat_mode === "infinite"
          ? `Loop ${rep.loop_count||0} (until stopped)`
          : `Loop ${rep.loop_count||0} / ${rep.repeat_count||1}`)
      : "";
    const newPlaying = rep.active ? rep.name : null;
    if(newPlaying !== playingName){ playingName = newPlaying; refreshLibrary(); }

    const lamp = $("lamp");
    if(rec.active){ lamp.className="lamp rec"; $("stateText").textContent="RECORDING"; }
    else if(rep.active){ lamp.className="lamp play"; $("stateText").textContent="PLAYBACK"; }
    else if(s.ros){ lamp.className="lamp ready"; $("stateText").textContent="READY"; }
    else { lamp.className="lamp"; $("stateText").textContent="NO ROS"; }

    modeStatus = s.mode || "unknown";
    const modeLamp = $("modeLamp");
    $("modeText").textContent = modeStatus.toUpperCase();
    if(modeStatus === "normal"){ modeLamp.className = "lamp ready"; }
    else if(modeStatus === "teach"){ modeLamp.className = "lamp play"; }
    else if(modeStatus === "transitioning"){ modeLamp.className = "lamp rec"; }
    else { modeLamp.className = "lamp"; }
    const modeBtn = $("btnModeToggle");
    modeBtn.textContent = modeStatus === "normal" ? "Switch to Teach" : "Switch to Normal";
    modeBtn.disabled = modeSwitching || rec.active || rep.active ||
      modeStatus === "transitioning" || modeStatus === "unknown";
  }catch(e){}
}
let folderCurrentPath = null;

async function toggleFolderBrowser(){
  const box = $("folderBrowser");
  if(box.style.display === "none"){
    box.style.display = "block";
    await loadFolderList($("recordingsDir").value);
  } else {
    box.style.display = "none";
  }
}

async function loadFolderList(path){
  const r = await fetch("/api/list_dirs?path=" + encodeURIComponent(path));
  const d = await r.json();
  folderCurrentPath = d.path;
  $("folderPath").textContent = d.path;
  const select = $("folderSelect");
  select.innerHTML = "";
  if(!d.dirs.length){
    const opt = document.createElement("option");
    opt.disabled = true;
    opt.textContent = "(no subfolders)";
    select.appendChild(opt);
  } else {
    d.dirs.forEach(name => {
      const opt = document.createElement("option");
      opt.value = name;
      opt.textContent = name;
      select.appendChild(opt);
    });
  }
}

function folderUp(){
  loadFolderList(folderCurrentPath + "/..");
}

function folderEnter(){
  const select = $("folderSelect");
  if(!select.value) return;
  loadFolderList(folderCurrentPath + "/" + select.value);
}

async function folderChoose(){
  const path = folderCurrentPath;
  $("recordingsDir").value = path;
  await post("/api/set_recordings_dir", {folder: path});
  toggleFolderBrowser();
  refreshLibrary();
  toast("Recording folder changed");
}

let lastLogId = 0;
async function pollLogs(){
  try{
    const r = await fetch(`/api/logs?since=${lastLogId}`);
    const d = await r.json();
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
    while(box.children.length > 400) box.removeChild(box.firstChild);
    if(atBottom) box.scrollTop = box.scrollHeight;
  }catch(e){}
}
function clearLog(){
  $("logBody").innerHTML = "";
}

let motorWatchers = []; // topics the user has added via the "+" tile

function renderMotorGrid(){
  const grid = $("motorGrid");
  grid.innerHTML = "";
  motorWatchers.forEach((topic, idx) => {
    const card = document.createElement("div");
    card.className = "card motor-card";

    const eyebrow = document.createElement("div");
    eyebrow.className = "eyebrow";
    const nameSpan = document.createElement("span");
    nameSpan.className = "topic-name";
    nameSpan.textContent = topic;
    const delBtn = document.createElement("button");
    delBtn.className = "icon-btn b-del";
    delBtn.textContent = "Remove";
    delBtn.onclick = () => removeMotorWatcher(idx);
    eyebrow.appendChild(nameSpan);
    eyebrow.appendChild(delBtn);

    const body = document.createElement("div");
    body.id = "motorBody_" + idx;
    body.innerHTML = `<div class="empty">Waiting for data…</div>`;

    card.appendChild(eyebrow);
    card.appendChild(body);
    grid.appendChild(card);
  });

  const addTile = document.createElement("div");
  addTile.className = "card motor-add";
  addTile.id = "motorAddTile";
  const addBtn = document.createElement("button");
  addBtn.className = "b-primary b-add";
  addBtn.textContent = "+";
  addBtn.onclick = showMotorTopicPicker;
  addTile.appendChild(addBtn);
  grid.appendChild(addTile);
}

async function showMotorTopicPicker(){
  const tile = $("motorAddTile");
  const r = await fetch("/api/motor_topics");
  const d = await r.json();
  const available = (d.topics || []).filter(t => !motorWatchers.includes(t));
  if(!available.length){
    toast(d.available ? "No more motor_status topics found." : "hw_interface motor_status not available.", true);
    return;
  }
  tile.innerHTML = "";
  const wrap = document.createElement("div");
  wrap.className = "picker";
  const select = document.createElement("select");
  available.forEach(t => {
    const opt = document.createElement("option");
    opt.value = t;
    opt.textContent = t;
    select.appendChild(opt);
  });
  const addBtn = document.createElement("button");
  addBtn.textContent = "Add";
  addBtn.onclick = () => confirmAddMotorWatcher(select.value);
  wrap.appendChild(select);
  wrap.appendChild(addBtn);
  tile.appendChild(wrap);
}

async function confirmAddMotorWatcher(topic){
  if(!topic) return;
  const {data} = await post("/api/motor_watch", {topic});
  if(!data.success){ toast(data.message, true); return; }
  motorWatchers.push(topic);
  renderMotorGrid();
  pollMotorStatus();
}

function removeMotorWatcher(idx){
  const topic = motorWatchers[idx];
  post("/api/motor_unwatch", {topic});
  motorWatchers.splice(idx, 1);
  renderMotorGrid();
}

async function pollMotorStatus(){
  if(!motorWatchers.length) return;
  try{
    const r = await fetch("/api/motor_status");
    const d = await r.json();
    motorWatchers.forEach((topic, idx) => {
      const body = $("motorBody_" + idx);
      if(!body) return;
      const motors = d.status[topic] || [];
      if(!motors.length){ body.innerHTML = `<div class="empty">Waiting for data…</div>`; return; }
      let rows = motors.map(m => {
        const fault = !(m.error === 0 || m.error === 1);
        return `<tr class="${fault ? 'motor-row-fault' : ''}">
          <td class="num"><b>${m.id}</b></td>
          <td>${m.error_name}</td>
          <td class="num">${m.mos_temp}&deg;C</td>
          <td class="num">${m.rotor_temp}&deg;C</td>
        </tr>`;
      }).join("");
      body.innerHTML = `<table>
        <thead><tr><th>Motor</th><th>Status</th><th>MOS</th><th>Rotor</th></tr></thead>
        <tbody>${rows}</tbody></table>`;
    });
  }catch(e){}
}

toggleRepeatCount();
renderQueue();
refreshLibrary();
refreshSequenceLibrary();
poll(); setInterval(poll, 250);
pollLogs(); setInterval(pollLogs, 1000);
renderMotorGrid();
setInterval(pollMotorStatus, 500);
pollSpeedLimits(); setInterval(pollSpeedLimits, 3000);
