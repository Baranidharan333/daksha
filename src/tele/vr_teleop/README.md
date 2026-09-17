# vr_teleop

Meta Quest → ROS 2 teleoperation bridge. A Unity app on the headset streams the head
and controller poses over TCP; this package receives them via the Unity
[ROS-TCP-Endpoint](https://github.com/Unity-Technologies/ROS-TCP-Endpoint) server and
republishes them as TF frames that the rest of the robot stack can consume.

Built and tested on **ROS 2 Humble**.

---

## Build

```bash
cd ~/gen2_quest/rostcpend
source /opt/ros/humble/setup.bash
colcon build --packages-select vr_teleop
source install/setup.bash
```

Re-run `source install/setup.bash` in every new terminal.

---

## Quick start

Put the workstation and the headset on the same network, note the workstation's IP
(`hostname -I`), and enter it as the ROS IP in the Unity app on the Quest. Then:

```bash
ros2 launch vr_teleop vr_control_switch.py
```

That starts the TCP endpoint on `0.0.0.0:10000` plus the TF broadcaster. Confirm poses
are arriving:

```bash
ros2 topic hz /quest/head
ros2 run tf2_tools view_frames        # or just open RViz2 and add a TF display
```

---

## Data flow

```
Quest (Unity)  --TCP :10000-->  default_server_endpoint  --/quest/*-->  TF broadcaster  --> /tf
```

**Topics published by the endpoint** (all `geometry_msgs/PoseStamped`, in Unity's
left-handed frame):

| Topic | Source |
|---|---|
| `/quest/head` | headset |
| `/quest/left/pose` | left controller |
| `/quest/right/pose` | right controller |

**TF frames published** (children of `world`, in ROS FLU convention):
`quest_head`, `quest_left`, `quest_right`.

---

## Launch files

| Launch file | Starts | Use when |
|---|---|---|
| `vr_control_switch.py` | endpoint + `quest_tf_switch` | **Default.** Normal or mirrored, switchable at runtime. |
| `vr_control.py` | endpoint + `quest_tf` | Normal mapping only, fixed. |
| `vr_control_mirror.py` | endpoint + `quest_tf_mirror` | Mirrored mapping only, fixed. |
| `endpoint.py` | endpoint only | You want to run a TF node yourself, or debug the raw `/quest/*` topics. |

```bash
ros2 launch vr_teleop vr_control_switch.py
ros2 launch vr_teleop vr_control.py
ros2 launch vr_teleop vr_control_mirror.py
ros2 launch vr_teleop endpoint.py
```

Nodes can also be run individually:

```bash
ros2 run vr_teleop default_server_endpoint --ros-args -p ROS_IP:=0.0.0.0 -p ROS_TCP_PORT:=10000
ros2 run vr_teleop quest_tf_switch
```

---

## Normal vs. mirrored

**Normal** is the direct Unity → ROS conversion. The robot is treated as if you were
sitting inside it: your left hand drives `quest_left`.

**Mirrored** reflects everything across the robot's forward axis and swaps the two
controllers, so the robot moves like your reflection. Use this when you are standing in
front of the robot watching it head-on — your left hand then drives the arm that appears
on your left.

One deliberate exception: in mirrored mode the **head's yaw is not mirrored**. Position
is reflected, but turning your head left still turns `quest_head` left, because a
reversed gaze direction is disorienting to drive. Set `mirror_head_yaw:=true` if you
want a strict geometric mirror instead.

---

## `quest_tf_switch` (recommended node)

Does the job of both `quest_tf` and `quest_tf_mirror`, with the mode selectable while
running.

### Service

Flip modes without restarting anything:

```bash
ros2 service call /quest_tf_switch/set_mirror std_srvs/srv/SetBool "{data: true}"    # mirrored
ros2 service call /quest_tf_switch/set_mirror std_srvs/srv/SetBool "{data: false}"   # normal
```

The response `message` field reports the mode now in effect (`NORMAL` / `MIRRORED`).

### State topic

The current mode is published on `/quest_tf_switch/mirror_state`
(`std_msgs/Bool`, `true` = mirrored). It uses latched (`TRANSIENT_LOCAL`) QoS, so a node
that subscribes late immediately receives the current value instead of waiting for the
next change:

```bash
ros2 topic echo /quest_tf_switch/mirror_state
```

### Parameters

| Parameter | Type | Default | Meaning |
|---|---|---|---|
| `mirror` | bool | `false` | Mode at startup. |
| `mirror_head_yaw` | bool | `false` | If `true`, mirror the head's yaw too (strict geometric mirror). |

```bash
ros2 run vr_teleop quest_tf_switch --ros-args -p mirror:=true
```

### Legacy nodes

`quest_tf` (normal) and `quest_tf_mirror` (mirrored) are the original fixed-mode nodes.
They still work and behave identically to the corresponding mode of `quest_tf_switch`;
they are kept so the older launch files keep working. Prefer `quest_tf_switch` for new
work.

---

## Endpoint parameters

| Parameter | Type | Default | Meaning |
|---|---|---|---|
| `ROS_IP` | string | `0.0.0.0` | Interface the TCP server binds to. `0.0.0.0` accepts any. |
| `ROS_TCP_PORT` | int | `10000` | TCP port. Must match the Unity app's setting. |

---

## Coordinate conversion

Unity is left-handed (X right, Y up, Z forward); ROS is right-handed FLU (X forward,
Y left, Z up). The normal mapping is the standard one used by Unity's
`ROS-TCP-Connector`:

```
position: (x, y, z)     = ( uz, -ux,  uy)
rotation: (x, y, z, w)  = ( uz, -ux,  uy, -uw)
```

The negated `w` is required, not a typo: relabelling axes across a handedness change is
an improper transform, so the rotation direction has to be reversed.

Mirroring reflects that result through the plane normal to ROS Y. Reflecting a rotation
negates its X and Z axis components, which reduces to dropping every sign flip above:

```
position: (x, y, z)     = ( uz,  ux,  uy)
rotation: (x, y, z, w)  = ( uz,  ux,  uy,  uw)
```

---

## Troubleshooting

**No `/quest/*` topics.** The headset is not connected. Check that the IP in the Unity
app matches `hostname -I` on this machine, that both are on the same subnet, and that
port 10000 is open: `sudo ufw allow 10000/tcp`.

**Topics publish but no TF appears.** The TF node is not running — `endpoint.py` alone
does not start one. Use `vr_control_switch.py`, or run `ros2 run vr_teleop
quest_tf_switch` alongside it.

**`TF_REPEATED_DATA` warnings, or frames flickering in RViz.** The TF nodes pass the
incoming `header.stamp` through unchanged. If the Unity side sends zero or
non-monotonic timestamps, TF will reject them. Verify with
`ros2 topic echo /quest/head --field header.stamp`.

**Left and right controllers feel swapped.** That is the difference between the two
modes — flip it with the `set_mirror` service.

**`colcon build` fails on a missing `resource/vr_teleop`.** That zero-byte file is the
ament package marker and must exist: `touch resource/vr_teleop`.
