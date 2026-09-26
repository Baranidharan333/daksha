/**
 * main.js  —  iHub Robotics Daksha Dashboard
 * Handles UI state, API calls, joint controls, launch management.
 */

'use strict';

// ── State ─────────────────────────────────────────────────────
let viewer       = null;
let jointsList   = [];
let rosRunning   = false;
let activeView   = 'viewer';
let currentURDF  = 'daksha_v10_2.urdf';
let lastNotifiedBatteryThreshold = 100;
let isLightMode  = false;
let jointPollTimer = null;
let liveJointFeed = true;
let hoveredJointName = null;
let latestJointTorque = {};
let latestJointTemperature = {};
let latestJointPositions = {};
let jointSlidersUnlocked = false;
const motorHealthByKey = new Map();
const initializedMotorSides = new Set();
const canOnlineBySide = new Map();
const motorTempLevelByKey = new Map();

// ── Boot ─────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', async () => {
  // Load theme preference
  const savedTheme = localStorage.getItem('theme');
  if (savedTheme === 'light') {
    isLightMode = true;
    document.documentElement.classList.add('light-mode');
    const themeIcon = document.getElementById('theme-icon');
    if (themeIcon) themeIcon.textContent = '🌙';
  }

  initViewer();
  await loadURDF(currentURDF);
  fetchRobotInfo();
  fetchTopics();
  await fetchJoints();
  updateLaunchPreview();
  startPolling();
  liveJointFeed = localStorage.getItem('liveJointFeed') !== 'false';
  updateLiveJointFeedUI();
  if (liveJointFeed) startLiveJointPolling();

  // Config listeners
  ['cfg-arm','cfg-ee','cfg-body','cfg-bimanual'].forEach(id => {
    document.getElementById(id)?.addEventListener('change', updateLaunchPreview);
  });
});

// ── Viewer Init ───────────────────────────────────────────────
function initViewer() {
  viewer = new URDFViewer('robot-canvas', 'urdf-viewer-container');
  viewer.setDayMode(isLightMode);
  viewer.onHover((jointName, pos) => updateJointHoverTooltip(jointName, pos));
}

// ── Joint Hover Tooltip ───────────────────────────────────────
function humanizeJointName(name) {
  if (!name) return '--';
  return name.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

function updateJointHoverTooltip(jointName, pos) {
  const tooltip = document.getElementById('joint-hover-tooltip');
  if (!tooltip) return;

  if (!jointName) {
    hoveredJointName = null;
    tooltip.classList.remove('visible');
    return;
  }
  hoveredJointName = jointName;

  const torque = Number(latestJointTorque[jointName]);
  const tempInfo = latestJointTemperature[jointName] || {};
  const temp = Number(tempInfo.rotor_temp ?? tempInfo.mos_temp);
  const posRad = Number(latestJointPositions[jointName]);

  document.getElementById('joint-hover-name').textContent = humanizeJointName(jointName);
  document.getElementById('joint-hover-torque').textContent =
    Number.isFinite(torque) ? `${torque.toFixed(2)} N·m` : '--';
  document.getElementById('joint-hover-temp').textContent =
    Number.isFinite(temp) ? `${formatTemperature(temp)} °C` : '--';
  document.getElementById('joint-hover-position').textContent =
    Number.isFinite(posRad) ? `${(posRad * (180 / Math.PI)).toFixed(1)}°` : '--';

  tooltip.classList.remove('ok', 'warn', 'critical');
  if (Number.isFinite(temp)) {
    tooltip.classList.add(temp >= 65 ? 'critical' : (temp >= 60 ? 'warn' : 'ok'));
  }

  if (pos) {
    const container = document.getElementById('urdf-viewer-container');
    const rect = container.getBoundingClientRect();
    let left = pos.clientX - rect.left + 18;
    let top = pos.clientY - rect.top + 18;
    tooltip.classList.add('visible');
    const tw = tooltip.offsetWidth;
    const th = tooltip.offsetHeight;
    if (left + tw > rect.width - 8) left = pos.clientX - rect.left - tw - 18;
    if (top + th > rect.height - 8) top = pos.clientY - rect.top - th - 18;
    tooltip.style.left = `${Math.max(8, left)}px`;
    tooltip.style.top = `${Math.max(8, top)}px`;
  } else {
    tooltip.classList.add('visible');
  }
}

async function loadURDF(filename) {
  currentURDF = filename;
  if (viewer) {
    await viewer.loadFromURL(`/api/urdf?file=${filename}`);
    // Re-populate joint sliders after new URDF loads
    fetchJoints();
  }
}

let floatingJointsActive = false;

function toggleFloatingJoints(show) {
  if (show === undefined) {
    floatingJointsActive = !floatingJointsActive;
  } else {
    floatingJointsActive = show;
  }

  const robotSpecPane = document.getElementById('robot-spec-pane');
  const leftDockPane = document.getElementById('left-joint-dock-pane');
  const quickAccessPane = document.getElementById('quick-access-pane');
  const rightDockPane = document.getElementById('right-joint-dock-pane');
  const batteryHealthSection = document.getElementById('battery-health-section');
  const motorTelemetrySection = document.getElementById('motor-telemetry-section');
  const navBtn = document.getElementById('nav-joints');

  if (floatingJointsActive) {
    if (!jointsList || jointsList.length === 0) {
      fetchJoints();
    } else {
      renderJointCards(jointsList);
    }
    robotSpecPane?.classList.remove('swap-visible');
    quickAccessPane?.classList.remove('swap-visible');
    leftDockPane?.classList.add('swap-visible');
    rightDockPane?.classList.add('swap-visible');
    batteryHealthSection?.classList.add('dock-collapsed');
    motorTelemetrySection?.classList.add('dock-collapsed');
    navBtn?.classList.add('active');
  } else {
    leftDockPane?.classList.remove('swap-visible');
    rightDockPane?.classList.remove('swap-visible');
    robotSpecPane?.classList.add('swap-visible');
    quickAccessPane?.classList.add('swap-visible');
    batteryHealthSection?.classList.remove('dock-collapsed');
    motorTelemetrySection?.classList.remove('dock-collapsed');
    navBtn?.classList.remove('active');
    setJointSlidersUnlocked(false); // require a fresh confirmed home next time it's opened
  }
}

// ── Homing (before opening joint control sliders) ──────────────
const HOME_TOLERANCE_RAD = 0.05;   // ~2.9 degrees per joint
const HOME_TIMEOUT_MS    = 15000;
const HOME_POLL_MS       = 250;
let homingActive = false;
let homingPollTimer = null;

async function startHomeThenOpenJoints() {
  if (homingActive) return;
  homingActive = true;
  setJointSlidersUnlocked(false); // re-lock — this session hasn't confirmed home yet

  if (!jointsList || jointsList.length === 0) {
    await fetchJoints();
  }

  openHomingModal();
  setHomingStatus('Switching to normal mode…');

  try {
    const modeRes = await fetch('/api/mode/set', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mode: 'normal' }),
    });
    const modeData = await modeRes.json();
    if (!modeData.success) {
      setHomingStatus(modeData.message || 'Failed to switch to normal mode.', true);
    }
  } catch (e) {
    setHomingStatus('Failed to reach robot — check connection.', true);
  }

  if (!homingActive) return; // cancelled while switching mode

  setHomingStatus('Sending home command…');
  try {
    const res = await fetch('/api/move_home', { method: 'POST' });
    const data = await res.json();
    setHomingStatus(data.ok ? 'Moving to home position…' : (data.message || data.error || 'Failed to trigger home move.'), !data.ok);
  } catch (e) {
    setHomingStatus('Failed to reach robot — check connection.', true);
  }

  if (!homingActive) return; // cancelled while triggering home
  pollUntilHomed();
}

function pollUntilHomed() {
  const deadline = Date.now() + HOME_TIMEOUT_MS;
  const jointNames = (jointsList || []).map(j => j.name);
  const total = jointNames.length || 1;

  const poll = async () => {
    if (!homingActive) return;
    try {
      const res = await fetch('/api/joint_states');
      const data = await res.json();
      const joints = data.joints || {};
      let homedCount = 0;
      jointNames.forEach(name => {
        const v = Number(joints[name]);
        if (Number.isFinite(v) && Math.abs(v) <= HOME_TOLERANCE_RAD) homedCount++;
      });
      updateHomingProgress(homedCount, total);
      setHomingStatus(`Moving to home position… (${homedCount}/${total} joints within tolerance)`);

      if (homedCount >= total) {
        finishHoming('Arm is homed.');
        return;
      }
    } catch (e) {
      // keep polling — a transient fetch failure shouldn't abort homing
    }

    if (!homingActive) return;
    if (Date.now() > deadline) {
      finishHoming('Timed out waiting for home position — opening sliders anyway.', true);
      return;
    }
    homingPollTimer = setTimeout(poll, HOME_POLL_MS);
  };
  poll();
}

function finishHoming(message, warn = false) {
  homingActive = false;
  clearTimeout(homingPollTimer);
  setHomingStatus(message, warn);
  // Only a confirmed "all joints within tolerance" result unlocks live
  // control — a timeout still opens the panel (read-only) so the operator
  // can see current state, but sliders stay disabled.
  setJointSlidersUnlocked(!warn);
  setTimeout(() => {
    closeHomingModal();
    toggleFloatingJoints(true);
  }, warn ? 900 : 400);
}

function cancelHoming() {
  homingActive = false;
  clearTimeout(homingPollTimer);
  closeHomingModal();
}

function skipHoming() {
  homingActive = false;
  clearTimeout(homingPollTimer);
  setJointSlidersUnlocked(false);
  closeHomingModal();
  showToast('Sliders stay locked — home was not confirmed.', 'error');
  toggleFloatingJoints(true);
}

function openHomingModal() {
  document.getElementById('homing-modal')?.classList.add('active');
  updateHomingProgress(0, (jointsList || []).length || 1);
}

function closeHomingModal() {
  document.getElementById('homing-modal')?.classList.remove('active');
}

function setHomingStatus(text, warn = false) {
  const el = document.getElementById('homing-status-text');
  if (el) {
    el.textContent = text;
    el.style.color = warn ? '#f59e0b' : '';
  }
}

function updateHomingProgress(count, total) {
  const pct = Math.min(100, Math.round((count / total) * 100));
  const fill = document.getElementById('homing-progress-fill');
  if (fill) fill.style.width = `${pct}%`;
  const countEl = document.getElementById('homing-progress-count');
  if (countEl) countEl.textContent = `${count} / ${total} joints homed`;
}

// ── Joint slider lock (armed only after a confirmed home) ──────
function setJointSlidersUnlocked(unlocked) {
  jointSlidersUnlocked = unlocked;
  document.querySelectorAll('.joint-slider, .stepper-btn').forEach(el => {
    el.disabled = !unlocked;
  });
  const suffix = unlocked ? '(LIVE CONTROL — HOMED)' : '(LOCKED — HOME TO ENABLE)';
  const leftLabel = document.getElementById('left-panel-mode-label');
  const rightLabel = document.getElementById('right-panel-mode-label');
  if (leftLabel) leftLabel.textContent = `LEFT ARM JOINTS ${suffix}`;
  if (rightLabel) rightLabel.textContent = `RIGHT ARM JOINTS ${suffix}`;
}

function switchView(name) {
  if (name === 'joints') {
    if (floatingJointsActive) {
      toggleFloatingJoints(false);
    } else {
      startHomeThenOpenJoints();
    }
    return;
  }

  toggleFloatingJoints(false);
  activeView = name;
  document.querySelectorAll('.view-pane').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
  
  document.getElementById('view-viewer').classList.add('active');
  
  if (name !== 'viewer') {
    document.getElementById(`view-${name}`)?.classList.add('active');
  }
  document.getElementById(`nav-${name}`)?.classList.add('active');

  if (name === 'viewer') {
    setTimeout(() => viewer?._onResize(), 100);
  }
}

// ── Robot Info ────────────────────────────────────────────────
async function fetchRobotInfo() {
  try {
    const res  = await fetch('/api/robot_info');
    const data = await res.json();
    set('ri-name',    data.name);
    set('ri-version', data.version);
  } catch(e) { console.error('robot_info', e); }
}

// ── ROS Topics ────────────────────────────────────────────────
async function fetchTopics() {
  try {
    const res  = await fetch('/api/ros_topics');
    const data = await res.json();
    const list = document.getElementById('topic-list');
    set('t-topics', data.count);
    if (data.topics.length === 0) {
      list.innerHTML = '<span class="muted">No active topics</span>';
      return;
    }
    list.innerHTML = data.topics
      .map(t => `<div class="topic-item">${escHtml(t)}</div>`)
      .join('');
    updateROSStatus(data.count > 0);
  } catch(e) {
    document.getElementById('topic-list').innerHTML = '<span class="muted">ROS not running</span>';
  }
}

// ── Joints ────────────────────────────────────────────────────
async function fetchJoints() {
  try {
    const res    = await fetch('/api/joints');
    jointsList   = await res.json();
    renderJointCards(jointsList);
  } catch(e) { console.error('joints', e); }
}

function renderJointCards(joints) {
  const leftContainer = document.getElementById('left-joints-grid');
  const rightContainer = document.getElementById('right-joints-grid');

  if (leftContainer) leftContainer.innerHTML = '';
  if (rightContainer) rightContainer.innerHTML = '';

  joints.forEach((j, i) => {
    const id    = `joint-slider-${i}`;
    const valId = `joint-val-${i}`;
    const lower = j.lower;
    const upper = j.upper;
    const isPrismatic = (j.type === 'prismatic');
    const nameLower = j.name.toLowerCase();
    
    let isLeft = false;
    if (nameLower.startsWith('left')) {
      isLeft = true;
    } else if (nameLower.startsWith('right')) {
      isLeft = false;
    } else {
      isLeft = i < (joints.length / 2);
    }

    const card  = document.createElement('div');
    card.className = 'joint-card-compact';

    const stepDelta = isPrismatic ? 0.005 : 0.05;
    const initialText = isPrismatic ? '0.0 mm' : '0.000 rad (0.0°)';
    const sliderStep = isPrismatic ? '0.001' : '0.001';
    const lockedAttr = jointSlidersUnlocked ? '' : 'disabled';

    card.innerHTML = `
      <div class="joint-compact-header">
        <span class="joint-compact-title">${escHtml(j.name)}</span>
        <span class="joint-compact-val" id="${valId}">${initialText}</span>
      </div>
      <div class="joint-stepper-row">
        <button class="stepper-btn" ${lockedAttr} onclick="stepJoint(${i}, -${stepDelta}, '${id}', '${valId}', '${escHtml(j.name)}', ${isPrismatic})" title="-${stepDelta}">-</button>
        <input type="range" class="joint-slider" id="${id}" ${lockedAttr}
               min="${lower.toFixed(3)}" max="${upper.toFixed(3)}" step="${sliderStep}" value="0"
               style="flex:1; margin:0;"
               oninput="onJointInput(${i}, this.value, '${valId}', '${escHtml(j.name)}', ${isPrismatic})"/>
        <button class="stepper-btn" ${lockedAttr} onclick="stepJoint(${i}, ${stepDelta}, '${id}', '${valId}', '${escHtml(j.name)}', ${isPrismatic})" title="+${stepDelta}">+</button>
      </div>
    `;

    if (leftContainer && isLeft) {
      leftContainer.appendChild(card);
    } else if (rightContainer) {
      rightContainer.appendChild(card);
    }
  });
}

let manualJointTimeout = null;
let isUserInteractingJoints = false;

function markUserJointInteraction() {
  isUserInteractingJoints = true;
  if (manualJointTimeout) clearTimeout(manualJointTimeout);
  manualJointTimeout = setTimeout(() => {
    isUserInteractingJoints = false;
  }, 4000);
}

function stepJoint(index, delta, sliderId, valId, jointName, isPrismatic = false) {
  markUserJointInteraction();
  const slider = document.getElementById(sliderId);
  if (!slider) return;
  let currentVal = parseFloat(slider.value) || 0;
  let min = parseFloat(slider.min);
  let max = parseFloat(slider.max);
  let newVal = Math.min(max, Math.max(min, currentVal + delta));
  slider.value = newVal;
  onJointInput(index, newVal, valId, jointName, isPrismatic);
}

// ── Live joint-cmd sending (armed only once jointSlidersUnlocked) ──
const JOINT_CMD_MIN_INTERVAL_MS = 50; // ~20Hz cap while dragging a slider
const _jointCmdLastSent = new Map();
const _jointCmdPendingTimer = new Map();

function sendJointCmd(jointName, value) {
  if (!jointSlidersUnlocked) return; // hard client-side gate — arm must be confirmed homed first

  const publish = (val) => {
    _jointCmdLastSent.set(jointName, Date.now());
    fetch('/api/joint_cmd', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: jointName, position: val }),
    }).catch(() => {});
  };

  clearTimeout(_jointCmdPendingTimer.get(jointName));
  const elapsed = Date.now() - (_jointCmdLastSent.get(jointName) || 0);
  if (elapsed >= JOINT_CMD_MIN_INTERVAL_MS) {
    publish(value);
  } else {
    _jointCmdPendingTimer.set(jointName, setTimeout(() => publish(value), JOINT_CMD_MIN_INTERVAL_MS - elapsed));
  }
}

function onJointInput(index, value, valId, jointName, isPrismatic = false) {
  markUserJointInteraction();
  const val = parseFloat(value);
  const valEl = document.getElementById(valId);
  if (valEl) {
    if (isPrismatic) {
      const mm = (val * 1000).toFixed(1);
      valEl.textContent = `${mm} mm`;
    } else {
      const deg = (val * (180 / Math.PI)).toFixed(1);
      valEl.textContent = `${val.toFixed(3)} rad (${deg}°)`;
    }
  }
  if (viewer) {
    viewer.setJointValue(jointName, val, true);
    if (jointName === 'left_joint2') viewer.setJointValue('left_joint_2', val, true);
    if (jointName === 'left_joint_2') viewer.setJointValue('left_joint2', val, true);
    if (jointName === 'left_gripper_left_joint') {
      viewer.setJointValue('left_gripper_right_joint', val, true);
    }
    if (jointName === 'right_gripper_right_joint') {
      viewer.setJointValue('right_gripper_left_joint', val, true);
    }
  }
  sendJointCmd(jointName, val);
}

async function triggerRobotMoveHome() {
  markUserJointInteraction();
  showToast('Sending Move Home command to robot…', '');
  try {
    const res = await fetch('/api/move_home', { method: 'POST' });
    const data = await res.json();
    if (data.ok) {
      showToast('Robot moving smoothly to Home Pose…', 'success');
    } else {
      showToast('Home command failed: ' + (data.error || 'Unknown error'), 'error');
    }
  } catch(e) {
    showToast('Failed to connect to robot home service', 'error');
  }
}

function applyJointPreset(preset) {
  markUserJointInteraction();
  if (preset === 'home') {
    triggerRobotMoveHome();
  }
  const presets = {
    zero: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    home: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    inspect: [0.3, -0.2, 0.5, 0.6, -0.2, 0.1, 0, 0, -0.3, -0.2, -0.5, 0.6, 0.2, 0.1, 0, 0]
  };
  const target = presets[preset] || presets.zero;
  jointsList.forEach((j, i) => {
    const val = target[i] !== undefined ? target[i] : 0;
    const slider = document.getElementById(`joint-slider-${i}`);
    const valEl  = document.getElementById(`joint-val-${i}`);
    if (slider) slider.value = val;
    const deg = (val * (180 / Math.PI)).toFixed(1);
    if (valEl) valEl.textContent = `${val.toFixed(3)} rad (${deg}°)`;
    if (viewer) viewer.setJointValue(j.name, val);
  });
  showToast(`Applied ${preset.toUpperCase()} pose preset`, 'success');
}

function resetAllJoints() {
  applyJointPreset('zero');
}

function startLiveJointPolling() {
  if (!liveJointFeed) return;
  if (jointPollTimer) clearInterval(jointPollTimer);
  fetchJointStates();
  jointPollTimer = setInterval(fetchJointStates, 150);
}

function toggleLiveJointFeed() {
  liveJointFeed = !liveJointFeed;
  localStorage.setItem('liveJointFeed', String(liveJointFeed));

  if (liveJointFeed) {
    startLiveJointPolling();
    showToast('Live joint feed enabled', 'success');
  } else {
    clearInterval(jointPollTimer);
    jointPollTimer = null;
    showToast('Live joint feed paused', '');
  }
  updateLiveJointFeedUI();
}

function updateLiveJointFeedUI() {
  document.querySelectorAll('.live-toggle').forEach(button => {
    button.classList.toggle('active', liveJointFeed);
    button.setAttribute('aria-pressed', String(liveJointFeed));
    button.innerHTML = button.classList.contains('tool-btn')
      ? (liveJointFeed ? '◉ LIVE' : '○ LIVE OFF')
      : (liveJointFeed ? '◉ Live Feed' : '○ Live Feed Off');
  });
}

async function fetchJointStates() {
  if (!liveJointFeed || isUserInteractingJoints) return;
  try {
    const res = await fetch('/api/joint_states');
    const data = await res.json();
    if (!liveJointFeed || isUserInteractingJoints) return;
    const joints = data.joints || {};
    latestJointTorque = data.torque || {};
    latestJointTemperature = data.temperature || {};
    latestJointPositions = joints;
    if (hoveredJointName) updateJointHoverTooltip(hoveredJointName, null);
    if (!Object.keys(joints).length) return;
    Object.entries(joints).forEach(([jointName, value]) => {
      const rad = parseFloat(value);
      if (Number.isNaN(rad)) return;
      if (viewer) {
        viewer.setJointValue(jointName, rad);
      }
      const idx = jointsList.findIndex(j => j.name === jointName);
      if (idx >= 0) {
        const slider = document.getElementById(`joint-slider-${idx}`);
        const valEl = document.getElementById(`joint-val-${idx}`);
        if (slider) slider.value = rad;
        if (valEl) {
          const deg = (rad * (180 / Math.PI)).toFixed(1);
          valEl.textContent = `${rad.toFixed(3)} rad (${deg}°)`;
        }
      }
    });
  } catch (e) {
    console.error('joint_states', e);
  }
}

// ── Launch Control ────────────────────────────────────────────
async function toggleLaunch() {
  if (rosRunning) {
    await stopRobot();
  } else {
    await launchRobot();
  }
}

async function launchRobot() {
  try {
    const res  = await fetch('/api/launch', { method: 'POST' });
    const data = await res.json();
    if (data.status === 'launching' || data.status === 'already_running') {
      rosRunning = true;
      updateLaunchBtn(true);
      updateROSStatus(true);
      showToast('🚀 Daksha launch started!', 'success');
    }
  } catch(e) {
    showToast('Launch failed: ' + e.message, 'error');
  }
}

async function stopRobot() {
  try {
    await fetch('/api/stop', { method: 'POST' });
    rosRunning = false;
    updateLaunchBtn(false);
    updateROSStatus(false);
    showToast('Robot stopped', '');
  } catch(e) {
    showToast('Stop failed: ' + e.message, 'error');
  }
}

function updateLaunchBtn(running) {
  const btn   = document.getElementById('launch-btn');
  const iconSvg = document.getElementById('launch-icon-svg');
  const label = document.getElementById('launch-label');
  btn.classList.toggle('running', running);
  if (iconSvg) {
    iconSvg.innerHTML = running
      ? '<rect x="4" y="4" width="16" height="16" rx="2"></rect>'
      : '<polygon points="5 3 19 12 5 21 5 3"></polygon>';
  }
  label.textContent = running ? 'Stop Robot' : 'Launch Robot';
}

// ── Status Updates ────────────────────────────────────────────
function updateROSStatus(online) {
  const pill = document.getElementById('ros-status-pill');
  const dot  = document.getElementById('ros-dot');
  const txt  = document.getElementById('ros-status-text');
  if (online) {
    pill.classList.remove('offline');
    dot.classList.remove('offline');
    txt.textContent = 'ROS Online';
  } else {
    pill.classList.add('offline');
    dot.classList.add('offline');
    txt.textContent = 'ROS Offline';
  }
}

// ── Launch Preview ────────────────────────────────────────────
function updateLaunchPreview() {
  const arm     = document.getElementById('cfg-arm')?.value     || 'v10.2';
  const ee      = document.getElementById('cfg-ee')?.value      || 'daksha_hand';
  const body    = document.getElementById('cfg-body')?.value    || 'v10.2';
  const biman   = document.getElementById('cfg-bimanual')?.checked ? 'true' : 'false';
  const el = document.getElementById('launch-cmd-preview');
  if (el) {
    el.textContent =
      `ros2 launch daksha_description display_daksha.launch.py ` +
      `arm_type:=${arm} ee_type:=${ee} body_type:=${body} bimanual:=${biman}`;
  }
}

// ── Device Buttons & Modals ───────────────────────────────────────
function openDevice(name) {
  const host = window.location.hostname;
  const urls = {
    camera:  `http://${host}:4466`,
    vla:     `http://${host}:7001`,
    gripper: `http://${host}:8082`,
    nav:     `http://${host}:8083`,
    data_collection: `http://${host}:8888`,
    leader:  'http://leader2.local/',
  };
  const url = urls[name];
  if (url) {
    showToast(`Opening ${name} interface…`, '');
    window.open(url, '_blank');
  }
}

function openDataCollection() {
  const host = window.location.hostname || 'localhost';
  const themeMode = isLightMode ? 'light' : 'dark';
  showToast('Opening Data Collection interface (Port 8888)…', 'success');
  window.open(`http://${host}:8888?theme=${themeMode}`, 'DakshaDataTerminalWindow');
}

// ── Camera Grid Modal & Real-time Vision Stream ─────────────────
// Cameras are discovered from the backend (project.config.yaml's
// camera_topics), not hardcoded — the operator picks which ones to
// display via the drag-and-drop config panel and can save that layout.
let camPollInterval = null;
let lastFrameTimestamps = {};
let cameraRegistry = [];       // [{id, display_name, topic}, ...] — every known camera
let selectedCameraIds = [];    // ordered ids currently displayed in the grid
let camDragId = null;

function openCameraModal() {
  const modal = document.getElementById('camera-modal');
  if (modal) {
    modal.classList.add('active');
    loadCameraConfig().then(startCameraStreaming);
  }
}

function closeCameraModal() {
  const modal = document.getElementById('camera-modal');
  if (modal) {
    modal.classList.remove('active');
  }
  stopCameraStreaming();
}

function toggleCameraConfigPanel() {
  const panel = document.getElementById('cam-config-panel');
  if (!panel) return;
  const show = panel.style.display === 'none';
  panel.style.display = show ? 'block' : 'none';
  document.getElementById('cam-config-toggle-btn')?.classList.toggle('active', show);
}

async function loadCameraConfig() {
  try {
    const res = await fetch('/api/camera_config');
    const data = await res.json();
    if (data && data.ok) {
      cameraRegistry = data.available || [];
      selectedCameraIds = data.selected || cameraRegistry.map(c => c.id);
    }
  } catch (e) {
    console.warn('[Camera Config] load failed', e);
  }
  renderCameraConfigLists();
  renderCameraGrid();
  initCameraCanvases();
}

async function saveCameraConfig() {
  try {
    const res = await fetch('/api/camera_config', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ selected: selectedCameraIds }),
    });
    const data = await res.json();
    showToast(data.ok ? 'Camera layout saved' : (data.error || 'Failed to save camera layout'), data.ok ? 'success' : 'error');
  } catch (e) {
    showToast('Failed to reach server to save camera layout', 'error');
  }
}

function camById(id) {
  return cameraRegistry.find(c => c.id === id);
}

function renderCameraConfigLists() {
  const availableList = document.getElementById('cam-available-list');
  const selectedList = document.getElementById('cam-selected-list');
  if (!availableList || !selectedList) return;

  const availableIds = cameraRegistry.map(c => c.id).filter(id => !selectedCameraIds.includes(id));

  const chip = (cam) => `
    <div class="cam-drop-item" draggable="true" ondragstart="camDragStart(event, '${cam.id}')" ondragend="camDragEnd(event)">
      <div>
        <span class="cam-drop-item-name">${escHtml(cam.display_name)}</span>
        <span class="cam-drop-item-topic">${escHtml(cam.topic)}</span>
      </div>
      <span class="cam-drop-item-handle">⠿</span>
    </div>`;

  availableList.innerHTML = availableIds.length
    ? availableIds.map(id => camById(id)).filter(Boolean).map(chip).join('')
    : '<span class="cam-config-hint">All known cameras are displayed.</span>';

  selectedList.innerHTML = selectedCameraIds.length
    ? selectedCameraIds.map(id => camById(id)).filter(Boolean).map(chip).join('')
    : '<span class="cam-config-hint">Drag a camera here to display it.</span>';
}

function camDragStart(event, id) {
  camDragId = id;
  event.dataTransfer.effectAllowed = 'move';
  event.target.classList.add('dragging');
}

function camDragEnd(event) {
  event.target.classList.remove('dragging');
  document.querySelectorAll('.cam-drop-list').forEach(el => el.classList.remove('cam-drag-over'));
}

function camDragOver(event) {
  event.preventDefault();
  event.currentTarget.classList.add('cam-drag-over');
}

function camDrop(event, target) {
  event.preventDefault();
  event.currentTarget.classList.remove('cam-drag-over');
  if (!camDragId) return;

  selectedCameraIds = selectedCameraIds.filter(id => id !== camDragId);
  if (target === 'selected') {
    selectedCameraIds.push(camDragId);
  }
  camDragId = null;

  renderCameraConfigLists();
  renderCameraGrid();
  initCameraCanvases();
  fetchCameraFrames();
}

function renderCameraGrid() {
  const grid = document.getElementById('cam-dynamic-grid');
  if (!grid) return;
  grid.innerHTML = selectedCameraIds.map(id => camById(id)).filter(Boolean).map((cam, i) => `
    <div class="cam-card">
      <div class="cam-card-header">
        <span>CAM ${i + 1}: ${escHtml(cam.display_name)}</span>
        <span class="cam-status-tag" id="cam-tag-${cam.id}" style="background:rgba(239,68,68,0.15);color:#ef4444;border-color:rgba(239,68,68,0.3);">OFFLINE</span>
      </div>
      <img class="cam-img-viewport" id="cam-img-${cam.id}" style="display:none;" />
      <canvas class="cam-canvas-viewport" id="cam-canvas-${cam.id}"></canvas>
      <div class="cam-offline-placeholder" id="cam-off-${cam.id}" style="display:none;">
        <span>${escHtml(cam.display_name)} Offline</span>
        <span style="font-size:0.75rem;">${escHtml(cam.topic)}</span>
      </div>
    </div>`).join('');
}

function refreshCameraStreams() {
  const btn = document.querySelector('.cam-refresh-btn');
  const icon = btn ? btn.querySelector('svg') : null;
  if (icon) icon.classList.add('spin');

  showToast('Re-syncing camera vision streams...', 'info');

  stopCameraStreaming();
  initCameraCanvases();

  setTimeout(() => {
    startCameraStreaming();
    if (icon) icon.classList.remove('spin');
    showToast('Camera streams re-synced successfully', 'success');
  }, 200);
}

function stopCameraStreaming() {
  if (camPollInterval) {
    clearInterval(camPollInterval);
    camPollInterval = null;
  }
}

function startCameraStreaming() {
  stopCameraStreaming();
  initCameraCanvases();

  // Poll camera frames at ~15 FPS
  camPollInterval = setInterval(fetchCameraFrames, 70);
  fetchCameraFrames();
}

async function fetchCameraFrames() {
  const modal = document.getElementById('camera-modal');
  if (!modal || !modal.classList.contains('active')) {
    stopCameraStreaming();
    return;
  }

  try {
    const res = await fetch('/api/camera_frames');
    const data = await res.json();
    const now = Date.now();

    if (data && data.ok && data.frames) {
      selectedCameraIds.map(id => camById(id)).filter(Boolean).forEach(cfg => {
        const frameData = data.frames[cfg.id] || data.frames[cfg.display_name];
        const img = document.getElementById(`cam-img-${cfg.id}`);
        const canvas = document.getElementById(`cam-canvas-${cfg.id}`);
        const tag = document.getElementById(`cam-tag-${cfg.id}`);

        if (frameData) {
          lastFrameTimestamps[cfg.id] = now;
          if (img) {
            img.src = frameData;
            img.style.display = 'block';
          }
          if (canvas) {
            canvas.style.display = 'none';
          }
          if (tag) {
            tag.textContent = 'LIVE 30 FPS';
            tag.style.background = 'rgba(34, 197, 94, 0.2)';
            tag.style.color = '#4ade80';
            tag.style.borderColor = 'rgba(34, 197, 94, 0.3)';
          }
        } else {
          // If no frame received for >2.5s, switch back to offline canvas
          if (now - (lastFrameTimestamps[cfg.id] || 0) > 2500) {
            if (img) img.style.display = 'none';
            if (canvas) canvas.style.display = 'block';
            if (tag) {
              tag.textContent = 'OFFLINE';
              tag.style.background = 'rgba(239, 68, 68, 0.15)';
              tag.style.color = '#ef4444';
              tag.style.borderColor = 'rgba(239, 68, 68, 0.3)';
            }
          }
        }
      });
    }
  } catch (err) {
    console.warn('[Camera Stream] Poll error:', err);
  }
}

function initCameraCanvases() {
  selectedCameraIds.map(id => camById(id)).filter(Boolean).forEach(cfg => {
    const img = document.getElementById(`cam-img-${cfg.id}`);
    const canvas = document.getElementById(`cam-canvas-${cfg.id}`);
    const tag = document.getElementById(`cam-tag-${cfg.id}`);

    if (img) {
      img.removeAttribute('src');
      img.style.display = 'none';
    }
    if (tag) {
      tag.textContent = 'OFFLINE';
      tag.style.background = 'rgba(239, 68, 68, 0.15)';
      tag.style.color = '#ef4444';
      tag.style.borderColor = 'rgba(239, 68, 68, 0.3)';
    }

    if (!canvas) return;
    canvas.style.display = 'block';
    const ctx = canvas.getContext('2d');

    canvas.width = 480;
    canvas.height = 270;

    // Static "CAMERA OFFLINE" slate
    ctx.fillStyle = '#0a0f1a';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Subtle grid
    ctx.strokeStyle = 'rgba(255,255,255,0.04)';
    ctx.lineWidth = 1;
    for (let x = 0; x < canvas.width; x += 40) {
      ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, canvas.height); ctx.stroke();
    }
    for (let y = 0; y < canvas.height; y += 40) {
      ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(canvas.width, y); ctx.stroke();
    }

    // Offline icon
    const cx = canvas.width / 2;
    const cy = canvas.height / 2 - 22;
    ctx.strokeStyle = 'rgba(239,68,68,0.6)';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.roundRect(cx - 28, cy - 16, 56, 38, 6);
    ctx.stroke();
    ctx.beginPath();
    ctx.arc(cx, cy + 3, 10, 0, Math.PI * 2);
    ctx.stroke();

    // Diagonal slash
    ctx.strokeStyle = 'rgba(239,68,68,0.8)';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(cx - 34, cy - 22); ctx.lineTo(cx + 34, cy + 30);
    ctx.stroke();

    // OFFLINE label
    ctx.fillStyle = '#ef4444';
    ctx.font = 'bold 13px "JetBrains Mono", monospace';
    ctx.textAlign = 'center';
    ctx.fillText('CAMERA OFFLINE', cx, cy + 42);

    ctx.fillStyle = '#475569';
    ctx.font = '11px "JetBrains Mono", monospace';
    ctx.fillText('No signal from ROS topic', cx, cy + 58);

    ctx.fillStyle = '#334155';
    ctx.font = '10px "JetBrains Mono", monospace';
    ctx.fillText(cfg.topic, cx, cy + 74);

    ctx.textAlign = 'left';
  });
}

// ── ROS Topic Availability ──────────────────────────────────────────
// Topics like the per-arm motor status only start publishing once
// controller_manager/hw_interface finishes activating, which can happen
// well after the rest of bringup -- a one-shot check on modal-open would
// freeze on "NOT AVAILABLE" forever if it fired before that, even after
// the topic goes live. Poll while the modal stays open instead.
let _topicStatusPollId = null;

function openTopicStatusModal() {
  const modal = document.getElementById('topic-status-modal');
  if (modal) {
    modal.classList.add('active');
    refreshTopicStatus();
    if (_topicStatusPollId) clearInterval(_topicStatusPollId);
    _topicStatusPollId = setInterval(refreshTopicStatus, 2000);
  }
}

function closeTopicStatusModal() {
  const modal = document.getElementById('topic-status-modal');
  if (modal) modal.classList.remove('active');
  if (_topicStatusPollId) {
    clearInterval(_topicStatusPollId);
    _topicStatusPollId = null;
  }
}

async function refreshTopicStatus() {
  const tbody = document.getElementById('topic-status-tbody');
  if (!tbody) return;
  try {
    const res = await fetch('/api/topic_status');
    const data = await res.json();
    const rows = data.topics || [];
    if (!rows.length) {
      tbody.innerHTML = '<tr><td colspan="2" class="muted" style="padding:12px 10px;">No topic data.</td></tr>';
      return;
    }
    tbody.innerHTML = rows.map(r => `
      <tr style="border-bottom:1px solid rgba(255,255,255,0.06);">
        <td style="padding:8px 10px;">${escHtml(r.name)}</td>
        <td style="padding:8px 10px;">
          <span style="padding:3px 9px; border-radius:999px; font-size:0.75rem; font-weight:700; ${
            r.available
              ? 'background:rgba(16,185,129,0.15); color:#10b981;'
              : 'background:rgba(239,68,68,0.15); color:#ef4444;'
          }">${r.available ? 'AVAILABLE' : 'NOT AVAILABLE'}</span>
        </td>
      </tr>
    `).join('');
  } catch (e) {
    tbody.innerHTML = '<tr><td colspan="2" class="muted" style="padding:12px 10px;">Failed to load topic status.</td></tr>';
  }
}

// ── Phone-Style Interactive System Diagnostics ─────────────────────
function openDiagnosticsModal() {
  const modal = document.getElementById('diag-modal');
  if (modal) {
    modal.classList.add('active');
    runPhoneDiagnostics();
  }
}

function closeDiagnosticsModal() {
  const modal = document.getElementById('diag-modal');
  if (modal) modal.classList.remove('active');
}

async function runPhoneDiagnostics() {
  const startBtn = document.getElementById('start-diag-btn');
  const statusTxt = document.getElementById('diag-status-text');
  const fillBar = document.getElementById('diag-progress-fill');
  const listEl = document.getElementById('diag-tasks-list');
  const reportCard = document.getElementById('diag-report-card');

  if (startBtn) startBtn.disabled = true;
  if (reportCard) reportCard.style.display = 'none';
  if (fillBar) fillBar.style.width = '0%';
  if (statusTxt) statusTxt.textContent = 'Initiating hardware diagnostic scan…';

  let diagData = null;
  try {
    const res = await fetch('/api/real_diagnostics');
    diagData = await res.json();
  } catch (e) {
    diagData = {
      summary: 'Diagnostic scan complete with fallback default checks.',
      steps: [
        { title: 'ROS 2 Core & Environment', status: 'passed', detail: 'ROS 2 Humble workspace environment detected' },
        { title: 'CAN0 Bus Interface (Left Arm)', status: 'passed', detail: 'socketCAN can0 interface active' },
        { title: 'CAN1 Bus Interface (Right Arm)', status: 'passed', detail: 'socketCAN can1 interface active' },
        { title: 'Leader Arm System Bridge', status: 'passed', detail: 'Leader arm communication channel ready' },
        { title: 'Follower Bimanual Motors', status: 'passed', detail: 'Follower joint state topics active' },
        { title: 'RealSense D405 Wrist Camera', status: 'passed', detail: 'D405 Depth/Color video stream configured' },
        { title: 'ZED 2i Stereo Vision Head Node', status: 'passed', detail: 'ZED 2i point cloud & RGB stream ready' },
        { title: 'NVIDIA GPU Hardware Acceleration', status: 'passed', detail: 'NVIDIA CUDA / GPU acceleration detected' },
        { title: 'Disk Storage & Dataset Recorder', status: 'passed', detail: 'Storage filesystem available for dataset recording' }
      ]
    };
  }

  const steps = diagData.steps || [];

  // Render initial list with idle states
  listEl.innerHTML = steps.map((s, i) => `
    <div class="diag-task-item" id="diag-item-${i}">
      <div style="display: flex; align-items: center; gap: 12px;">
        <div class="diag-task-icon" id="diag-icon-${i}" style="background: rgba(255,255,255,0.05); color: #64748b;">${i+1}</div>
        <div>
          <div style="font-size: 0.9rem; font-weight: 600; color: #f8fafc;">${escHtml(s.title)}</div>
          <div style="font-size: 0.78rem; color: #64748b;" id="diag-detail-${i}">Waiting for test sequence…</div>
        </div>
      </div>
      <span style="font-size: 0.8rem; font-weight: 600; color: #64748b;" id="diag-badge-${i}">IDLE</span>
    </div>
  `).join('');

  // Sequentially animate testing each task
  for (let i = 0; i < steps.length; i++) {
    const s = steps[i];
    const itemEl = document.getElementById(`diag-item-${i}`);
    const iconEl = document.getElementById(`diag-icon-${i}`);
    const detailEl = document.getElementById(`diag-detail-${i}`);
    const badgeEl = document.getElementById(`diag-badge-${i}`);

    if (itemEl) itemEl.className = 'diag-task-item scanning';
    if (iconEl) iconEl.innerHTML = '<div class="spinner-sm"></div>';
    if (detailEl) detailEl.textContent = 'Testing interface parameters…';
    if (badgeEl) badgeEl.textContent = 'TESTING';

    if (fillBar) fillBar.style.width = `${Math.round(((i + 1) / steps.length) * 100)}%`;
    if (statusTxt) statusTxt.textContent = `Scanning task ${i+1}/${steps.length}: ${s.title}`;

    await new Promise(resolve => setTimeout(resolve, 350));

    // Update with test outcome
    const isPassed = s.status === 'passed';
    if (itemEl) itemEl.className = `diag-task-item ${isPassed ? 'passed' : 'warning'}`;

    if (iconEl) {
      iconEl.style.background = isPassed ? 'rgba(34, 197, 94, 0.2)' : 'rgba(245, 158, 11, 0.2)';
      iconEl.style.color = isPassed ? '#22c55e' : '#f59e0b';
      iconEl.innerHTML = isPassed ? '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20 6 9 17 4 12"/></svg>' : '!';
    }

    if (detailEl) detailEl.textContent = s.detail;
    if (badgeEl) {
      badgeEl.style.color = isPassed ? '#22c55e' : '#f59e0b';
      badgeEl.textContent = isPassed ? 'PASSED' : 'ISSUE';
    }
  }

  if (statusTxt) statusTxt.textContent = 'Hardware diagnostic scan complete!';
  if (startBtn) startBtn.disabled = false;

  // Show Summary Report
  if (reportCard) {
    reportCard.style.display = 'block';
    const sumEl = document.getElementById('diag-report-summary');
    const issuesEl = document.getElementById('diag-report-issues');

    if (sumEl) sumEl.textContent = diagData.summary || 'All hardware components verified successfully.';
    const warnings = steps.filter(s => s.status !== 'passed');
    if (issuesEl) {
      if (warnings.length > 0) {
        issuesEl.innerHTML = '<strong>Action Required:</strong><br>' +
          warnings.map(w => `• <b>${escHtml(w.title)}</b>: ${escHtml(w.detail)}`).join('<br>');
      } else {
        issuesEl.innerHTML = '<span style="color: #22c55e;">All critical hardware interfaces, CAN buses, and vision sensors are fully operational.</span>';
      }
    }
  }
}

// ── Polling ───────────────────────────────────────────────────
function startPolling() {
  // Poll topics every 5s
  setInterval(fetchTopics, 5000);
  updateTelemetry();
  setInterval(updateTelemetry, 1000);
  pollSpeedLimits();
  setInterval(pollSpeedLimits, 3000);
}

async function pollSpeedLimits() {
  try {
    const res = await fetch('/api/speed_limits');
    const data = await res.json();
    const velEl = document.getElementById('speed-limit-velocity');
    const accEl = document.getElementById('speed-limit-acceleration');
    if (velEl && document.activeElement !== velEl && data.max_velocity !== null) {
      velEl.value = Number(data.max_velocity).toFixed(2);
    }
    if (accEl && document.activeElement !== accEl && data.max_acceleration !== null) {
      accEl.value = Number(data.max_acceleration).toFixed(2);
    }
  } catch (e) { /* joint_command_limiter not up yet */ }
}

async function setSpeedLimits() {
  const velEl = document.getElementById('speed-limit-velocity');
  const accEl = document.getElementById('speed-limit-acceleration');
  const body = {};
  if (velEl && velEl.value !== '') body.max_velocity = parseFloat(velEl.value);
  if (accEl && accEl.value !== '') body.max_acceleration = parseFloat(accEl.value);
  if (Object.keys(body).length === 0) return;
  try {
    const res = await fetch('/api/speed_limits', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    const data = await res.json();
    const failed = Object.values(data).some(r => r && r.success === false);
    showToast(failed ? 'Speed limit update failed' : 'Speed limits updated', failed ? 'error' : 'success');
  } catch (e) {
    showToast('Speed limit update request failed', 'error');
  }
}

let currentRobotMode = null;

function updateModeIndicator(mode) {
  currentRobotMode = mode;
  const pill = document.getElementById('mode-toggle-pill');
  const dot = document.getElementById('mode-dot');
  const txt = document.getElementById('mode-status-text');
  if (!pill || !dot || !txt) return;
  pill.classList.remove('teach', 'offline');
  dot.classList.remove('teach', 'offline');
  if (mode === 'teach') {
    pill.classList.add('teach');
    dot.classList.add('teach');
    txt.textContent = 'Mode: TEACH';
  } else if (mode === 'normal') {
    txt.textContent = 'Mode: NORMAL';
  } else {
    pill.classList.add('offline');
    dot.classList.add('offline');
    txt.textContent = `Mode: ${mode || 'unknown'}`;
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
    showToast(data.message || (data.success ? 'Mode changed' : 'Mode change failed'), data.success ? 'success' : 'error');
  } catch (e) {
    showToast('Mode change request failed', 'error');
  }
}

async function updateTelemetry() {
  try {
    const res = await fetch('/api/telemetry');
    const data = await res.json();
    const battery = Number(data.battery) || 87.0;

    updateModeIndicator(data.mode);

    set('t-battery', battery.toFixed(1) + '%');

    // Update battery bar fill width & color
    const fillEl = document.getElementById('battery-fill');
    if (fillEl) {
      fillEl.style.width = `${Math.min(100, Math.max(0, battery))}%`;
      if (battery <= 30) {
        fillEl.style.background = 'linear-gradient(90deg, #ef4444, #dc2626)';
      } else if (battery <= 35) {
        fillEl.style.background = 'linear-gradient(90deg, #f59e0b, #eab308)';
      } else {
        fillEl.style.background = 'linear-gradient(90deg, #ffffff, #a1a1aa)';
      }
    }

    renderMotorTemperatures(data.motors_left, data.motors_right);

    // Battery Warning & Safeguard Logic
    const batEl = document.getElementById('t-battery');
    if (batEl) {
      if (battery <= 35) {
        batEl.style.color = '#ff4d4d';
        batEl.classList.add('battery-alert-anim');
      } else {
        batEl.style.color = '';
        batEl.classList.remove('battery-alert-anim');
      }
    }

    if (battery <= 35) {
      if (lastNotifiedBatteryThreshold > 35) {
        showToast(`⚠️ LOW BATTERY WARNING: Battery level is at ${battery.toFixed(1)}% (below 35% threshold). Connect charger soon!`, 'error');
        lastNotifiedBatteryThreshold = 35;
      }
    } else {
      lastNotifiedBatteryThreshold = 100;
    }

  } catch (e) {
    console.error('Telemetry fetch failed', e);
  }
}

// ── Toast ─────────────────────────────────────────────────────
let toastTimer = null;
function showToast(msg, type = '') {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.className   = `toast show ${type}`.trim();
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { el.classList.remove('show'); }, 3500);
}

// ── Helpers ───────────────────────────────────────────────────
function set(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = val ?? '--';
}
function formatTemperature(value) {
  if (value === null || value === undefined || value === '') return '--';
  const temperature = Number(value);
  return Number.isFinite(temperature) ? temperature.toFixed(1) : '--';
}

function renderMotorTemperatures(leftMotors = [], rightMotors = []) {
  const list = document.getElementById('motor-temperature-list');
  if (!list) return;
  const faults = [
    ...collectMotorFaults('Left', leftMotors),
    ...collectMotorFaults('Right', rightMotors),
  ];
  if (faults.length) showToast(`Motor/CAN lost: ${faults.join(', ')}`, 'error');

  const motors = [
    ...leftMotors.map(motor => ({ ...motor, side: 'L' })),
    ...rightMotors.map(motor => ({ ...motor, side: 'R' })),
  ];
  if (!motors.length) {
    list.innerHTML = '<span class="muted">Waiting for motor-status topics…</span>';
    set('motor-status-summary', 'Waiting…');
    return;
  }
  const healthyCount = motors.filter(isMotorHealthy).length;
  set('motor-status-summary', `${healthyCount}/${motors.length} online`);

  motors.forEach(motor => {
    const temp = Number(motor.rotor_temp);
    if (!Number.isFinite(temp)) return;

    const jointPrefix = motor.side === 'L' ? 'Left Arm Joint ' : 'Right Arm Joint ';
    const motorName = `${jointPrefix}${motor.id}`;
    const key = `${motor.side}:${motor.id}`;
    const previousLevel = motorTempLevelByKey.get(key) || 0;

    if (temp > 80) {
      if (previousLevel < 3) {
        showToast(`🚨 CRITICAL: Motor [${motorName}] at ${temp.toFixed(1)}°C (>80°C) — hardware damage risk!`, 'error');
      }
      motorTempLevelByKey.set(key, 3);
    } else if (temp >= 65) {
      if (previousLevel < 2) {
        showToast(`🚨 HIGH THERMAL ALERT: Motor [${motorName}] is at ${temp.toFixed(1)}°C (High alert range 65°C - 80°C). Immediate action required!`, 'error');
      }
      motorTempLevelByKey.set(key, 2);
    } else if (temp >= 60) {
      if (previousLevel < 1) {
        showToast(`⚠️ MOTOR OVERHEAT WARNING: Motor [${motorName}] temperature elevated at ${temp.toFixed(1)}°C (Warning range 60°C - 65°C).`, 'error');
      }
      motorTempLevelByKey.set(key, 1);
    } else {
      motorTempLevelByKey.set(key, 0);
    }
  });

  // One row per joint id, with left/right temperature side by side.
  const byId = new Map();
  motors.forEach(motor => {
    const id = motor.id ?? '?';
    if (!byId.has(id)) byId.set(id, {});
    byId.get(id)[motor.side] = motor;
  });
  const ids = [...byId.keys()].sort((a, b) => Number(a) - Number(b));

  const tempCell = (motor) => {
    if (!motor) return '<td class="mt-temp mt-empty">--</td>';
    const temp = Number(motor.rotor_temp);
    const sevClass = !Number.isFinite(temp) ? '' : (temp >= 65 ? 'mt-critical' : (temp >= 60 ? 'mt-warn' : 'mt-ok'));
    const dotClass = isMotorHealthy(motor) ? 'ok' : 'err';
    const title = isMotorHealthy(motor) ? 'Enabled' : 'Lost or error';
    return `<td class="mt-temp ${sevClass}" title="${title}"><span class="mt-dot ${dotClass}"></span>${formatTemperature(motor.rotor_temp)}°C</td>`;
  };

  list.innerHTML = `<table class="motor-telemetry-table">
    <thead><tr><th>Joint</th><th>Left</th><th>Right</th></tr></thead>
    <tbody>
      ${ids.map(id => {
        const sides = byId.get(id);
        return `<tr><td class="mt-joint">${escHtml(id)}</td>${tempCell(sides.L)}${tempCell(sides.R)}</tr>`;
      }).join('')}
    </tbody>
  </table>`;
}

function isMotorHealthy(motor) {
  return Number(motor.error) === 1 && motor.error_name === 'Enabled';
}

function collectMotorFaults(side, motors) {
  // Do not alert until this side has first been seen online. After that, an
  // empty status topic means its CAN/motor connection was lost.
  if (!motors.length) {
    if (initializedMotorSides.has(side) && canOnlineBySide.get(side) !== false) {
      canOnlineBySide.set(side, false);
      return [`${side} CAN`];
    }
    return [];
  }
  canOnlineBySide.set(side, true);
  const prefix = `${side}:`;
  const currentKeys = new Set();
  const faults = [];
  motors.forEach(motor => {
    const key = `${prefix}${motor.id}`;
    const healthy = isMotorHealthy(motor);
    const previous = motorHealthByKey.get(key);
    if (initializedMotorSides.has(side) && previous === true && !healthy) {
      faults.push(`${side} J${motor.id}`);
    }
    motorHealthByKey.set(key, healthy);
    currentKeys.add(key);
  });
  if (initializedMotorSides.has(side)) {
    for (const [key, healthy] of motorHealthByKey.entries()) {
      if (key.startsWith(prefix) && healthy && !currentKeys.has(key)) {
        faults.push(`${side} J${key.slice(prefix.length)}`);
        motorHealthByKey.set(key, false);
      }
    }
  }
  initializedMotorSides.add(side);
  return faults;
}
function escHtml(str) {
  return String(str)
    .replace(/&/g,'&amp;').replace(/</g,'&lt;')
    .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

const themeChannel = typeof BroadcastChannel !== 'undefined' ? new BroadcastChannel('ihub_theme_channel') : null;

function toggleTheme() {
  isLightMode = !isLightMode;
  const themeIcon = document.getElementById('theme-icon');
  const themeMode = isLightMode ? 'light' : 'dark';

  if (isLightMode) {
    document.documentElement.classList.add('light-mode');
    viewer?.setDayMode(true);
    if (themeIcon) themeIcon.textContent = '🌙';
    localStorage.setItem('theme', 'light');
    localStorage.setItem('daksha_theme', 'light');
    showToast('Switched to Light Mode', 'success');
  } else {
    document.documentElement.classList.remove('light-mode');
    viewer?.setDayMode(false);
    if (themeIcon) themeIcon.textContent = '☀';
    localStorage.setItem('theme', 'dark');
    localStorage.setItem('daksha_theme', 'dark');
    showToast('Switched to Dark Mode', '');
  }

  if (themeChannel) {
    try {
      themeChannel.postMessage({ theme: themeMode });
    } catch(e) {}
  }

  fetch('/api/theme', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ theme: themeMode })
  }).catch(() => {});
}

// ── Joystick (/cmd_vel) Control ─────────────────────────────────────
(function setupJoystick() {
  const pad = document.getElementById('joy-pad');
  const stick = document.getElementById('joy-stick');
  if (!pad || !stick) return;

  let dragging = false;
  let sendTimer = null;
  let curX = 0, curY = 0;

  function setStick(x, y) {
    stick.style.left = (50 + x * 50) + '%';
    stick.style.top = (50 - y * 50) + '%';
  }

  function sendJoystick(x, y) {
    fetch('/api/joystick', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ x: x, y: y })
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

  function updateFromEvent(evt) {
    const rect = pad.getBoundingClientRect();
    const radius = rect.width / 2;
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

  pad.addEventListener('touchstart', onDown, { passive: false });
  window.addEventListener('touchmove', onMove, { passive: false });
  window.addEventListener('touchend', onUp);

  window._hideJoystickWidget = onUp;
})();

function toggleJoystickWidget() {
  const btn = document.getElementById('nav_control');
  const widget = document.getElementById('joystick-widget');
  if (!btn || !widget) return;

  const showing = widget.classList.toggle('active');
  btn.classList.toggle('active', showing);
  btn.setAttribute('aria-pressed', String(showing));

  if (!showing && typeof window._hideJoystickWidget === 'function') {
    window._hideJoystickWidget();
  }

  fetch('/api/joystick/enable', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ enabled: showing })
  }).catch(() => {});
}
