"""
ina226.py - MicroPython INA226 Current/Power Monitor Driver & I2C Recovery
"""
import time
import machine

# MicroPython / CPython compatibility helpers for time
if not hasattr(time, "sleep_ms"):
    time.sleep_ms = lambda ms: time.sleep(ms / 1000.0)
if not hasattr(time, "sleep_us"):
    time.sleep_us = lambda us: time.sleep(us / 1000000.0)


# Register Map
REG_CONFIG   = 0x00
REG_SHUNTV   = 0x01
REG_BUSV     = 0x02
REG_POWER    = 0x03
REG_CURRENT  = 0x04
REG_CALIB    = 0x05
REG_MANUF_ID = 0xFE

MANUF_ID_VAL = 0x5449
SHUNT_LSB_V  = 2.5e-6   # 2.5 uV per bit
BUS_LSB_V    = 1.25e-3  # 1.25 mV per bit
SHUNT_FS_V   = 0.08192  # 81.92 mV full scale

# Config defaults: AVG=16 (2), VBUS_CT=1.1ms (4), VSH_CT=1.1ms (4), Mode=Shunt+Bus Continuous (7)
# 0x4000 | (2 << 9) | (4 << 6) | (4 << 3) | 7 = 0x4527
CONFIG_DEFAULT = 0x4527
CONFIG_RESET   = 0x8000


def parse_pin(pin_arg, mode=machine.Pin.IN, pull=-1):
    """Safely resolve pin names ('B7', 'PB7', Pin objects) for STM32 MicroPython."""
    if isinstance(pin_arg, machine.Pin):
        return pin_arg
    p_obj = pin_arg
    if isinstance(pin_arg, str):
        if hasattr(machine.Pin, "board") and hasattr(machine.Pin.board, pin_arg):
            p_obj = getattr(machine.Pin.board, pin_arg)
        elif pin_arg.startswith("P") and hasattr(machine.Pin, "board") and hasattr(machine.Pin.board, pin_arg[1:]):
            p_obj = getattr(machine.Pin.board, pin_arg[1:])
        elif hasattr(machine.Pin, "cpu") and hasattr(machine.Pin.cpu, pin_arg):
            p_obj = getattr(machine.Pin.cpu, pin_arg)

    if pull != -1:
        return machine.Pin(p_obj, mode, pull)
    return machine.Pin(p_obj, mode)


def bus_is_stuck(sda_pin_name):
    """Check if the SDA line is held LOW by a slave device."""
    try:
        pin = parse_pin(sda_pin_name, machine.Pin.IN)
        return pin.value() == 0
    except Exception:
        return False


def bus_recover(scl_pin_name, sda_pin_name):
    """
    Bit-bang SCL line up to 18 cycles to un-stick an I2C bus device holding SDA low.
    Returns True if SDA line was successfully freed.
    """
    scl = parse_pin(scl_pin_name, machine.Pin.OUT_OD, machine.Pin.PULL_UP)
    sda = parse_pin(sda_pin_name, machine.Pin.OUT_OD, machine.Pin.PULL_UP)

    scl.value(1)
    sda.value(1)
    time.sleep_us(10)

    freed = False
    for _ in range(18):
        if sda.value() == 1:
            freed = True
            break
        scl.value(0)
        time.sleep_us(5)
        scl.value(1)
        time.sleep_us(5)

    if sda.value() == 1:
        freed = True

    # Generate STOP condition: SDA low -> SCL high -> SDA high
    sda.value(0)
    time.sleep_us(5)
    scl.value(1)
    time.sleep_us(5)
    sda.value(1)
    time.sleep_us(10)

    return freed


class INA226:
    def __init__(self, i2c, addr7):
        self.i2c = i2c
        self.addr = addr7
        self.present = False
        self.err_count = 0
        self.last_err = ""
        self._r_shunt = 0.002
        self._cal = 0
        self._current_lsb = 0.0
        self._power_lsb = 0.0

    def write_reg(self, reg, val):
        """Write a 16-bit register value (big-endian)."""
        try:
            buf = bytes([(val >> 8) & 0xFF, val & 0xFF])
            self.i2c.writeto_mem(self.addr, reg, buf)
            return True
        except Exception as e:
            self.err_count += 1
            self.last_err = str(e)
            return False

    def read_reg(self, reg):
        """Read a 16-bit register value (big-endian). Returns None on error."""
        try:
            data = self.i2c.readfrom_mem(self.addr, reg, 2)
            if len(data) == 2:
                return (data[0] << 8) | data[1]
            self.err_count += 1
            self.last_err = "read incomplete"
            return None
        except Exception as e:
            self.err_count += 1
            self.last_err = str(e)
            return None

    def begin(self, r_shunt=0.002, i_max=40.96, config=CONFIG_DEFAULT):
        self._r_shunt = r_shunt
        self.present = False

        manuf_id = self.read_reg(REG_MANUF_ID)
        if manuf_id != MANUF_ID_VAL:
            self.last_err = f"invalid ID: {hex(manuf_id) if manuf_id is not None else 'None'}"
            return False

        if not self.write_reg(REG_CONFIG, CONFIG_RESET):
            return False
        time.sleep_ms(2)

        self._compute_cal(i_max)
        if not self.write_reg(REG_CALIB, self._cal):
            return False
        if not self.write_reg(REG_CONFIG, config):
            return False

        self.present = True
        return True

    def _compute_cal(self, i_max):
        if i_max <= 0.0:
            i_max = SHUNT_FS_V / self._r_shunt
        lsb = i_max / 32768.0
        cal_f = 0.00512 / (lsb * self._r_shunt)
        self._cal = min(max(int(cal_f + 0.5), 1), 65535)
        self._current_lsb = 0.00512 / (self._cal * self._r_shunt)
        self._power_lsb = 25.0 * self._current_lsb

    def trim_cal(self, ratio):
        cal_f = self._cal * ratio
        self._cal = min(max(int(cal_f + 0.5), 1), 65535)
        self._current_lsb = 0.00512 / (self._cal * self._r_shunt)
        self._power_lsb = 25.0 * self._current_lsb
        return self.write_reg(REG_CALIB, self._cal)

    def read(self):
        """
        Reads shunt voltage, bus voltage, current, and power.
        Returns tuple: (online, bus_V, current_A, power_W, shunt_mV)
        """
        raw_s = self.read_reg(REG_SHUNTV)
        if raw_s is None:
            self.present = False
            return False, 0.0, 0.0, 0.0, 0.0
        # Convert unsigned 16-bit to signed 16-bit
        signed_s = raw_s if raw_s < 32768 else raw_s - 65536
        shunt_mv = signed_s * SHUNT_LSB_V * 1000.0

        raw_b = self.read_reg(REG_BUSV)
        if raw_b is None:
            self.present = False
            return False, 0.0, 0.0, 0.0, 0.0
        bus_v = raw_b * BUS_LSB_V

        raw_c = self.read_reg(REG_CURRENT)
        if raw_c is None:
            self.present = False
            return False, 0.0, 0.0, 0.0, 0.0
        signed_c = raw_c if raw_c < 32768 else raw_c - 65536
        current_a = signed_c * self._current_lsb

        raw_p = self.read_reg(REG_POWER)
        if raw_p is None:
            self.present = False
            return False, 0.0, 0.0, 0.0, 0.0
        power_w = raw_p * self._power_lsb

        self.present = True
        return True, bus_v, current_a, power_w, shunt_mv

    @property
    def cal(self):
        return self._cal

    @property
    def current_lsb(self):
        return self._current_lsb
