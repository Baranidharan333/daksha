#!/usr/bin/env python3

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import PoseStamped
from std_srvs.srv import SetBool
from message_filters import Subscriber, ApproximateTimeSynchronizer


class PoseRelay(Node):
    def __init__(self):
        super().__init__("pose_relay")

        self.enabled = True

        # Publishers
        self.right_pub = self.create_publisher(
            PoseStamped, "/right/pose", 1
        )
        self.left_pub = self.create_publisher(
            PoseStamped, "/left/pose", 1
        )

        # Message filter subscribers
        self.left_sub = Subscriber(
            self,
            PoseStamped,
            "/quest/left/pose"
        )

        self.right_sub = Subscriber(
            self,
            PoseStamped,
            "/quest/right/pose"
        )

        # Synchronize left and right poses
        self.sync = ApproximateTimeSynchronizer(
            [self.left_sub, self.right_sub],
            queue_size=10,
            slop=0.02,          # 20 ms tolerance
        )

        self.sync.registerCallback(self.pose_callback)

        # Enable/Disable service
        self.srv = self.create_service(
            SetBool,
            "/vr_enable",
            self.enable_callback,
        )

        self.get_logger().info("Pose relay started.")

    def enable_callback(self, request, response):
        self.enabled = request.data

        response.success = True

        if self.enabled:
            response.message = "VR relay enabled"
            self.get_logger().info("VR relay ENABLED")
        else:
            response.message = "VR relay disabled"
            self.get_logger().info("VR relay DISABLED")

        return response

    def pose_callback(self, left_msg, right_msg):
        if not self.enabled:
            return

        self.left_pub.publish(left_msg)
        self.right_pub.publish(right_msg)


def main(args=None):
    rclpy.init(args=args)

    node = PoseRelay()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass

    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()

#ros2 service call /vr_enable std_srvs/srv/SetBool "{data: true}"

#ros2 service call /vr_enable std_srvs/srv/SetBool "{data: false}"
