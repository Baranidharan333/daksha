#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32


class BatteryInfo(Node):

    def __init__(self):
        super().__init__("battery_info")
        self.publisher_ = self.create_publisher(Float32, "battery_info", 10)
        self.timer = self.create_timer(1.0, self._publish_battery_info)

    def _publish_battery_info(self):
        msg = Float32()
        msg.data = 50.0
        self.publisher_.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = BatteryInfo()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
