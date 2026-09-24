document.addEventListener('DOMContentLoaded', () => {
    const promptInput = document.getElementById('prompt-input');
    const previewBtn = document.getElementById('preview-btn');
    
    // Steps
    const step1 = document.getElementById('step-1-input');
    const step2 = document.getElementById('step-2-preview');
    const step3 = document.getElementById('step-3-execution');

    // Preview Elements
    const confirmBtn = document.getElementById('confirm-btn');
    const cancelPreviewBtn = document.getElementById('cancel-preview-btn');
    const previewInstruction = document.getElementById('preview-instruction');
    const execTaskName = document.getElementById('exec-task-name');

    // Execution Elements
    const pauseBtn = document.getElementById('pause-btn');
    const stopBtn = document.getElementById('stop-btn');
    
    const topStatus = document.getElementById('top-status');
    const topStatusText = document.getElementById('top-status-text');
    const pulseDot = document.querySelector('.pulse-dot');
    const logConsole = document.getElementById('log-console');
    const clockElement = document.getElementById('sys-clock');

    // Progress simulation
    const progressBarFill = document.getElementById('progress-bar-fill');
    const progressPercentText = document.getElementById('progress-percent-text');
    let executionInterval;
    let progress = 0;
    let isPaused = false;

    // Update Clock with Milliseconds to look high-tech
    setInterval(() => {
        const now = new Date();
        clockElement.textContent = now.toLocaleTimeString('en-US', { hour12: false }) + '.' + Math.floor(now.getMilliseconds() / 100).toString();
    }, 100);

    function addLog(message, type = 'info') {
        const time = new Date().toLocaleTimeString('en-US', { hour12: false });
        const entry = document.createElement('div');
        entry.className = `log-entry ${type}`;
        entry.textContent = `[${time}] ${message}`;
        logConsole.appendChild(entry);
        logConsole.scrollTop = logConsole.scrollHeight; // Auto-scroll to bottom
    }

    function updateStatus(state, label) {
        pulseDot.className = 'pulse-dot ' + state;
        topStatusText.textContent = label;
        
        if (state === 'active') {
            topStatus.style.borderColor = 'rgba(16, 185, 129, 0.4)';
            topStatus.style.background = 'rgba(16, 185, 129, 0.1)';
            topStatusText.style.color = '#10b981';
        } else if (state === 'error') {
            topStatus.style.borderColor = 'rgba(239, 68, 68, 0.4)';
            topStatus.style.background = 'rgba(239, 68, 68, 0.1)';
            topStatusText.style.color = '#ef4444';
        } else {
            topStatus.style.borderColor = 'rgba(255,255,255,0.05)';
            topStatus.style.background = 'rgba(0,0,0,0.4)';
            topStatusText.style.color = 'inherit';
        }
    }

    function switchStep(hideElement, showElement) {
        hideElement.style.display = 'none';
        showElement.style.display = 'block';
    }

    previewBtn.addEventListener('click', () => {
        const prompt = promptInput.value.trim();
        if (!prompt) {
            addLog('ERROR: Task instruction cannot be empty.', 'error');
            updateStatus('error', 'INPUT ERROR');
            
            // Input field shake effect for feedback
            promptInput.style.transform = 'translateX(10px)';
            setTimeout(() => promptInput.style.transform = 'translateX(-10px)', 100);
            setTimeout(() => promptInput.style.transform = 'translateX(0)', 200);
            
            promptInput.focus();
            return;
        }

        previewInstruction.textContent = `"${prompt}"`;
        execTaskName.textContent = prompt.length > 20 ? prompt.substring(0, 20) + '...' : prompt;
        addLog(`Analyzing task: "${prompt}"...`, 'info');
        
        switchStep(step1, step2);
    });

    cancelPreviewBtn.addEventListener('click', () => {
        addLog('Task cancelled by user.', 'warning');
        switchStep(step2, step1);
    });

    confirmBtn.addEventListener('click', async () => {
        const prompt = promptInput.value.trim();
        addLog(`Transmitting policy to GR00T Engine: "${prompt}"`, 'info');
        updateStatus('idle', 'TRANSMITTING...');
        
        switchStep(step2, step3);
        
        try {
            const response = await fetch('/api/instruct', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ prompt })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                addLog('Transmission successful. Inference actively running.', 'success');
                updateStatus('active', 'POLICY EXECUTING');
                startProgressSimulation();
            } else {
                addLog(`Transmission failed: ${data.message}`, 'error');
                updateStatus('error', 'SYSTEM FAULT');
            }
        } catch (error) {
            addLog(`Connection error: ${error.message}`, 'error');
            updateStatus('error', 'CONNECTION LOST');
        }
    });

    function startProgressSimulation() {
        progress = 0;
        isPaused = false;
        progressBarFill.style.width = '0%';
        progressPercentText.textContent = '0%';
        pauseBtn.innerHTML = '<i class="fa-solid fa-pause"></i> PAUSE';
        
        if(executionInterval) clearInterval(executionInterval);
        
        executionInterval = setInterval(() => {
            if (isPaused) return;
            
            progress += Math.random() * 5;
            if (progress >= 100) {
                progress = 100;
                clearInterval(executionInterval);
                addLog('Task completed successfully.', 'success');
                updateStatus('idle', 'SYSTEM STANDBY');
                setTimeout(() => {
                    switchStep(step3, step1);
                    promptInput.value = '';
                }, 3000);
            }
            
            progressBarFill.style.width = `${progress}%`;
            progressPercentText.textContent = `${Math.floor(progress)}%`;
            
            // Update steps based on progress
            const steps = document.querySelectorAll('.execution-steps-list li');
            if (progress > 25 && progress <= 50) {
                setStepState(steps[0], 'completed');
                setStepState(steps[1], 'active');
            } else if (progress > 50 && progress <= 75) {
                setStepState(steps[1], 'completed');
                setStepState(steps[2], 'active');
            } else if (progress > 75) {
                setStepState(steps[2], 'completed');
                setStepState(steps[3], 'active');
            }
            if (progress === 100) {
                setStepState(steps[3], 'completed');
            }
        }, 500);
    }
    
    function setStepState(element, state) {
        if (state === 'completed') {
            element.className = 'step-completed';
            element.innerHTML = element.innerHTML.replace(/fa-(circle-dot|regular fa-circle|check)/, 'fa-check');
        } else if (state === 'active') {
            element.className = 'step-active';
            element.innerHTML = element.innerHTML.replace(/fa-(check|regular fa-circle|circle-dot)/, 'fa-circle-dot');
        }
    }

    pauseBtn.addEventListener('click', () => {
        isPaused = !isPaused;
        if (isPaused) {
            pauseBtn.innerHTML = '<i class="fa-solid fa-play"></i> RESUME';
            addLog('Execution paused.', 'warning');
            updateStatus('idle', 'PAUSED');
        } else {
            pauseBtn.innerHTML = '<i class="fa-solid fa-pause"></i> PAUSE';
            addLog('Execution resumed.', 'info');
            updateStatus('active', 'POLICY EXECUTING');
        }
    });

    async function haltSystem() {
        if(executionInterval) clearInterval(executionInterval);

        addLog('Initiating halt sequence...', 'warning');
        
        try {
            const response = await fetch('/api/stop', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            
            if (response.ok) {
                addLog('System halted successfully. Returned to standby.', 'success');
                updateStatus('idle', 'SYSTEM STANDBY');
                switchStep(step3, step1);
                promptInput.value = '';
            } else {
                addLog(`Halt failed: ${data.message}`, 'error');
                updateStatus('error', 'HALT FAILED');
            }
        } catch (error) {
            addLog(`Connection error during halt: ${error.message}`, 'error');
            updateStatus('error', 'CONNECTION ERROR');
        }
    }

    stopBtn.addEventListener('click', () => haltSystem());

    const diagBtn = document.getElementById('diag-btn');
    const diagnosticsPanel = document.getElementById('diagnostics-panel');
    const closeDiagBtn = document.getElementById('close-diag-btn');
    let diagInterval;

    if (diagBtn && diagnosticsPanel && closeDiagBtn) {
        diagBtn.addEventListener('click', () => {
            step1.style.display = 'none';
            step2.style.display = 'none';
            step3.style.display = 'none';
            diagnosticsPanel.style.display = 'block';
            startDiagnosticsPolling();
        });

        closeDiagBtn.addEventListener('click', () => {
            diagnosticsPanel.style.display = 'none';
            step1.style.display = 'block';
            stopDiagnosticsPolling();
        });
    }

    function startDiagnosticsPolling() {
        if(diagInterval) clearInterval(diagInterval);
        fetchDiagnostics();
        diagInterval = setInterval(fetchDiagnostics, 2000);
    }

    function stopDiagnosticsPolling() {
        if(diagInterval) clearInterval(diagInterval);
    }

    async function fetchDiagnostics() {
        try {
            const response = await fetch('/api/diagnostics');
            if (response.ok) {
                const data = await response.json();
                
                const healthKeys = ['ros', 'can0', 'can1', 'leader', 'follower', 'd405', 'zed', 'gpu', 'recorder'];
                healthKeys.forEach(key => {
                    const el = document.getElementById(`health-${key}`);
                    if(el && data.health && data.health[key]) {
                        el.textContent = data.health[key] === 'ok' ? '🟢' : '🔴';
                    }
                });

                if(data.metrics) {
                    const m = data.metrics;
                    if(document.getElementById('metric-ros-freq')) document.getElementById('metric-ros-freq').textContent = `${m.ros_freq} Hz`;
                    if(document.getElementById('metric-cam-fps')) document.getElementById('metric-cam-fps').textContent = `${m.cam_fps} FPS`;
                    if(document.getElementById('metric-can-rate')) document.getElementById('metric-can-rate').textContent = `${m.can_rate} msg/s`;
                    if(document.getElementById('metric-cpu')) document.getElementById('metric-cpu').textContent = `${m.cpu_usage} %`;
                    if(document.getElementById('metric-gpu-usage')) document.getElementById('metric-gpu-usage').textContent = `${m.gpu_usage} %`;
                    if(document.getElementById('metric-gpu-temp')) document.getElementById('metric-gpu-temp').textContent = `${m.gpu_temp} °C`;
                    if(document.getElementById('metric-memory')) document.getElementById('metric-memory').textContent = `${m.memory} GB`;
                    if(document.getElementById('metric-network')) document.getElementById('metric-network').textContent = `${m.network} ms`;
                }
            }
        } catch (error) {
            console.error("Failed to fetch diagnostics", error);
        }
    }

    promptInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            previewBtn.click();
        }
    });
});
