const $ = id => document.getElementById(id);

function toast(msg, err=false){
  const t = $("toast"); t.textContent = msg;
  t.className = "toast show" + (err ? " err" : "");
  clearTimeout(t._t); t._t = setTimeout(()=> t.className = "toast", 3200);
}

async function post(url){
  const r = await fetch(url, {method:"POST"});
  return {ok:r.ok, data: await r.json()};
}

let launching = false;
let killing = false;
let bringupRunning = false;

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
    $("uptime").textContent = (s.uptime_s || 0).toFixed(1) + "s";

    $("btnLaunch").disabled = launching || s.running;
    $("btnKill").disabled = killing || !s.running;

    const lamp = $("lamp");
    if(s.running){
      lamp.className = "lamp running";
      $("stateText").textContent = "RUNNING";
    } else {
      lamp.className = "lamp";
      $("stateText").textContent = "STOPPED";
    }

    bringupRunning = s.running;
    $("motorSection").style.display = s.running ? "" : "none";
  }catch(e){}
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
    while(box.children.length > 800) box.removeChild(box.firstChild);
    if(atBottom) box.scrollTop = box.scrollHeight;
  }catch(e){}
}

function clearLog(){
  $("logBody").innerHTML = "";
}

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
    <thead><tr><th>ID</th><th>Status</th><th>MOS</th><th>Rotor</th><th>Recoveries</th></tr></thead>
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

function renderSocStats(stats, available){
  if(!available){
    for(const id of ["socCpu","socGpu","socRam","socCpuTemp","socSocTemp","socPower"]) $(id).textContent = "n/a";
    $("socCores").innerHTML = "";
    return;
  }
  const cores = stats.cpu || [];
  const active = cores.filter(c => !c.off);
  const cpuAvg = active.length ? Math.round(active.reduce((a,c)=>a+c.usage,0)/active.length) : 0;

  $("socCpu").textContent = cpuAvg + "%";
  $("socGpu").textContent = (stats.gpu || 0) + "%";
  $("socRam").textContent = `${stats.ram_used}/${stats.ram_total}MB`;
  $("socCpuTemp").textContent = (stats.cpu_temp || 0).toFixed(1) + "°C";
  $("socSocTemp").textContent = (stats.soc_temp || 0).toFixed(1) + "°C";
  $("socPower").textContent = ((stats.power_system || 0) / 1000).toFixed(2) + "W";

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

poll(); setInterval(poll, 1000);
pollLogs(); setInterval(pollLogs, 1000);
pollMotorStatus(); setInterval(pollMotorStatus, 1000);
pollSocStats(); setInterval(pollSocStats, 1000);
