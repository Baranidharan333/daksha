#!/usr/bin/env python3

import socket
import struct

import rclpy
from rclpy.node import Node

from std_msgs.msg import Int32MultiArray


class Gen2Leader(Node):

    def __init__(self):

        super().__init__('gen2_leader')

        self.motor_pub = self.create_publisher(
            Int32MultiArray,
            '/leader_motor_values',
            10
        )

        self.button_pub = self.create_publisher(
            Int32MultiArray,
            '/leader_buttons',
            10
        )

        self.sock = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM
        )

        self.sock.bind(("0.0.0.0", 5005))
        self.sock.setblocking(False)

        self.timer = self.create_timer(
            0.001,
            self.receive_udp
        )

        self.get_logger().info(
            "Listening UDP 5005"
        )

    def receive_udp(self):

        while True:

            try:
                data, addr = self.sock.recvfrom(4096)

            except BlockingIOError:
                break

            # print("FROM:", addr)
            # print("LEN :", len(data))
            # print("RAW :", repr(data[:100]))

            self.process_packet(data)

    def process_packet(self, data):

        try:

            if len(data) != 35:
                self.get_logger().warn(
                    f"Bad packet size: {len(data)}"
                )
                return

            values = struct.unpack("<16hBBB", data)

            servo_values = list(values[:16])
            buttons = list(values[16:])

            # print("SERVOS:", servo_values)
            # print("BUTTONS:", buttons)

            motor_msg = Int32MultiArray()
            motor_data = []

            for sid in range(1, 17):
                motor_data.append(sid)
                motor_data.append(servo_values[sid - 1])

            motor_msg.data = motor_data
            self.motor_pub.publish(motor_msg)

            button_msg = Int32MultiArray()
            button_msg.data = buttons
            self.button_pub.publish(button_msg)

        except Exception as e:

            self.get_logger().error(
                f"Parse Error: {e}"
            )

def main(args=None):

    rclpy.init(args=args)

    node = Gen2Leader()

    rclpy.spin(node)

    node.destroy_node()

    rclpy.shutdown()


if __name__ == '__main__':
    main()
