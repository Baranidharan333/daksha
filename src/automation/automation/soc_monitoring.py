#!/usr/bin/env python3

from flask import Flask, jsonify, render_template_string
import subprocess
import re
import threading
import time

app = Flask(__name__)

# ---------------------------------------------------------
# Global statistics
# ---------------------------------------------------------

stats = {
    "cpu": [],
    "gpu": 0,
    "ram_used": 0,
    "ram_total": 0,
    "swap_used": 0,
    "swap_total": 0,
    "cpu_temp": 0,
    "soc_temp": 0,
    "power_gpu": 0,
    "power_cpu": 0,
    "power_system": 0,
    "timestamp": ""
}

lock = threading.Lock()


# ---------------------------------------------------------
# Parse tegrastats
# ---------------------------------------------------------

def parse_tegrastats(line):

    new_stats = {
        "cpu": [],
        "gpu": 0,
        "ram_used": 0,
        "ram_total": 0,
        "swap_used": 0,
        "swap_total": 0,
        "cpu_temp": 0,
        "soc_temp": 0,
        "power_gpu": 0,
        "power_cpu": 0,
        "power_system": 0,
        "timestamp": time.strftime("%H:%M:%S")
    }

    # RAM
    m = re.search(r"RAM\s+(\d+)/(\d+)MB", line)

    if m:
        new_stats["ram_used"] = int(m.group(1))
        new_stats["ram_total"] = int(m.group(2))

    # SWAP
    m = re.search(r"SWAP\s+(\d+)/(\d+)MB", line)

    if m:
        new_stats["swap_used"] = int(m.group(1))
        new_stats["swap_total"] = int(m.group(2))

    # CPU
    m = re.search(r"CPU\s+\[(.*?)\]", line)

    if m:

        cpu_string = m.group(1)

        cores = []

        for item in cpu_string.split(","):

            item = item.strip()

            if item == "off":
                cores.append({
                    "usage": 0,
                    "freq": 0,
                    "off": True
                })

            else:
                match = re.search(r"(\d+)%@(\d+)", item)

                if match:
                    cores.append({
                        "usage": int(match.group(1)),
                        "freq": int(match.group(2)),
                        "off": False
                    })

        new_stats["cpu"] = cores

    # GPU
    m = re.search(r"GR3D_FREQ\s+(\d+)%", line)

    if m:
        new_stats["gpu"] = int(m.group(1))

    # CPU temperature
    m = re.search(r"cpu@([\d.]+)C", line)

    if m:
        new_stats["cpu_temp"] = float(m.group(1))

    # SoC temperature
    m = re.search(r"soc0@([\d.]+)C", line)

    if m:
        new_stats["soc_temp"] = float(m.group(1))

    # GPU / SoC power
    m = re.search(r"VDD_GPU_SOC\s+(\d+)mW", line)

    if m:
        new_stats["power_gpu"] = int(m.group(1))

    # CPU power
    m = re.search(r"VDD_CPU_CV\s+(\d+)mW", line)

    if m:
        new_stats["power_cpu"] = int(m.group(1))

    # System input power
    m = re.search(r"VIN_SYS_5V0\s+(\d+)mW", line)

    if m:
        new_stats["power_system"] = int(m.group(1))

    return new_stats


# ---------------------------------------------------------
# tegrastats background thread
# ---------------------------------------------------------

def monitor():

    global stats

    while True:

        try:

            process = subprocess.Popen(
                [
                    "tegrastats",
                    "--interval",
                    "1000"
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                bufsize=1
            )

            for line in process.stdout:

                parsed = parse_tegrastats(line)

                with lock:
                    stats = parsed

        except Exception as e:

            print("tegrastats error:", e)

            time.sleep(2)


# ---------------------------------------------------------
# API
# ---------------------------------------------------------

@app.route("/api/stats")
def api_stats():

    with lock:
        return jsonify(stats)


# ---------------------------------------------------------
# Web UI
# ---------------------------------------------------------

HTML = """
<!DOCTYPE html>
<html>
<head>

<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">

<title>Jetson Monitor</title>

<style>

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    background: #080b12;
    color: #ffffff;
    font-family: Arial, sans-serif;
}

.header {
    height: 70px;
    background: #10151f;
    border-bottom: 1px solid #252c38;

    display: flex;
    align-items: center;
    justify-content: space-between;

    padding: 0 30px;

    font-size: 23px;
    font-weight: bold;
}

.live {
    font-size: 13px;
    color: #39e58c;

    padding: 7px 13px;

    border: 1px solid #1d7048;
    border-radius: 20px;
}

.container {
    max-width: 1300px;
    margin: auto;

    padding: 25px;
}

.dashboard {

    display: grid;

    grid-template-columns:
        repeat(3, 1fr);

    gap: 20px;
}

.card {

    background: #10151f;

    border: 1px solid #222a36;

    border-radius: 16px;

    padding: 18px;

    text-align: center;

    min-height: 300px;

    display: flex;

    flex-direction: column;

    align-items: center;

    justify-content: center;
}

.title {

    color: #8d98a8;

    font-size: 14px;

    letter-spacing: 1px;

    margin-bottom: 5px;
}


/* =====================================================
   RADIAL GAUGE
   ===================================================== */

.gauge {

    width: 240px;
    height: 180px;

    position: relative;

    overflow: hidden;
}

.gauge svg {

    width: 100%;
    height: 100%;
}

.gauge-bg {

    fill: none;

    stroke: #29313e;

    stroke-width: 18;

    stroke-linecap: round;

    stroke-dasharray: 283;

    stroke-dashoffset: 0;
}

.gauge-value {

    fill: none;

    stroke: #35e58b;

    stroke-width: 18;

    stroke-linecap: round;

    stroke-dasharray: 283;

    stroke-dashoffset: 283;

    transition:
        stroke-dashoffset 0.5s ease,
        stroke 0.3s ease;
}

.gauge-text {

    position: absolute;

    left: 0;
    right: 0;

    bottom: 28px;

    text-align: center;

    font-size: 36px;

    font-weight: bold;
}

.gauge-unit {

    font-size: 14px;

    color: #8993a3;

    margin-top: 2px;
}


/* =====================================================
   INFORMATION
   ===================================================== */

.sub-info {

    margin-top: 5px;

    color: #8993a3;

    font-size: 13px;
}


/* =====================================================
   CPU CORES
   ===================================================== */

.core-container {

    width: 100%;

    display: grid;

    grid-template-columns:
        repeat(4, 1fr);

    gap: 8px;

    margin-top: 10px;
}

.core {

    background: #080b12;

    border-radius: 8px;

    padding: 9px 4px;

    border: 1px solid #202735;
}

.core-name {

    font-size: 11px;

    color: #7d8796;
}

.core-value {

    font-size: 17px;

    font-weight: bold;

    margin-top: 3px;
}

.core-freq {

    font-size: 10px;

    color: #6f7988;

    margin-top: 2px;
}


/* =====================================================
   POWER
   ===================================================== */

.power-value {

    font-size: 42px;

    font-weight: bold;

    margin: 15px 0;
}

.power-row {

    width: 100%;

    display: flex;

    justify-content: space-around;

    color: #9aa4b2;

    font-size: 13px;
}


/* =====================================================
   TEMPERATURE
   ===================================================== */

.temp-value {

    font-size: 42px;

    font-weight: bold;

    margin: 15px;
}


/* =====================================================
   RESPONSIVE
   ===================================================== */

@media(max-width: 900px) {

    .dashboard {

        grid-template-columns:
            repeat(2, 1fr);
    }
}

@media(max-width: 600px) {

    .dashboard {

        grid-template-columns: 1fr;
    }

    .container {

        padding: 12px;
    }

}

</style>

</head>


<body>


<div class="header">

    <div>
        JETSON SYSTEM MONITOR
    </div>

    <div class="live">
        ● LIVE
    </div>

</div>


<div class="container">


<div class="dashboard">


<!-- ==================================================
     CPU
     ================================================== -->

<div class="card">

    <div class="title">
        CPU UTILIZATION
    </div>

    <div class="gauge">

        <svg viewBox="0 0 240 180">

            <!-- background -->

            <path
                class="gauge-bg"
                d="M 30 145
                   A 90 90 0 0 1 210 145"
            />

            <!-- value -->

            <path
                id="cpuGauge"
                class="gauge-value"
                d="M 30 145
                   A 90 90 0 0 1 210 145"
            />

        </svg>

        <div
            class="gauge-text"
            id="cpuValue">
            0%
        </div>

    </div>

    <div
        class="sub-info"
        id="activeCores">
        Active cores: 0 / 0
    </div>

</div>


<!-- ==================================================
     GPU
     ================================================== -->

<div class="card">

    <div class="title">
        GPU UTILIZATION
    </div>

    <div class="gauge">

        <svg viewBox="0 0 240 180">

            <path
                class="gauge-bg"
                d="M 30 145
                   A 90 90 0 0 1 210 145"
            />

            <path
                id="gpuGauge"
                class="gauge-value"
                d="M 30 145
                   A 90 90 0 0 1 210 145"
            />

        </svg>

        <div
            class="gauge-text"
            id="gpuValue">
            0%
        </div>

    </div>

    <div class="sub-info">
        GR3D
    </div>

</div>


<!-- ==================================================
     RAM
     ================================================== -->

<div class="card">

    <div class="title">
        RAM UTILIZATION
    </div>

    <div class="gauge">

        <svg viewBox="0 0 240 180">

            <path
                class="gauge-bg"
                d="M 30 145
                   A 90 90 0 0 1 210 145"
            />

            <path
                id="ramGauge"
                class="gauge-value"
                d="M 30 145
                   A 90 90 0 0 1 210 145"
            />

        </svg>

        <div
            class="gauge-text"
            id="ramValue">
            0%
        </div>

    </div>

    <div
        class="sub-info"
        id="ramText">
        0 / 0 MB
    </div>

</div>


<!-- ==================================================
     POWER
     ================================================== -->

<div class="card">

    <div class="title">
        SYSTEM POWER
    </div>

    <div
        class="power-value"
        id="systemPower">
        0.00 W
    </div>

    <div class="power-row">

        <div>
            CPU<br>
            <b id="cpuPower">0.00 W</b>
        </div>

        <div>
            GPU / SoC<br>
            <b id="gpuPower">0.00 W</b>
        </div>

    </div>

</div>


<!-- ==================================================
     TEMPERATURE
     ================================================== -->

<div class="card">

    <div class="title">
        TEMPERATURE
    </div>

    <div
        class="temp-value"
        id="cpuTemp">
        0 °C
    </div>

    <div class="sub-info">

        SoC:
        <span id="socTemp">
            0 °C
        </span>

    </div>

</div>


<!-- ==================================================
     CPU CORES
     ================================================== -->

<div class="card">

    <div class="title">
        CPU CORES
    </div>

    <div
        class="core-container"
        id="coreContainer">
    </div>

</div>


</div>


<br>


<div
    class="sub-info"
    style="text-align:center">

    Last update:
    <span id="timestamp">
        --
    </span>

</div>


</div>


<script>


/* =====================================================
   GAUGE UPDATE
   ===================================================== */

function setGauge(id, value) {

    value =
        Math.max(
            0,
            Math.min(100, value)
        );

    const length = 283;

    const offset =
        length -
        (length * value / 100);

    const gauge =
        document.getElementById(id);

    gauge.style.strokeDasharray =
        length;

    gauge.style.strokeDashoffset =
        offset;


    if (value < 60) {

        gauge.style.stroke =
            "#35e58b";

    }
    else if (value < 85) {

        gauge.style.stroke =
            "#f5c542";

    }
    else {

        gauge.style.stroke =
            "#ff5252";

    }

}


/* =====================================================
   UPDATE DATA
   ===================================================== */

function updateStats() {

    fetch("/api/stats")

        .then(response => response.json())

        .then(data => {


            /* -----------------------------------------
               CPU
               ----------------------------------------- */

            let active = [];

            data.cpu.forEach(core => {

                if (!core.off) {

                    active.push(
                        core.usage
                    );

                }

            });


            let cpuAvg = 0;

            if (active.length > 0) {

                cpuAvg =
                    active.reduce(
                        (a, b) => a + b,
                        0
                    ) / active.length;

            }


            cpuAvg =
                Math.round(cpuAvg);


            document.getElementById(
                "cpuValue"
            ).innerText =
                cpuAvg + "%";


            setGauge(
                "cpuGauge",
                cpuAvg
            );


            document.getElementById(
                "activeCores"
            ).innerText =
                "Active cores: " +
                active.length +
                " / " +
                data.cpu.length;


            /* -----------------------------------------
               GPU
               ----------------------------------------- */

            document.getElementById(
                "gpuValue"
            ).innerText =
                data.gpu + "%";


            setGauge(
                "gpuGauge",
                data.gpu
            );


            /* -----------------------------------------
               RAM
               ----------------------------------------- */

            let ramPercent = 0;

            if (data.ram_total > 0) {

                ramPercent =
                    (
                        data.ram_used /
                        data.ram_total
                    ) * 100;

            }


            ramPercent =
                Math.round(ramPercent);


            document.getElementById(
                "ramValue"
            ).innerText =
                ramPercent + "%";


            document.getElementById(
                "ramText"
            ).innerText =
                data.ram_used +
                " / " +
                data.ram_total +
                " MB";


            setGauge(
                "ramGauge",
                ramPercent
            );


            /* -----------------------------------------
               POWER
               ----------------------------------------- */

            document.getElementById(
                "systemPower"
            ).innerText =
                (
                    data.power_system / 1000
                ).toFixed(2) +
                " W";


            document.getElementById(
                "cpuPower"
            ).innerText =
                (
                    data.power_cpu / 1000
                ).toFixed(2) +
                " W";


            document.getElementById(
                "gpuPower"
            ).innerText =
                (
                    data.power_gpu / 1000
                ).toFixed(2) +
                " W";


            /* -----------------------------------------
               TEMPERATURE
               ----------------------------------------- */

            document.getElementById(
                "cpuTemp"
            ).innerText =
                data.cpu_temp.toFixed(1) +
                " °C";


            document.getElementById(
                "socTemp"
            ).innerText =
                data.soc_temp.toFixed(1) +
                " °C";


            /* -----------------------------------------
               CPU CORES
               ----------------------------------------- */

            const container =
                document.getElementById(
                    "coreContainer"
                );


            container.innerHTML = "";


            data.cpu.forEach(
                (core, index) => {


                    const div =
                        document.createElement(
                            "div"
                        );


                    div.className =
                        "core";


                    if (core.off) {

                        div.innerHTML = `

                            <div class="core-name">
                                CPU ${index}
                            </div>

                            <div class="core-value">
                                OFF
                            </div>

                            <div class="core-freq">
                                --
                            </div>

                        `;

                    }

                    else {

                        div.innerHTML = `

                            <div class="core-name">
                                CPU ${index}
                            </div>

                            <div class="core-value">
                                ${core.usage}%
                            </div>

                            <div class="core-freq">
                                ${core.freq} MHz
                            </div>

                        `;

                    }


                    container.appendChild(
                        div
                    );

                }
            );


            /* -----------------------------------------
               TIME
               ----------------------------------------- */

            document.getElementById(
                "timestamp"
            ).innerText =
                data.timestamp;

        })

        .catch(error => {

            console.log(
                "Monitor connection error:",
                error
            );

        });

}


/* =====================================================
   START
   ===================================================== */

updateStats();

setInterval(
    updateStats,
    1000
);

</script>


</body>
</html>
"""


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

@app.route("/")
def index():

    return render_template_string(HTML)


if __name__ == "__main__":

    thread = threading.Thread(
        target=monitor,
        daemon=True
    )

    thread.start()

    print("")
    print("====================================")
    print(" Jetson Monitor")
    print("====================================")
    print("")
    print("Open:")
    print("http://JETSON_IP:5000")
    print("")

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False,
        threaded=True
    )
