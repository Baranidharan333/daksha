# vajara

ROS 2 bridge + web UI for the Vajara STM32 power-monitor board.

## Layout

- `vajara/power_monitor_node.py` — the ROS 2 node (`ros2 run vajara power_monitor_node`).
  Reads JSON telemetry lines from the STM32 over serial (`/dev/ttyACM0` by default),
  republishes them on `/vajra/power_telemetry`, and serves the dashboard in
  `vajara/index.html` at `http://<host>:8080`.
- `launch/vajara.launch.py` — launches the node (included from `gen2`'s `bringup.launch.py`).
- `firmware/` — **MicroPython** firmware that runs *on the STM32 itself*, not under ROS 2.
  It talks to the five INA226 current sensors over I2C and prints the JSON lines that
  `power_monitor_node.py` consumes. Flash `firmware/main.py`, `firmware/ina226.py`, and
  `firmware/config.py` to the STM32's MicroPython filesystem (e.g. with `mpremote` or
  `ampy`); they are not Python packages usable on the host and are not installed on the
  Python import path.
