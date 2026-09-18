# motor_configure

ROS 2 (`ament_python`) package providing a local web UI for scanning and
configuring CAN bus motor controllers over SocketCAN.

This is a **local** tool: it must run on the machine that owns the SocketCAN
interface, since a browser cannot talk to CAN hardware directly. There is no
authentication, so don't expose `--host` beyond `127.0.0.1` on an untrusted
network.

## Package layout

```
motor_configure/
├── motor_configure/
│   ├── main.py          # entry point: opens the CAN bus, starts the Flask app
│   ├── motor_driver.py  # CAN protocol layer (scan/probe/enable/disable/zero/id-write)
│   ├── motor_web.py     # Flask app + HTTP API routes
│   └── static/
│       └── index.html   # single-page UI
├── launch/
│   └── motor_configure.launch.py
├── resource/motor_configure
├── package.xml
├── setup.py
└── setup.cfg
```

## Dependencies

- ROS 2 Humble (or compatible)
- `python3-can` (rosdep-resolvable)
- `python3-flask` (rosdep-resolvable)
- A SocketCAN interface, real (`can0`) or virtual (`vcan0`)

```bash
sudo apt install python3-can python3-flask
```

### Setting up a virtual CAN interface for testing

```bash
sudo modprobe vcan
sudo ip link add dev vcan0 type vcan
sudo ip link set up vcan0
```

## Build

From the workspace root:

```bash
colcon build --packages-select motor_configure --symlink-install
source install/setup.bash
```

## Run

`motor_configure` is an `rclpy` node (`main.py`'s `MotorConfigureNode`);
`channel`, `host`, and `port` are ROS parameters, not CLI flags.

Directly:

```bash
ros2 run motor_configure motor_configure --ros-args -p channel:=vcan0 -p port:=8000
# then open http://127.0.0.1:8000 in a browser on this machine
```

Or via the launch file, which also starts `gen2`'s `vcan_bridge` node
(bridges a physical canalystii CAN adapter to `vcan0`/`vcan1`) by default:

```bash
ros2 launch motor_configure motor_configure.launch.py channel:=vcan0 host:=0.0.0.0 port:=8000
```

Pass `run_vcan_bridge:=false` to skip `vcan_bridge` -- e.g. when pointing
`channel` at a real `can0` interface that already exists, or one you set up
yourself (see below). `vcan_bridge` itself needs the canalystii hardware and
a `VCAN_SUDO_PASSWORD` environment variable for the `sudo` calls it makes to
create `vcan0`/`vcan1`. Since creating those interfaces takes it a moment,
the launch file delays starting `motor_configure` by 2s so the channel
exists before `motor_configure` tries to open it.

Launch arguments:

| Arg | Default | Description |
|------|---------|-------------|
| `channel` | `vcan0` | SocketCAN interface name to open on startup -- matches `vcan_bridge`'s output since that node runs alongside this one by default |
| `host` | `0.0.0.0` | Bind address for the web server |
| `port` | `8000` | Bind port for the web server |
| `run_vcan_bridge` | `true` | Also launch `gen2`'s `vcan_bridge` node |

The channel can also be changed at runtime from the **Connection** panel in
the UI (or by `POST /api/set_channel {"channel": "vcan0"}`), without
restarting the process.

## HTTP API

| Route | Method | Purpose |
|-------|--------|---------|
| `/api/status` | GET | Current channel |
| `/api/set_channel` | POST | Switch the SocketCAN interface at runtime |
| `/api/scan` | POST | Scan a range of CAN ids for responding controllers |
| `/api/probe` | POST | Ping a single CAN id and read back its feedback |
| `/api/set_id` | POST | Write a new CAN id and/or feedback id, then save to flash |
| `/api/enable` / `/api/disable` | POST | Enable/disable a controller |
| `/api/zero` / `/api/zero_all` | POST | Set current shaft position as the new zero |
