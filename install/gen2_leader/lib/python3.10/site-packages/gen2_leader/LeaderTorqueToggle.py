#!/usr/bin/env python3

import requests

import rclpy
from rclpy.node import Node

from std_msgs.msg import Int32MultiArray

class LeaderTorqueToggle(Node):

    def __init__(self):

        super().__init__('leader_torque_toggle')

        self.subscription = self.create_subscription(
            Int32MultiArray,
            '/leader_buttons',
            self.button_callback,
            10
        )

        self.prev_button3 = 0

        # False = torque disabled
        # True  = torque enabled
        self.torque_enabled = False

        self.base_url = "http://leader2.local"

        self.get_logger().info(
            "Leader Torque Toggle Started"
        )

        self.get_logger().info(
            f"Using host: {self.base_url}"
        )

    def button_callback(self, msg):

        if len(msg.data) < 3:
            return

        button3 = msg.data[2]

        # Rising edge detection
        if button3 == 1 and self.prev_button3 == 0:

            self.torque_enabled = not self.torque_enabled

            try:

                if self.torque_enabled:

                    response = requests.get(
                        f"{self.base_url}/enableall",
                        timeout=2
                    )

                    self.get_logger().info(
                        f"Torque ENABLED ({response.status_code})"
                    )

                else:

                    response = requests.get(
                        f"{self.base_url}/disableall",
                        timeout=2
                    )

                    self.get_logger().info(
                        f"Torque DISABLED ({response.status_code})"
                    )

            except Exception as e:

                self.get_logger().error(
                    f"HTTP Error: {e}"
                )

        self.prev_button3 = button3


def main(args=None):

    rclpy.init(args=args)

    node = LeaderTorqueToggle()

    try:
        rclpy.spin(node)

    except KeyboardInterrupt:
        pass

    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
