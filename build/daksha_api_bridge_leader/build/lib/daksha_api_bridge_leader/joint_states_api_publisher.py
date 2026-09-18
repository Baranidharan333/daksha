#!/usr/bin/env python3
"""
Connects to the Daksha API websocket (see api/lsitener.py) and republishes
any joint_states event it receives as a ROS2 JointState on the global
/joint_states_api topic, so the follower's reported joint feedback can be
consumed by the rest of the ROS graph on the leader side.
"""

import json
import threading
import time

import requests
import websocket  # from the websocket-client package

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState


class JointStatesApiPublisher(Node):

    def __init__(self):
        super().__init__("joint_states_api_publisher")

        self.declare_parameter("api_url", "https://daksha-v1.onrender.com")
        self.declare_parameter("robot_id", "s1")
        self.declare_parameter("username", "ihub")
        self.declare_parameter("password", "ihub_ihr")

        self.api_url = self.get_parameter("api_url").get_parameter_value().string_value.rstrip("/")
        self.robot_id = self.get_parameter("robot_id").get_parameter_value().string_value
        self.username = self.get_parameter("username").get_parameter_value().string_value
        self.password = self.get_parameter("password").get_parameter_value().string_value

        self.pub = self.create_publisher(JointState, "/joint_states_api", 10)

        # Reuse one HTTP connection (keep-alive) instead of a new TCP/TLS
        # handshake per login request.
        self.session = requests.Session()

        self.get_logger().info(
            f"Forwarding {self.api_url} events (robot '{self.robot_id}') -> /joint_states_api"
        )

        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self):
        while rclpy.ok():
            try:
                token = self._login()
                self._listen(token)
            except Exception as e:
                self.get_logger().warn(f"[ws] error: {e}, retrying in 3s")
            time.sleep(3)

    def _login(self):
        self.get_logger().info(f"[login] POST {self.api_url}/login as '{self.username}'")
        r = self.session.post(
            f"{self.api_url}/login",
            data={"username": self.username, "password": self.password},
            timeout=30,
        )
        r.raise_for_status()
        token = r.json()["access_token"]
        self.get_logger().info("[login] ok")
        return token

    def _listen(self, token):
        ws_url = self.api_url.replace("https://", "wss://").replace("http://", "ws://")
        ws_url = f"{ws_url}/ws?token={token}&robot_id={self.robot_id}"

        def on_open(_ws):
            self.get_logger().info(f"[ws] connected, listening for robot '{self.robot_id}'")

        def on_message(_ws, message):
            self._handle_event(json.loads(message))

        def on_error(_ws, error):
            self.get_logger().warn(f"[ws] error: {error}")

        def on_close(_ws, *_):
            self.get_logger().info("[ws] closed")

        ws = websocket.WebSocketApp(
            ws_url,
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
        )
        ws.run_forever(ping_interval=20, ping_timeout=10)

    def _handle_event(self, event):
        if event.get("type") == "connected":
            return

        if event.get("action") != "joint_states":
            return

        robot = event.get("robot")
        if robot and robot != self.robot_id:
            return

        body = event.get("body") or {}

        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.name = list(body.get("name", []))
        msg.position = [float(v) for v in body.get("position", [])]
        msg.velocity = [float(v) for v in body.get("velocity", [])]
        msg.effort = [float(v) for v in body.get("effort", [])]

        self.pub.publish(msg)
        # debug, not info: logging every message at info level forces a
        # synchronous console write on every frame, which was capping the
        # achievable rate well below what the websocket can actually deliver.
        self.get_logger().debug(f"[joint_states_api] published {len(msg.name)} joints")


def main(args=None):
    rclpy.init(args=args)
    node = JointStatesApiPublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
