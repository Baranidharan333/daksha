# Gesture Management

A ROS 2 package to record `sensor_msgs/JointState` streams ("gestures") to
Parquet files, replay them back as joint commands, and group them into
named, ordered **sequences**. Everything is available two ways:

- **Web UI** — a Flask operator console (`gesture_management_app.py`) at
  `http://localhost:5000`.
- **ROS services** — the exact same record/replay/sequence/status
  operations, callable from any ROS 2 node or `ros2 service call`, with no
  HTTP involved. The UI and the services share the same underlying node
  state, so they never diverge — a gesture recorded from one is visible
  and playable from the other.

## Dependencies
```bash
pip install flask pandas pyarrow fastparquet
```
> On Ubuntu 24.04 / newer pip, add `--break-system-packages` or use a venv.

## Build
```bash
cd ~/gen2_ws   # or wherever this workspace lives
colcon build --packages-select gesture_management
source install/setup.bash
```

## Running

```bash
ros2 run gesture_management gesture_management_app.py
# or:
ros2 launch gesture_management gesture_management.launch.py
```

This starts both the Flask UI (`http://localhost:5000`) and the ROS node
(`gesture_management`) with all services below, in the same process. The
recordings directory defaults to `<share>/gesture_management/recordings`
(overridable — see the UI's directory picker or the `recordings_dir`
handling in `gesture_management_app.py`).

Records from `/joint_states` (configurable per-call) and replays to
`/joint_cmd` (configurable per-call) by default. Replaying switches
`mode_toggler` to `normal` first (and recording switches it to `teach`),
waiting for the mode to actually settle on the hardware before proceeding.

## ROS Service API

All services are on the `gesture_management` node once it's running (no
namespace prefix by default).

### Record a gesture — `/record` (`gesture_management/srv/StartRecording`)
```bash
ros2 service call /record gesture_management/srv/StartRecording \
  "{topic_name: '/joint_states', recording_name: 'wave_hello', action: 'start'}"

# ... move the arm (recording switches mode_toggler to teach automatically) ...

ros2 service call /record gesture_management/srv/StartRecording \
  "{action: 'stop'}"
```
`recording_name`/`topic_name` are only read on `start`; `stop` just needs
`action: 'stop'`. Saves `<recording_name>.parquet` and updates the shared
recordings index (so it immediately shows up in the UI and in
`/list_sequences`/the recordings list).

### Replay one gesture — `/play_recording` (`gesture_management/srv/PlayRecording`)
```bash
ros2 service call /play_recording gesture_management/srv/PlayRecording \
  "{recording_name: 'wave_hello', output_topic: '/joint_cmd', replay_speed: 1.0,
    repeat_mode: 'once', repeat_count: 1, interval_s: 0.0}"
```
`repeat_mode` is one of `once` / `count` / `infinite`. For `count`,
`repeat_count` loops are played with `interval_s` seconds between them; for
`infinite` it loops until `/stop_replay` is called.

### Sequences

A sequence is a named, ordered list of recordings, saved once and replayed
by name — the equivalent of a single-recording replay, generalized to a
playlist. Internally a single-recording replay *is* a one-item sequence,
so replay status (below) reports playlist progress either way.

**Save** — `/save_sequence` (`gesture_management/srv/SaveSequence`)
```bash
ros2 service call /save_sequence gesture_management/srv/SaveSequence \
  "{name: 'greeting', recording_names: ['wave_hello', 'nod']}"
```

**List** — `/list_sequences` (`gesture_management/srv/ListSequences`)
```bash
ros2 service call /list_sequences gesture_management/srv/ListSequences "{}"
# -> sequences_json: '[{"name": "greeting", "recording_names": [...], "created_at": "..."}]'
```

**Delete** — `/delete_sequence` (`gesture_management/srv/DeleteSequence`)
```bash
ros2 service call /delete_sequence gesture_management/srv/DeleteSequence \
  "{name: 'greeting'}"
```

**Play** — `/play_sequence` (`gesture_management/srv/PlaySequence`)

Either play a saved sequence by name, or pass an explicit, ad-hoc list of
recordings without saving it first — `sequence_name` takes priority when
both are set:
```bash
# by saved name
ros2 service call /play_sequence gesture_management/srv/PlaySequence \
  "{sequence_name: 'greeting', output_topic: '/joint_cmd', replay_speed: 1.0,
    repeat_mode: 'once', repeat_count: 1, interval_s: 0.0}"

# ad hoc, no saved sequence needed
ros2 service call /play_sequence gesture_management/srv/PlaySequence \
  "{recording_names: ['wave_hello', 'nod'], output_topic: '/joint_cmd',
    replay_speed: 1.0, repeat_mode: 'count', repeat_count: 3, interval_s: 1.0}"
```

### Stop any active replay — `/stop_replay` (`std_srvs/srv/Trigger`)
```bash
ros2 service call /stop_replay std_srvs/srv/Trigger "{}"
```
Works the same whether a single recording or a sequence is playing.

### Status — `/get_status` (`gesture_management/srv/GetReplayStatus`)
```bash
ros2 service call /get_status gesture_management/srv/GetReplayStatus "{}"
```
Returns `status_json`, the same JSON shape the UI polls and the node
publishes periodically (every 0.25s) on the `/gesture_status_topic` topic
(`std_msgs/String`):
```bash
ros2 topic echo /gesture_status_topic --truncate-length 100000
```
> `ros2 topic echo` truncates string fields to 128 characters by default,
> so without `--truncate-length` the JSON gets cut off mid-line (this does
> **not** happen with `ros2 service call`, which is unaffected by that
> flag). Drop `--once` if you want to watch it update live.

The `replay` object always carries sequence-aware fields, whether a single
recording or a saved/ad-hoc sequence is playing:

```json
{
  "recording": {"active": false, "name": null, "topic": null, "frames": 0, "joints": 0, "elapsed_s": 0.0},
  "replay": {
    "active": true, "name": "wave_hello", "output_topic": "/joint_cmd",
    "speed": 1.0, "percent": 0.42, "frame": 610, "total": 1450,
    "message": "playing", "mode_msg": "",
    "playlist": ["wave_hello", "nod"], "playlist_index": 0, "playlist_total": 2,
    "repeat_mode": "count", "repeat_count": 3, "loop_count": 1, "interval_s": 1.0
  },
  "mode": "normal"
}
```
`playlist_index`/`playlist_total` track progress through the current
sequence; `loop_count` tracks repeats when `repeat_mode` is `count` or
`infinite`.

## Standalone legacy servers

Two older, single-purpose nodes exist alongside the main app above, each
with their own narrower ROS service and no sequence/status support. Use
these only if you specifically want a minimal recorder or replayer without
the rest of the UI/app running:

```bash
ros2 run gesture_management recorder_server.py   # /recording        (StartRecording.srv)
ros2 run gesture_management replay_server.py     # /replay_recording (ReplayRecording.srv), publishes sensor_msgs/JointState
```
These keep their own separate recording/replay state — they do **not**
share state with `gesture_management_app.py`, so a gesture recorded here
won't show progress via `/get_status`, and vice versa.

> There used to be a second, older `replay_server.py` that published
> `std_msgs/Float64MultiArray` instead of `JointState`, and a separate
> `replay_server_js.py` publishing `JointState`. Nothing downstream in this
> workspace consumes `Float64MultiArray` on a replay topic, and both nodes
> shared the same `/replay_recording` service name and `replay_server` ROS
> node name, so running them together (as the launch file used to) was a
> latent conflict. The `Float64MultiArray` one was removed and
> `replay_server_js.py` was renamed to `replay_server.py`.
