#!/usr/bin/env python3

import cv2

import rclpy
from rclpy.node import Node

from sensor_msgs.msg import CompressedImage


class CameraPublisher(Node):

    def __init__(self):
        super().__init__("compressed_camera_publisher")

        self.publisher = self.create_publisher(
            CompressedImage,
            "/camera/image_raw/compressed",
            10,
        )

        self.cap = cv2.VideoCapture(0)

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.cap.set(cv2.CAP_PROP_FPS, 30)

        # JPEG quality (0-100)
        self.jpeg_quality = 80

        self.timer = self.create_timer(1.0 / 30.0, self.publish_frame)

        self.get_logger().info("Compressed Camera Publisher Started")

    def publish_frame(self):
        ret, frame = self.cap.read()

        if not ret:
            self.get_logger().warning("Failed to grab frame")
            return

        success, encoded = cv2.imencode(
            ".jpg",
            frame,
            [int(cv2.IMWRITE_JPEG_QUALITY), self.jpeg_quality],
        )

        if not success:
            self.get_logger().warning("JPEG encoding failed")
            return

        msg = CompressedImage()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "camera"
        msg.format = "jpeg"
        msg.data = encoded.tobytes()

        self.publisher.publish(msg)

    def destroy_node(self):
        self.cap.release()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)

    node = CameraPublisher()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass

    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
