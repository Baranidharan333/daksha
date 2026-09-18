"""
config.py - Configuration file for MicroPython INA226 Power Monitor on STM32
"""

# I2C Hardware Configuration (STM32 Black Pill)
# MicroPython WEACT_F411_BLACKPILL board pin names: SCL='B6', SDA='B7'
I2C_ID = 1
PIN_SCL = 'B6'
PIN_SDA = 'B7'
I2C_FREQ_HZ = 100000
I2C_TIMEOUT_MS = 50


# Global Sensor Parameters
SHUNT_OHMS = 0.002        # 2 mOhm shunt resistor
I_MAX_A = 40.96           # Max current calculation baseline (CAL 2048 -> 1.25 mA/bit)
SAMPLE_PERIOD_MS = 200    # Sensor read interval in ms
SERIAL_PERIOD_MS = 300     # Serial print/transmit interval in ms
SERIAL_HEADER_EVERY = 12  # Re-print table column headers every N log cycles
JSON_OUTPUT = True        # True = Stream JSON for ROS 2 node & Web UI; False = ASCII table


# Port Configuration
# addr: I2C 7-bit address
# name: Display name
# rail: Nominal voltage (24 or 12 V)
# limit: Hard current limit (A)
# warn: Caution/warning current threshold (A)
# thermal: True if caution band causes thermal load (12V port)
# trim: Calibration adjustment multiplier (default 1.0)
PORT_CONFIG = [
    {"addr": 0x40, "name": "24V Port 1", "rail": 24, "limit": 20.0, "warn": 16.0, "thermal": False, "trim": 1.0},
    {"addr": 0x41, "name": "24V Port 2", "rail": 24, "limit": 20.0, "warn": 16.0, "thermal": False, "trim": 1.0},
    {"addr": 0x42, "name": "24V Port 3", "rail": 24, "limit": 20.0, "warn": 16.0, "thermal": False, "trim": 1.0},
    {"addr": 0x43, "name": "24V Port 4", "rail": 24, "limit": 20.0, "warn": 16.0, "thermal": False, "trim": 1.0},
    {"addr": 0x44, "name": "12V Port",   "rail": 12, "limit": 5.0,  "warn": 3.0,  "thermal": True,  "trim": 1.0},
]
