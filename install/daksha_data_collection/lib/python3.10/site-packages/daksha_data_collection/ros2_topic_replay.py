#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import threading
from pathlib import Path
from typing import Any, Dict, Optional

import cv2
import numpy as np
import rclpy
import yaml
from rclpy.node import Node
from rclpy.qos import QoSDurabilityPolicy, QoSProfile, QoSReliabilityPolicy
from sensor_msgs.msg import CompressedImage, Image, JointState
from std_msgs.msg import Float64MultiArray, String
from std_srvs.srv import Trigger
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from daksha_msgs.srv import StartReplay


def _default_config_path() -> str:
    """Prefer the installed share/ copy (ros2 run/launch); fall back to the
    source-tree config/ next to this package when run straight from source
    (e.g. python3 ros2_topic_replay.py during development)."""
    try:
        from ament_index_python.packages import get_package_share_directory
        return str(Path(get_package_share_directory("daksha_data_collection")) / "config" / "config.yaml")
    except Exception:
        return str(Path(__file__).resolve().parent.parent / "config" / "config.yaml")


def _acquire_singleton_lock(name: str):
    """Refuse to start a second instance of this node -- see the matching
    guard in ros2_topic_recorder.py for why duplicates are dangerous here."""
    import fcntl
    lock_path = f"/tmp/daksha_{name}.lock"
    lock_file = open(lock_path, "w")
    try:
        fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        print(
            f"Another {name} instance is already running (lock held on {lock_path}). "
            f"Kill it before starting a new one -- exiting.",
            file=sys.stderr,
        )
        sys.exit(1)
    lock_file.write(str(os.getpid()))
    lock_file.flush()
    return lock_file  # keep referenced for the process lifetime; GC would release the flock


def _default_dataset_dir() -> str:
    """Fallback used only if config.yaml has no dataset.root_dir at all —
    the config value is the real source of truth (see config/config.yaml)."""
    return str(Path(__file__).resolve().parent.parent / "datasets")


try:
    from .config import ReplayConfig
    from .replay import V3DatasetReplay
except ImportError:
    from config import ReplayConfig
    from replay import V3DatasetReplay

ROS2_TOPIC_CONFIG = "ros2_topics.json"

DEFAULT_RIGHT_CONTROLLER_JOINT_NAMES = [
    "daksha_right_joint1", "daksha_right_joint2", "daksha_right_joint3",
    "daksha_right_joint4", "daksha_right_joint5", "daksha_right_joint6",
    "daksha_right_joint7", "daksha_right_finger_joint1",
]

DEFAULT_LEFT_CONTROLLER_JOINT_NAMES = [
    "daksha_left_joint1", "daksha_left_joint2", "daksha_left_joint3",
    "daksha_left_joint4", "daksha_left_joint5", "daksha_left_joint6",
    "daksha_left_joint7", "daksha_left_finger_joint1",
]

def _load_topic_config(root: Path) -> Dict[str, Any]:
    path = root / ROS2_TOPIC_CONFIG
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))

def _to_numpy(value: Any) -> np.ndarray:
    if isinstance(value, np.ndarray): return value
    if hasattr(value, "detach") and hasattr(value, "cpu"): return value.detach().cpu().numpy()
    if hasattr(value, "numpy"): return value.numpy()
    return np.asarray(value)

def _to_vector(value: Any) -> list[float]:
    arr = _to_numpy(value)
    if arr.ndim == 0: return [float(arr.item())]
    return arr.astype(np.float32).reshape(-1).tolist()

def _to_rgb_image(value: Any) -> np.ndarray:
    arr = _to_numpy(value)
    if arr.ndim != 3: raise ValueError(f"Expected 3D image array, got shape {arr.shape}")
    if arr.shape[0] in (1, 3) and arr.shape[-1] not in (1, 3): arr = np.moveaxis(arr, 0, -1)
    if arr.dtype != np.uint8:
        max_value = float(np.max(arr)) if arr.size else 0.0
        if np.issubdtype(arr.dtype, np.floating) and max_value <= 1.0:
            arr = np.clip(arr * 255.0, 0, 255).astype(np.uint8)
        else:
            arr = np.clip(arr, 0, 255).astype(np.uint8)
    return arr

def _is_compressed_topic(topic: str) -> bool:
    return topic.rstrip("/").endswith("/compressed")

class Ros2V3TopicReplay(Node):
    def __init__(self, config_path: str) -> None:
        super().__init__("custom_v3_topic_replay")

        self.config_path = config_path
        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)

        dataset_cfg = self.config.get("dataset", {})
        replay_cfg = self.config.get("replay", {})
        topics_cfg = self.config.get("replay_topics", self.config.get("topics", {}))

        self.repo_id = dataset_cfg.get("repo_id", "local/task1")
        self.dataset_name = dataset_cfg.get("dataset_name", "task1")
        self.root_dir = Path(dataset_cfg.get("root_dir", _default_dataset_dir())).expanduser().resolve() / self.dataset_name

        self.episode_index = int(replay_cfg.get("episode_index", 0))
        self.speed = max(float(replay_cfg.get("speed", 1.0)), 1e-6)
        self.video_backend = replay_cfg.get("video_backend", None)
        self.replay_fps = float(replay_cfg.get("fps", 10.0))

        self.camera_topics: Dict[str, str] = topics_cfg.get("camera_topics", {})

        # Leader / Follower State Topics
        self.leader_left_topic = topics_cfg.get("leader_topic_left", "/left_leader/joint_states")
        self.leader_right_topic = topics_cfg.get("leader_topic_right", "/right_leader/joint_states")
        self.follower_left_topic = topics_cfg.get("follower_topic_left", "/LeftArmSystem_ordered_joint_states")
        self.follower_right_topic = topics_cfg.get("follower_topic_right", "/RightArmSystem_ordered_joint_states")

        # Controller joint names (overridable from config, defaults to daksha names)
        yaml_joint_names = topics_cfg.get("joint_names", [])
        self.right_controller_joint_names = [n for n in yaml_joint_names if "right" in n.lower()] or DEFAULT_RIGHT_CONTROLLER_JOINT_NAMES
        self.left_controller_joint_names  = [n for n in yaml_joint_names if "left"  in n.lower()] or DEFAULT_LEFT_CONTROLLER_JOINT_NAMES

        # Publishers
        self.follower_left_state_pub = self.create_publisher(JointState, self.follower_left_topic, 10)
        self.follower_right_state_pub = self.create_publisher(JointState, self.follower_right_topic, 10)

        # Command topic(s) + message type: set up once here, refreshed on
        # every /replay/start by _refresh_command_publisher() (see there for
        # why -- this used to be __init__-only and never noticed a topic
        # changed in config.yaml after the node started).
        self.follower_cmd_pub = None
        self.follower_left_cmd_pub = None
        self.follower_right_cmd_pub = None
        self.use_unified_cmd_topic = False
        self.follower_cmd_topic = ""
        self.follower_cmd_msg_type = ""
        self._refresh_command_publisher(topics_cfg, log_result=True)

        reliable_qos = QoSProfile(depth=10)
        reliable_qos.reliability = QoSReliabilityPolicy.RELIABLE
        reliable_qos.durability = QoSDurabilityPolicy.VOLATILE
        self.camera_pubs: Dict[str, tuple] = {}
        for camera_key, topic in self.camera_topics.items():
            is_compressed = _is_compressed_topic(topic)
            msg_type = CompressedImage if is_compressed else Image
            self.camera_pubs[camera_key] = (self.create_publisher(msg_type, topic, reliable_qos), is_compressed)

        # State
        self.frames: list = []
        self.current_step = 0
        self.timer = None
        self.is_playing = False
        self._topic_cfg: Dict[str, Any] = {}

        # Episode loading happens on a background thread (see _handle_start)
        # -- decoding every frame of every camera for a whole episode
        # synchronously inside the service callback used to block this
        # node's single-threaded executor entirely for as long as loading
        # took (tens of seconds on this rig's embedded hardware for a
        # several-hundred-step episode), during which even /replay/stop
        # could not be serviced.
        self._loading = False
        self._load_cancel = threading.Event()
        self._load_thread: Optional[threading.Thread] = None

        # Services
        self.srv_start = self.create_service(StartReplay, "/replay/start", self._handle_start)
        self.srv_stop  = self.create_service(Trigger, "/replay/stop", self._handle_stop)



        # UI Status Publisher
        self.status_pub = self.create_publisher(String, '/replay/ui_status', 10)
        self.status_timer = self.create_timer(1.0, self._publish_status)

        self.get_logger().info(f"Replay node ready. Dataset: {self.root_dir}")

    # ── Status Publisher ──────────────────────────────────────────────────

    def _publish_status(self) -> None:
        try:
            status = {
                "is_playing": self.is_playing,
                "is_loading": self._loading,
                "dataset_name": self.dataset_name,
                "episode_index": self.episode_index,
                "speed": self.speed,
                "current_step": self.current_step,
                "total_steps": len(self.frames) if self.frames else 0,
            }
            msg = String()
            msg.data = json.dumps(status)
            self.status_pub.publish(msg)
        except Exception as e:
            self.get_logger().error(f"Error publishing replay status: {e}")

    # ── Command publisher (re)configuration ─────────────────────────────────

    def _refresh_command_publisher(self, topics_cfg: Dict[str, Any], log_result: bool = False) -> None:
        """(Re)build the follower command publisher(s) from `topics_cfg`.

        ros2_topic_recorder.py reloads config.yaml and re-points its
        subscriptions on every /recorder/start (see _set_joint_subscription)
        specifically because topics used to be wired up once in __init__ and
        never touched again, so picking a different topic in the UI after
        the node had already started silently kept using the old one. This
        node had the exact same bug for its command publisher: if the
        operator changed follower_cmd_topic_left/right or joint_cmd_topic
        (e.g. back to the unified /joint_cmd, which is what the real
        arm/joint_cmd.py control loop actually consumes) after
        ros2_topic_replay had already started, replay kept publishing to
        whatever topic was configured at startup -- often this file's
        hardcoded per-arm defaults (/left_arm_controller/commands,
        /right_arm_controller/commands), which nothing downstream consumes.
        """
        follower_cmd_topic = topics_cfg.get("joint_cmd_topic", topics_cfg.get("follower_cmd_topic", ""))
        follower_cmd_left_topic = topics_cfg.get("follower_cmd_topic_left", "/left_arm_controller/commands")
        follower_cmd_right_topic = topics_cfg.get("follower_cmd_topic_right", "/right_arm_controller/commands")

        # If left and right command topics are the same, treat as a unified command topic
        if not follower_cmd_topic and follower_cmd_left_topic == follower_cmd_right_topic and follower_cmd_left_topic:
            follower_cmd_topic = follower_cmd_left_topic

        use_unified_cmd_topic = bool(follower_cmd_topic)

        follower_cmd_msg_type = str(topics_cfg.get("follower_cmd_msg_type", "")).strip().lower()
        if not follower_cmd_msg_type:
            reference_topic = follower_cmd_topic if use_unified_cmd_topic else follower_cmd_left_topic
            if reference_topic.endswith("/joint_trajectory"):
                follower_cmd_msg_type = "joint_trajectory"
            elif reference_topic.endswith("/commands"):
                follower_cmd_msg_type = "float64_multi_array"
            else:
                follower_cmd_msg_type = "joint_state"  # default for joint_cmd
        if follower_cmd_msg_type == "jointstate":
            follower_cmd_msg_type = "joint_state"

        unchanged = (
            use_unified_cmd_topic == self.use_unified_cmd_topic
            and follower_cmd_msg_type == self.follower_cmd_msg_type
            and (
                (use_unified_cmd_topic and follower_cmd_topic == self.follower_cmd_topic)
                or (not use_unified_cmd_topic
                    and follower_cmd_left_topic == self.follower_cmd_left_topic
                    and follower_cmd_right_topic == self.follower_cmd_right_topic)
            )
        )
        self.follower_cmd_left_topic = follower_cmd_left_topic
        self.follower_cmd_right_topic = follower_cmd_right_topic
        if unchanged and (self.follower_cmd_pub or self.follower_left_cmd_pub):
            return

        for pub_attr in ("follower_cmd_pub", "follower_left_cmd_pub", "follower_right_cmd_pub"):
            old_pub = getattr(self, pub_attr, None)
            if old_pub is not None:
                self.destroy_publisher(old_pub)
                setattr(self, pub_attr, None)

        self.follower_cmd_topic = follower_cmd_topic
        self.use_unified_cmd_topic = use_unified_cmd_topic
        self.follower_cmd_msg_type = follower_cmd_msg_type
        cmd_msg_type = (
            JointTrajectory if follower_cmd_msg_type == "joint_trajectory"
            else JointState if follower_cmd_msg_type == "joint_state"
            else Float64MultiArray
        )
        if use_unified_cmd_topic:
            self.follower_cmd_pub = self.create_publisher(cmd_msg_type, follower_cmd_topic, 10)
        else:
            self.follower_left_cmd_pub = self.create_publisher(cmd_msg_type, follower_cmd_left_topic, 10)
            self.follower_right_cmd_pub = self.create_publisher(cmd_msg_type, follower_cmd_right_topic, 10)

        if log_result:
            self.get_logger().info(f"Using unified cmd topic? {use_unified_cmd_topic}")
            if use_unified_cmd_topic:
                self.get_logger().info(f"Unified Topic: {follower_cmd_topic} ({follower_cmd_msg_type})")
            else:
                self.get_logger().info(
                    f"Left/right cmd topics: {follower_cmd_left_topic}, {follower_cmd_right_topic} ({follower_cmd_msg_type})"
                )

    # ── Service handlers ──────────────────────────────────────────────────

    def _handle_start(self, request, response):
        if self.is_playing:
            response.success = False
            response.message = "Replay already running."
            return response
        if self._loading:
            response.success = False
            response.message = "Still finishing the previous load/stop; try again in a moment."
            return response

        # Reload configuration YAML file to catch topic changes made after
        # this node started (see _refresh_command_publisher).
        try:
            with open(self.config_path, "r") as f:
                self.config = yaml.safe_load(f) or {}
            topics_cfg = self.config.get("replay_topics", self.config.get("topics", {}))
            self._refresh_command_publisher(topics_cfg, log_result=True)
        except Exception as e:
            self.get_logger().error(f"Failed to reload config.yaml in replay start handler: {e}")

        if request.dataset_name:
            self.dataset_name = request.dataset_name
            dataset_cfg = self.config.get("dataset", {})
            self.root_dir = Path(dataset_cfg.get("root_dir", _default_dataset_dir())).expanduser().resolve() / self.dataset_name
        if request.episode_index >= 0:
            self.episode_index = request.episode_index
        if request.speed > 0.0:
            self.speed = float(request.speed)

        # Loading decodes every frame of every camera for the whole episode
        # up front (see _load_episode/V3DatasetReplay.iter_episode) -- doing
        # that synchronously here used to block this node's single-threaded
        # executor for as long as it took (tens of seconds on this rig's
        # embedded hardware for a several-hundred-step episode), during
        # which /replay/start's own caller would time out waiting for a
        # response, and /replay/stop couldn't even be serviced to cancel
        # it. Loading on a background thread keeps the node responsive and
        # gives /replay/stop something to actually cancel.
        self._loading = True
        self._load_cancel.clear()
        self._load_thread = threading.Thread(
            target=self._load_and_start, args=(self.episode_index,), daemon=True
        )
        self._load_thread.start()

        response.success = True
        response.message = f"Loading episode {self.episode_index}; playback will begin once ready."
        return response

    def _load_and_start(self, episode_index: int) -> None:
        """Runs on a background thread -- see _handle_start."""
        try:
            try:
                self._load_episode(episode_index, cancel_event=self._load_cancel)
            except Exception as e:
                self.get_logger().error(f"Failed to load episode {episode_index}: {e}")
                return
            if self._load_cancel.is_set():
                self.get_logger().info(f"Load of episode {episode_index} cancelled.")
                self.frames = []
                return
            if not self.frames:
                self.get_logger().warn(f"No frames in episode {episode_index}.")
                return
            self.is_playing = True
            self.current_step = 0
            self._schedule_next_step(0.0)
        finally:
            self._loading = False

    def _handle_stop(self, request, response):
        # Set even when nothing is currently loading -- harmless, and
        # covers the case where a load is in flight (see _load_and_start).
        self._load_cancel.set()
        self.is_playing = False
        if self.timer is not None:
            self.timer.cancel()
            self.timer = None

        response.success = True
        response.message = "Replay stopped."
        return response

    # ── Episode loading ───────────────────────────────────────────────────

    def _load_episode(self, episode_index: int, cancel_event: Optional[threading.Event] = None) -> None:
        self._topic_cfg = _load_topic_config(self.root_dir)
        replay = V3DatasetReplay(
            ReplayConfig(repo_id=self.repo_id, root=self.root_dir, episodes=[episode_index], download_videos=False, video_backend=self.video_backend)
        )
        self.frames = list(replay.iter_episode(episode_index, cancel_event=cancel_event))

        first_row = self.frames[0].item if self.frames else {}
        leader_state_vec = _to_vector(first_row.get("observation.leader_state", []))
        follower_state_vec = _to_vector(first_row.get("observation.state", []))
        action_vec = _to_vector(first_row.get("action", []))

        # Per-arm joint names: prefer the flat top-level keys this package's
        # own recorder writes, falling back to the nested "joint_names" dict
        # used by the reference bi_arm_daksha recorder, in case this dataset
        # was recorded by that script instead.
        _joint_names_nested = self._topic_cfg.get("joint_names") or {}
        self.leader_left_joint_names = [
            str(n) for n in (self._topic_cfg.get("leader_left_joint_names") or _joint_names_nested.get("leader_left") or [])
        ]
        self.leader_right_joint_names = [
            str(n) for n in (self._topic_cfg.get("leader_right_joint_names") or _joint_names_nested.get("leader_right") or [])
        ]
        self.follower_left_joint_names = [
            str(n) for n in (self._topic_cfg.get("follower_left_joint_names") or _joint_names_nested.get("follower_left") or [])
        ]
        self.follower_right_joint_names = [
            str(n) for n in (self._topic_cfg.get("follower_right_joint_names") or _joint_names_nested.get("follower_right") or [])
        ]

        self.leader_right_count = len(self.leader_right_joint_names) if self.leader_right_joint_names else max(0, len(leader_state_vec) // 2)
        self.follower_right_count = len(self.follower_right_joint_names) if self.follower_right_joint_names else max(0, len(follower_state_vec) // 2)
        self.action_right_count = len(self.leader_right_joint_names) if self.leader_right_joint_names else max(0, len(action_vec) // 2)

        # Whether observation.leader_state / action store the right arm's
        # joints first or the left arm's. Prefer the explicit
        # "state_concat_order" this package's recorder now writes; fall back
        # to sniffing the legacy comma-joined "leader_state_topic" string for
        # datasets recorded before that field existed; a nested
        # {"left":..,"right":..} "leader_state_topic" with no explicit order
        # means a dataset recorded by the reference bi_arm_daksha script,
        # which always concatenates left-then-right.
        state_order = self._topic_cfg.get("state_concat_order")
        cfg_leader_state = self._topic_cfg.get("leader_state_topic", "")
        if state_order:
            self.leader_state_right_first = str(state_order[0]).strip().lower() == "right"
        elif isinstance(cfg_leader_state, str) and cfg_leader_state:
            leader_parts = [p.strip() for p in cfg_leader_state.split(",") if p.strip()]
            self.leader_state_right_first = False
            if leader_parts:
                first_topic = "/" + leader_parts[0].lstrip("/")
                cfg_right = "/" + str(self._topic_cfg.get("leader_right_topic", "")).lstrip("/")
                if first_topic == cfg_right:
                    self.leader_state_right_first = True
        elif isinstance(cfg_leader_state, dict):
            self.leader_state_right_first = False
        else:
            # No ordering info at all -- default to this recorder's own
            # convention (left-then-right, matching the reference
            # bi_arm_daksha recorder).
            self.leader_state_right_first = False

        self.action_right_first = self.leader_state_right_first

        if self.action_right_first:
            self.unified_cmd_joint_names = (
                list(self.follower_right_joint_names) + list(self.follower_left_joint_names)
                if (self.follower_right_joint_names or self.follower_left_joint_names)
                else list(self.leader_right_joint_names) + list(self.leader_left_joint_names)
            )
        else:
            self.unified_cmd_joint_names = (
                list(self.follower_left_joint_names) + list(self.follower_right_joint_names)
                if (self.follower_left_joint_names or self.follower_right_joint_names)
                else list(self.leader_left_joint_names) + list(self.leader_right_joint_names)
            )

    # ── Replay loop ───────────────────────────────────────────────────────

    def _schedule_next_step(self, delay_sec: float) -> None:
        self.timer = self.create_timer(max(delay_sec, 0.0), self._replay_step)

    def _replay_step(self) -> None:
        if self.timer is not None:
            self.timer.cancel()
            self.timer = None
        if not self.is_playing:
            return
        if self.current_step >= len(self.frames):
            self.get_logger().info("Replay finished.")
            self.is_playing = False

            return

        row = self.frames[self.current_step].item
        self._publish_joints(row)
        self._publish_images(row)

        if self.current_step < len(self.frames) - 1:
            current_ts = self._timestamp_of(row)
            next_ts = self._timestamp_of(self.frames[self.current_step + 1].item)
            delay_sec = (next_ts - current_ts) / self.speed
            if not np.isfinite(delay_sec) or delay_sec <= 0.0:
                delay_sec = 1.0 / (self.replay_fps * self.speed)
        else:
            delay_sec = 0.0

        self.current_step += 1
        self._schedule_next_step(delay_sec)

    # ── Message formatting ────────────────────────────────────────────────

    def _joint_msg(self, vector: list[float], names: Optional[list[str]] = None) -> JointState:
        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()
        if names and len(names) == len(vector):
            msg.name = list(names)
        else:
            msg.name = [f"joint{i+1}" for i in range(len(vector))]
        msg.position = list(vector)
        return msg

    def _float64_array_msg(self, vector: list[float]) -> Float64MultiArray:
        msg = Float64MultiArray()
        msg.data = [float(v) for v in vector]
        return msg

    def _joint_trajectory_msg(self, vector: list[float], names: Optional[list[str]] = None) -> JointTrajectory:
        msg = JointTrajectory()
        msg.header.stamp = self.get_clock().now().to_msg()
        if names and len(names) == len(vector): msg.joint_names = list(names)
        else: msg.joint_names = [f"joint{i+1}" for i in range(len(vector))]
        point = JointTrajectoryPoint()
        point.positions = list(vector)
        point.time_from_start.sec = 0
        point.time_from_start.nanosec = int(1e9 / max(self.replay_fps, 1e-6))
        msg.points = [point]
        return msg

    def _cmd_msg(self, vector: list[float], names: Optional[list[str]] = None):
        if self.follower_cmd_msg_type == "joint_trajectory":
            return self._joint_trajectory_msg(vector, names)
        elif self.follower_cmd_msg_type == "joint_state":
            return self._joint_msg(vector, names)
        return self._float64_array_msg(vector)

    # ── Joint publishing ──────────────────────────────────────────────────

    def _split_right_left(self, vec: list[float], right_count: int, right_first: bool) -> tuple[list[float], list[float]]:
        if right_first: return vec[:right_count], vec[right_count:]
        else: left_count = len(vec) - right_count; return vec[left_count:], vec[:left_count]

    def _publish_joints(self, item: Dict[str, Any]) -> None:
        leader_state   = _to_vector(item.get("observation.leader_state", []))
        follower_state = _to_vector(item.get("observation.state", []))
        action         = _to_vector(item.get("action", []))

        leader_right,   leader_left   = self._split_right_left(leader_state,   self.leader_right_count,   self.leader_state_right_first)
        follower_right, follower_left = self._split_right_left(follower_state, self.follower_right_count, self.leader_state_right_first)
        action_right,   action_left   = self._split_right_left(action,         self.action_right_count,   self.action_right_first)

        self.follower_left_state_pub.publish(self._joint_msg(follower_left,   self.follower_left_joint_names  or None))
        self.follower_right_state_pub.publish(self._joint_msg(follower_right, self.follower_right_joint_names or None))

        if self.use_unified_cmd_topic:
            cmd_names = self.unified_cmd_joint_names if len(self.unified_cmd_joint_names) == len(action) else None
            cmd_msg = self._cmd_msg(action, cmd_names)
            self.follower_cmd_pub.publish(cmd_msg)
            self.get_logger().debug(f"CMD UNIFIED (len {len(action)})")
        else:
            cmd_left = self._cmd_msg(action_left, self.follower_left_joint_names or self.left_controller_joint_names)
            cmd_right = self._cmd_msg(action_right, self.follower_right_joint_names or self.right_controller_joint_names)
            self.follower_left_cmd_pub.publish(cmd_left)
            self.follower_right_cmd_pub.publish(cmd_right)
            self.get_logger().debug(f"CMD SPLIT right={len(action_right)} left={len(action_left)}")

    # ── Image publishing ──────────────────────────────────────────────────

    def _publish_images(self, item: Dict[str, Any]) -> None:
        stamp = self.get_clock().now().to_msg()
        for camera_key, (pub, is_compressed) in self.camera_pubs.items():
            # Check both prefixed and original keys for compatibility
            k_obs = f"observation.images.{camera_key}"
            found_key = None
            if k_obs in item:
                found_key = k_obs
            elif camera_key in item:
                found_key = camera_key
                
            if found_key is None: continue
            try: frame_rgb = _to_rgb_image(item[found_key])
            except Exception: continue
            if is_compressed:
                ok, encoded = cv2.imencode(".jpg", cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR))
                if ok:
                    msg = CompressedImage()
                    msg.header.stamp = stamp
                    msg.format = "jpeg"
                    msg.data = encoded.tobytes()
                    pub.publish(msg)
            else:
                image = np.ascontiguousarray(frame_rgb, dtype=np.uint8)
                msg = Image()
                msg.header.stamp, msg.height, msg.width = stamp, int(image.shape[0]), int(image.shape[1])
                msg.encoding, msg.is_bigendian, msg.step = "rgb8", 0, int(image.shape[1] * image.shape[2])
                msg.data = image.tobytes()
                pub.publish(msg)

    def _timestamp_of(self, item: Dict[str, Any]) -> float:
        ts = item.get("timestamp")
        if ts is None: return float(self.current_step)
        arr = _to_numpy(ts)
        return float(arr.reshape(-1)[0]) if arr.ndim > 0 else float(arr.item())

    def destroy_node(self) -> bool:
        if self.timer is not None: self.timer.cancel()
        return super().destroy_node()

def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Replay v3 dataset via ROS2 (service-based)")
    parser.add_argument("--config", default=_default_config_path())
    return parser

def main() -> None:
    _lock = _acquire_singleton_lock("ros2_topic_replay")
    parser = build_arg_parser()
    args, _ = parser.parse_known_args()
    rclpy.init()
    node = Ros2V3TopicReplay(args.config)
    try: rclpy.spin(node)
    except KeyboardInterrupt: pass
    finally:
        node.destroy_node()
        if rclpy.ok(): rclpy.shutdown()

if __name__ == "__main__":
    main()
