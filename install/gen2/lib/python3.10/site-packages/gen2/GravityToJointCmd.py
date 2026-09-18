#!/usr/bin/env python3

import rclpy
from rclpy.node import Node

from sensor_msgs.msg import JointState


# NOTE: direction sign, per-joint ff_scale and the max_ff_torque safety clamp
# are all applied upstream now, in dynamics/gravity_torque_node.cpp (ported
# from gen3's hw_interface Dynamics integration). /gravity_torque already
# carries hardware-ready torques -- this node's only job is to pick which
# joints are allowed to receive that feedforward.
def build_joint_cmd_message(gravity_msg, enabled_joints, stamp):
    cmd = JointState()
    cmd.header.stamp = stamp

    cmd.name = []
    cmd.effort = []

    for joint_name, enabled in enabled_joints.items():
        if not enabled:
            continue

        if joint_name not in gravity_msg.name:
            continue

        idx = gravity_msg.name.index(joint_name)

        cmd.name.append(joint_name)
        cmd.effort.append(float(gravity_msg.effort[idx]))

    return cmd


class GravityToJointCmd(Node):

    def __init__(self):
        super().__init__("gravity_to_joint_cmd")

        # Enable any subset of joints by changing this dictionary.
        self.enabled_joints = {
            "left_joint_1": True,
            "left_joint_2": True,
            "left_joint_3": True,
            "left_joint_4": True,
            "left_joint_5": True,
            "left_joint_6": True,
            "left_joint_7": True,
            "right_joint_1": True,
            "right_joint_2": True,
            "right_joint_3": True,
            "right_joint_4": True,
            "right_joint_5": True,
            "right_joint_6": True,
            "right_joint_7": True,
        }

        self.sub = self.create_subscription(
            JointState,
            "/gravity_torque",
            self.gravity_callback,
            10
        )

        self.pub = self.create_publisher(
            JointState,
            "/gravity_torque_temp",
            10
        )

        enabled_names = [name for name, enabled in self.enabled_joints.items() if enabled]
        self.get_logger().info(
            f"Publishing gravity torque for {enabled_names}"
        )

    def gravity_callback(self, msg):

        cmd = build_joint_cmd_message(
            msg,
            self.enabled_joints,
            self.get_clock().now().to_msg(),
        )

        if len(cmd.name) > 0:
            self.pub.publish(cmd)


def main(args=None):

    rclpy.init(args=args)

    node = GravityToJointCmd()

    rclpy.spin(node)

    node.destroy_node()

    rclpy.shutdown()


if __name__ == "__main__":
    main()
