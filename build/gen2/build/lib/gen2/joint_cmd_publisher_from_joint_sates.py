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

# teach_mode_node zeroes gains for all 8 motors per arm (7 joints + gripper,
# see TEACH_KP/TEACH_KD in teach_mode_node.py), so the gripper goes
# compliant in teach mode same as the arm joints - it must be echoed back
# here too, or its JointCommandLimiter target goes stale while teach mode
# is active and the gripper snaps to that stale target the moment normal
# gains are restored.
GRIPPER_JOINTS = [
    "left_gripper_left_joint",
    "right_gripper_right_joint",
]


class JointCmdPublisher(Node):

    def __init__(self):
        super().__init__("joint_cmd_publisher_from_joint_sates_node")

        self.declare_parameter("publish_joint_cmd", False)

        self.publish_enabled = self.get_parameter(
            "publish_joint_cmd"
        ).value

        self.get_logger().info(
            f"publish_joint_cmd = {self.publish_enabled}"
        )

        self.pub = self.create_publisher(
            JointState,
            "/joint_cmd",
            10
        )

        self.create_subscription(
            JointState,
            "/joint_states",
            self.callback,
            10
        )

    def callback(self, msg):

        publish = self.get_parameter(
            "publish_joint_cmd"
        ).value

        # Log only when parameter changes
        if publish != self.publish_enabled:

            self.publish_enabled = publish

            if publish:
                self.get_logger().info(
                    "Joint command publishing ENABLED"
                )
            else:
                self.get_logger().info(
                    "Joint command publishing DISABLED"
                )

        if not publish:
            return

        pos = {}

        for name, position in zip(msg.name, msg.position):
            pos[name] = position

        cmd = JointState()

        cmd.header.stamp = self.get_clock().now().to_msg()

        cmd.name = LEFT_JOINTS + RIGHT_JOINTS + GRIPPER_JOINTS

        cmd.position = []

        for j in LEFT_JOINTS:
            cmd.position.append(pos.get(j, 0.0))

        for j in RIGHT_JOINTS:
            cmd.position.append(pos.get(j, 0.0))

        for j in GRIPPER_JOINTS:
            cmd.position.append(pos.get(j, 0.0))

        self.pub.publish(cmd)


def main(args=None):

    rclpy.init(args=args)

    node = JointCmdPublisher()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass

    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()