# Daksha

ROS 2 workspace for **Daksha**, a dual-arm robot with two 7-DoF arms and two
single-finger grippers driven by DAMIAO CAN motors. The workspace covers the
full stack: the `ros2_control` hardware interface and CAN bridge, MIT-mode
position/velocity/effort controllers, gravity compensation, kinematics,
teleoperation (leader arms and VR), data collection and replay, diagnostics, and
the operator web UI.

> Older, unedited operator notes from previous bring-ups live in
> [docs/NOTES.md](docs/NOTES.md). They reference other machines and sibling
> robots and are kept for history only.

---

## Table of contents

- [Requirements](#requirements)
- [Installation](#installation)
- [Building](#building)
- [CAN setup](#can-setup)
- [Running the robot](#running-the-robot)
- [Controllers, topics and services](#controllers-topics-and-services)
- [Teleoperation](#teleoperation)
- [Data collection and replay](#data-collection-and-replay)
- [Running as a systemd service](#running-as-a-systemd-service)
- [Repository layout](#repository-layout)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## Requirements

| Component | Version |
| --- | --- |
| OS | Ubuntu 22.04 |
| ROS 2 | Humble Hawksbill |
| Python | 3.10+ |
| CAN adapter | CANalyst-II (USB `04d8:0053`) |

Python dependencies are pinned in [src/requirements.txt](src/requirements.txt)
(PyQt6, python-can, pinocchio, placo, pyarrow, Flask, OpenCV, …).

---

## Installation

### 1. Clone

```bash
git clone git@github.com:Baranidharan333/daksha.git ~/daksha
cd ~/daksha
```

### 2. Grant access to the CAN adapter

Without a udev rule the CANalyst-II device is root-only and the bridge fails to
open it.

```bash
sudo tee /etc/udev/rules.d/99-canalyst.rules >/dev/null <<'EOF'
SUBSYSTEM=="usb", ATTR{idVendor}=="04d8", ATTR{idProduct}=="0053", MODE="0666"
EOF

sudo udevadm control --reload-rules
sudo udevadm trigger
```

Replug the adapter afterwards.

### 3. System packages

```bash
sudo apt update
sudo apt install -y \
    python3-pip python3-dev python3-venv python3-setuptools python3-wheel \
    python3-packaging build-essential cmake ninja-build git pkg-config \
    libgl1 libglib2.0-0 libxcb-xinerama0 libxkbcommon-x11-0 libegl1 \
    libdbus-1-3 libfontconfig1 qt6-base-dev \
    ros-humble-joint-state-publisher-gui ros-humble-topic-tools
```

### 4. Python packages

```bash
python3 -m pip install --user --upgrade \
    pip setuptools==79.0.1 wheel packaging sip pyqt6-sip

export PATH=$HOME/.local/bin:$PATH

python3 -m pip install --user --no-build-isolation -r src/requirements.txt
python3 -m pip install --user canalystii "python-can[canalystii]"
```

`--no-build-isolation` is required: `placo` and `pin` build against the
system-installed Eigen/Boost headers.

---

## Building

```bash
cd ~/daksha
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash
```

Build a single package while iterating:

```bash
colcon build --packages-select hw_interface
```

Clean rebuild:

```bash
rm -rf build install log && colcon build
```

---

## CAN setup

The hardware interface talks to two virtual CAN buses (`vcan0`, `vcan1`) that a
bridge process forwards to the physical CANalyst-II adapter.

```bash
sudo modprobe vcan

sudo ip link add dev vcan0 type vcan
sudo ip link add dev vcan1 type vcan
sudo ip link set up vcan0
sudo ip link set up vcan1
```

[src/scripts/can_up.sh](src/scripts/can_up.sh) performs the same steps.

The bridge is started automatically by `bringup.launch.py`. Run it standalone
with either implementation — **only one may run at a time**, since both claim the
same USB device and virtual interfaces:

```bash
# C++ (default, from hw_interface)
ros2 run hw_interface vcan_bridge_node

# Python equivalent
python3 src/scripts/vcan_bridge.py
```

For a directly attached (non-virtual) adapter:

```bash
sudo ip link set can0 down
sudo ip link set can0 type can bitrate 1000000
sudo ip link set can0 up

damiao scan                       # enumerate motors
damiao set-motor-id --current 11 --target 15
damiao gui --host 192.168.200.153
```

---

## Running the robot

Full bring-up — CAN bridge, `controller_manager`, `robot_state_publisher`,
controller spawners, gravity compensation, gesture management, diagnostics,
logging and the operator UI:

```bash
source /opt/ros/humble/setup.bash
source ~/daksha/install/setup.bash

ros2 launch gen2 bringup.launch.py
```

Launch arguments:

| Argument | Default | Description |
| --- | --- | --- |
| `use_cpp_vcan_bridge` | `true` | Use the C++ `hw_interface/vcan_bridge_node` instead of the Python `gen2/vcan_bridge` node. |

### Manual bring-up

Useful when testing a single URDF or controller configuration:

```bash
URDF=$(ros2 pkg prefix daksha_description_full_body)/share/daksha_description_full_body/urdf/robot.urdf

ros2 run controller_manager ros2_control_node \
  --ros-args \
  --params-file src/gen2/config/controllers.yaml \
  -p robot_description:="$(cat $URDF)"

ros2 run robot_state_publisher robot_state_publisher \
  --ros-args -p robot_description:="$(cat $URDF)"
```

Then load the controllers:

```bash
ros2 control load_controller --set-state active joint_state_broadcaster && \
ros2 control load_controller --set-state active left_arm_mit_controller && \
ros2 control load_controller --set-state active right_arm_mit_controller && \
ros2 control load_controller --set-state active left_gripper_mit_controller && \
ros2 control load_controller --set-state active right_gripper_mit_controller
```

Inspect state:

```bash
ros2 control list_hardware_components
ros2 control list_controllers
```

---

## Controllers, topics and services

### Controllers

Defined in [src/gen2/config/controllers.yaml](src/gen2/config/controllers.yaml),
running at **200 Hz**.

| Controller | Type | Joints |
| --- | --- | --- |
| `joint_state_broadcaster` | `joint_state_broadcaster/JointStateBroadcaster` | all |
| `left_arm_mit_controller` | `posveleff_controllers/PosVelEffController` | `left_joint_1` … `left_joint_7` |
| `right_arm_mit_controller` | `posveleff_controllers/PosVelEffController` | `right_joint_1` … `right_joint_7` |
| `left_gripper_mit_controller` | `posveleff_controllers/PosVelEffController` | `left_gripper_left_joint` |
| `right_gripper_mit_controller` | `posveleff_controllers/PosVelEffController` | `right_gripper_right_joint` |

### Key topics

| Topic | Type | Description |
| --- | --- | --- |
| `/joint_cmd` | `sensor_msgs/JointState` | Primary command entry point; accepts partial joint name lists. |
| `/jnt_cmt_to_ctrl` | `sensor_msgs/JointState` | Fully populated command forwarded to the controllers. |
| `/joint_states` | `sensor_msgs/JointState` | Measured state from the broadcaster. |
| `/<controller>/joint_trajectory` | `trajectory_msgs/JointTrajectory` | Per-controller trajectory input. |
| `/<Arm>System_ordered_joint_states` | `sensor_msgs/JointState` | Per-arm measured state in motor order. |
| `/gravity_torque` | `sensor_msgs/JointState` | Computed gravity feed-forward effort. |
| `/joint_cmd_predict` | `sensor_msgs/JointState` | Policy predictions, filtered by `vla_bridge`. |

Command a single gripper (open / close):

```bash
ros2 topic pub -1 /joint_cmd sensor_msgs/msg/JointState \
  "{name: ['right_gripper_right_joint'], position: [-0.044]}"   # close

ros2 topic pub -1 /joint_cmd sensor_msgs/msg/JointState \
  "{name: ['right_gripper_right_joint'], position: [0.0]}"      # open
```

Send an arm trajectory:

```bash
ros2 topic pub --once /left_arm_mit_controller/joint_trajectory \
  trajectory_msgs/msg/JointTrajectory "
joint_names: [left_joint_1, left_joint_2, left_joint_3, left_joint_4,
              left_joint_5, left_joint_6, left_joint_7]
points:
- positions: [0.2, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
  velocities: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
  effort: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
  time_from_start: {sec: 2}
"
```

Drive the arms from a GUI:

```bash
ros2 run joint_state_publisher_gui joint_state_publisher_gui \
  --ros-args -r /joint_states:=/joint_cmd
```

### `gen2` nodes

| Executable | Purpose |
| --- | --- |
| `vcan_bridge` | Python CAN bridge (alternative to the C++ `hw_interface` node). |
| `joint_cmd` | Fans `/joint_cmd` out to the per-arm controllers. |
| `GravityToJointCmd` | Injects gravity feed-forward effort into commands. |
| `joint_cmd_publisher_from_joint_sates` | Echoes measured state back as commands. |
| `teach_mode_node` | Free-drive / teach mode. |
| `mode_toggler` | Switch between teach and control modes. |
| `gravity_scale_setter` | Apply the tuned per-joint `ff_scale` preset. |
| `gravity_ff_tuner` | Interactive feed-forward tuning. |
| `HomeMoveService` | Provides `/move_home`. |
| `arm_recovery_watchdog` | Auto-recovers arms after a motor fault. |
| `battery_info` | Battery telemetry. |
| `leader_controller_ui` | Leader-arm control panel. |
| `joint_cmd_web_ui` | Browser-based joint jogging. |

### Services

| Service | Type | Purpose |
| --- | --- | --- |
| `/<Arm>System/set_motor_gains` | `hw_interface/srv/SetMotorGains` | Set per-motor `kp`/`kd`. |
| `/<Arm>System/arm_recover` | `std_srvs/srv/Trigger` | Clear motor faults and re-enable the arm. |
| `/move_home` | `std_srvs/srv/Trigger` | Move both arms to the home pose. |

`<Arm>` is `LeftArm` or `RightArm`, matching the hardware component names in
[controllers.yaml](src/gen2/config/controllers.yaml).

#### Gain presets

Gains are the main tuning knob and differ sharply between modes. Motor IDs
`1–7` are the arm joints; `8` is the gripper.

```bash
# Stiff — normal operation / holding payload
ros2 service call /LeftArmSystem/set_motor_gains hw_interface/srv/SetMotorGains \
"motor_ids: [1,2,3,4,5,6,7,8]
kp: [100.0,100.0,70.0,70.0,30.0,30.0,30.0,10.0]
kd: [5.0,5.0,4.0,4.0,2.0,2.0,2.0,1.0]"

# Medium — VLA / policy inference
ros2 service call /LeftArmSystem/set_motor_gains hw_interface/srv/SetMotorGains \
"motor_ids: [1,2,3,4,5,6,7,8]
kp: [40.0,40.0,25.0,25.0,10.0,10.0,10.0,2.5]
kd: [2.0,2.0,1.5,1.5,0.5,0.5,0.5,0.25]"

# Near-zero — teach mode / free-drive
ros2 service call /LeftArmSystem/set_motor_gains hw_interface/srv/SetMotorGains \
"motor_ids: [1,2,3,4,5,6,7,8]
kp: [0.05,0.05,0.05,0.05,0.05,0.05,0.05,1.0]
kd: [0.01,0.01,0.01,0.01,0.01,0.01,0.01,0.3]"
```

Apply the same call to `/RightArmSystem/set_motor_gains` for the other arm.

#### Gravity compensation

`gravity_torque_node` (from the `dynamics` package) computes
`effort = gravity(q) * direction * ff_scale` and publishes it on
`/gravity_torque`. The per-joint feed-forward scale is a live-tunable
parameter:

```bash
ros2 param set /gravity_torque_node ff_scale.left_joint_1 0.22
ros2 param get /gravity_torque_node ff_scale.left_joint_1
```

`gen2/gravity_scale_setter` applies the full tuned preset for all 14 arm joints
in one pass and is started by the bring-up launch:

```bash
ros2 run gen2 gravity_scale_setter
```

#### Fault recovery

```bash
ros2 service call /LeftArmSystem/arm_recover std_srvs/srv/Trigger "{}"
ros2 service call /RightArmSystem/arm_recover std_srvs/srv/Trigger "{}"
```

---

## Teleoperation

### Leader–follower arms

```bash
ros2 launch gen2_leader gen2_leader.launch.py           # leader arms
ros2 launch gen2_leader gen2_leader_mirror.launch.py    # mirrored mapping
```

Individual nodes from the `gen2_leader` package:

| Executable | Purpose |
| --- | --- |
| `leader_raw` | Raw leader-arm reader over CAN. |
| `leader_serial` | Raw leader-arm reader over serial. |
| `leader_wifi` | Leader with trigger services over Wi-Fi. |
| `leader_mirror` | Mirrored leader-follower mapping over Wi-Fi. |
| `leader_torque_toggle` | Toggle torque on the leader arms. |

### VR / Meta Quest

```bash
ros2 run ros_tcp_endpoint default_server_endpoint
python3 src/scripts/quest_bridge.py
python3 src/scripts/vr_pose_relay.py
```

### Cameras

```bash
ros2 launch world_camera_launch start_all_cameras.launch.py   # all RealSense units
ros2 launch world_camera_launch world_camera.launch.py        # world camera only
```

Camera topics consumed by the recorder and the UI:

| Name | Topic |
| --- | --- |
| Left wrist | `/left/camera/color/image_raw/compressed` |
| Right wrist | `/right/camera/color/image_raw/compressed` |
| Binocular (left) | `/zed/zed_node/left/color/rect/image/compressed` |
| Binocular (right) | `/zed/zed_node/right/color/rect/image/compressed` |

---

## Data collection and replay

The `daksha_data_collection` package records joint states and camera streams to
Parquet plus chunked MP4, and replays them back onto the robot. It ships a web
UI alongside the terminal interface — see its own
[README](src/ui/Clients_UI/daksha_data_collection/README.md) for the UI and the
CycloneDDS peer-discovery setup.

```bash
ros2 launch daksha_data_collection data_collection.launch.py
```

Recording:

```bash
ros2 service call /recorder/start daksha_msgs/srv/StartRecord \
  "{dataset_name: 'terminal_demo', episode_length: 200, record_hz: 20.0, max_episodes: 1}"

ros2 service call /recorder/stop std_srvs/srv/Trigger
```

Replay:

```bash
ros2 service call /replay/start daksha_msgs/srv/StartReplay \
  "{dataset_name: 'terminal_demo', episode_index: 0, speed: 1.0}"

ros2 service call /replay/stop std_srvs/srv/Trigger
```

Teleop multiplexer (safety and leader-follower alignment):

```bash
ros2 service call /teleop_mux/mimic std_srvs/srv/Trigger   # follow the leader
ros2 service call /teleop_mux/hold  std_srvs/srv/Trigger   # hold position
```

Progress is published on `/recorder/ui_status` and `/replay/ui_status`.

> `src/custom_v3format_dataset/` is an earlier standalone recorder. Only
> compiled `.pyc` files remain in the tree — the sources are not checked in, so
> use `daksha_data_collection` instead. The historical CLI invocations are
> preserved in [docs/NOTES.md](docs/NOTES.md).

### Policy inference bridge

[src/scripts/vla_bridge.py](src/scripts/vla_bridge.py) filters policy output
before it reaches the arms: it reads predictions on `/joint_cmd_predict`, median-
filters them, and republishes to `/joint_cmd`. Each arm can be locked
independently so a policy drives one arm while the other holds.

```bash
python3 src/scripts/vla_bridge.py

ros2 service call /left_arm_trigger_handler  std_srvs/srv/Trigger "{}"
ros2 service call /right_arm_trigger_handler std_srvs/srv/Trigger "{}"
```

| Topic | Direction | Description |
| --- | --- | --- |
| `/joint_cmd_predict` | in | Raw policy predictions. |
| `/LeftArmSystem_ordered_joint_states` | in | Measured left-arm state. |
| `/RightArmSystem_ordered_joint_states` | in | Measured right-arm state. |
| `/joint_cmd` | out | Filtered command to the robot. |

The policy server itself lives outside this repository. The validation UI
expects an Isaac-GR00T virtual environment; its path is configurable via `VENV`
in [src/ui/Clients_UI/validation/run_validation_ui.sh](src/ui/Clients_UI/validation/run_validation_ui.sh).

---

## Running as a systemd service

To bring the robot up automatically on boot:

```bash
sudo tee /etc/systemd/system/gen2.service >/dev/null <<'EOF'
[Unit]
Description=Gen2 Robot Bringup
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=ihub
WorkingDirectory=/home/ihub/daksha

Environment=HOME=/home/ihub
Environment=VCAN_SUDO_PASSWORD=1234

ExecStart=/bin/bash -c 'source /opt/ros/humble/setup.bash && source /home/ihub/daksha/install/setup.bash && ros2 launch gen2 bringup.launch.py'

Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now gen2.service
```

Adjust `User` and the paths to match the target machine. `VCAN_SUDO_PASSWORD` is
used by the bridge to create the virtual CAN interfaces at startup — replace the
placeholder with the real password, and prefer a passwordless sudoers rule for
`ip link` over storing a password in the unit file.

Monitor:

```bash
sudo systemctl status gen2.service
journalctl -u gen2.service -f
```

---

## Repository layout

```
src/
├── gen2/                          # Bring-up launch, joint_cmd, teach mode, gravity scaling
├── controllers/
│   ├── hw_interface/              # ros2_control hardware interface + C++ CAN bridge
│   ├── posveleff_controllers/     # MIT-mode position/velocity/effort controller
│   ├── dynamics/                  # Gravity torque computation
│   ├── kinematics/                # FK/IK solvers
│   ├── collision_management/      # Self-collision checks
│   └── moveit_collision_management/
├── daksha_description_full_body/  # URDF, meshes, Placo IK sim
├── tele/
│   ├── gen2_leader/               # Leader-arm teleoperation
│   ├── vr_teleop/                 # VR pose relay and management UI
│   └── ROS-TCP-Endpoint/          # Unity/Quest bridge
├── ui/
│   ├── Clients_UI/
│   │   ├── daksha_ui/             # Operator web UI
│   │   ├── daksha_data_collection/# Recorder, replay and data management UI
│   │   ├── daksha_msgs/           # StartRecord / StartReplay interfaces
│   │   └── daksha_final_urdf_description/
│   └── analyzer/                  # joint_analyzer
├── gesture_management/            # Record, save and replay gesture sequences
├── global/                        # API bridges (leader / follower)
├── diagnosis/                     # vajara diagnostics, temp graphs
├── joint_cmd_logger/              # CSV logging of /joint_cmd and /jnt_cmt_to_ctrl
├── automation/                    # Web panel to launch/kill bring-up
├── navigation/                    # Web navigation site
├── world_camera_launch/           # World camera launch files
├── custom_v3format_dataset/       # Legacy recorder (compiled artifacts only)
├── scripts/                       # Standalone bridges and utilities
└── requirements.txt
```

---

## Troubleshooting

**CAN device is not accessible.** Confirm the udev rule is installed and the
adapter replugged: `lsusb | grep 04d8`. The rule matches product id `0053`; some
adapters enumerate as `1234` instead — adjust `ATTR{idProduct}` to match.

**Bridge starts but no motor feedback.** Two bridges are likely running. The C++
and Python bridges both claim the same USB device and `vcan0`/`vcan1`; stop one,
or pass `use_cpp_vcan_bridge:=false`.

**Arm does not move after a fault.** Call `arm_recover` on that arm, then
re-apply the gain preset — recovery resets gains to their defaults.

**Arm is limp or oscillating.** Wrong gain preset for the mode. Near-zero gains
are teach mode only; re-apply the stiff preset before commanding trajectories.

**Controllers fail to spawn.** Verify `robot_description` was actually loaded:
`ros2 control list_hardware_components`. An unreadable URDF path leaves the
controller manager running with no hardware.

**Relay joint commands into `/joint_states`** (for visualization without
hardware):

```bash
ros2 run topic_tools relay /joint_cmd /joint_states
```

---

## License

Apache License 2.0 — see [src/gen2/LICENSE](src/gen2/LICENSE).
