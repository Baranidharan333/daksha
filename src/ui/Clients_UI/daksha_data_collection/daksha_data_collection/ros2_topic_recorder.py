#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import cv2
import numpy as np
import rclpy
import yaml
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import CompressedImage, Image, JointState
from std_msgs.msg import String
from std_srvs.srv import Trigger
from daksha_msgs.srv import StartRecord


def _default_config_path() -> str:
    """Prefer the installed share/ copy (ros2 run/launch); fall back to the
    source-tree config/ next to this package when run straight from source
    (e.g. python3 ros2_topic_recorder.py during development)."""
    try:
        from ament_index_python.packages import get_package_share_directory
        return str(Path(get_package_share_directory("daksha_data_collection")) / "config" / "config.yaml")
    except Exception:
        return str(Path(__file__).resolve().parent.parent / "config" / "config.yaml")


def _acquire_singleton_lock(name: str):
    """Refuse to start a second instance of this node.

    A stray duplicate leaves two /recorder/start service servers and two
    /recorder/ui_status publishers on the ROS graph at once -- the UI then
    flip-flops between whichever instance's status message arrived last,
    and Start Record can silently get serviced by the stale one. Unlike
    web_data_management_ui (naturally deduped by its fixed HTTP port), this
    node has no OS resource to collide on, so we take an explicit lock.
    """
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


def _load_validate_dataset_module():
    """validate_dataset.py lives in Clients_UI/validation/ — a plain script
    folder, not a ROS package (no package.xml/CMakeLists, nothing installed
    to any share/ dir) — shared as-is with the standalone validation_ui.py.
    Only resolvable via a source-relative walk-up from this file's real
    location: works when this file resolves back to the source tree (true
    for --symlink-install), has no path back to it at all for a real,
    non-symlink install. Returns None (never raises) if it can't be found or
    imported, so a missing/broken validator degrades to "no live check"
    rather than taking the whole recorder node down.
    """
    candidate = Path(__file__).resolve().parent.parent.parent / "validation"
    if not (candidate / "validate_dataset.py").is_file():
        return None
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))
    try:
        import validate_dataset as vd
        return vd
    except Exception:
        return None


vd = _load_validate_dataset_module()


try:
    from .config import CameraSpec, V3DatasetConfig, V3FeatureSpec
    from .recorder import V3DatasetRecorder
except ImportError:
    from config import CameraSpec, V3DatasetConfig, V3FeatureSpec
    from recorder import V3DatasetRecorder


ROS2_TOPIC_CONFIG = "ros2_topics.json"

# This rig's real leader->follower bridge (gen2_leader package,
# main_with_service_mirror_wifi.py, "Mirror" teleop mode) cross-maps each
# leader arm's raw reading onto the OPPOSITE follower arm and multiplies by
# this fixed per-joint sign array before publishing /joint_cmd. Verified by
# comparing a live /leader/left_joint_states sample against the
# simultaneous /joint_cmd right-arm segment: every index matched exactly
# except joint_1 and joint_3 (index 0, 2), which were sign-flipped -- e.g.
# leader_left [-0.19481556, -0.02147573, -0.24697091, -0.00920388,
# 0.37122335, -0.01073787, -0.00613592, -0.0] vs joint_cmd right-segment
# [0.19481556, -0.02147573, 0.24697091, -0.00920388, 0.37122335,
# -0.01073787, -0.00613592, 0.0]. This one array is applied uniformly in
# both cross-body directions (leader_right->follower_left and
# leader_left->follower_right) -- there is no per-arm or per-joint-5
# asymmetry on this rig (unlike the different bi_arm_daksha rig this logic
# was originally ported from). Order is [joint_1..joint_7, gripper],
# matching this rig's fixed 8-DOF-per-arm joint layout (see
# follower_*_joint_names in ros2_topics.json). If a rig's arm dim doesn't
# match this length, _remap_action() falls back to raw (uncorrected) leader
# readings rather than misapplying these signs.
JOINT_SIGN_CORRECTION = np.array([-1.0, 1.0, -1.0, 1.0, 1.0, 1.0, 1.0, -1.0], dtype=np.float32)

# Static leader/follower zero-calibration offset, in radians, added to
# `action` (post sign-remap, [follower_left(8), follower_right(8)] order) so
# a leader held at rest maps onto the follower's true rest pose instead of a
# constant per-joint bias. Confirmed constant at rest (not motion-dependent
# tracking lag) on 2026-09-12 from a live at-rest sample:
#   index : action(rad)  observation.state(rad)  offset = action - obs
#   0 (L joint_1): 0.055223 - 0.077434  = -0.022211
#   3 (L joint_4): -0.001534 - 0.021172 = -0.022706
#   9 (R joint_2): 0.084369 - 0.037576  = +0.046793
#   11 (R joint_4): -0.006136 - (-0.036969) = +0.030833
#   12 (R joint_5): -0.015340 - 0.017744 = -0.033084
#   14 (R joint_7): 0.001534 - 0.050546  = -0.049012
# Every other index measured under 1 deg of at-rest offset and is left
# uncorrected. Re-derive (hold both arms still, compare recorded action vs
# observation.state) if the rig is ever recalibrated or these joints drift.
#
# Re-checked later the same day (2026-09-12) against a fresh at-rest sample
# with the above offsets already applied; indices 9 and 14 still showed
# >1 deg of residual bias and two more indices had drifted past 1 deg, so
# their offsets are additive corrections (new = old + residual):
#   index : action(rad)  observation.state(rad)  residual = action - obs
#   1 (L joint_2): -0.033748 - 0.017031  = -2.909 deg -> offset -0.050778 (new)
#   8 (R joint_1): -0.021476 - (-0.002480) = -1.088 deg -> offset -0.018996 (new)
#   9 (R joint_2): 0.037576 - 0.005148 = +1.858 deg -> offset 0.046793 + 0.032428 = 0.079221
#   14 (R joint_7): 0.050546 - 0.071734 = -1.214 deg -> offset -0.049012 + -0.021188 = -0.070200
ACTION_CALIBRATION_OFFSET = np.zeros(16, dtype=np.float32)
ACTION_CALIBRATION_OFFSET[0] = -0.022211
ACTION_CALIBRATION_OFFSET[1] = -0.050778
ACTION_CALIBRATION_OFFSET[3] = -0.022706
ACTION_CALIBRATION_OFFSET[8] = -0.018996
ACTION_CALIBRATION_OFFSET[9] = 0.079221
ACTION_CALIBRATION_OFFSET[11] = 0.030833
ACTION_CALIBRATION_OFFSET[12] = -0.033084
ACTION_CALIBRATION_OFFSET[14] = -0.070200


def _joint_array(values) -> np.ndarray:
    return np.asarray(values, dtype=np.float32).reshape(-1)


def _joint_names(msg: Optional[JointState]) -> list[str]:
    if msg is None:
        return []
    return [str(name) for name in list(msg.name or [])]


def _raw_image_msg_to_bgr(msg: Image) -> np.ndarray:
    height = int(msg.height)
    width = int(msg.width)
    encoding = str(msg.encoding).lower()
    
    if "bgra" in encoding or "rgba" in encoding or "8uc4" in encoding:
        channels = 4
    elif "mono" in encoding or "8uc1" in encoding or "mono8" in encoding:
        channels = 1
    else:
        channels = 3
        
    row_bytes = int(msg.step) if int(msg.step) > 0 else width * channels
    array = np.frombuffer(msg.data, dtype=np.uint8)
    image = array.reshape(height, row_bytes)[:, : width * channels]
    
    if channels == 1:
        mono = image.reshape(height, width)
        return cv2.cvtColor(mono, cv2.COLOR_GRAY2BGR)
    elif channels == 4:
        image_4c = image.reshape(height, width, 4)
        if "bgra" in encoding:
            return cv2.cvtColor(image_4c, cv2.COLOR_BGRA2BGR)
        else: # rgba
            return cv2.cvtColor(image_4c, cv2.COLOR_RGBA2BGR)
    else: # channels == 3
        image_3c = image.reshape(height, width, 3)
        if "rgb" in encoding:
            return cv2.cvtColor(image_3c, cv2.COLOR_RGB2BGR)
        else:
            return image_3c


def _write_ros2_topic_config(root: Path, payload: dict) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / ROS2_TOPIC_CONFIG).write_text(json.dumps(payload, indent=2), encoding="utf-8")


class Ros2V3TopicRecorder(Node):
    def __init__(self, config_path: str) -> None:
        super().__init__("custom_v3_topic_recorder")
        self.config_path = config_path

        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)

        dataset_cfg = self.config.get("dataset", {})
        record_cfg = self.config.get("recording", {})
        topics_cfg = self.config.get("recording_topics", self.config.get("topics", {}))

        self.dataset_name = dataset_cfg.get("dataset_name", "task1")
        self.repo_id = f"local/{self.dataset_name}"
        self.root_dir = (
            Path(dataset_cfg.get("root_dir", _default_dataset_dir()))
            .expanduser()
            .resolve()
            / self.dataset_name
        )
        self.task = dataset_cfg.get("task", "task1")
        self.prompt = dataset_cfg.get("prompt", "")
        self.robot_type = dataset_cfg.get("robot_type", "bimanual_leader_follower")

        self.record_hz = float(record_cfg.get("record_hz", 10.0))
        self.episode_len = int(record_cfg.get("episode_len", 250))
        self.max_episodes = int(record_cfg.get("max_episodes", 1))
        self.inter_episode_delay = float(record_cfg.get("inter_episode_delay", 5.0))
        self.fps = int(record_cfg.get("fps", 10))
        self.width = int(record_cfg.get("width", 320))
        self.height = int(record_cfg.get("height", 240))
        self.disable_videos = bool(record_cfg.get("disable_videos", False))
        self.vcodec = str(record_cfg.get("vcodec", "h264"))
        self.disable_streaming_encoding = bool(record_cfg.get("disable_streaming_encoding", False))
        self.leader_dim_override = record_cfg.get("leader_dim")
        self.follower_dim_override = record_cfg.get("follower_dim")
        self.action_dim_override = record_cfg.get("action_dim")
        self.include_follower_state_duplicate = bool(
            record_cfg.get("include_follower_state_duplicate", False)
        )

        # Gripper sign is baked into JOINT_SIGN_CORRECTION[-1] (= -1.0,
        # confirmed against this rig's real /joint_cmd), but stays
        # config-overridable (uniform across both arms -- the real bridge's
        # mirror_signs applies one array symmetrically in both cross-body
        # directions, with no per-arm asymmetry) in case the gripper sensor
        # is ever re-zeroed/reconnected with the opposite convention.
        # Reloaded on every /recorder/start in case config.yaml changed.
        self.leader_gripper_sign = float(record_cfg.get("leader_gripper_sign", JOINT_SIGN_CORRECTION[-1]))
        self._rebuild_action_signs()
        # Fallback only, in case _calibrate_action_offset() hasn't run yet
        # (e.g. logged before the first episode starts). Real value is
        # captured fresh at the start of every episode -- see
        # _calibrate_action_offset() for why a static table doesn't work.
        self.action_calibration_offset = ACTION_CALIBRATION_OFFSET.copy()

        self.camera_topics: Dict[str, str] = topics_cfg.get("camera_topics", {})
        self.leader_left_topic = topics_cfg.get("leader_topic_left", "/leader/left_joint_states")
        self.leader_right_topic = topics_cfg.get("leader_topic_right", "/leader/right_joint_states")
        self.follower_left_topic = topics_cfg.get("follower_topic_left", "/LeftArmSystem_ordered_joint_states")
        self.follower_right_topic = topics_cfg.get("follower_topic_right", "/RightArmSystem_ordered_joint_states")
        self.follower_cmd_left_topic = topics_cfg.get("follower_cmd_topic_left", "/left_arm_controller/commands")
        self.follower_cmd_right_topic = topics_cfg.get("follower_cmd_topic_right", "/right_arm_controller/commands")
        self.follower_cmd_topic = topics_cfg.get("joint_cmd_topic", topics_cfg.get("follower_cmd_topic", ""))
        if not self.follower_cmd_topic and self.follower_cmd_left_topic == self.follower_cmd_right_topic and self.follower_cmd_left_topic:
            self.follower_cmd_topic = self.follower_cmd_left_topic
        self.follower_cmd_msg_type = self._infer_follower_cmd_msg_type(topics_cfg)

        # --- State ---
        # Initialize as None so we block recording until actual topics are publishing.
        self.latest_leader_left: Optional[JointState] = None
        self.latest_leader_right: Optional[JointState] = None
        self.latest_follower_left: Optional[JointState] = None
        self.latest_follower_right: Optional[JointState] = None

        # Reference joint name lists (learned from first received messages)
        self.reference_leader_left_joint_names: list[str] = []
        self.reference_leader_right_joint_names: list[str] = []
        self.reference_follower_left_joint_names: list[str] = []
        self.reference_follower_right_joint_names: list[str] = []

        self._warned_keys: set[str] = set()
        self.camera_subs: Dict[str, Any] = {}
        self._camera_topic_by_key: Dict[str, str] = {}
        self.current_images: Dict[str, Optional[np.ndarray]] = {
            key: None for key in self.camera_topics
        }

        self.recorder: Optional[V3DatasetRecorder] = None
        self.record_timer = None
        self.restart_timer = None
        self.step_count = 0
        self.episodes_recorded = 0
        self.last_wait_log_ns = 0
        self.is_finalized = False
        self.stop_requested = False
        self.control_start_requested = False

        # --- Post-save validation (validate_dataset.check_episode) ---
        # Thresholds/flags only -- check_episode() never reads args.dataset,
        # so these don't need rebuilding when root_dir changes mid-session.
        self._validation_args = vd.build_parser().parse_args(["."]) if vd else None
        if vd is None:
            self.get_logger().warn(
                "validate_dataset module not found (Clients_UI/validation/ "
                "unreachable) -- episodes will be saved without the post-save "
                "validation check."
            )
        self.last_episode_validation: Optional[dict] = None
        self.validation_blocked = False

        # --- Subscriptions ---
        self.topics_to_check: list[str] = []
        self._sub_leader_left = None
        self._sub_leader_right = None
        self._sub_follower_left = None
        self._sub_follower_right = None

        self._set_joint_subscription("_sub_leader_left", "leader_left_topic",
                                      self.leader_left_topic, self._leader_left_callback)
        self._set_joint_subscription("_sub_leader_right", "leader_right_topic",
                                      self.leader_right_topic, self._leader_right_callback)
        self._set_joint_subscription("_sub_follower_left", "follower_left_topic",
                                      self.follower_left_topic, self._follower_left_callback)
        self._set_joint_subscription("_sub_follower_right", "follower_right_topic",
                                      self.follower_right_topic, self._follower_right_callback)

        for camera_key, topic in self.camera_topics.items():
            self._create_camera_subscription(camera_key, topic)
            self.topics_to_check.append(topic)

        # --- Services ---
        self.srv_start = self.create_service(StartRecord, "/recorder/start", self._handle_start)
        self.srv_stop = self.create_service(Trigger, "/recorder/stop", self._handle_stop)
        self.srv_ack_validation = self.create_service(
            Trigger, "/recorder/acknowledge_validation", self._handle_acknowledge_validation
        )

        # --- UI Status Publisher ---
        self.status_pub = self.create_publisher(String, '/recorder/ui_status', 10)
        self.create_timer(1.0, self._publish_status)

        self.check_timer = self.create_timer(0.5, self._check_topics_ready)
        self.get_logger().info(f"Recorder initialized. Dataset path: {self.root_dir}")

    # ── Status Publisher ──────────────────────────────────────────────────

    def _publish_status(self) -> None:
        try:
            status = {
                "recording": self.record_timer is not None,
                "step_count": self.step_count,
                "max_steps": self.episode_len,
                "episodes_recorded": self.episodes_recorded,
                "camera_topics": self.camera_topics,
                "dataset_name": self.dataset_name,
                "validation_blocked": self.validation_blocked,
                "last_episode_validation": self.last_episode_validation,
            }
            msg = String()
            msg.data = json.dumps(status)
            self.status_pub.publish(msg)
        except Exception as e:
            self.get_logger().error(f"Error publishing status: {e}")

    # ── Callbacks ──────────────────────────────────────────────────────────

    def _leader_left_callback(self, msg: JointState) -> None:
        self.latest_leader_left = msg
        self._update_joint_name_reference()

    def _leader_right_callback(self, msg: JointState) -> None:
        self.latest_leader_right = msg
        self._update_joint_name_reference()

    def _follower_left_callback(self, msg: JointState) -> None:
        self.latest_follower_left = msg
        self._update_joint_name_reference()

    def _follower_right_callback(self, msg: JointState) -> None:
        self.latest_follower_right = msg
        self._update_joint_name_reference()

    # ── Services ───────────────────────────────────────────────────────────

    def _handle_start(self, request, response):
        self.get_logger().info("Service called to START recording.")
        if self.record_timer is not None:
            response.success = False
            response.message = "Recording is already in progress."
            return response

        # --- Reload configuration YAML file to detect updated tasks and prompts ---
        try:
            with open(self.config_path, "r") as f:
                self.config = yaml.safe_load(f) or {}
            dataset_cfg = self.config.get("dataset", {})
            self.task = dataset_cfg.get("task", self.task)
            self.prompt = dataset_cfg.get("prompt", self.prompt)
            
            record_cfg = self.config.get("recording", {})
            self.fps = int(record_cfg.get("fps", self.fps))
            self.leader_gripper_sign = float(
                record_cfg.get("leader_gripper_sign", self.leader_gripper_sign)
            )
            self._rebuild_action_signs()

            # Reload and update camera + joint topics dynamically!
            topics_cfg = self.config.get("recording_topics", self.config.get("topics", {}))
            # `or self.camera_topics`: an empty dict here almost always means
            # a caller (e.g. the web UI before "Load Topics"/camera list has
            # populated) sent nothing rather than "intentionally remove every
            # camera" -- see the matching guard in web_data_management_ui.py.
            # Silently accepting it would let recording start with zero
            # cameras subscribed (see _handle_start's readiness check and the
            # camera-count guard below).
            new_camera_topics = topics_cfg.get("camera_topics", {}) or self.camera_topics

            # 1. Remove cameras that are no longer present
            for old_key in list(self.camera_topics.keys()):
                if old_key not in new_camera_topics:
                    self._remove_camera_subscription(old_key)

            # 2. Add or update subscriptions
            self.camera_topics = new_camera_topics
            self.topics_to_check = []

            # Re-point joint subscriptions if the operator picked different
            # leader/follower topics in the UI since this node started.
            # `or` (not dict.get's default=) deliberately treats an empty
            # string the same as an absent key: the web UI's topic-selector
            # dropdowns aren't wired up (getVal() returns '' when the
            # element doesn't exist), so an empty string here means "nothing
            # was picked", not "the operator explicitly wants no topic" --
            # it must never blank out an already-good subscription.
            self._set_joint_subscription(
                "_sub_leader_left", "leader_left_topic",
                topics_cfg.get("leader_topic_left") or self.leader_left_topic,
                self._leader_left_callback,
            )
            self._set_joint_subscription(
                "_sub_leader_right", "leader_right_topic",
                topics_cfg.get("leader_topic_right") or self.leader_right_topic,
                self._leader_right_callback,
            )
            self._set_joint_subscription(
                "_sub_follower_left", "follower_left_topic",
                topics_cfg.get("follower_topic_left") or self.follower_left_topic,
                self._follower_left_callback,
            )
            self._set_joint_subscription(
                "_sub_follower_right", "follower_right_topic",
                topics_cfg.get("follower_topic_right") or self.follower_right_topic,
                self._follower_right_callback,
            )
            self.follower_cmd_left_topic = topics_cfg.get("follower_cmd_topic_left") or self.follower_cmd_left_topic
            self.follower_cmd_right_topic = topics_cfg.get("follower_cmd_topic_right") or self.follower_cmd_right_topic
            new_follower_cmd_topic = topics_cfg.get("joint_cmd_topic", topics_cfg.get("follower_cmd_topic", ""))
            if not new_follower_cmd_topic and self.follower_cmd_left_topic == self.follower_cmd_right_topic and self.follower_cmd_left_topic:
                new_follower_cmd_topic = self.follower_cmd_left_topic
            self.follower_cmd_topic = new_follower_cmd_topic
            self.follower_cmd_msg_type = self._infer_follower_cmd_msg_type(topics_cfg)

            # Rebuild topics_to_check with basic joint/cmd topics
            if self.leader_left_topic: self.topics_to_check.append(self.leader_left_topic)
            if self.leader_right_topic: self.topics_to_check.append(self.leader_right_topic)
            if self.follower_left_topic: self.topics_to_check.append(self.follower_left_topic)
            if self.follower_right_topic: self.topics_to_check.append(self.follower_right_topic)

            for camera_key, topic in self.camera_topics.items():
                self._create_camera_subscription(camera_key, topic)
                self.topics_to_check.append(topic)
                if camera_key not in self.current_images:
                    self.current_images[camera_key] = None
            
            # Recompute base directory from reloaded config if the request didn't override it
            if not request.dataset_name:
                self.root_dir = (
                    Path(dataset_cfg.get("root_dir", _default_dataset_dir()))
                    .expanduser()
                    .resolve()
                    / self.dataset_name
                )
        except Exception as e:
            self.get_logger().error(f"Failed to reload config.yaml in start handler: {e}")

        if request.dataset_name:
            self.dataset_name = request.dataset_name
            self.repo_id = f"local/{self.dataset_name}"
            dataset_cfg = self.config.get("dataset", {})
            self.root_dir = (
                Path(dataset_cfg.get("root_dir", _default_dataset_dir()))
                .expanduser()
                .resolve()
                / self.dataset_name
            )
        if request.episode_length > 0:
            self.episode_len = request.episode_length
        if request.record_hz > 0.0:
            self.record_hz = float(request.record_hz)
        if request.max_episodes > 0:
            self.max_episodes = request.max_episodes

        self.control_start_requested = True
        self.stop_requested = False
        self.last_episode_validation = None
        self.validation_blocked = False

        if self._all_topics_ready():
            self._start_episode()
            response.success = True
            response.message = "Recording started successfully."
        else:
            response.success = False
            response.message = (
                f"Failed to start recording. Offline topics: {', '.join(self._missing_inputs())}"
            )
        return response

    def _handle_stop(self, request, response):
        self.get_logger().info("Service called to STOP recording.")
        self.stop_requested = True
        self.control_start_requested = False
        if self.record_timer is not None:
            self._finish_episode()
        response.success = True
        response.message = "Recording stopped."
        return response

    def _set_joint_subscription(self, sub_attr: str, topic_attr: str, new_topic: str, callback) -> None:
        """(Re)point a leader/follower joint subscription at `new_topic`.

        Camera subscriptions already get recreated on every /recorder/start
        call when their topic changes (see _create_camera_subscription in
        the reload block below); joint subscriptions used to be wired up
        once in __init__ and never touched again, so picking a different
        leader/follower topic in the UI silently kept recording from the
        old one. This makes joint topics reconfigurable the same way.
        """
        if new_topic == getattr(self, topic_attr, "") and getattr(self, sub_attr) is not None:
            return
        old_sub = getattr(self, sub_attr)
        if old_sub is not None:
            self.destroy_subscription(old_sub)
        setattr(self, topic_attr, new_topic)
        setattr(
            self, sub_attr,
            self.create_subscription(JointState, new_topic, callback, 10) if new_topic else None,
        )
        # Drop the stale message from the old topic -- otherwise
        # _all_topics_ready() would treat leftover data from a topic we're
        # no longer subscribed to as proof the new one is already live.
        setattr(self, "latest_" + sub_attr[len("_sub_"):], None)

    # ── Camera subscriptions ───────────────────────────────────────────────

    def _create_camera_subscription(self, camera_key: str, topic: str) -> None:
        """(Re)point a camera subscription at `topic`. Skips the actual
        destroy+recreate when the topic hasn't changed -- /recorder/start
        calls this for every configured camera on every single click (same
        as _set_joint_subscription used to for leader/follower topics), and
        needlessly tearing down a live subscription forces DDS through a
        rediscovery/QoS-rematch cycle right before _all_topics_ready() is
        checked synchronously in that same call. Without this guard, a
        camera that was already receiving frames fine can show up as
        "offline" on the very next Start click for no reason."""
        if topic == self._camera_topic_by_key.get(camera_key) and camera_key in self.camera_subs:
            return
        if camera_key in self.camera_subs:
            try:
                self.destroy_subscription(self.camera_subs[camera_key])
            except Exception:
                pass

        if topic.rstrip("/").endswith("/compressed"):
            sub = self.create_subscription(
                CompressedImage,
                topic,
                self._make_compressed_image_callback(camera_key),
                qos_profile_sensor_data,
            )
        else:
            sub = self.create_subscription(
                Image,
                topic,
                self._make_raw_image_callback(camera_key),
                qos_profile_sensor_data,
            )
        self.camera_subs[camera_key] = sub
        self._camera_topic_by_key[camera_key] = topic
        # Drop any stale frame from the old subscription -- otherwise
        # _all_topics_ready() would treat leftover data from a topic we're
        # no longer subscribed to as proof the new one is already live
        # (same reasoning as _set_joint_subscription's reset).
        self.current_images[camera_key] = None

    def _remove_camera_subscription(self, camera_key: str) -> None:
        if camera_key in self.camera_subs:
            try:
                self.destroy_subscription(self.camera_subs[camera_key])
            except Exception:
                pass
            del self.camera_subs[camera_key]
        self._camera_topic_by_key.pop(camera_key, None)
        if camera_key in self.current_images:
            del self.current_images[camera_key]

    def _make_compressed_image_callback(self, camera_key: str):
        def callback(msg: CompressedImage) -> None:
            self.current_images[camera_key] = msg
        return callback

    def _make_raw_image_callback(self, camera_key: str):
        def callback(msg: Image) -> None:
            self.current_images[camera_key] = msg
        return callback

    # ── Joint name tracking (from reference) ──────────────────────────────

    def _warn_once(self, key: str, message: str) -> None:
        if key in self._warned_keys:
            return
        self._warned_keys.add(key)
        self.get_logger().warn(message)

    def _update_reference_names(
        self,
        msg: Optional[JointState],
        reference_names: list[str],
        stream_label: str,
    ) -> bool:
        names = _joint_names(msg)
        if names and not reference_names:
            reference_names[:] = names
            return True
        if names and reference_names and names != reference_names:
            self._warn_once(
                f"{stream_label}_joint_order_changed",
                f"{stream_label} joint name/order changed. Recorder will remap by name.",
            )
        return False

    def _update_joint_name_reference(self) -> None:
        changed = any([
            self._update_reference_names(self.latest_leader_left, self.reference_leader_left_joint_names, "leader_left"),
            self._update_reference_names(self.latest_leader_right, self.reference_leader_right_joint_names, "leader_right"),
            self._update_reference_names(self.latest_follower_left, self.reference_follower_left_joint_names, "follower_left"),
            self._update_reference_names(self.latest_follower_right, self.reference_follower_right_joint_names, "follower_right"),
        ])
        if changed:
            self._write_topic_config()

    def _combined_joint_names(self, left_names: list[str], right_names: list[str]) -> list[str]:
        """Stored as left-then-right to match recording order (see
        _record_step's leader_state/follower_state concatenation)."""
        return [f"left/{n}" for n in left_names] + [f"right/{n}" for n in right_names]

    def _leader_joint_names(self) -> list[str]:
        return self._combined_joint_names(
            self.reference_leader_left_joint_names,
            self.reference_leader_right_joint_names,
        )

    def _follower_joint_names(self) -> list[str]:
        return self._combined_joint_names(
            self.reference_follower_left_joint_names,
            self.reference_follower_right_joint_names,
        )

    def _write_topic_config(self) -> None:
        payload = {
            "repo_id": self.repo_id,
            "fps": self.fps,
            # Nested {"left":.., "right":..} shape so ros2_topic_replay.py
            # doesn't have to guess an ordering from a comma-joined string.
            "leader_state_topic": {"left": self.leader_left_topic, "right": self.leader_right_topic},
            "follower_state_topic": {"left": self.follower_left_topic, "right": self.follower_right_topic},
            "follower_cmd_topic": {"left": self.follower_cmd_left_topic, "right": self.follower_cmd_right_topic},
            "camera_topics": self.camera_topics,
            "joint_names": {
                "leader_left": self.reference_leader_left_joint_names,
                "leader_right": self.reference_leader_right_joint_names,
                "follower_left": self.reference_follower_left_joint_names,
                "follower_right": self.reference_follower_right_joint_names,
            },
            # This recorder always concatenates state/action vectors
            # left-arm-first then right-arm (see _combined_joint_names and
            # _record_step) -- spelled out explicitly so
            # ros2_topic_replay.py doesn't have to infer it.
            "state_concat_order": ["left", "right"],
            # Kept for ros2_topic_replay.py, which looks these up as flat
            # top-level keys.
            "leader_left_topic": self.leader_left_topic,
            "leader_right_topic": self.leader_right_topic,
            "follower_left_topic": self.follower_left_topic,
            "follower_right_topic": self.follower_right_topic,
            "follower_cmd_msg_type": self.follower_cmd_msg_type,
            "leader_state_joint_names": self._leader_joint_names(),
            "follower_state_joint_names": self._follower_joint_names(),
            # `action` is remapped into follower left/right order (see
            # _remap_action), so its names follow that convention rather
            # than the raw leader order.
            "action_joint_names": self._follower_joint_names(),
            "leader_left_joint_names": self.reference_leader_left_joint_names,
            "leader_right_joint_names": self.reference_leader_right_joint_names,
            "follower_left_joint_names": self.reference_follower_left_joint_names,
            "follower_right_joint_names": self.reference_follower_right_joint_names,
            "action_convention": "follower_left_right_sign_corrected",
            "leader_state_convention": "raw_leader_device_order",
            "leader_gripper_sign": self.leader_gripper_sign,
        }
        _write_ros2_topic_config(self.root_dir, payload)

    # ── Joint vector building (from reference) ─────────────────────────────

    def _ordered_joint_vector(
        self, msg: JointState, reference_names: list[str], stream_label: str
    ) -> np.ndarray:
        """Build a fixed-order vector using reference joint names.

        Looks up each reference name in the incoming message by name so that
        the order in the dataset is always stable regardless of what order the
        robot publishes joints.
        """
        if not reference_names:
            return _joint_array(msg.position)

        names = _joint_names(msg)
        positions = list(msg.position)
        if names and len(names) == len(positions):
            position_by_name = {str(n): float(p) for n, p in zip(names, positions)}
            missing = [n for n in reference_names if n not in position_by_name]
            if not missing:
                return np.asarray(
                    [position_by_name[n] for n in reference_names], dtype=np.float32
                ).reshape(-1)
            self._warn_once(
                f"{stream_label}_missing_joint_names",
                f"{stream_label} missing reference joints; falling back to raw order.",
            )
        elif names and len(names) != len(positions):
            self._warn_once(
                f"{stream_label}_len_mismatch",
                f"{stream_label} has {len(names)} names but {len(positions)} positions; falling back.",
            )
        return _joint_array(positions)

    def _infer_follower_cmd_msg_type(self, topics_cfg: dict) -> str:
        """Mirror ros2_topic_replay.py's _refresh_command_publisher type
        inference, so the metadata this recorder writes into
        ros2_topics.json (follower_cmd_msg_type) reflects what replay will
        actually publish for the same config, instead of a hardcoded
        constant that doesn't match (this used to always say
        'float64_multi_array' even when the real topic was /joint_cmd,
        which replay infers as 'joint_state')."""
        msg_type = str(topics_cfg.get("follower_cmd_msg_type", "")).strip().lower()
        if msg_type:
            return "joint_state" if msg_type == "jointstate" else msg_type
        reference_topic = self.follower_cmd_topic if self.follower_cmd_topic else self.follower_cmd_left_topic
        if reference_topic.endswith("/joint_trajectory"):
            return "joint_trajectory"
        elif reference_topic.endswith("/commands"):
            return "float64_multi_array"
        return "joint_state"  # default for joint_cmd

    def _rebuild_action_signs(self) -> None:
        """(Re)build the sign vector used by _remap_action. The real
        gen2_leader bridge applies one mirror_signs array uniformly in both
        cross-body directions (no per-arm asymmetry), so a single vector
        covers both leader_right->follower_left and leader_left
        ->follower_right. Call whenever leader_gripper_sign changes."""
        self.action_sign = JOINT_SIGN_CORRECTION.copy()
        self.action_sign[-1] = self.leader_gripper_sign

    def _sign_corrected_action(
        self, leader_left_vec: np.ndarray, leader_right_vec: np.ndarray
    ) -> Optional[np.ndarray]:
        """Cross-body sign remap only (leader_right -> follower_left target,
        leader_left -> follower_right target), matching this rig's
        left-then-right storage order -- no zero-calibration offset applied.
        Returns None if the arm dim doesn't match this rig's fixed layout
        (caller falls back to raw, uncorrected leader readings)."""
        if (
            leader_left_vec.shape[0] != JOINT_SIGN_CORRECTION.shape[0]
            or leader_right_vec.shape[0] != JOINT_SIGN_CORRECTION.shape[0]
        ):
            self._warn_once(
                "action_sign_dim_mismatch",
                f"Leader arm dim != {JOINT_SIGN_CORRECTION.shape[0]}; recording action as "
                "raw leader readings without cross-arm sign correction.",
            )
            return None
        return np.concatenate(
            [self.action_sign * leader_right_vec, self.action_sign * leader_left_vec]
        ).astype(np.float32)

    def _calibrate_action_offset(self) -> None:
        """Re-measure the leader/follower zero-calibration offset fresh from
        the current (assumed at-rest, since this runs right as an episode
        starts) sample, instead of relying on the static
        ACTION_CALIBRATION_OFFSET table.

        That table was measured once (2026-09-12) and had already gone
        stale within the same day -- two joints needed re-correction and
        two more had newly drifted past 1 deg, all within hours. A fixed
        constant can't track an offset that moves that fast (leader
        encoder/backlash drift, and/or the follower never quite settling to
        a repeatable rest pose). Re-measuring at the start of every episode
        self-corrects for whatever the drift is *right now* instead of
        replaying a stale snapshot from a previous session.
        """
        leader_right_vec = self._ordered_joint_vector(
            self.latest_leader_right, self.reference_leader_right_joint_names, "leader_right"
        )
        leader_left_vec = self._ordered_joint_vector(
            self.latest_leader_left, self.reference_leader_left_joint_names, "leader_left"
        )
        follower_right_vec = self._ordered_joint_vector(
            self.latest_follower_right, self.reference_follower_right_joint_names, "follower_right"
        )
        follower_left_vec = self._ordered_joint_vector(
            self.latest_follower_left, self.reference_follower_left_joint_names, "follower_left"
        )

        raw_action = self._sign_corrected_action(leader_left_vec, leader_right_vec)
        follower_state = np.concatenate([follower_left_vec, follower_right_vec]).astype(np.float32)

        if raw_action is None or raw_action.shape[0] != follower_state.shape[0]:
            self.get_logger().warn(
                "Skipping session zero-calibration (dim mismatch); using previous/default offset."
            )
            return

        self.action_calibration_offset = (raw_action - follower_state).astype(np.float32)
        offsets_str = ", ".join(f"{v:+.4f}" for v in self.action_calibration_offset)
        self.get_logger().info(f"Session zero-calibration captured: [{offsets_str}]")

    def _remap_action(self, leader_left_vec: np.ndarray, leader_right_vec: np.ndarray) -> np.ndarray:
        """Remap raw leader readings into the follower's own left/right +
        sign convention, then apply this session's zero-calibration offset
        (see _calibrate_action_offset) so action lines up index-for-index
        with observation.state, and replaying `action` onto
        follower_cmd_left/right drives the correct arm."""
        remapped = self._sign_corrected_action(leader_left_vec, leader_right_vec)
        if remapped is None:
            return np.concatenate([leader_left_vec, leader_right_vec]).astype(np.float32)
        if remapped.shape[0] == self.action_calibration_offset.shape[0]:
            remapped = remapped - self.action_calibration_offset
        return remapped

    # ── Topic readiness ────────────────────────────────────────────────────

    def _all_topics_ready(self) -> bool:
        # An empty camera_topics dict must never read as "ready" -- with no
        # cameras configured, all(...) over an empty iterable is vacuously
        # True, which would let recording start (and silently complete a
        # full episode) with zero camera frames captured. See the
        # camera_topics reload guards in _handle_start / config.py for how
        # an empty dict can end up here in the first place.
        if not self.camera_topics: return False
        if self.latest_leader_left is None: return False
        if self.latest_leader_right is None: return False
        if self.latest_follower_left is None: return False
        if self.latest_follower_right is None: return False
        return all(f is not None for f in self.current_images.values())

    def _missing_inputs(self) -> list[str]:
        missing = []
        if not self.camera_topics: missing.append("cameras:none_configured")
        if self.latest_leader_left is None: missing.append(f"leader_left:{self.leader_left_topic}")
        if self.latest_leader_right is None: missing.append(f"leader_right:{self.leader_right_topic}")
        if self.latest_follower_left is None: missing.append(f"follower_left:{self.follower_left_topic}")
        if self.latest_follower_right is None: missing.append(f"follower_right:{self.follower_right_topic}")
        for key, frame in self.current_images.items():
            if frame is None:
                missing.append(f"camera:{key}")
        return missing

    # ── Dataset config ─────────────────────────────────────────────────────

    def _build_v3_config(self) -> V3DatasetConfig:
        self._update_joint_name_reference()
        leader_names = self._leader_joint_names()
        follower_names = self._follower_joint_names()

        leader_dim = (
            int(self.leader_dim_override)
            if self.leader_dim_override is not None
            else (len(leader_names) if leader_names else
                  len(self.latest_leader_left.position) + len(self.latest_leader_right.position))
        )
        follower_dim = (
            int(self.follower_dim_override)
            if self.follower_dim_override is not None
            else (len(follower_names) if follower_names else
                  len(self.latest_follower_left.position) + len(self.latest_follower_right.position))
        )
        action_dim = int(self.action_dim_override) if self.action_dim_override is not None else leader_dim

        cameras = [
            CameraSpec(key=f"observation.images.{k}", width=self.width, height=self.height, role="secondary")
            for k in self.camera_topics
        ]

        return V3DatasetConfig(
            repo_id=self.repo_id,
            root=self.root_dir,
            fps=self.fps,
            robot_type=self.robot_type,
            cameras=cameras,
            feature_spec=V3FeatureSpec(
                action_dim=action_dim,
                follower_state_dim=follower_dim,
                leader_state_dim=leader_dim,
                include_follower_state_duplicate=self.include_follower_state_duplicate,
            ),
            use_videos=not self.disable_videos,
            vcodec=self.vcodec,
            streaming_encoding=not self.disable_streaming_encoding,
        )

    def _ensure_recorder(self) -> V3DatasetRecorder:
        if self.recorder is not None:
            return self.recorder
        cfg = self._build_v3_config()
        if (cfg.root / "meta" / "info.json").exists():
            self.recorder = V3DatasetRecorder.resume_existing(cfg)
        else:
            self.recorder = V3DatasetRecorder.create_new(cfg)
        self._write_topic_config()
        return self.recorder

    # ── Episode control ────────────────────────────────────────────────────

    def _check_topics_ready(self) -> None:
        if self.stop_requested or self.record_timer is not None or self.restart_timer is not None:
            return
        if not self.control_start_requested:
            return
        if not self._all_topics_ready():
            now_ns = self.get_clock().now().nanoseconds
            if now_ns - self.last_wait_log_ns >= int(2e9):
                self.get_logger().info("Waiting for: %s" % ", ".join(self._missing_inputs()))
                self.last_wait_log_ns = now_ns
            return
        self.get_logger().info("All topics ready. Starting recording.")
        self._start_episode()

    def _start_episode(self) -> None:
        self._ensure_recorder()
        self._calibrate_action_offset()
        self.step_count = 0
        self.record_timer = self.create_timer(1.0 / self.record_hz, self._record_step)
        self.get_logger().info(
            f"Recording episode into {self.root_dir} (target: {self.episode_len} steps)"
        )

    def _record_step(self) -> None:
        if self.stop_requested or self.recorder is None:
            return
        if not self._all_topics_ready():
            self.get_logger().warn("Skipping step — topic(s) missing")
            return

        frames = {}
        for k, f in self.current_images.items():
            if f is not None:
                try:
                    img_data = None
                    if isinstance(f, np.ndarray):
                        img_data = f.copy()
                    elif hasattr(f, 'data') and (hasattr(f, 'format') or 'CompressedImage' in str(type(f))):
                        # CompressedImage
                        encoded = np.frombuffer(f.data, dtype=np.uint8)
                        frame_bgr = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
                        if frame_bgr is not None:
                            img_data = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
                    else:
                        # Raw Image msg
                        frame_bgr = _raw_image_msg_to_bgr(f)
                        img_data = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
                        
                    if img_data is not None:
                        frames[f"observation.images.{k}"] = img_data
                except Exception as exc:
                    self.get_logger().warn(f"Lazy decoding failed for camera '{k}': {exc}")

        self._update_joint_name_reference()

        # Build per-arm ordered vectors using reference joint names
        leader_right_vec = self._ordered_joint_vector(
            self.latest_leader_right, self.reference_leader_right_joint_names, "leader_right"
        )
        leader_left_vec = self._ordered_joint_vector(
            self.latest_leader_left, self.reference_leader_left_joint_names, "leader_left"
        )
        follower_right_vec = self._ordered_joint_vector(
            self.latest_follower_right, self.reference_follower_right_joint_names, "follower_right"
        )
        follower_left_vec = self._ordered_joint_vector(
            self.latest_follower_left, self.reference_follower_left_joint_names, "follower_left"
        )

        # Concatenate left-then-right (matches _combined_joint_names / the
        # state_concat_order written to ros2_topics.json). observation.state
        # is recorded as-is from the follower's own joint state topics --
        # no per-joint correction; only `action` (the leader->follower
        # command) needs the cross-body sign remap, per this rig's real
        # gen2_leader bridge (see JOINT_SIGN_CORRECTION above).
        leader_state = np.concatenate([leader_left_vec, leader_right_vec]).astype(np.float32)
        follower_state = np.concatenate([follower_left_vec, follower_right_vec]).astype(np.float32)
        action = self._remap_action(leader_left_vec, leader_right_vec)

        self.recorder.add_step(
            frames_by_camera=frames,
            action=action,
            follower_state=follower_state,
            leader_state=leader_state,
            task=self.task,
            prompt=self.prompt,
            timestamp=self.get_clock().now().nanoseconds / 1e9,
        )

        self.step_count += 1
        if self.step_count == 1 or self.step_count % max(1, int(self.record_hz)) == 0 or self.step_count == self.episode_len:
            self.get_logger().info(f"Episode buffer: {self.step_count}/{self.episode_len} steps")

        if self.episode_len > 0 and self.step_count >= self.episode_len:
            self._finish_episode()

    def _finish_episode(self) -> None:
        if self.record_timer is not None:
            self.record_timer.cancel()
            self.record_timer = None
        if self.recorder is None:
            return

        self.recorder.save_episode(parallel_encoding=True)
        episode_index = self.recorder.num_episodes - 1
        self.step_count = 0
        self.episodes_recorded += 1
        self.get_logger().info(f"Saved v3 episode {episode_index} to {self.root_dir}")

        self._validate_last_episode(episode_index)

        if self.max_episodes > 0 and self.episodes_recorded >= self.max_episodes:
            self.get_logger().info("Max episodes reached. Finalizing.")
            if not self.is_finalized:
                self.recorder.finalize()
                self.is_finalized = True
            self.control_start_requested = False
            return

        if self.stop_requested:
            return

        if self.validation_blocked:
            self.get_logger().error(
                f"Recording PAUSED: episode {episode_index} failed validation. Call "
                "/recorder/acknowledge_validation (or the UI's Acknowledge button) to continue."
            )
            return

        delay_sec = max(0.0, float(self.inter_episode_delay))
        if delay_sec == 0.0:
            self._start_episode()
            return

        self.get_logger().info(f"Waiting {delay_sec:.1f}s before next episode.")
        self.restart_timer = self.create_timer(delay_sec, self._restart_after_delay)

    def _validate_last_episode(self, episode_index: int) -> None:
        """Run validate_dataset.check_episode() against the episode that was
        just written (save_episode() has already flushed parquet + video +
        metadata to disk by the time this is called). Any ERROR-severity
        issue sets validation_blocked, which _finish_episode() checks before
        scheduling the next episode -- cleared by acknowledge_validation()."""
        if self._validation_args is None:
            return
        try:
            ds, load_issues = vd.load_dataset(self.root_dir)
            for li in load_issues:
                self.get_logger().warn(f"[validate] dataset: {li.message}")
            issues, _summary = vd.check_episode(ds, episode_index, self._validation_args)
        except Exception as e:
            self.get_logger().error(f"Episode {episode_index} validation crashed: {e}")
            self.last_episode_validation = {
                "episode": episode_index,
                "ok": False,
                "acknowledged": False,
                "issues": [{"episode": episode_index, "code": "validator-crash",
                            "severity": "ERROR", "message": str(e)}],
            }
            self.validation_blocked = True
            return

        errors = [i for i in issues if i.severity == vd.ERROR]
        ok = not errors
        self.last_episode_validation = {
            "episode": episode_index,
            "ok": ok,
            "acknowledged": False,
            "issues": [i.as_dict() for i in issues],
        }
        if ok:
            self.validation_blocked = False
            if issues:
                self.get_logger().warn(
                    f"Episode {episode_index}: {len(issues)} warning(s) -- "
                    + "; ".join(i.message for i in issues)
                )
            else:
                self.get_logger().info(f"Episode {episode_index}: validation OK.")
        else:
            self.validation_blocked = True
            self.get_logger().error(
                f"Episode {episode_index}: {len(errors)} ERROR(s) -- "
                + "; ".join(i.message for i in errors)
            )

    def _handle_acknowledge_validation(self, request, response):
        """Operator confirms a validation-failed episode has been reviewed;
        resumes the auto-restart that _finish_episode() paused for it."""
        if not self.validation_blocked:
            response.success = False
            response.message = "No blocked episode to acknowledge."
            return response

        if self.last_episode_validation is not None:
            self.last_episode_validation["acknowledged"] = True
        self.validation_blocked = False
        response.success = True
        response.message = "Acknowledged. Resuming."

        if self.control_start_requested and not self.stop_requested and self.record_timer is None:
            delay_sec = max(0.0, float(self.inter_episode_delay))
            if delay_sec == 0.0:
                self._start_episode()
            else:
                self.restart_timer = self.create_timer(delay_sec, self._restart_after_delay)
        return response

    def _restart_after_delay(self) -> None:
        if self.stop_requested:
            return
        if self.restart_timer is not None:
            self.restart_timer.cancel()
            self.restart_timer = None
        if self.control_start_requested and self._all_topics_ready():
            self._start_episode()

    def destroy_node(self) -> bool:
        if hasattr(self, '_destroyed') and self._destroyed:
            return True
        self._destroyed = True
        if self.record_timer is not None:
            self.record_timer.cancel()
            self.record_timer = None
        if self.restart_timer is not None:
            self.restart_timer.cancel()
            self.restart_timer = None
        if self.recorder is not None:
            try:
                if self.step_count > 0:
                    self.recorder.save_episode(parallel_encoding=True)
                    self._validate_last_episode(self.recorder.num_episodes - 1)
                if not self.is_finalized:
                    self.recorder.finalize()
            finally:
                self.recorder = None
        return super().destroy_node()


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Record ROS2 data using config file (service-based)")
    parser.add_argument("--config", default=_default_config_path())
    return parser


def main() -> None:
    _lock = _acquire_singleton_lock("ros2_topic_recorder")
    parser = build_arg_parser()
    args, _ = parser.parse_known_args()
    rclpy.init()
    node = Ros2V3TopicRecorder(args.config)
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()

