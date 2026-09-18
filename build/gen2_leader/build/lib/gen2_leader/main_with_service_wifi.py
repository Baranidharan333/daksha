#!/usr/bin/env python3

import math

import rclpy
from rclpy.node import Node

from std_msgs.msg import Int32MultiArray
from sensor_msgs.msg import JointState

class LeaderToPositionController(Node):


    def __init__(self):

        super().__init__('leader_to_position_controller')

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
            -1, 1, 1, 1, 1, -1, 1
        ]

        self.left_direction = [
            -1, 1, -1, -1, 1, 1, 1
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

        stamp = self.get_clock().now().to_msg()

        joint_msg = JointState()
        joint_msg.header.stamp = stamp
        joint_msg.name = self.joint_names
        joint_msg.position = positions

        self.pub.publish(joint_msg)

        right_msg = JointState()
        right_msg.header.stamp = stamp
        right_msg.name = self.right_joints
        right_msg.position = positions[:8]

        self.right_pub.publish(right_msg)

        left_msg = JointState()
        left_msg.header.stamp = stamp
        left_msg.name = self.left_joints
        left_msg.position = positions[8:]

        self.left_pub.publish(left_msg)


def main(args=None):

    rclpy.init(args=args)

    node = LeaderToPositionController()

    rclpy.spin(node)

    node.destroy_node()

    rclpy.shutdown()

if __name__ == '__main__':
    main()