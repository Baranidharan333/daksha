# Raw operator notes

Unedited scratch notes kept from the original README. Commands here may refer to
other machines, older workspace paths, or sibling robots (astra, bipadel,
damiao_hardware_interface). Treat them as history, not as instructions.

---

# daksha



sudo nano /etc/udev/rules.d/99-canalyst.rules

SUBSYSTEM=="usb", ATTR{idVendor}=="04d8", ATTR{idProduct}=="0053", MODE="0666"

sudo udevadm control --reload-rules
sudo udevadm trigger


sudo nano /etc/systemd/system/gen2.service

[Unit]
Description=Gen2 Robot Bringup
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=ihub
WorkingDirectory=/home/ihub/.barani/gen2_full

Environment=HOME=/home/ihub
Environment=VCAN_SUDO_PASSWORD=1234

ExecStart=/bin/bash -c 'source /opt/ros/humble/setup.bash && source /home/ihub/.barani/gen2_full/install/setup.bash && ros2 launch gen2 bringup.launch.py'

Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target

sudo systemctl daemon-reload

sudo systemctl enable gen2.service

sudo systemctl start gen2.service


sudo systemctl status gen2.service

journalctl -u gen2.service -f


#!/usr/bin/env bash
set -e

echo "========================================="
echo " Updating apt packages"
echo "========================================="
sudo apt update

echo "========================================="
echo " Installing system dependencies"
echo "========================================="
sudo apt install -y \
    python3-pip \
    python3-dev \
    python3-venv \
    python3-setuptools \
    python3-wheel \
    python3-packaging \
    build-essential \
    cmake \
    ninja-build \
    git \
    pkg-config \
    libgl1 \
    libglib2.0-0 \
    libxcb-xinerama0 \
    libxkbcommon-x11-0 \
    libegl1 \
    libdbus-1-3 \
    libfontconfig1 \
    qt6-base-dev

echo "========================================="
echo " Upgrading pip packages"
echo "========================================="
python3 -m pip install --user --upgrade \
    pip \
    setuptools==79.0.1 \
    wheel \
    packaging \
    sip \
    pyqt6-sip

export PATH=$HOME/.local/bin:$PATH

echo "========================================="
echo " Installing requirements"
echo "========================================="
python3 -m pip install \
    --user \
    --no-build-isolation \
    -r requirements.txt

echo "========================================="
echo " Done"
echo "========================================="
python3 -m pip install --user pyarrow



sudo apt update
sudo apt install ros-humble-joint-state-publisher-gui


python3 -m pip install --user \
    PyQt6==6.7.1 \
    PyQt6-Qt6 \
    PyQt6-sip


ros2 service call \
/LeftArmSystem/set_motor_gains \
hw_interface/srv/SetMotorGains \
"motor_ids: [1,2,3,4,5,6,7]
kp: [300.0,300.0,300.0,300.0,100.0,100.0,80.0]
kd: [3.0,3.0,3.0,3.0,1.0,1.0,1]"


ros2 service call \
/RightArmSystem/set_motor_gains \
hw_interface/srv/SetMotorGains \
"motor_ids: [1,2,3,4,5,6,7]
kp: [300.0,300.0,300.0,300.0,100.0,100.0,80.0]
kd: [3.0,3.0,3.0,3.0,1.0,1.0,1]"

sudo apt update
sudo apt install ros-humble-topic-tools



/home/ihub/.barani/gen2_full/src/gen2/gen2/joint_cmd.py

in this code Last login: Thu Aug  6 19:33:21 2026 from 192.168.200.239
ihub@s1:~$ ros2 topic echo /joint_cmd --once
header:
  stamp:
    sec: 1786025024
    nanosec: 241310029
  frame_id: ''
name:
- right_joint_1
- right_joint_2
- right_joint_3
- right_joint_4
- right_joint_5
- right_joint_6
- right_joint_7
- left_joint_1
- left_joint_2
- left_joint_3
- left_joint_4
- left_joint_5
- left_joint_6
- left_joint_7
position:
- -0.00013976920000002835
- -0.00022684019999985594
- 0.0
- 0.758589869
- 0.0
- 0.0
- 0.0
- -0.0003489230000006671
- -0.00022684019999985594
- 0.0
- 0.0
- 0.0
- 0.0
- 0.0
velocity: []
effort: []
---
ihub@s1:~$ ros2 topic echo /jnt_cmt_to_ctrl --once
header:
  stamp:
    sec: 1786025032
    nanosec: 355107307
  frame_id: ''
name:
- left_joint_1
- left_joint_2
- left_joint_3
- left_joint_4
- left_joint_5
- left_joint_6
- left_joint_7
- right_joint_1
- right_joint_2
- right_joint_3
- right_joint_4
- right_joint_5
- right_joint_6
- right_joint_7
- left_gripper_left_joint
- right_gripper_right_joint
position:
- -0.00028973592014463296
- -0.00027527473245020253
- 4.9502540064744256e-05
- -4.9502540064744256e-05
- 3.3779787568995964e-05
- 0.0
- 4.839683715827577e-05
- -0.00019403419439994286
- -0.00017654991055183526
- -4.9502540064744256e-05
- 0.758548677795424
- -4.462255135589704e-05
- 5.272701457094674e-05
- -3.3779787568995964e-05
- 0.0
- 0.0
velocity:
- 0.04000104983202085
- -0.039996045994066934
- 0.03999958457161213
- -0.03999958457161213
- 0.040003585684987845
- 0.0
- 0.040001124760848515
- -0.04000088808528082
- 0.04000085645628521
- -0.03999958457161213
- -0.04002706410652747
- -0.0400004620049039
- 0.04000197973592172
- -0.040003585684987845
- 0.0
- 0.0
effort:
- 0.04851237412433247
- 0.058179507644962554
- 0.000285536011876009
- 0.06584887206302312
- -0.0013521976697640724
- -0.0708341762699193
- -0.09787162411452406
- 0.5453584999335747
- -0.02124339632974317
- 0.00012509439261484552
- -0.8696750365676137
- -0.09877608409385856
- 0.7141037540968213
- 0.0877350629770624
- 0.0
- 0.0







ros2 launch gen2 bringup.launch.py

python3 .barani/.gen2/src/scripts/vcan_bridge.py


/home/jetson/Desktop/camera/start_realsense.sh


/home/jetson/Desktop/camera/start_zed.sh


python3 .barani/.gen2/src/scripts/vivaka.py




links:

  base_link:
    mass: 1.0

  right_link_2_1:
    mass: 1.091

  right_link_3_1:
    mass: 0.250

  right_link_4_1:
    mass: 1.103

  right_link_5_1:
    mass: 0.577

  right_link_6_1:
    mass: 0.402

  right_link_7_1:
    mass: 0.542

  right_link_8_1:
    mass: 0.466

  left_link_2_1:
    mass: 1.091

  left_link_3_1:
    mass: 0.250

  left_link_4_1:
    mass: 1.103

  left_link_5_1:
    mass: 0.577

  left_link_6_1:
    mass: 0.402

  left_link_7_1:
    mass: 0.542

  left_link_8_1:
    mass: 0.466

  right_gripper_mount_1:
    mass: 0.250

  left_gripper_mount_1:
    mass: 0.250

  left_405_1:
    mass: 0.057

  right_405_1:
    mass: 0.057

  right_gripper_right_finger_1:
    mass: 0.030

  right_gripper_left_finger_1:
    mass: 0.030

  left_gripper_right_finger_1:
    mass: 0.030

  left_gripper_left_finger_1:
    mass: 0.030

  left_link_1_1:
    mass: 1.050

  right_link_1_1:
    mass: 1.050


ros2 topic pub -1 /joint_cmd sensor_msgs/msg/JointState "{name: ['right_gripper_right_joint'], position: [-0.044]}"

#open
ros2 topic pub -1 /joint_cmd sensor_msgs/msg/JointState "{name: ['right_gripper_right_joint'], position: [0.0]}"


ros2 topic pub -1 /joint_cmd sensor_msgs/msg/JointState "{name: ['left_gripper_left_joint'], position: [0.044]}"


ros2 topic pub -1 /joint_cmd sensor_msgs/msg/JointState "{name: ['left_gripper_left_joint'], position: [0.0]}"


 python3 gen2_ws/src/scripts/vcan_bridge.py 



ros2 launch gen2 bringup.launch.py 

ros2  launch gen2_leader gen2_leader_mirror.launch.py


python3 -m custom_v3format_dataset.ros2_topic_recorder \
  --root-dir /home/jetson/Documents/dataset \
  --dataset-name task1 \
  --task "place the blue box on to the table." \
  --prompt "place the blue box on to the table." \
  --episode-len 300 \
  --record-hz 30 \
  --fps 30
  
  
  python3 custom_v3format_dataset/ros2_topic_replay.py \
  --root-dir /home/jetson/Documents/dataset \
  --dataset-name task1 \
  --episode-index 1 \
  --speed 1.0 \
  --follower-cmd-topic /joint_cmd \
  --follower-cmd-msg-type joint_state
  
  
while true; do
    ros2 topic pub -1 /joint_cmd sensor_msgs/msg/JointState "{name: ['right_gripper_right_joint'], position: [-0.044]}"
    ros2 topic pub -1 /joint_cmd sensor_msgs/msg/JointState "{name: ['right_gripper_right_joint'], position: [0.0]}"
    ros2 topic pub -1 /joint_cmd sensor_msgs/msg/JointState "{name: ['left_gripper_left_joint'], position: [0.044]}"
    ros2 topic pub -1 /joint_cmd sensor_msgs/msg/JointState "{name: ['left_gripper_left_joint'], position: [0.0]}"
    sleep 1
done


ros2 run topic_tools relay /joint_cmd /joint_states


/status/health
CAMERA_TOPICS = {
    zed_right": "/zed/zed_node/right/color/rect/image/compressed",
    zed_left": "/zed/zed_node/left/color/rect/image/compressed",
    wrist_right": "/right/camera/color/image_raw/compressed",
    wrist_left": "/left/camera/color/image_raw/compressed",
}

ros2 run topic_tools relay /joint_cmd /joint_states


ros2 topic pub /arm_controller/joint_trajectory trajectory_msgs/msg/JointTrajectory "
joint_names: ['joint1']
points:
- positions: [1.0]
  time_from_start: {sec: 0.2}
" --once

source /opt/ros/humble/setup.bash
source ~/damiao_hardware_interface/install/setup.bash

ros2 control list_hardware_components

ros2 control list_controllers


ros2 run controller_manager ros2_control_node   --ros-args   --params-file ~/damiao_hardware_interface/src/robot_desctiption/config/controller.yaml   -p robot_description:="$(cat ~/damiao_hardware_interface/src/robot_desctiption/urdf/joint_test.urdf)"


ros2 run robot_state_publisher robot_state_publisher \
  --ros-args \
  -p robot_description:="$(cat ~/damiao_hardware_interface/src/robot_desctiption/urdf/joint_test.urdf)"
  
  
  
  
  
  
  
  
  
  




ros2 control load_controller joint_state_broadcaster
ros2 control load_controller arm_controller

ros2 control set_controller_state joint_state_broadcaster inactive
ros2 control set_controller_state arm_controller inactive

ros2 control set_controller_state joint_state_broadcaster active
ros2 control set_controller_state arm_controller active




rm -rf build install log
colcon build
source install/setup.bash

ros2 run controller_manager ros2_control_node   --ros-args   --params-file ~/damiao_hardware_interface/src/robot_desctiption/config/controller.yaml   -p robot_description:="$(cat ~/damiao_hardware_interface/src/robot_desctiption/urdf/joint_test.urdf)"


/home/baranidharan/hw_interface_daksha


ros2 run controller_manager ros2_control_node   --ros-args   --params-file ~/hw_interface_daksha/src/robot_desctiption/config/controller.yaml   -p robot_description:="$(cat ~/hw_interface_daksha/src/robot_desctiption/urdf/joint_test.urdf)"


damiao gui --host 192.168.200.153

sudo ip link set can0 down
sudo ip link set can0 type can bitrate 1000000
sudo ip link set can0 up

damiao scan



ros2 topic pub /arm_controller/joint_trajectory trajectory_msgs/msg/JointTrajectory "
joint_names: ['joint1', 'joint2']
points:
- positions: [1.0, .0220,]
  time_from_start: {sec: 1}
" --once


ros2 topic pub /arm_controller/joint_trajectory trajectory_msgs/msg/JointTrajectory "
joint_names: ['joint1', 'joint2','joint3']
points:
- positions: [5.0, 5.0, 5.0]
  time_from_start: {sec: 1}
" --once



ros2 topic pub /arm_controller/joint_trajectory trajectory_msgs/msg/JointTrajectory "
joint_names: ['joint1', 'joint2']
points:
- positions: [3.0, 3.0]
  time_from_start: {sec: 1}
" --once

ros2 topic pub /arm_controller/joint_trajectory trajectory_msgs/msg/JointTrajectory "
joint_names: ['joint1', 'joint2']
points:
- positions: [-3.0, -3.0]
  time_from_start: {sec: 1}
" --once


ros2 service call /arm_recover std_srvs/srv/Trigger





source /opt/ros/humble/setup.bash

source ~/damiao_hardware_interface/install/setup.bash

ros2 run controller_manager ros2_control_node \
  --ros-args \
  --params-file ~/damiao_hardware_interface/src/robot_desctiption/config/controller.yaml \
  -p robot_description:="$(cat ~/damiao_hardware_interface/src/robot_desctiption/urdf/joint_test.urdf)"
  
  
  source /opt/ros/humble/setup.bash
source ~/damiao_hardware_interface/install/setup.bash


ros2 control load_controller \
--set-state active \
joint_state_broadcaster

ros2 control load_controller \
--set-state active joint_cmd


ros2 service call /set_motor_gains \
hw_interface/srv/SetMotorGains "
motor_ids: [1, 2]
kp: [0.3, 0.3]
kd: [0.005, 0.005]
"

ros2 service call /set_motor_gains hw_interface/srv/SetMotorGains "
motor_ids: [1, 2]
kp: [5, 5]
kd: [0.5, 0.5]
"


ros2 topic pub /joint_cmd/commands \
std_msgs/msg/Float64MultiArray "
data: [1.0, 0.22]
" --once



asthara

ros2 run controller_manager ros2_control_node \
  --ros-args \
  --params-file ~/damiao_hardware_interface/src/robot_desctiption/config/controller.yaml \
  -p robot_description:="$(cat ~/damiao_hardware_interface/src/Asthra_description/urdf/robot.urdf)"
  
  
damiao_hardware_interface/src/Asthra_description/urdf/robot.urdf


ros2 run robot_state_publisher robot_state_publisher \
  --ros-args \
  -p robot_description:="$(cat ~/damiao_hardware_interface/src/Asthra_description/urdf/robot.urdf)"
  
  ==================================================================================================================================
  
  
  gen2
  
    


 cd /home/baranidharan/gen2
 source ./install/setup.bash
  
  
  /home/baranidharan/gen2/src/daksha_description/config/controller.yaml
  
  
  /home/baranidharan/gen2/src/daksha_description/urdf/right.urdf
  
  
  right
  
  ros2 run controller_manager ros2_control_node \
  --ros-args \
  --params-file ~/gen2/src/daksha_description/config/controller_bk.yaml \
  -p robot_description:="$(cat /home/baranidharan/gen2/src/daksha_description/urdf/right.urdf)"
  
  
  
  ros2 run robot_state_publisher robot_state_publisher \
  --ros-args \
  -p robot_description:="$(cat /home/baranidharan/gen2/src/daksha_description/urdf/right.urdf)"
  
  left
  
    ros2 run controller_manager ros2_control_node \
  --ros-args \
  --params-file ~/gen2/src/daksha_description/config/controller_left.yaml \
  -p robot_description:="$(cat /home/baranidharan/gen2/src/daksha_description/urdf/left.urdf)"
  
  
  
  ros2 run robot_state_publisher robot_state_publisher \
  --ros-args \
  -p robot_description:="$(cat /home/baranidharan/gen2/src/daksha_description/urdf/left.urdf)"
  
  both
  /home/baranidharan/gen2/src/daksha_description/urdf/dual_arm.urdf
  /home/baranidharan/gen2/src/daksha_description/config/controller.yaml
  
  ros2 run controller_manager ros2_control_node \
  --ros-args \
  --params-file ~/gen2/src/daksha_description/config/controller.yaml \
  -p robot_description:="$(cat /home/baranidharan/gen2/src/daksha_description/urdf/dual_arm.urdf)"
  
    ros2 run robot_state_publisher robot_state_publisher \
  --ros-args \
  -p robot_description:="$(cat /home/baranidharan/gen2/src/daksha_description/urdf/dual_arm.urdf)"
  
  ros2 control load_controller \
--set-state active \
left_arm_controller

ros2 control load_controller \
--set-state active \
right_arm_controller
  
  ros2 control load_controller \
--set-state active \
joint_state_broadcaster

ros2 service call \
/LeftArmSystem/set_motor_gains \
hw_interface/srv/SetMotorGains \
"motor_ids: [1,2,3,4,5,6,7,8]
kp: [15.0,15.0,15.0,15.0,15.0,15.0,15.0,15.0]
kd: [1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0]"


ros2 service call \
/RightArmSystem/set_motor_gains \
hw_interface/srv/SetMotorGains \
"motor_ids: [1,2,3,4,5,6,7,8]
kp: [15.0,15.0,15.0,15.0,15.0,15.0,15.0,15.0]
kd: [1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0]"


ros2 service call \
/RightArmSystem/set_motor_gains \
hw_interface/srv/SetMotorGains \
"motor_ids: [1,2,3,4,5,6,7,8]
kp: [0.05,0.05,0.05,0.05,0.05,0.05,0.05,0.05]
kd: [0.01,0.01,0.01,0.01,0.01,0.01,0.01,0.01]"


ros2 service call \
/LeftArmSystem/set_motor_gains \
hw_interface/srv/SetMotorGains \
"motor_ids: [1,2,3,4,5,6,7,8]
kp: [0.05,0.05,0.05,0.05,0.05,0.05,0.05,0.05]
kd: [0.01,0.01,0.01,0.01,0.01,0.01,0.01,0.01]"

ros2 service call \
/LeftArmSystem/set_motor_gains \
hw_interface/srv/SetMotorGains \
"motor_ids: [1,2,3,4,5,6,7,8]
kp: [30.0,30.0,30.0,30.0,30.0,30.0,30.0,30.0]
kd: [2.0,2.0,2.0,2.0,2.0,2.0,2.0,2.0]"


ros2 service call \
/AstraArmSystem/set_motor_gains \
hw_interface/srv/SetMotorGains \
"motor_ids: [1,2,3,4,5,6]
kp: [30.0,30.0,30.0,30.0,30.0,3.0]
kd: [2.0,2.0,2.0,2.0,2.0,2.0]"


ros2 service call \
/RightArmSystem/set_motor_gains \
hw_interface/srv/SetMotorGains \
"motor_ids: [1,2,3,4,5,6,7,8]
kp: [30.0,30.0,30.0,30.0,30.0,30.0,30.0,30.0]
kd: [2.0,2.0,2.0,2.0,2.0,2.0,2.0,2.0]"

ros2 service call \
/LeftArmSystem/set_motor_gains \
hw_interface/srv/SetMotorGains \
"motor_ids: [1,2,3,4,5,6,7,8]
kp: [70.0,70.0,50.0,50.0,30.0,30.0,30.0,10.0]
kd: [4.0,4.0,3.0,3.0,2.0,2.0,2.0,1.0]"

ros2 service call \
/RightArmSystem/set_motor_gains \
hw_interface/srv/SetMotorGains \
"motor_ids: [1,2,3,4,5,6,7,8]
kp: [70.0,70.0,50.0,50.0,30.0,30.0,30.0,10.0]
kd: [4.0,4.0,3.0,3.0,2.0,2.0,2.0,1.0]"

ros2 service call \
/LeftArmSystem/set_motor_gains \
hw_interface/srv/SetMotorGains \
"motor_ids: [1,2,3,4,5,6,7,8]
kp: [100.0,100.0,70.0,70.0,30.0,30.0,30.0,10.0]
kd: [5.0,5.0,4.0,4.0,2.0,2.0,2.0,1.0]"

ros2 service call \
/RightArmSystem/set_motor_gains \
hw_interface/srv/SetMotorGains \
"motor_ids: [1,2,3,4,5,6,7,8]
kp: [100.0,100.0,70.0,70.0,30.0,30.0,30.0,10.0]
kd: [5.0,5.0,4.0,4.0,2.0,2.0,2.0,1.0]"




ros2 topic pub --once /left_arm_controller/commands std_msgs/msg/Float64MultiArray "
data:
- 0.0
- 0.0
- 0.0
- 0.0
- 0.0
- 0.0
- 0.0
"

ros2 topic pub --once /right_arm_controller/commands std_msgs/msg/Float64MultiArray "
data:
- 0.0
- 0.0
- 0.0
- 0.0
- 0.0
- 0.0
- 0.0
"

ros2 service call /recording joint_parquet_recorder/srv/StartRecording \
"{topic_name: '/joint_states', recording_name: 'test_run', action: 'start'}"
ros2 service call /recording joint_parquet_recorder/srv/StartRecording \
"{topic_name: '/LeftArmSystem_ordered_joint_states', recording_name: 'test_run', action: 'stop'}"
ros2 service call /replay_recording joint_parquet_recorder/srv/ReplayRecording "{recording_name: 'test_run', output_topic: '/joint_cmd', replay_speed: 1.0}"
ros2 service call /replay_recording \
joint_parquet_recorder/srv/ReplayRecording \
"{recording_name: 'test_run', output_topic: '/right_arm_controller/commands', replay_speed: 1.0}"

ros2 run joint_state_publisher_gui joint_state_publisher_gui \
--ros-args \
-r /joint_states:=/joint_cmd

python3 gen2/src/scripts/test.py


/home/baranidharan/gen2/src/daksha_description/urdf/karthika_arm.urdf

/home/baranidharan/gen2/src/moveit_config/config/ros2_controllers.yaml

  ros2 run controller_manager ros2_control_node \
  --ros-args \
  --params-file /home/baranidharan/gen2/src/moveit_config/config/ros2_controllers.yaml \
  -p robot_description:="$(cat /home/baranidharan/gen2/src/daksha_description/urdf/karthika_arm.urdf)"
  
    ros2 run robot_state_publisher robot_state_publisher \
  --ros-args \
  -p robot_description:="$(cat /home/baranidharan/gen2/src/daksha_description/urdf/karthika_arm.urdf)"


ros2 control load_controller --set-state active joint_state_broadcaster && ros2 control load_controller --set-state active left_arm_controller && ros2 control load_controller --set-state active right_arm_controller && ros2 control load_controller --set-state active left_gripper_controller && ros2 control load_controller --set-state active right_gripper_controller


ros2 topic pub /left_arm_target geometry_msgs/PoseStamped "
pose:
  position:
    x: 0.35
    y: 0.25
    z: 1.1
  orientation:
    x: 0.0
    y: 0.0
    z: 0.0
    w: 1.0
" --once


can
python3 gen2/src/scripts/test.py

python3 gen2/src/scripts/quest_bridge.py

ros2 run ros_tcp_endpoint default_server_endpoint
python3 quest/src/scripts/main1.py


python3 JointCommandBridge.py
python3 ik_solver.py

ros2 run robot_state_publisher robot_state_publisher \
--ros-args \
-p robot_description:="$(cat /home/baranidharan/gen2/src/daksha_description/urdf/karthika_arm.urdf)" \
-r /joint_states:=/joint_states_ik \
-r /robot_description:=/robot_description_ik


ros2 service call \
/LeftArmSystem/gravity_compensation \
std_srvs/srv/SetBool \
"{data: true}"

ros2 service call \
/LeftArmSystem/gravity_compensation \
std_srvs/srv/SetBool \
"{data: false}"

ros2 service call \
/LeftArmSystem/gravity_scale \
hw_interface/srv/SetGravityScale \
"{percentage: 50.0}"

ros2 service call \
/LeftArmSystem/gravity_scale \
hw_interface/srv/SetGravityScale \
"{percentage: 100.0}"


ros2 service call /RightArmSystem/arm_recover std_srvs/srv/Trigger "{}"
ros2 service call /LeftArmSystem/arm_recover std_srvs/srv/Trigger "{}"

  ===========================================
  
  bipadel
  
  
 cd /home/baranidharan/bipadel
 source ./install/setup.bash
  
/home/baranidharan/bipadel/src/config/controllers.yaml
  
  
/home/baranidharan/bipadel/src/restleg_arm/robot_with_hw.urdf
  
  
  ros2 run controller_manager ros2_control_node \
  --ros-args \
  --params-file /home/baranidharan/bipadel/src/config/controllers.yaml \
  -p robot_description:="$(cat /home/baranidharan/bipadel/src/restleg_arm/robot_with_hw.urdf)"
  
  
  
  ros2 run robot_state_publisher robot_state_publisher \
  --ros-args \
  -p robot_description:="$(cat /home/baranidharan/bipadel/src/restleg_arm/robot_with_hw.urdf)"
  
  
ros2 control load_controller \
--set-state active \
joint_state_broadcaster

ros2 control load_controller \
--set-state active joint_cmd

cd /home/jetson/.barani/.bipadel
 source ./install/setup.bash
 
 /home/jetson/.barani/.bipadel/src/config/controllers.yaml
 /home/jetson/.barani/.bipadel/src/restleg_arm/robot_with_hw.urdf
 
   
  ros2 run controller_manager ros2_control_node \
  --ros-args \
  --params-file /home/jetson/.barani/.bipadel/src/config/controllers.yaml \
  -p robot_description:="$(cat /home/jetson/.barani/.bipadel/src/restleg_arm/robot_with_hw.urdf)"
  
  
    ros2 run robot_state_publisher robot_state_publisher \
  --ros-args \
  -p robot_description:="$(cat  /home/jetson/.barani/.bipadel/src/restleg_arm/robot_with_hw.urdf)"
  
  
 
===============================================================================



  
  =================================================================================
  
  
  damiao set-motor-id --current 11 --target 15
  
  

sudo modprobe vcan

sudo ip link add dev vcan0 type vcan
sudo ip link add dev vcan1 type vcan

sudo ip link set up vcan0
sudo ip link set up vcan1

python3 /home/baranidharan/gen2/src/scripts/bridge_can0.py
python3 /home/baranidharan/gen2/src/scripts/bridge_can1.py

sudo nano /etc/udev/rules.d/99-canalyst.rules


SUBSYSTEM=="usb", ATTR{idVendor}=="04d8", ATTR{idProduct}=="0053", MODE="0666"

sudo udevadm control --reload-rules
sudo udevadm trigger



ros2 service call \
/LeftArmSystem/gravity_compensation \
std_srvs/srv/SetBool \
"{data: true}"

ros2 service call \
/LeftArmSystem/gravity_compensation \
std_srvs/srv/SetBool \
"{data: false}"



cd /home/deeptech/.barani/.gen2
source ./install/setup.bash


source ~/.barani/.gen2/install/setup.bash


can
python3 /home/deeptech/.barani/.gen2/src/scripts/vcan_bridge.py

ros2 launch gen2 bringup.launch.py


ros2 run b1_leader leader_with_service

ros2 topic pub --once /left_gripper_controller/commands std_msgs/msg/Float64MultiArray \
"{data: [0.04]}"

ros2 service call \
/LeftArmSystem/set_motor_gains \
hw_interface/srv/SetMotorGains \
"motor_ids: [1,2,3,4,5,6,7,8]
kp: [80.0,80.0,50.0,50.0,20.0,20.0,20.0,5.0]
kd: [4.0,4.0,3.0,3.0,1.0,1.0,1.0,0.5]"



ros2 service call \
/RightArmSystem/set_motor_gains \
hw_interface/srv/SetMotorGains \
"motor_ids: [1,2,3,4,5,6,7,8]
kp: [80.0,80.0,50.0,50.0,20.0,20.0,20.0,5.0]
kd: [4.0,4.0,3.0,3.0,1.0,1.0,1.0,0.5]"

ros2 service call \
/LeftArmSystem/set_motor_gains \
hw_interface/srv/SetMotorGains \
"motor_ids: [1,2,3,4,5,6,7,8]
kp: [0.05,0.05,0.05,0.05,0.05,0.05,0.05,1]
kd: [0.01,0.01,0.01,0.01,0.01,0.01,0.01,0.3]"



ros2 service call \
/RightArmSystem/set_motor_gains \
hw_interface/srv/SetMotorGains \
"motor_ids: [1,2,3,4,5,6,7,8]
kp: [0.05,0.05,0.05,0.05,0.05,0.05,0.05,1]
kd: [0.01,0.01,0.01,0.01,0.01,0.01,0.01,0.3]"



inference
ros2 service call \
/LeftArmSystem/set_motor_gains \
hw_interface/srv/SetMotorGains \
"motor_ids: [1,2,3,4,5,6,7,8]
kp: [10.0,10.0,7.0,7.0,3.0,3.0,3.0,1.0]
kd: [2.0,2.0,1.0,1.0,0.5,0.5,2.0,0.2]"

ros2 service call \
/RightArmSystem/set_motor_gains \
hw_interface/srv/SetMotorGains \
"motor_ids: [1,2,3,4,5,6,7,8]
kp: [10.0,10.0,7.0,7.0,3.0,3.0,3.0,1.0]
kd: [2.0,2.0,1.0,1.0,0.5,0.5,2.0,0.2]"

ros2 service call /RightArmSystem/arm_recover std_srvs/srv/Trigger "{}"
ros2 service call /LeftArmSystem/arm_recover std_srvs/srv/Trigger "{}"



================================astra===============================




/home/baranidharan/astra/src/astra_description/urdf/robot.urdf
  ros2 run controller_manager ros2_control_node \
  --ros-args \
  --params-file /home/baranidharan/astra/src/astra/config/controllers.yaml \
  -p robot_description:="$(cat /home/baranidharan/astra/src/astra_description/urdf/robot.urdf)"
  
    ros2 run robot_state_publisher robot_state_publisher \
  --ros-args \
  -p robot_description:="$(cat /home/baranidharan/astra/src/astra_description/urdf/robot.urdf)"


ros2 control load_controller --set-state active joint_state_broadcaster && \
ros2 control load_controller --set-state active arm_controller && \
ros2 control load_controller --set-state active gripper_controller

ros2 topic pub --once /arm_controller/commands std_msgs/msg/Float64MultiArray \
"{data: [0.0, 1.0, -0.5, 0.3, 0.0]}"
ros2 topic pub --once /arm_controller/commands std_msgs/msg/Float64MultiArray \
"{data: [0.0, 1.0, -0.5, 0.3, 0.0]}"
ros2 topic pub --once /gripper_controller/commands std_msgs/msg/Float64MultiArray \
"{data: [0.07]}"
ros2 topic pub --once /gripper_controller/commands std_msgs/msg/Float64MultiArray \
"{data: [0.0]}"

ros2 service call \
/AstraArmSystem/set_motor_gains \
hw_interface/srv/SetMotorGains \
"motor_ids: [1,2,3,4,5,6]
kp: [10.0,10.0,7.0,7.0,3.0,3.0]
kd: [1.0,1.0,1.0,1.0,0.5,0.5]"

ros2 service call \
/AstraArmSystem/set_motor_gains \
hw_interface/srv/SetMotorGains \
"motor_ids: [1,2,3,4,5,6]
kp: [15.0,15.0,10.0,10.0,10.0,3.0]
kd: [1.0,1.0,1.0,1.0,0.5,0.5]"

ros2 service call \
/AstraArmSystem/set_motor_gains \
hw_interface/srv/SetMotorGains \
"motor_ids: [1,2,3,4,5,6]
kp: [10.0,10.0,7.0,7.0,3.0,3.0]
kd: [1.0,1.0,1.0,1.0,0.5,0.5]"


vla


python3 /home/deeptech/.barani/.gen2/src/scripts/gripper_controller_vla.py
python3 /home/deeptech/.barani/.gen2/src/scripts/vla_bridge.py

python3 /home/deeptech/.barani/.gen2/src/scripts/usb_gripper_handler.py

ros2 topic pub --once /left_gripper_controller/commands \
std_msgs/msg/Float64MultiArray \
"{data: [0.044]}"
ros2 topic pub --once /right_gripper_controller/commands \
std_msgs/msg/Float64MultiArray \
"{data: [0.044]}"

ros2 topic pub --once /left_gripper_controller/commands \
std_msgs/msg/Float64MultiArray \
"{data: [0.0]}"
ros2 topic pub --once /right_gripper_controller/commands \
std_msgs/msg/Float64MultiArray \
"{data: [0.00]}"


./Desktop/DataCollection_b2/start_all_rgb_cameras.sh

ros2 topic pub --once /gr00t_instruction std_msgs/msg/String \
"{data: 'Both arms grasp the blue box from the table and hold it securely'}"

ros2 topic pub --once /gr00t_instruction std_msgs/msg/String \
"{data: 'place the blue box on to the table'}"

ros2 topic pub --once /gr00t_instruction std_msgs/msg/String \
"{data: 'STOP'}"


python3 /home/deeptech/.barani/.gen2/src/scripts/vla_bridge.py

ros2 topic pub /gripper_trigger_handler std_msgs/msg/String "{data: 'RIGHT'}" --once

ros2 topic pub /gripper_trigger_handler std_msgs/msg/String "{data: 'LEFT'}" --once

cd /home/deeptech/Documents/groot/Isaac-GR00T
source .venv/bin/activate
POLICY_HOST=192.168.200.208 \
POLICY_PORT=5555 \
LANG_INSTRUCTION="Both arms grasp the blue box from the table and hold it securely." \
bash examples/daksha_b1/run_system_b_daksha_b1_ros2.sh

cd /home/deeptech/Documents/groot/Isaac-GR00T
source .venv/bin/activate
POLICY_HOST=192.168.200.208 \
POLICY_PORT=5555 \
LANG_INSTRUCTION="Both arms grasp the blue box from the table and hold it securely." \
bash examples/daksha_b1/run_system_b_daksha_b1_ros2.sh

cd /home/deeptech/Documents/groot/Isaac-GR00T
source .venv/bin/activate
POLICY_HOST=192.168.200.206 POLICY_PORT=5555 LANG_INSTRUCTION="place the box on the table." bash examples/daksha_b1/run_system_b_daksha_b1_ros2.sh

topic based
/home/deeptech/Documents/groot/Isaac-GR00T/gr00t/eval/real_robot/daksha_b1/eval_daksha_b1_ros2_topic_inst.py

POLICY_HOST=192.168.200.208 POLICY_PORT=5555 \
LANG_INSTRUCTION="Both arms grasp the blue box from the table and hold it securely." \
bash examples/daksha_b1/run_system_b_daksha_b1_ros2_topic_inst.sh





python3 /home/deeptech/.barani/.gen2/src/scripts/vcan_bridge.py

ros2 launch gen2 bringup.launch.py

ros2 launch b1_leader leader.launch.py 

./Desktop/DataCollection_b2/start_all_rgb_cameras.sh


ros2 run b1_leader leader_with_service

ros2 run b1_leader  leader_torque_toggle









ros2 service call /right_arm_trigger_handler std_srvs/srv/Trigger "{}"

ros2 service call /left_arm_trigger_handler std_srvs/srv/Trigger "{}"

ros2 service call /move_home std_srvs/srv/Trigger {}

os2 launch b1_leader leader_mirror.launch.py


python3 /home/deeptech/.barani/.gen2/src/scripts/HomeMoveService.py

python3 /home/deeptech/.barani/.gen2/src/scripts/vla_bridge.py

ros2 service call \
/LeftArmSystem/set_motor_gains \
hw_interface/srv/SetMotorGains \
"motor_ids: [1,2,3,4,5,6,7,8]
kp: [40.0,40.0,25.0,25.0,10.0,10.0,10.0,2.5]
kd: [2.0,2.0,1.5,1.5,0.5,0.5,0.5,0.25]"

ros2 service call \
/RightArmSystem/set_motor_gains \
hw_interface/srv/SetMotorGains \
"motor_ids: [1,2,3,4,5,6,7,8]
kp: [40.0,40.0,25.0,25.0,10.0,10.0,10.0,2.5]
kd: [2.0,2.0,1.5,1.5,0.5,0.5,0.5,0.25]"



python3 .barani/.gen2/src/scripts/vcan_bridge.py

ros2 launch gen2 bringup.launch.py


ros2 launch gen2_leader gen2_leader_mirror.launch.py



============================================================================================================

ros2 topic pub --once /left_arm_mit_controller/joint_trajectory trajectory_msgs/msg/JointTrajectory "
joint_names:
- daksha_left_joint1
- daksha_left_joint2
- daksha_left_joint3
- daksha_left_joint4
- daksha_left_joint5
- daksha_left_joint6
- daksha_left_joint7
points:
- positions: [0.2, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
  velocities: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
  effort: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
  time_from_start:
    sec: 2
"

ros2 topic pub --once /right_arm_mit_controller/joint_trajectory trajectory_msgs/msg/JointTrajectory "
joint_names:
- daksha_right_joint1
- daksha_right_joint2
- daksha_right_joint3
- daksha_right_joint4
- daksha_right_joint5
- daksha_right_joint6
- daksha_right_joint7
points:
- positions: [0.2, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
  velocities: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
  effort: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
  time_from_start:
    sec: 2
"

ros2 topic pub --once /right_gripper_mit_controller/joint_trajectory trajectory_msgs/msg/JointTrajectory "
joint_names:
- daksha_right_finger_joint1
points:
- positions: [0.03]
  velocities: [0.0]
  effort: [0.0]
  time_from_start:
    sec: 2
"

ros2 topic pub --once /right_gripper_mit_controller/joint_trajectory trajectory_msgs/msg/JointTrajectory "
joint_names:
- daksha_right_finger_joint1
points:
- positions: [0.0]
  velocities: [0.0]
  effort: [0.0]
  time_from_start:
    sec: 2
"
ros2 topic pub --once /left_gripper_mit_controller/joint_trajectory trajectory_msgs/msg/JointTrajectory "
joint_names:
- daksha_left_finger_joint1
points:
- positions: [0.03]
  velocities: [0.0]
  effort: [0.0]
  time_from_start:
    sec: 2
"
ros2 topic pub --once /left_gripper_mit_controller/joint_trajectory trajectory_msgs/msg/JointTrajectory "
joint_names:
- daksha_left_finger_joint1
points:
- positions: [0.0]
  velocities: [0.0]
  effort: [0.0]
  time_from_start:
    sec: 2
"
ros2 topic pub --once /left_arm_mit_controller/joint_trajectory trajectory_msgs/msg/JointTrajectory "
joint_names:
- daksha_left_joint1
- daksha_left_joint2
- daksha_left_joint3
- daksha_left_joint4
- daksha_left_joint5
- daksha_left_joint6
- daksha_left_joint7
points:
- positions: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
  velocities: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
  effort: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
  time_from_start:
    sec: 2
"

ros2 topic pub --once /right_arm_mit_controller/joint_trajectory trajectory_msgs/msg/JointTrajectory "
joint_names:
- daksha_right_joint1
- daksha_right_joint2
- daksha_right_joint3
- daksha_right_joint4
- daksha_right_joint5
- daksha_right_joint6
- daksha_right_joint7
points:
- positions: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
  velocities: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
  effort: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
  time_from_start:
    sec: 2
"


ros2 topic pub --once /joint_cmd sensor_msgs/msg/JointState "
name:
- daksha_left_joint1
- daksha_left_joint2
- daksha_left_joint3
- daksha_left_joint4
- daksha_left_joint5
- daksha_left_joint6
- daksha_left_joint7
- daksha_right_joint1
- daksha_right_joint2
- daksha_right_joint3
- daksha_right_joint4
- daksha_right_joint5
- daksha_right_joint6
- daksha_right_joint7
- daksha_left_finger_joint1
- daksha_right_finger_joint1

position:
- 0.0
- 0.0
- 0.0
- 0.0
- 0.0
- 0.0
- 0.0
- 0.0
- 0.0
- 0.0
- 0.0
- 0.0
- 0.0
- 0.0
- 0.0
- 0.0

velocity:
- 0.0
- 0.0
- 0.0
- 0.0
- 0.0
- 0.0
- 0.0
- 0.0
- 0.0
- 0.0
- 0.0
- 0.0
- 0.0
- 0.0
- 0.0
- 0.0

effort:
- 0.0
- 0.0
- 0.0
- 0.0
- 0.0
- 0.0
- 0.0
- 0.0
- 0.0
- 0.0
- 0.0
- 0.0
- 0.0
- 0.0
- 0.0
- 0.0
"

ros2 service call \
/LeftArmSystem/set_motor_gains \
hw_interface/srv/SetMotorGains \
"motor_ids: [1,2,3,4,5,6,7,8]
kp: [40.0,40.0,25.0,25.0,10.0,10.0,10.0,2.5]
kd: [2.0,2.0,1.5,1.5,0.5,0.5,0.5,0.25]"

ros2 service call \
/RightArmSystem/set_motor_gains \
hw_interface/srv/SetMotorGains \
"motor_ids: [1,2,3,4,5,6,7,8]
kp: [40.0,40.0,25.0,25.0,10.0,10.0,10.0,2.5]
kd: [2.0,2.0,1.5,1.5,0.5,0.5,0.5,0.25]"



ros2 service call \
/LeftArmSystem/set_motor_gains \
hw_interface/srv/SetMotorGains \
"motor_ids: [1,2,3,4,5,6,7,8]
kp: [5.0,5.0,4.0,3.0,2.0,2.0,2.0,0.5]
kd: [0.8,0.8,0.6,0.5,0.3,0.3,0.3,0.1]"

ros2 service call \
/RightArmSystem/set_motor_gains \
hw_interface/srv/SetMotorGains \
"motor_ids: [1,2,3,4,5,6,7,8]
kp: [5.0,5.0,4.0,3.0,2.0,2.0,2.0,0.5]
kd: [0.8,0.8,0.6,0.5,0.3,0.3,0.3,0.1]"



python3 -m pip install --user canalystii

python3 -m pip install --user "python-can[canalystii]"


sudo nano /etc/udev/rules.d/99-canalyst.rules

SUBSYSTEM=="usb", ATTR{idVendor}=="04d8", ATTR{idProduct}=="1234", MODE="0666"

sudo udevadm control --reload-rules
sudo udevadm trigger

ros2 service call /start_recording dc_interfaces/srv/StartRecording \
"{config_file: '/home/deeptech/.barani/.gen2/src/dc/config/pick_place.yaml'}"

ros2 service call /record_status dc_interfaces/srv/RecorderStatus "{}"

ros2 service call /stop_recording dc_interfaces/srv/StopRecording "{}"

ros2 service call \
/start_replay \
dc_interfaces/srv/StartReplay \
"{episode_path:'/home/.../episode_000001.parquet'}"


cd ~/.barani/.gen2

colcon build --packages-select dc

source install/setup.bash


ros2 run dc recorder_service

ros2 service call /start_replay dc_interfaces/srv/StartReplay \
"{config_file: '/home/deeptech/.barani/.gen2/src/dc/config/pick_place.yaml',
  episode_index: 0,
  speed: 1.0}"


ros2 service call /replay_status dc_interfaces/srv/ReplayStatus "{}"

ros2 service call /stop_replay dc_interfaces/srv/StopReplay "{}"

