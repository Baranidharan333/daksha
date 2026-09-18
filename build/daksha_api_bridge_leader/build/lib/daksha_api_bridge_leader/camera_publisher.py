#!/usr/bin/env python3
"""
Connects to the Daksha API websocket (see api/lsitener.py) and republishes
each camera event it receives as a ROS2 CompressedImage, routed by the
event's camera_id to the matching topic in receive_cameras.yaml (ids must
match daksha_api_bridge_follower's send_cameras.yaml), so frames sent from
the dashboard/API can be consumed by the rest of the ROS graph.

Camera frames carry the envelope that daksha_api_bridge_follower's
camera_suscriber.py builds,

    [4-byte big-endian header length][UTF-8 JSON header][raw JPEG bytes]

and every way it can arrive is auto-detected, so only the sender's
wire_format parameter decides which is used:

  binary websocket frame   the envelope verbatim (wire_format:=binary)
  text starting "DKB1:"    base85-wrapped envelope (wire_format:=base85),
                           which is how frames survive a backend that
                           relays with send_text()
  text JSON object         control events, plus the older
                           base64-image-in-JSON camera event

A text frame holding raw envelope bytes is reported as corruption rather
than parsed: a send_text() backend decodes the body as UTF-8 first, which
destroys JPEG bytes irrecoverably.
"""

import base64
import json
import os
import struct
import threading
import time

import requests
import websocket  # from the websocket-client package
import yaml
from ament_index_python.packages import get_package_share_directory

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import CompressedImage


def _unwrap_json(value):
    """Parse JSON that may be double-encoded.

    The backend has been observed sending a JSON *string* whose contents
    are themselves JSON, which json.loads() turns into a str rather than a
    dict - the source of "'str' object has no attribute 'get'". Unwrap up
    to twice, which covers one level of double-encoding without looping
    forever on a payload that is genuinely just text.
    """
    for _ in range(2):
        if not isinstance(value, str):
            break
        try:
            value = json.loads(value)
        except (json.JSONDecodeError, ValueError):
            return value
    return value


class CameraApiPublisher(Node):

    def __init__(self):
        super().__init__("camera_publisher")

        self.declare_parameter("api_url", "https://daksha-v1.onrender.com")
        self.declare_parameter("robot_id", "s1")
        self.declare_parameter("username", "ihub")
        self.declare_parameter("password", "ihub_ihr")
        # Empty -> <install share dir>/config/receive_cameras.yaml
        self.declare_parameter("config_file", "")

        self.api_url = self.get_parameter("api_url").get_parameter_value().string_value.rstrip("/")
        self.robot_id = self.get_parameter("robot_id").get_parameter_value().string_value
        self.username = self.get_parameter("username").get_parameter_value().string_value
        self.password = self.get_parameter("password").get_parameter_value().string_value

        cameras = self._load_cameras()
        # First configured camera is the fallback used when an incoming
        # event has no camera_id (e.g. a backend that doesn't echo it back,
        # or a single-camera setup) so that case still works.
        self.default_camera_id = cameras[0]["id"]

        # image_transport plugins (rqt_image_view, etc.) parse a topic as
        # <base_topic>/<transport_name> and look for a plugin registered
        # under that exact transport name - "compressed", "raw",
        # "compressedDepth", "theora" - so each receive_topic in the config
        # must end in exactly "/compressed".
        self._pub_by_id = {}
        for cam in cameras:
            self._pub_by_id[cam["id"]] = self.create_publisher(
                CompressedImage, cam["topic"], 10
            )
            self.get_logger().info(
                f"Forwarding {self.api_url} camera_id='{cam['id']}' events "
                f"-> {cam['topic']}"
            )

        # Reuse one HTTP connection (keep-alive) instead of a new TCP/TLS
        # handshake per login request.
        self.session = requests.Session()

        self._odd_message_last_log = 0.0

        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _load_cameras(self):
        config_path = self.get_parameter("config_file").get_parameter_value().string_value
        if not config_path:
            config_path = os.path.join(
                get_package_share_directory("daksha_api_bridge_leader"), "config", "receive_cameras.yaml"
            )
        with open(config_path) as f:
            data = yaml.safe_load(f) or {}
        cameras = data.get("cameras") or []
        if not cameras:
            raise RuntimeError(f"No cameras defined in {config_path}")
        return cameras

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
            # websocket-client hands back bytes for binary frames and str
            # for text ones. Binary is the camera path (see the envelope
            # described in the module docstring); text is still JSON for
            # control events and any backend that has not been switched
            # over to binary relaying yet.
            if isinstance(message, (bytes, bytearray)):
                self._handle_binary_frame(message)
                return

            # "DKB1:" is the base85-wrapped envelope sent when the follower
            # runs wire_format:=base85, which is how frames survive a
            # backend that relays with send_text().
            if message.startswith("DKB1:"):
                self._handle_base85_frame(message)
                return

            event = _unwrap_json(message)
            if isinstance(event, dict):
                self._handle_event(event)
            else:
                self._report_odd_message(message, event)

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

    def _report_odd_message(self, message, parsed):
        """A text frame that did not parse into a dict. Rate-limited: the
        backend relays these at camera rate, so logging every one would
        flood the console and stall this thread on the writes."""
        now = time.monotonic()
        if now - self._odd_message_last_log < 5.0:
            return
        self._odd_message_last_log = now

        # Our envelope starts with a 4-byte big-endian header length, so a
        # text frame beginning with NULs is the binary payload arriving over
        # a text websocket frame. Worth calling out by name: it is silent
        # data corruption, not a parse quirk, and the fix is server-side.
        if message[:2] == "\x00\x00":
            self.get_logger().warn(
                f"[ws] received the BINARY envelope as a TEXT frame ({len(message)} chars). "
                f"The API must relay camera frames with send_bytes(), not send_text() - "
                f"JPEG bytes cannot survive UTF-8 text framing and will arrive corrupted."
            )
            return

        # repr(), not the raw string: these payloads are full of control
        # bytes that render as nothing in a terminal, which makes the log
        # look empty and hides the actual shape.
        self.get_logger().warn(
            f"[ws] ignoring text frame that is not a JSON object "
            f"(parsed as {type(parsed).__name__}, {len(message)} chars): {message[:160]!r}"
        )

    def _handle_event(self, event):
        if event.get("type") == "connected":
            return

        if event.get("action") != "camera":
            return

        robot = event.get("robot")
        if robot and robot != self.robot_id:
            return

        raw_body = event.get("body")

        # The backend wraps a non-JSON POST body in the event envelope
        # documented in api/lsitener.py, handing it over as a plain string
        # field rather than a nested object - so the base85 frame arrives
        # here rather than as a top-level "DKB1:" message. Checked before
        # _unwrap_json() so a 300 KB payload does not eat a doomed
        # json.loads() attempt on every frame.
        if isinstance(raw_body, str) and raw_body.startswith("DKB1:"):
            self._handle_base85_frame(raw_body)
            return

        # 'body' has also been seen arriving as a JSON string rather than a
        # nested object, so unwrap that too before subscripting it.
        body = _unwrap_json(raw_body) or {}
        if not isinstance(body, dict):
            self._report_odd_message(str(raw_body), body)
            return

        image_b64 = body.get("image")
        if not image_b64:
            return

        self._publish_frame(
            camera_id=body.get("camera_id") or self.default_camera_id,
            image=base64.b64decode(image_b64),
            fmt=body.get("format", "jpeg"),
            frame_id=body.get("frame_id"),
        )

    def _handle_base85_frame(self, message):
        """Undo the "DKB1:" + base85 wrapper, then parse the envelope
        underneath exactly as if it had arrived as a binary frame."""
        try:
            envelope = base64.b85decode(message[5:])
        except ValueError as e:
            self.get_logger().warn(f"[camera] undecodable base85 frame: {e}")
            return
        self._handle_binary_frame(envelope)

    def _handle_binary_frame(self, message):
        """Unpack the binary envelope sent by daksha_api_bridge_follower's
        camera_suscriber.py:

            [4-byte big-endian header length][UTF-8 JSON header][JPEG bytes]
        """
        if len(message) < 4:
            self.get_logger().warn(f"[camera] runt binary frame ({len(message)} bytes), ignoring")
            return

        header_len = struct.unpack_from(">I", message, 0)[0]
        # Guard before slicing: a mismatched/blank envelope would otherwise
        # silently yield an empty or truncated image instead of an error.
        if 4 + header_len > len(message):
            self.get_logger().warn(
                f"[camera] binary frame header length {header_len} exceeds "
                f"{len(message)} byte payload, ignoring"
            )
            return

        try:
            header = json.loads(bytes(message[4:4 + header_len]).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as e:
            self.get_logger().warn(f"[camera] undecodable binary frame header: {e}")
            return

        self._publish_frame(
            camera_id=header.get("camera_id") or self.default_camera_id,
            image=bytes(message[4 + header_len:]),
            fmt=header.get("format", "jpeg"),
            frame_id=header.get("frame_id"),
        )

    def _publish_frame(self, camera_id, image, fmt, frame_id):
        pub = self._pub_by_id.get(camera_id)
        if pub is None:
            self.get_logger().warn(f"[camera] unknown camera_id '{camera_id}', ignoring frame")
            return

        msg = CompressedImage()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = frame_id or camera_id
        msg.format = fmt
        msg.data = image

        pub.publish(msg)
        # debug, not info: logging every frame at info level forces a
        # synchronous console write on every message, which capped
        # /joint_cmd_api's rate the same way earlier - see
        # joint_cmd_api_subscriber.py.
        self.get_logger().debug(f"[camera] '{camera_id}' published {len(msg.data)} byte frame")


def main(args=None):
    rclpy.init(args=args)
    node = CameraApiPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        # rclpy may already have torn the context down on SIGINT; calling
        # shutdown() again raises instead of exiting cleanly.
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
