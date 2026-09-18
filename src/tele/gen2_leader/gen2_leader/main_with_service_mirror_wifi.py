#!/usr/bin/env python3

import math
import os

import yaml

import rclpy
from ament_index_python.packages import get_package_share_directory
from rclpy.node import Node

from std_msgs.msg import Int32MultiArray
from sensor_msgs.msg import JointState


def load_joint_limits(yaml_path):
    """name -> (lower, upper), loaded from leader_limit_limit.yaml.

    Same layout as gen2/config/arm_limit.yaml: joints grouped per
    controller, each controller a ros__parameters block mapping
    joint name -> {lower, upper}. Flattened into a single dict here."""
    with open(yaml_path) as f:
        data = yaml.safe_load(f) or {}

    limits = {}
    for controller in data.values():
        for name, bounds in controller.get("ros__parameters", {}).items():
            limits[name] = (float(bounds["lower"]), float(bounds["upper"]))
    return limits


class LeaderToPositionController(Node):


    def __init__(self):

        super().__init__('leader_to_position_controller')

        self.declare_parameter("joint_limits_path", "")
        joint_limits_path = self.get_parameter(
            "joint_limits_path").get_parameter_value().string_value
        if not joint_limits_path:
            joint_limits_path = os.path.join(
                get_package_share_directory("gen2_leader"),
                "config", "leader_limit_limit.yaml")

        self.joint_limits = load_joint_limits(joint_limits_path)

        self.CENTER = 2048
        self.RAD_PER_COUNT = 2 * math.pi / 4096

        self.right_ids = list(range(1, 8))
        self.left_ids  = list(range(9, 16))

        self.right_gripper_id = 8
        self.left_gripper_id  = 16

        self.GRIPPER_CLOSED    = {8: 2065, 16: 2039}
        self.GRIPPER_DIR       = {8: 1,   16: -1}
        self.GRIPPER_RANGE_DEG = 45.0
        # right_gripper_right_joint opens toward +0.044, but
        # left_gripper_left_joint opens toward -0.044 (opposite sign
        # convention confirmed from a working record/replay session) -
        # using one constant for both drove the left gripper into its
        # closed-side hard stop instead of opening it. Both signs flipped
        # from that baseline to reverse gripper direction on both sides.
        self.GRIPPER_OPEN_M    = {8: 0.044, 16: -0.044}

        self.GRIPPER_SPAN = round(
            self.GRIPPER_RANGE_DEG / 360.0 * 4096
        )

        self.right_direction = [
            -1, -1, -1, -1, -1, -1, -1
        ]

        self.left_direction = [
            -1, 1, 1, 1, -1, -1, 1
        ]

        self.left_joints = [
            "left_joint_1",
            "left_joint_2",
            "left_joint_3",
            "left_joint_4",
            "left_joint_5",
            "left_joint_6",
            "left_joint_7",
            "left_gripper_left_joint"
        ]

        self.right_joints = [
            "right_joint_1",
            "right_joint_2",
            "right_joint_3",
            "right_joint_4",
            "right_joint_5",
            "right_joint_6",
            "right_joint_7",
            "right_gripper_right_joint"
        ]

        self.joint_names = (
            self.right_joints +
            self.left_joints
        )

        self.pub = self.create_publisher(
            JointState,
            '/joint_cmd',
            10
        )

        self.left_pub = self.create_publisher(
            JointState,
            '/leader/left_joint_states',
            10
        )

        self.right_pub = self.create_publisher(
            JointState,
            '/leader/right_joint_states',
            10
        )

        self.mirror_signs = [
            -1,  # joint1
             1,  # joint2
            -1,  # joint3
             1,  # joint4
             1,  # joint5
             1,  # joint6
             1,  # joint7
             -1   # gripper
        ]

        self.create_subscription(
            Int32MultiArray,
            '/leader_motor_values',
            self.motor_callback,
            10
        )

        self.get_logger().info(
            "Leader motor subscriber started"
        )

    def gripper_to_meters(self, servo_id, raw):

        closed = self.GRIPPER_CLOSED[servo_id]
        d      = self.GRIPPER_DIR[servo_id]
        span   = self.GRIPPER_SPAN

        travel = (d * (raw - closed)) % 4096

        if travel <= span:
            frac = travel / span
        else:
            dead = 4096 - span
            frac = 1.0 if (
                (travel - span) < dead / 2
            ) else 0.0

        frac = max(0.0, min(1.0, frac))

        return frac * self.GRIPPER_OPEN_M[servo_id]

    def filter_positions(self, names, positions):
        # Clamps each commanded position into its leader_limit_limit.yaml
        # range before it goes out on /joint_cmd, so the leader never asks
        # for a position past the joint's limit in the first place (rather
        # than relying solely on joint_command_limiter downstream to reject
        # it and hold the last valid target).
        filtered = []
        for name, pos in zip(names, positions):
            limit = self.joint_limits.get(name)
            if limit is not None:
                pos = max(limit[0], min(limit[1], pos))
            filtered.append(pos)
        return filtered

    def mirror_positions(self, positions):
        # positions are built as:
        # right arm + right gripper, then left arm + left gripper
        right = positions[:8]
        left = positions[8:]

        mirror_left = [
            right[i] * self.mirror_signs[i]
            for i in range(8)
        ]

        mirror_right = [
            left[i] * self.mirror_signs[i]
            for i in range(8)
        ]

        return mirror_left + mirror_right

    def motor_callback(self, msg):

        motors = {}

        data = msg.data

        for i in range(0, len(data), 2):

            sid = data[i]
            pos = data[i + 1]

            motors[sid] = pos

        positions = []

        # RIGHT ARM
        for i, sid in enumerate(self.right_ids):

            raw = motors.get(sid, self.CENTER)

            zero = raw - self.CENTER

            rad = (
                self.right_direction[i]
                * zero
                * self.RAD_PER_COUNT
            )

            positions.append(rad)

        # RIGHT GRIPPER
        positions.append(
            self.gripper_to_meters(
                self.right_gripper_id,
                motors.get(
                    self.right_gripper_id,
                    self.CENTER
                )
            )
        )

        # LEFT ARM
        for i, sid in enumerate(self.left_ids):

            raw = motors.get(sid, self.CENTER)

            zero = raw - self.CENTER

            rad = (
                self.left_direction[i]
                * zero
                * self.RAD_PER_COUNT
            )

            positions.append(rad)

        # LEFT GRIPPER
        positions.append(
            self.gripper_to_meters(
                self.left_gripper_id,
                motors.get(
                    self.left_gripper_id,
                    self.CENTER
                )
            )
        )

        # self.get_logger().info(
        #     f"Right gripper: {positions[7]:.4f}, "
        #     f"Left gripper: {positions[15]:.4f}"
        # )

        stamp = self.get_clock().now().to_msg()

        joint_msg = JointState()
        joint_msg.header.stamp = stamp
        joint_msg.name = (
            self.left_joints +
            self.right_joints
        )
        joint_msg.position = self.filter_positions(
            joint_msg.name, self.mirror_positions(positions))

        self.pub.publish(joint_msg)

        right_positions = list(positions[:8])
        # right_positions[7] = -right_positions[7]

        right_msg = JointState()
        right_msg.header.stamp = stamp
        right_msg.name = self.right_joints
        right_msg.position = right_positions

        self.right_pub.publish(right_msg)

        left_positions = list(positions[8:])
        # left_positions[7] = -left_positions[7]

        left_msg = JointState()
        left_msg.header.stamp = stamp
        left_msg.name = self.left_joints
        left_msg.position = left_positions

        self.left_pub.publish(left_msg)


def main(args=None):

    rclpy.init(args=args)

    node = LeaderToPositionController()

    rclpy.spin(node)

    node.destroy_node()

    rclpy.shutdown()

if __name__ == '__main__':
    main()
