#!/usr/bin/env python3
"""
collision_guard_node.py
------------------------
Per-joint collision guard combining two independent signals:

  protective (predictive, geometric) - self-collision distance query
      against the same fitted primitive geometry ik_node.py (kinematics
      package) uses for IK self-collision avoidance (robot_collision.urdf
      + the collision_pairs.json allowlist, both from
      kinematics/scripts/gen_collision_*.py). Primitives enclose the
      real mesh (see gen_collision_primitives.py), so this trips
      slightly BEFORE actual contact would occur - a protective stop.

  reactive (measured, force-based) - per-joint effort mismatch between
      the commanded trajectory (/jnt_cmt_to_ctrl, published by
      joint_command_limiter) and the actual measured effort
      (/joint_states). A large unexplained torque means something is
      physically pushing back on that joint - contact has already
      happened, so this is a reactive stop.

Publishes on /joint_collision as a sensor_msgs/JointState, reusing its
numeric fields to carry three parallel per-joint boolean arrays
(0.0/1.0) instead of physical quantities - the same trick
joint_command_limiter's debug topic and ik_node's simulation publisher
already use in this repo, so no new message package is needed:

    name      joint names
    position  collision[i]  = protective[i] or reactive[i]  (headline flag)
    velocity  protective[i] = predicted, geometry-only
    effort    reactive[i]   = measured, force-only

All three default to 0.0 (False) when nothing is wrong.

Also exposes a get_collision_status service (collision_management/srv/
GetCollisionStatus) so other nodes can poll the latest result on demand
instead of waiting on the next /joint_states callback.

Requires the generated collision artifacts (run once, from the
kinematics package, or whenever the URDF geometry changes):
    python3 kinematics/scripts/gen_collision_primitives.py
    python3 kinematics/scripts/gen_collision_pairs.py --urdf <robot_collision.urdf>
"""

from __future__ import annotations

import os
import xml.etree.ElementTree as ET

import placo
import rclpy
from ament_index_python.packages import get_package_share_directory
from rclpy.node import Node
from sensor_msgs.msg import JointState

from collision_management.srv import GetCollisionStatus


def _joint_child_links(urdf_path: str) -> dict:
    """joint name -> its child link name, for revolute/prismatic joints."""
    root = ET.parse(urdf_path).getroot()
    out = {}
    for joint in root.iter("joint"):
        if joint.get("type") not in ("revolute", "prismatic"):
            continue
        child = joint.find("child")
        if child is not None:
            out[joint.get("name")] = child.get("link")
    return out


def _strip_geom_suffix(name: str) -> str:
    """placo suffixes collision geometry names with _<index>; strip it back
    to the URDF link name (same convention as gen_collision_pairs.py)."""
    head, _, tail = name.rpartition("_")
    return head if tail.isdigit() else name


# Fixed output order: right arm, right gripper, left arm, left gripper -
# independent of whatever order /joint_states happens to publish names in.
JOINT_ORDER = (
    [f"right_joint_{i}" for i in range(1, 8)]
    + ["right_gripper_left_joint", "right_gripper_right_joint"]
    + [f"left_joint_{i}" for i in range(1, 8)]
    + ["left_gripper_left_joint", "left_gripper_right_joint"]
)
_JOINT_RANK = {name: i for i, name in enumerate(JOINT_ORDER)}


def _sort_names(names: list) -> list:
    """Sort joint names into JOINT_ORDER; unknown names keep their relative
    order and are appended after every known joint."""
    return sorted(names, key=lambda n: (_JOINT_RANK.get(n, len(JOINT_ORDER)), n))


class CollisionGuardNode(Node):

    def __init__(self):
        super().__init__("collision_guard_node")

        self.declare_parameter("joint_states_topic", "/joint_states")
        self.declare_parameter("commanded_topic", "/jnt_cmt_to_ctrl")
        self.declare_parameter("collision_topic", "/joint_collision")
        self.declare_parameter("collision_status_service", "get_collision_status")
        self.declare_parameter("collision_pairs_file", "")
        self.declare_parameter("collision_urdf_file", "")
        self.declare_parameter("protective_margin", 0.005)         # metres
        self.declare_parameter("reactive_effort_threshold", 5.0)   # N*m

        joint_states_topic = self.get_parameter(
            "joint_states_topic").get_parameter_value().string_value
        commanded_topic = self.get_parameter(
            "commanded_topic").get_parameter_value().string_value
        collision_topic = self.get_parameter(
            "collision_topic").get_parameter_value().string_value
        collision_status_service = self.get_parameter(
            "collision_status_service").get_parameter_value().string_value
        self.protective_margin = self.get_parameter(
            "protective_margin").get_parameter_value().double_value
        self.reactive_threshold = self.get_parameter(
            "reactive_effort_threshold").get_parameter_value().double_value

        pairs_path = self.get_parameter(
            "collision_pairs_file").get_parameter_value().string_value
        if not pairs_path:
            pairs_path = os.path.join(
                get_package_share_directory("kinematics"),
                "config", "collision_pairs.json")

        urdf_path = self.get_parameter(
            "collision_urdf_file").get_parameter_value().string_value
        if not urdf_path:
            urdf_path = os.path.join(
                get_package_share_directory("daksha_description_full_body"),
                "urdf", "robot_collision.urdf")

        missing = [p for p in (pairs_path, urdf_path) if not os.path.exists(p)]
        if missing:
            # Refuse rather than silently publishing "no collision" forever -
            # a guard that can't actually check is worse than no guard at
            # all. Same philosophy ik_node.py uses for the same artifacts.
            raise FileNotFoundError(
                f"collision_guard_node needs generated collision artifacts, "
                f"missing: {missing}. Generate them with "
                f"kinematics/scripts/gen_collision_primitives.py and "
                f"gen_collision_pairs.py --urdf <robot_collision.urdf>"
            )

        self.robot = placo.RobotWrapper(urdf_path)
        self.robot.load_collision_pairs(pairs_path)
        self.robot.update_kinematics()

        self._geom_link = [
            _strip_geom_suffix(g.name)
            for g in self.robot.collision_model.geometryObjects
        ]
        self._joint_child_link = _joint_child_links(urdf_path)
        self._known_joints = set(self.robot.joint_names())

        # Latest commanded effort per joint, from /jnt_cmt_to_ctrl.
        self._commanded_effort = {}

        # Latest computed status, served on demand by get_collision_status.
        self._last_status = JointState()

        self.pub = self.create_publisher(JointState, collision_topic, 10)
        self.create_subscription(JointState, commanded_topic, self._commanded_cb, 10)
        self.create_subscription(JointState, joint_states_topic, self._joint_states_cb, 10)
        self.create_service(GetCollisionStatus, collision_status_service, self._get_status_cb)

        self.get_logger().info(
            f"collision_guard_node up: {joint_states_topic} + {commanded_topic} "
            f"-> {collision_topic}  (protective_margin={self.protective_margin} m, "
            f"reactive_effort_threshold={self.reactive_threshold} N*m)"
        )

    def _commanded_cb(self, msg: JointState) -> None:
        for i, name in enumerate(msg.name):
            if i < len(msg.effort):
                self._commanded_effort[name] = msg.effort[i]

    def _get_status_cb(self, request, response):
        response.status = self._last_status
        response.in_collision = any(v >= 1.0 for v in self._last_status.position)
        return response

    def _joint_states_cb(self, msg: JointState) -> None:
        names = list(msg.name)

        # ---- protective: geometric self-collision on the live pose ----
        for i, name in enumerate(names):
            if name in self._known_joints and i < len(msg.position):
                self.robot.set_joint(name, float(msg.position[i]))
        self.robot.update_kinematics()

        close_links = set()
        for d in self.robot.distances():
            if float(d.min_distance) <= self.protective_margin:
                close_links.add(self._geom_link[d.objA])
                close_links.add(self._geom_link[d.objB])

        protective_by_name = {
            name: 1.0 if self._joint_child_link.get(name) in close_links else 0.0
            for name in names
        }

        # ---- reactive: measured-vs-commanded effort mismatch ----
        reactive_by_name = {}
        for i, name in enumerate(names):
            actual_eff = msg.effort[i] if i < len(msg.effort) else 0.0
            commanded_eff = self._commanded_effort.get(name, actual_eff)
            reactive_by_name[name] = (
                1.0 if abs(actual_eff - commanded_eff) > self.reactive_threshold else 0.0
            )

        ordered_names = _sort_names(names)
        protective = [protective_by_name[name] for name in ordered_names]
        reactive = [reactive_by_name[name] for name in ordered_names]
        collision = [max(p, r) for p, r in zip(protective, reactive)]

        out = JointState()
        out.header.stamp = self.get_clock().now().to_msg()
        out.name = ordered_names
        out.position = collision
        out.velocity = protective
        out.effort = reactive
        self.pub.publish(out)
        self._last_status = out


def main(args=None):
    rclpy.init(args=args)
    node = CollisionGuardNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
