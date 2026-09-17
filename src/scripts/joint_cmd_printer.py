#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState


LEFT_JOINTS = [
    "left_joint_1",
    "left_joint_2",
    "left_joint_3",
    "left_joint_4",
    "left_joint_5",
    "left_joint_6",
    "left_joint_7",
]

RIGHT_JOINTS = [
    "right_joint_1",
    "right_joint_2",
    "right_joint_3",
    "right_joint_4",
    "right_joint_5",
    "right_joint_6",
    "right_joint_7",
]


class JointCmdPrinter(Node):

    def __init__(self):
        super().__init__("joint_cmd_printer")

        self.create_subscription(
            JointState,
            "/joint_states",
            self.callback,
            10
        )

    def callback(self, msg):

        pos = {}

        for name, p in zip(msg.name, msg.position):
            pos[name] = p

        print("\n" + "=" * 90)
        print("Copy this command:\n")

        print('ros2 topic pub --once /joint_cmd sensor_msgs/msg/JointState "')

        print("name:")

        for j in LEFT_JOINTS:
            print(f"- {j}")

        for j in RIGHT_JOINTS:
            print(f"- {j}")

        print("\nposition:")

        for j in LEFT_JOINTS:
            print(f"- {pos.get(j, 0.0)}")

        for j in RIGHT_JOINTS:
            print(f"- {pos.get(j, 0.0)}")

        print('"')

        print("=" * 90)

        rclpy.shutdown()


def main(args=None):
    rclpy.init(args=args)
    node = JointCmdPrinter()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
