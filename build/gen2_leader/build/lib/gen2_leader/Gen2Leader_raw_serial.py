#!/usr/bin/env python3

import argparse
import serial
import struct

import rclpy
from rclpy.node import Node

from std_msgs.msg import Int32MultiArray

class Gen2Leader(Node):

    def __init__(self, port, baudrate):

        super().__init__("gen2_leader")

        self.motor_pub = self.create_publisher(
            Int32MultiArray,
            "/leader_motor_values",
            10
        )

        self.button_pub = self.create_publisher(
            Int32MultiArray,
            "/leader_buttons",
            10
        )

        self.ser = serial.Serial(
            port=port,
            baudrate=baudrate,
            timeout=0.01
        )

        self.packet_count = 0

        self.timer = self.create_timer(
            0.001,
            self.read_serial
        )

        self.hz_timer = self.create_timer(
            1.0,
            self.print_rate
        )

        self.get_logger().info(
            f"Listening on {port} @ {baudrate}"
        )

    def print_rate(self):

        self.get_logger().info(
            f"RX Rate: {self.packet_count} Hz"
        )

        self.packet_count = 0

    def read_serial(self):

        try:

            data = self.ser.read(35)

            if not data:
                return

            print("LEN =", len(data))
            print("HEX =", data.hex())

            if len(data) != 35:
                self.get_logger().warn(
                    f"Short serial packet: {len(data)} bytes"
                )
                return

            values = struct.unpack(
                "<16hBBB",
                data
            )

            servo_values = list(values[:16])
            button_values = list(values[16:])

            print("SERVOS:", servo_values)
            print("BUTTONS:", button_values)

            # Interleave as [sid, value, sid, value, ...] to match the UDP
            # transport (Gen2Leader_raw.py) -- main_with_service_wifi.py's
            # parser expects this id-tagged format from either transport.
            # Publishing raw servo_values here (as before) made every value
            # get misread as alternating (sid, pos) pairs downstream.
            motor_data = []
            for sid in range(1, 17):
                motor_data.append(sid)
                motor_data.append(servo_values[sid - 1])

            motor_msg = Int32MultiArray()
            motor_msg.data = motor_data
            self.motor_pub.publish(motor_msg)

            button_msg = Int32MultiArray()
            button_msg.data = button_values
            self.button_pub.publish(button_msg)

            self.packet_count += 1

        except Exception as e:

            self.get_logger().error(
                f"Serial Error: {e}"
            )

def main(args=None):

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--port",
        default="/dev/ttyUSB0",
        help="Serial device"
    )

    parser.add_argument(
        "--baudrate",
        type=int,
        default=115200,
        help="Serial baudrate"
    )

    parsed_args, ros_args = parser.parse_known_args()

    rclpy.init(args=ros_args)

    node = Gen2Leader(
        parsed_args.port,
        parsed_args.baudrate
    )

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
