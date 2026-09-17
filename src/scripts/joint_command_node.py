#!/usr/bin/env python3

import rclpy
from rclpy.node import Node

from sensor_msgs.msg import JointState
from std_msgs.msg import Float64MultiArray

import math
import time


class JointCommandNode(Node):

    def __init__(self):

        super().__init__("joint_command_node")

        # ==========================================
        # PUBLISHERS
        # ==========================================

        self.left_pub = self.create_publisher(
            Float64MultiArray,
            "/left_arm_controller/commands",
            10
        )

        self.right_pub = self.create_publisher(
            Float64MultiArray,
            "/right_arm_controller/commands",
            10
        )

        # ==========================================
        # SUBSCRIBER
        # ==========================================

        self.sub = self.create_subscription(
            JointState,
            "/joint_cmd",
            self.joint_callback,
            10
        )

        # ==========================================
        # JOINT ORDER
        # ==========================================

        self.left_joints = [
            "left_shoulder_pitch",
            "left_shoulder_roll",
            "left_elbow_yaw",
            "left_elbow_pitch",
            "left_wrist_roll",
            "left_wrist_yaw",
            "left_wrist_pitch",
            "left_gripper"
        ]

        self.right_joints = [
            "right_shoulder_pitch",
            "right_shoulder_roll",
            "right_elbow_yaw",
            "right_elbow_pitch",
            "right_wrist_roll",
            "right_wrist_yaw",
            "right_wrist_pitch",
            "right_gripper"
        ]

        # ==========================================
        # FILTER
        # ==========================================

        self.alpha = 0.6

        self.left_filtered = [0.0] * 8
        self.right_filtered = [0.0] * 8

        # ==========================================
        # VELOCITY LIMIT
        # ==========================================

        self.max_velocity = 4.0

        # ==========================================
        # ACCELERATION LIMIT
        # ==========================================

        self.max_acceleration = 8.0

        self.prev_left_velocity = [0.0] * 8
        self.prev_right_velocity = [0.0] * 8

        self.prev_time = time.time()

        self.get_logger().info("Joint Command Node Started")

    # ==========================================
    # ALPHA FILTER
    # ==========================================

    def low_pass_filter(self, prev, current):

        return (
            self.alpha * current +
            (1.0 - self.alpha) * prev
        )

    # ==========================================
    # VELOCITY LIMITER
    # ==========================================

    def limit_velocity(self, target, current, dt):

        diff = target - current

        max_step = self.max_velocity * dt

        diff = max(
            min(diff, max_step),
            -max_step
        )

        return current + diff

    # ==========================================
    # ACCELERATION LIMITER
    # ==========================================

    def limit_acceleration(
        self,
        velocity,
        prev_velocity,
        dt
    ):

        accel = (velocity - prev_velocity) / dt

        accel = max(
            min(accel, self.max_acceleration),
            -self.max_acceleration
        )

        return prev_velocity + accel * dt

    # ==========================================
    # CALLBACK
    # ==========================================

    def joint_callback(self, msg):

        now = time.time()

        dt = now - self.prev_time

        if dt <= 0.0:
            dt = 0.01

        self.prev_time = now

        # ==========================================
        # CREATE JOINT MAP
        # ==========================================

        joint_map = dict(
            zip(msg.name, msg.position)
        )

        # ==========================================
        # LEFT ARM
        # ==========================================

        left_cmd = []

        for i, joint in enumerate(self.left_joints):

            target = joint_map.get(joint, 0.0)

            # Alpha filter
            filtered = self.low_pass_filter(
                self.left_filtered[i],
                target
            )

            # Velocity limit
            velocity_limited = self.limit_velocity(
                filtered,
                self.left_filtered[i],
                dt
            )

            # Acceleration limit
            accel_limited = self.limit_acceleration(
                velocity_limited,
                self.prev_left_velocity[i],
                dt
            )

            self.prev_left_velocity[i] = accel_limited
            self.left_filtered[i] = accel_limited

            left_cmd.append(accel_limited)

        # ==========================================
        # RIGHT ARM
        # ==========================================

        right_cmd = []

        for i, joint in enumerate(self.right_joints):

            target = joint_map.get(joint, 0.0)

            # Alpha filter
            filtered = self.low_pass_filter(
                self.right_filtered[i],
                target
            )

            # Velocity limit
            velocity_limited = self.limit_velocity(
                filtered,
                self.right_filtered[i],
                dt
            )

            # Acceleration limit
            accel_limited = self.limit_acceleration(
                velocity_limited,
                self.prev_right_velocity[i],
                dt
            )

            self.prev_right_velocity[i] = accel_limited
            self.right_filtered[i] = accel_limited

            right_cmd.append(accel_limited)

        # ==========================================
        # PUBLISH LEFT
        # ==========================================

        left_msg = Float64MultiArray()
        left_msg.data = left_cmd

        self.left_pub.publish(left_msg)

        # ==========================================
        # PUBLISH RIGHT
        # ==========================================

        right_msg = Float64MultiArray()
        right_msg.data = right_cmd

        self.right_pub.publish(right_msg)


# ==========================================
# MAIN
# ==========================================

def main(args=None):

    rclpy.init(args=args)

    node = JointCommandNode()

    try:

        rclpy.spin(node)

    except KeyboardInterrupt:

        pass

    node.destroy_node()

    rclpy.shutdown()


if __name__ == "__main__":
    main()
