# iHub Giga Factory — Clients UI Platform

Unified industrial web control platform for the **Daksha Bimanual Humanoid Robot**:
a 3D dashboard + camera/sub-UI stack (`daksha_ui`) and an autonomous dataset
recorder (`daksha_data_collection`), both proper ROS 2 packages built and
launched the normal way — no bespoke shell scripts, no nested workspaces.

---

## Project Structure

```
Clients_UI/
├── project.config.yaml                    # Single source of truth (edit here)
├── daksha_final_urdf_description/         # Unused legacy URDF + mesh assets — kept
│                                           # for reference only; the UI reads the URDF
│                                           # from ../daksha_description_full_body/ instead
├── daksha_msgs/                           # StartRecord/StartReplay .srv definitions
├── daksha_data_collection/                # Dataset recording/replay + web console
│   ├── config/config.yaml                 # Node config (domain_id, topics, dataset.root_dir)
│   ├── datasets/                          # Recorded episodes (gitignored, real data)
│   ├── launch/data_collection.launch.py   # recorder + replay + web UI, all three
│   └── daksha_data_collection/
│       ├── ros2_topic_recorder.py
│       ├── ros2_topic_replay.py
│       └── web_data_management_ui.py
└── daksha_ui/                              # Daksha 3D dashboard + sub-UI + camera stream
    ├── launch/client_ui.launch.py          # dashboard + sub-UI + camera viewer, all three
    └── daksha_ui/
        ├── dashboard_app.py                 # main 3D WebGL dashboard (Flask)
        └── subui/
            ├── subui_app.py                 # secondary control sub-UI (Flask)
            └── viveka_camera_ui.py           # camera-stream viewer (Flask)
```

Each of `daksha_msgs`, `daksha_data_collection`, and `daksha_ui` is an ordinary
package under the main workspace — build them with the workspace's own
`colcon build` from the repo root, same as any other package in `src/`.
`daksha_ui` also depends on `daksha_description_full_body`
(`src/daksha_description_full_body/`, a sibling of `Clients_UI/`) for the
robot's URDF and mesh assets — build that package too.

---

## Configuration — Single Source of Truth

All network, ROS, topic, and safety settings live in **`project.config.yaml`**
(this directory). `dashboard_app.py` and `daksha_data_collection`'s `config.py`
both read it dynamically via `__file__`-relative resolution — edit once,
restart the relevant node.

Current values in use (check `project.config.yaml` for the authoritative copy —
these are quoted here only as a quick reference and can drift):

```yaml
ros:
  domain_id: 33

network:
  daksha_ui_port: 7070            # dashboard_app.py
  data_collection_port: 8888      # web_data_management_ui.py
```

`subui_app.py` and `viveka_camera_ui.py` currently bind fixed ports (`7001`
and `7002` respectively) rather than reading them from config — check those
two files directly if you need the exact current values.

---

## Build

```bash
cd /home/s1/.ihub/.barani/gen2_full
source /opt/ros/humble/setup.bash
colcon build --packages-select daksha_description_full_body daksha_msgs daksha_data_collection daksha_ui
source install/setup.bash
```

---

## Running

### Data collection stack

```bash
ros2 launch daksha_data_collection data_collection.launch.py
```

Brings up the topic recorder, replay node, and the web console together.

### Client UI stack (dashboard + sub-UI + camera viewer)

```bash
ros2 launch daksha_ui client_ui.launch.py
```

Open the dashboard at `http://localhost:<daksha_ui_port>` (see
`project.config.yaml`).

---

## Camera Topics (Jetson — Domain 33)

| Camera Slot | ROS Topic | Format |
|---|---|---|
| CAM 1 — Left Wrist | `/left/camera/color/image_raw/compressed` | CompressedImage |
| CAM 2 — Right Wrist | `/right/camera/color/image_raw/compressed` | CompressedImage |
| CAM 3 — ZED Left | `/zed/zed_node/left/color/rect/image/compressed` | CompressedImage |
| CAM 4 — ZED Right | `/zed/zed_node/right/color/rect/image/compressed` | CompressedImage |

Cameras show **CAMERA OFFLINE** until topics are actively publishing. No fake
signals or placeholder animations.

---

## Joints (18 DOF)

| Group | Joints | Type |
|---|---|---|
| Right Arm | `right_joint` → `right_joint_7` | Revolute |
| Left Arm | `left_joint` → `left_joint_7` | Revolute |
| Right Gripper | `right_right_finger_joint`, `right_left_finger_joint` | Prismatic |
| Left Gripper | `left_left_gripper_joint`, `left_right_gripper_joint` | Prismatic |

---

## Developer Notes

- **No hardcoded absolute paths** in Python — path resolution goes through
  `__file__`-relative candidate lists (`dashboard_app.py`) or
  `ament_index_python.get_package_share_directory()` (`daksha_data_collection`),
  with a source-tree fallback for running scripts directly during development.
- **Never edit `install/` or `build/`** — colcon-generated, gitignored.
- **Recorded datasets** live in `daksha_data_collection/datasets/` (gitignored,
  real operator data — don't delete without checking with whoever's using it).
