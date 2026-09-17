"""
main.py - MicroPython INA226 5-Channel Power Monitor for STM32 (Serial Output)
"""
import json
import time
import machine
import sys
import config
from ina226 import INA226, bus_is_stuck, bus_recover, parse_pin



# MicroPython / CPython compatibility helpers for time ticks
if not hasattr(time, "ticks_ms"):
    time.ticks_ms = lambda: int(time.time() * 1000)
if not hasattr(time, "ticks_diff"):
    time.ticks_diff = lambda t1, t0: t1 - t0
if not hasattr(time, "sleep_ms"):
    time.sleep_ms = lambda ms: time.sleep(ms / 1000.0)



class PortState:
    def __init__(self):
        self.online = False
        self.v = 0.0
        self.i = 0.0
        self.p = 0.0
        self.errs = 0


# System State
num_ports = len(config.PORT_CONFIG)
ina_devices = []
pstates = [PortState() for _ in range(num_ports)]

recover_count = 0
consecutive_fails = 0
log_blocks = 0
start_ticks = time.ticks_ms()

# Hardware I2C Initialization
i2c = None


def init_i2c():
    global i2c
    try:
        scl_pin = parse_pin(config.PIN_SCL)
        sda_pin = parse_pin(config.PIN_SDA)
        try:
            i2c = machine.I2C(
                config.I2C_ID,
                scl=scl_pin,
                sda=sda_pin,
                freq=config.I2C_FREQ_HZ,
            )
        except (TypeError, ValueError):
            # Fallback for hardware I2C default pin mapping
            i2c = machine.I2C(config.I2C_ID, freq=config.I2C_FREQ_HZ)

        devices = i2c.scan()
        print(f"[I2C BUS] Detected I2C addresses: {[hex(d) for d in devices]}")
    except Exception as e:
        print(f"[I2C ERROR] Failed to initialize hardware I2C: {e}")


def port_state_str(idx):
    cfg = config.PORT_CONFIG[idx]
    st = pstates[idx]
    if not st.online:
        return "OFFLINE"
    if st.i >= cfg["limit"]:
        return "** OVER LIMIT **"
    if st.i >= cfg["warn"]:
        return "** HEATING **" if cfg["thermal"] else "HIGH LOAD"
    return "Nominal"


def init_all():
    print(f"\n=== {num_ports} ports, Rshunt={config.SHUNT_OHMS:.4f} ohm, bus={config.I2C_FREQ_HZ} Hz ===")

    for i in range(num_ports):
        cfg = config.PORT_CONFIG[i]
        sensor = ina_devices[i]
        if sensor.begin(r_shunt=config.SHUNT_OHMS, i_max=config.I_MAX_A):
            if cfg["trim"] != 1.0:
                sensor.trim_cal(cfg["trim"])
            pstates[i].online = True
            print(f"  0x{cfg['addr']:02X} {cfg['name']:<12s} OK  CAL={sensor.cal}  LSB={sensor.current_lsb * 1000.0:.4f} mA")
        else:
            pstates[i].online = False
            print(f"  0x{cfg['addr']:02X} {cfg['name']:<12s} FAILED ({sensor.last_err})")
    print()


def run_bus_recovery():
    global recover_count
    print("!! SDA low - recovering bus")
    freed = bus_recover(config.PIN_SCL, config.PIN_SDA)
    recover_count += 1
    for i in range(num_ports):
        ina_devices[i].present = False
        pstates[i].online = False
    init_i2c()
    return freed


def sample_all():
    global consecutive_fails, recover_count
    ok_count = 0

    for i in range(num_ports):
        cfg = config.PORT_CONFIG[i]
        sensor = ina_devices[i]


        if not sensor.present:
            if sensor.begin(r_shunt=config.SHUNT_OHMS, i_max=config.I_MAX_A):
                if cfg["trim"] != 1.0:
                    sensor.trim_cal(cfg["trim"])
            else:
                pstates[i].online = False
                pstates[i].errs = sensor.err_count
                continue

        online, v, current_a, p, shunt_mv = sensor.read()
        if online:
            ok_count += 1
            pstates[i].online = True
            pstates[i].v = v
            pstates[i].i = current_a
            pstates[i].p = p
            pstates[i].errs = sensor.err_count
        else:
            pstates[i].online = False
            pstates[i].errs = sensor.err_count
            sensor.present = False

    if ok_count == 0:
        consecutive_fails += 1
        if consecutive_fails >= 3:
            print("!! all ports down - forcing bus recovery")
            run_bus_recovery()
            consecutive_fails = 0
    else:
        consecutive_fails = 0


def log_serial():
    global log_blocks
    tot_p = 0.0
    tot_i24 = 0.0
    tot_i12 = 0.0
    online_count = 0

    for i in range(num_ports):
        st = pstates[i]
        cfg = config.PORT_CONFIG[i]
        if not st.online:
            continue
        online_count += 1
        tot_p += st.p
        if cfg["rail"] == 24:
            tot_i24 += st.i
        else:
            tot_i12 += st.i

    uptime_s = time.ticks_diff(time.ticks_ms(), start_ticks) // 1000
    hh = uptime_s // 3600
    mm = (uptime_s // 60) % 60
    ss = uptime_s % 60

    print(
        f"\n=== up {hh:02d}:{mm:02d}:{ss:02d} | total {tot_p:.1f} W | 24V {tot_i24:.3f} A | 12V {tot_i12:.3f} A"
        f" | {online_count}/{num_ports} online | recov {recover_count} ==="
    )

    if (log_blocks % config.SERIAL_HEADER_EVERY) == 0:
        print(" PORT          ADDR    VOLTAGE      CURRENT        POWER   LOAD  STATE")
        print(" ------------  ----  ----------  -----------  -----------  ----  ----------------")
    log_blocks += 1

    for i in range(num_ports):
        cfg = config.PORT_CONFIG[i]
        st = pstates[i]

        if st.online:
            pct = (st.i / cfg["limit"]) * 100.0 if cfg["limit"] > 0 else 0.0
            print(
                f" {cfg['name']:<12s}  0x{cfg['addr']:02X}  {st.v:8.3f} V  {st.i:9.4f} A  {st.p:9.3f} W  {pct:3.0f}%  {port_state_str(i)}"
            )
        else:
            err_msg = ina_devices[i].last_err or "OFFLINE"
            print(
                f" {cfg['name']:<12s}  0x{cfg['addr']:02X}  {'--':>8s}    {'--':>9s}    {'--':>9s}   {'--':>3s}   {port_state_str(i)} ({err_msg}, {st.errs} errs)"
            )


def log_json():
    tot_p = 0.0
    tot_i24 = 0.0
    tot_i12 = 0.0
    online_count = 0

    ports_list = []
    for i in range(num_ports):
        st = pstates[i]
        cfg = config.PORT_CONFIG[i]
        if st.online:
            online_count += 1
            tot_p += st.p
            if cfg["rail"] == 24:
                tot_i24 += st.i
            else:
                tot_i12 += st.i

        ports_list.append(
            {
                "n": cfg["name"],
                "a": cfg["addr"],
                "rail": cfg["rail"],
                "on": st.online,
                "v": round(st.v, 3) if st.online else 0.0,
                "i": round(st.i, 4) if st.online else 0.0,
                "p": round(st.p, 3) if st.online else 0.0,
                "lim": cfg["limit"],
                "warn": cfg["warn"],
                "th": cfg["thermal"],
                "e": st.errs,
            }
        )

    uptime_s = time.ticks_diff(time.ticks_ms(), start_ticks) // 1000
    payload = {
        "up": uptime_s,
        "rec": recover_count,
        "ports": ports_list,
        "tot": {
            "p": round(tot_p, 2),
            "i24": round(tot_i24, 3),
            "i12": round(tot_i12, 3),
            "on": online_count,
            "of": num_ports - online_count,
        },
    }
    print(json.dumps(payload))


def main():
    print("\n[BOOT] Vajara Power Monitor (MicroPython STM32)")

    # 1. Initialize Hardware I2C
    init_i2c()

    # 2. Check for stuck bus condition at startup
    if bus_is_stuck(config.PIN_SDA):
        print("[BOOT] SDA low at startup - recovering")
        run_bus_recovery()

    # 3. Create INA226 instances
    for cfg in config.PORT_CONFIG:
        ina_devices.append(INA226(i2c, cfg["addr"]))

    # 4. Probe and initialize all sensors
    init_all()

    last_sample = time.ticks_ms()
    last_log = time.ticks_ms()

    # Main non-blocking sampling loop
    while True:
        now = time.ticks_ms()

        if time.ticks_diff(now, last_sample) >= config.SAMPLE_PERIOD_MS:
            last_sample = now
            sample_all()

        if time.ticks_diff(now, last_log) >= config.SERIAL_PERIOD_MS:
            last_log = now
            if getattr(config, "JSON_OUTPUT", False):
                log_json()
            else:
                log_serial()

        # Brief pause to prevent CPU spin
        time.sleep_ms(10)



if __name__ == "__main__":
    main()
