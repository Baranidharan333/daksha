#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy
from sensor_msgs.msg import JointState


class JointCmdRelay(Node):

    def __init__(self):
        super().__init__('joint_cmd_relay')

        # Subscriber QoS
        sub_qos = QoSProfile(
            depth=10,
            reliability=ReliabilityPolicy.RELIABLE
        )

        # Subscribe
        self.subscription = self.create_subscription(
            JointState,
            '/joint_cmd_pri',
            self.callback,
            sub_qos
        )

        # Publisher: use default QoS
        self.publisher = self.create_publisher(
            JointState,
            '/joint_cmd',
            10
        )

        self.get_logger().info(
            'Relay: /joint_cmd_pri -> /joint_cmd'
        )

    def callback(self, msg):
        self.publisher.publish(msg)


def main(args=None):
    rclpy.init(args=args)

    node = JointCmdRelay()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()