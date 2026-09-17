#!/usr/bin/env python3
"""
Subscribes to one or more camera CompressedImage topics (listed in
send_cameras.yaml) and forwards each frame to the Daksha API as a camera
event tagged with its camera_id, so the live feed(s) show up on the
dashboard/websocket alongside joint_states. camera_id must match the
corresponding entry in daksha_api_bridge_leader's receive_cameras.yaml.

Frames are POSTed as an octet-stream carrying a self-describing envelope,

    [4-byte big-endian header length][UTF-8 JSON header][raw JPEG bytes]

which camera_publisher.py in daksha_api_bridge_leader unpacks with the
same layout - no base64 inside a JSON image field, and no per-frame JSON
parse of the image itself.

The 'wire_format' parameter picks how that envelope crosses the API:

  base85 (default)  The envelope is base85'd and prefixed with "DKB1:".
                    Costs +25% in size, but survives a backend that
                    relays websocket frames with send_text(): such a
                    backend decodes the body as UTF-8 first, which
                    silently destroys raw JPEG bytes (invalid sequences
                    collapse to U+FFFD and cannot be recovered). Base85
                    is pure ASCII, so that decode/encode round trip is
                    lossless.

  binary            The envelope is POSTed and relayed verbatim. This is
                    25% smaller and the right setting, but requires the
                    API to read the raw request body without decoding it
                    and to relay with send_bytes() rather than
                    send_text().

The receiver auto-detects all of it, so only the sender needs switching.
"""

import base64
import functools
import json
import os
import struct
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import requests
import yaml
from ament_index_python.packages import get_package_share_directory
from requests.adapters import HTTPAdapter
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import CompressedImage


class _CameraChannel:
    """Per-camera pacing state and send capacity: each camera gets its own
    'latest pending frame' slot, send cadence, executor, and inflight cap,
    so one busy/slow camera can never steal send capacity from another -
    fully isolated instead of competing for a shared pool."""

    def __init__(self, camera_id, topic, max_inflight):
        self.id = camera_id
        self.topic = topic
        self.lock = threading.Lock()
        self.new_data = threading.Event()
        self.pending_payload = None
        self.last_sent = 0.0
        self.executor = ThreadPoolExecutor(max_workers=max_inflight, thread_name_prefix=f"cam-{camera_id}")
        self.inflight = threading.Semaphore(max_inflight)

        # Counters for the periodic stats line. Kept as plain accumulators
        # updated under one short-lived lock rather than logged per frame:
        # an info-level log in the ROS callback would fire 30x/s/camera and
        # serialize on the console write, which would itself throttle the
        # thing we are trying to measure (this is what capped /joint_cmd_api
        # earlier - see joint_cmd_api_publish.py).
        self.stats_lock = threading.Lock()
        self.recv_count = 0          # frames delivered by ROS
        self.recv_bytes = 0          # raw JPEG bytes in
        self.encode_time = 0.0       # seconds spent framing the envelope
        self.sent_count = 0          # POSTs that returned a response
        self.sent_bytes = 0          # envelope bytes out (header + JPEG)
        self.latency_sum = 0.0       # seconds of POST round-trip
        self.fail_count = 0
        self.fail_kinds = {}         # exception/status -> count
        self.drop_inflight = 0       # dropped because all connections busy
        self.empty_count = 0         # zero-byte frames from a broken encoder
        self.transcode_time = 0.0    # seconds spent re-compressing
        self.transcode_bytes = 0     # JPEG bytes after re-compression
        self.transcode_count = 0     # frames re-compressed


class CameraApiSubscriber(Node):

    def __init__(self):
        super().__init__("camera_subscriber")

        self.declare_parameter("api_url", "https://daksha-v1.onrender.com")
        self.declare_parameter("robot_id", "s1")
        self.declare_parameter("username", "ihub")
        self.declare_parameter("password", "ihub_ihr")
        # Images are far heavier than a joint_cmd POST, so default to a
        # much lower send rate and concurrency than joint_cmd_api_publisher
        # to avoid saturating bandwidth with JPEG uploads.
        # max_inflight is per camera - each camera in send_cameras.yaml
        # gets its own executor/semaphore sized to this value, so cameras
        # never compete with each other for send capacity.
        self.declare_parameter("rate_limit_hz", 50.0)
        self.declare_parameter("max_inflight", 4)
        # Seconds between per-camera throughput reports. 0 disables them.
        self.declare_parameter("stats_period_sec", 1.0)
        # "base85" survives a send_text() backend; "binary" is 25% smaller
        # but needs the API to relay bytes. See the module docstring.
        self.declare_parameter("wire_format", "base85")
        # Re-compress each frame before upload. 0 disables it entirely and
        # the camera's own JPEG is forwarded untouched (the default - no
        # decode, no quality loss, no CPU). Set jpeg_quality to ~40 and/or
        # max_width to ~640 when the camera driver cannot be turned down
        # and the uplink is the limit; this trades Jetson CPU for bytes.
        self.declare_parameter("jpeg_quality", 0)
        self.declare_parameter("max_width", 0)
        # Empty -> <install share dir>/config/send_cameras.yaml
        self.declare_parameter("config_file", "")
        # Empty -> handle every camera in the config in this one process.
        # Set to an id from send_cameras.yaml to handle only that camera,
        # which is how camera_bridge.launch.py runs one process per camera
        # (see _load_cameras).
        self.declare_parameter("camera_id", "")

        self.api_url = self.get_parameter("api_url").get_parameter_value().string_value.rstrip("/")
        self.robot_id = self.get_parameter("robot_id").get_parameter_value().string_value
        self.username = self.get_parameter("username").get_parameter_value().string_value
        self.password = self.get_parameter("password").get_parameter_value().string_value
        self.max_inflight = self.get_parameter("max_inflight").get_parameter_value().integer_value

        rate_limit_hz = self.get_parameter("rate_limit_hz").get_parameter_value().double_value
        self.min_interval = 1.0 / rate_limit_hz if rate_limit_hz > 0.0 else 0.0

        cameras = self._load_cameras()

        # Reuse HTTP connections (keep-alive) instead of a new TCP/TLS
        # handshake per request. Pool sized for every camera's own
        # max_inflight sending concurrently at once.
        self.session = requests.Session()
        pool_size = self.max_inflight * len(cameras)
        adapter = HTTPAdapter(pool_connections=pool_size, pool_maxsize=pool_size)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

        self.token = None
        self._login_lock = threading.Lock()
        self._login()

        self.stats_period = self.get_parameter("stats_period_sec").get_parameter_value().double_value
        self._channels = []

        self.wire_format = self.get_parameter("wire_format").get_parameter_value().string_value.lower()
        if self.wire_format not in ("base85", "binary"):
            raise RuntimeError(
                f"wire_format must be 'base85' or 'binary', got '{self.wire_format}'"
            )
        if self.wire_format == "binary":
            self.get_logger().info(
                "[wire] binary - requires an API that relays camera frames with "
                "send_bytes(); frames arrive corrupted if it uses send_text()"
            )
        else:
            self.get_logger().info(
                "[wire] base85 (+25% size) - lossless through a send_text() API. "
                "Switch to wire_format:=binary once the API relays raw bytes."
            )

        self.jpeg_quality = self.get_parameter("jpeg_quality").get_parameter_value().integer_value
        self.max_width = self.get_parameter("max_width").get_parameter_value().integer_value
        self.transcode = self.jpeg_quality > 0 or self.max_width > 0
        if self.transcode:
            if not 0 < self.jpeg_quality <= 100:
                # max_width alone still needs a quality to re-encode at.
                self.jpeg_quality = 80
            # Imported only when actually transcoding, so the node keeps
            # working on a machine without OpenCV in the default
            # pass-through mode.
            try:
                import cv2
                import numpy
            except ImportError as e:
                raise RuntimeError(
                    f"jpeg_quality/max_width need OpenCV and numpy, which are not "
                    f"importable ({e}). Install them, or leave both at 0 to forward "
                    f"the camera's own JPEG untouched."
                )
            self._cv2, self._np = cv2, numpy
            self.get_logger().info(
                f"[transcode] re-encoding at quality={self.jpeg_quality}"
                + (f", max_width={self.max_width}" if self.max_width else "")
                + " - costs CPU per sent frame, cuts bytes on the wire"
            )

        for cam in cameras:
            # Each camera gets its own dispatcher thread (paces sends at
            # rate_limit_hz), executor, and inflight cap - a slow upload on
            # one camera can never block the ROS callback or steal send
            # capacity from another camera. Only the latest frame per
            # camera is kept between dispatches; if a camera's sender falls
            # behind, stale in-between frames are dropped instead of
            # queuing up and adding latency.
            channel = _CameraChannel(cam["id"], cam["topic"], self.max_inflight)
            self._channels.append(channel)
            # Queue depth 1: only the latest frame matters, no point
            # buffering old ones.
            self.create_subscription(
                CompressedImage, channel.topic,
                functools.partial(self._on_camera, channel), 1,
            )
            threading.Thread(target=self._sender_loop, args=(channel,), daemon=True).start()
            self.get_logger().info(
                f"Forwarding {channel.topic} -> {self.api_url}/daksha/{self.robot_id}/camera "
                f"(camera_id='{channel.id}')"
            )

        # Reporting runs on its own thread rather than piggybacking on the
        # POST path, so a stalled/timing-out upload can't also stall the
        # stats - the case where the numbers matter most.
        if self.stats_period > 0.0:
            threading.Thread(target=self._stats_loop, daemon=True).start()

    def _load_cameras(self):
        config_path = self.get_parameter("config_file").get_parameter_value().string_value
        if not config_path:
            config_path = os.path.join(
                get_package_share_directory("daksha_api_bridge_follower"), "config", "send_cameras.yaml"
            )
        with open(config_path) as f:
            data = yaml.safe_load(f) or {}
        cameras = data.get("cameras") or []
        if not cameras:
            raise RuntimeError(f"No cameras defined in {config_path}")

        only = self.get_parameter("camera_id").get_parameter_value().string_value
        if only:
            cameras = [c for c in cameras if c["id"] == only]
            if not cameras:
                # Fail loudly rather than idling forever with no
                # subscriptions - a typo'd or commented-out id would
                # otherwise look like a camera that is simply silent.
                raise RuntimeError(
                    f"camera_id '{only}' not found in {config_path}. Available: "
                    f"{[c['id'] for c in (data.get('cameras') or [])]}"
                )
        return cameras

    def _login(self):
        with self._login_lock:
            self.get_logger().info(f"[login] POST {self.api_url}/login as '{self.username}'")
            r = self.session.post(
                f"{self.api_url}/login",
                data={"username": self.username, "password": self.password},
                timeout=30,
            )
            r.raise_for_status()
            self.token = r.json()["access_token"]
            self.get_logger().info("[login] ok")

    def _on_camera(self, channel, msg):
        # Deliberately does no encoding at all: it stashes the frame and
        # returns. Everything expensive - transcode, envelope framing,
        # base85 - happens on the sender thread, for two reasons. It keeps
        # the ROS executor thread free, and it means CPU is only spent on
        # frames that actually get sent. At ~10 Hz in and ~3 Hz out most
        # frames are superseded before dispatch, so encoding here would
        # throw away two thirds of that work.
        raw = bytes(msg.data)

        # A broken encoder upstream (e.g. realsense2_camera's
        # CompressedPublisher failing to allocate) publishes zero-byte
        # CompressedImage messages at full rate. Uploading those burns a
        # request per frame to deliver nothing, and the receiver would
        # republish empty frames that look like a live feed. Drop them
        # here and surface the count in the stats line instead.
        if not raw:
            with channel.stats_lock:
                channel.empty_count += 1
            return

        frame = (raw, msg.format, msg.header.frame_id,
                 msg.header.stamp.sec, msg.header.stamp.nanosec)

        with channel.stats_lock:
            channel.recv_count += 1
            channel.recv_bytes += len(raw)

        with channel.lock:
            channel.pending_payload = frame
        channel.new_data.set()

    def _transcode(self, raw):
        """Decode, optionally downscale, re-encode smaller. Returns the
        original bytes unchanged if the frame cannot be decoded, so a
        non-JPEG or corrupt frame degrades to pass-through rather than
        being dropped."""
        cv2, np = self._cv2, self._np
        img = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            return raw

        if self.max_width and img.shape[1] > self.max_width:
            # INTER_AREA is the right filter for downscaling - it averages
            # over the source pixels instead of point-sampling, so the
            # result also compresses better than a nearest/linear shrink.
            scale = self.max_width / img.shape[1]
            img = cv2.resize(
                img, (self.max_width, max(1, int(round(img.shape[0] * scale)))),
                interpolation=cv2.INTER_AREA,
            )

        ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, self.jpeg_quality])
        return buf.tobytes() if ok else raw

    def _build_body(self, channel, frame):
        """Frame -> wire bytes. Runs on the sender thread, not the ROS
        callback, so only frames that survive to dispatch cost CPU."""
        raw, fmt, frame_id, sec, nanosec = frame

        if self.transcode:
            started = time.monotonic()
            raw = self._transcode(raw)
            with channel.stats_lock:
                channel.transcode_time += time.monotonic() - started
                channel.transcode_bytes += len(raw)
                channel.transcode_count += 1

        started = time.monotonic()
        header = json.dumps({
            "camera_id": channel.id,
            "format": fmt,
            "stamp": {"sec": sec, "nanosec": nanosec},
            "frame_id": frame_id,
        }).encode("utf-8")
        body = b"".join((struct.pack(">I", len(header)), header, raw))
        if self.wire_format == "base85":
            # "DKB1:" marks the frame for the receiver: JSON events start
            # with '{', and the base85 alphabet never does, so the two are
            # unambiguous without any content sniffing.
            body = b"DKB1:" + base64.b85encode(body)

        with channel.stats_lock:
            channel.encode_time += time.monotonic() - started
        return body

    def _sender_loop(self, channel):
        while rclpy.ok():
            channel.new_data.wait()

            with channel.lock:
                frame = channel.pending_payload
                channel.pending_payload = None
                channel.new_data.clear()

            if frame is None:
                continue

            # This camera's max_inflight connections are already busy
            # sending older frames - drop this one instead of queuing
            # (queuing would just mean uploading increasingly stale frames
            # with growing delay). A newer frame will be along by the next
            # dispatch.
            if not channel.inflight.acquire(blocking=False):
                with channel.stats_lock:
                    channel.drop_inflight += 1
                continue

            if self.min_interval:
                wait = self.min_interval - (time.monotonic() - channel.last_sent)
                if wait > 0:
                    time.sleep(wait)
            channel.last_sent = time.monotonic()

            # Encoded only now, after the drop and pacing decisions above:
            # a frame that loses its slot costs no CPU at all.
            body = self._build_body(channel, frame)

            future = channel.executor.submit(self._post, channel, body, True)
            future.add_done_callback(lambda _f: channel.inflight.release())

    def _post(self, channel, body, retry_on_auth_error):
        start = time.monotonic()
        try:
            resp = self.session.post(
                f"{self.api_url}/daksha/{self.robot_id}/camera",
                data=body,
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Content-Type": "application/octet-stream",
                    # Duplicated from the envelope header so the API can
                    # route without parsing the body at all.
                    "X-Camera-Id": channel.id,
                },
                timeout=5,
            )
        except requests.RequestException as e:
            # Record the exception type, not the message: ReadTimeout vs
            # ConnectTimeout vs ConnectionError point at different layers
            # (server too slow / can't reach it / link dropped).
            self._record_post(channel, time.monotonic() - start, len(body),
                              failure=type(e).__name__)
            self.get_logger().warn(f"[post] camera '{channel.id}' failed: {e}")
            return

        failure = None if resp.status_code == 200 else f"HTTP {resp.status_code}"
        self._record_post(channel, time.monotonic() - start, len(body), failure=failure)

        if resp.status_code == 401 and retry_on_auth_error:
            self.get_logger().info("[post] token expired, re-logging in")
            self._login()
            self._post(channel, body, retry_on_auth_error=False)
            return

        if resp.status_code != 200:
            self.get_logger().warn(
                f"[post] camera '{channel.id}' -> {resp.status_code}: {resp.text}"
            )

    def _record_post(self, channel, elapsed, sent_bytes, failure=None):
        with channel.stats_lock:
            channel.sent_count += 1
            channel.sent_bytes += sent_bytes
            channel.latency_sum += elapsed
            if failure:
                channel.fail_count += 1
                channel.fail_kinds[failure] = channel.fail_kinds.get(failure, 0) + 1

    def _stats_loop(self):
        last = time.monotonic()
        while rclpy.ok():
            time.sleep(self.stats_period)
            now = time.monotonic()
            span, last = now - last, now
            if span <= 0.0:
                continue
            for channel in self._channels:
                self._log_channel_stats(channel, span)

    def _log_channel_stats(self, channel, span):
        with channel.stats_lock:
            recv, recv_bytes = channel.recv_count, channel.recv_bytes
            encode_time = channel.encode_time
            sent, sent_bytes = channel.sent_count, channel.sent_bytes
            latency_sum, fails = channel.latency_sum, channel.fail_count
            fail_kinds = dict(channel.fail_kinds)
            drops = channel.drop_inflight
            empty = channel.empty_count
            tc_time, tc_bytes, tc_count = (
                channel.transcode_time, channel.transcode_bytes, channel.transcode_count)
            channel.empty_count = 0
            channel.recv_count = channel.recv_bytes = 0
            channel.encode_time = 0.0
            channel.sent_count = channel.sent_bytes = 0
            channel.latency_sum = 0.0
            channel.fail_count = 0
            channel.fail_kinds = {}
            channel.drop_inflight = 0
            channel.transcode_time = 0.0
            channel.transcode_bytes = channel.transcode_count = 0

        if empty and not recv:
            # Distinct from silence: the topic is alive at full rate, the
            # encoder upstream is what's broken.
            self.get_logger().warn(
                f"[stats] {channel.id}: {empty/span:.1f} Hz of ZERO-BYTE frames on "
                f"{channel.topic} - upstream encoder is failing, nothing to send"
            )
            return

        if not recv and not sent:
            self.get_logger().warn(f"[stats] {channel.id}: no frames on {channel.topic}")
            return

        parts = [f"[stats] {channel.id}:"]
        if recv:
            # KB/frame is the number that decides whether to attack the
            # transport or the camera settings.
            parts.append(
                f"in {recv/span:.1f} Hz x {recv_bytes/recv/1024:.0f} KB "
                f"({recv_bytes/span/1e6:.2f} MB/s),"
            )
        if tc_count:
            # The whole point of transcoding: how many KB it actually saved
            # and what that cost in CPU per frame.
            parts.append(
                f"transcode {recv_bytes/recv/1024:.0f}->{tc_bytes/tc_count/1024:.0f} KB "
                f"in {tc_time/tc_count*1000:.0f} ms/frame,"
            )
        if sent:
            # Divided by sent, not recv: encoding happens on the sender
            # thread now, so only dispatched frames are ever encoded.
            parts.append(f"encode {encode_time/sent*1000:.1f} ms/frame,")
            avg_latency = latency_sum / sent
            # Sustained rate can't exceed max_inflight/latency no matter how
            # many frames the camera offers - if 'out' sits at this ceiling,
            # concurrency is the limit; if it sits below, the camera or the
            # pacer is.
            ceiling = self.max_inflight / avg_latency if avg_latency > 0 else float("inf")
            parts.append(
                f"out {sent/span:.1f} Hz ({sent_bytes/span/1e6:.2f} MB/s), "
                f"avg {avg_latency*1000:.0f} ms, ceiling ~{ceiling:.1f} Hz"
                f" @ inflight={self.max_inflight},"
            )
        else:
            parts.append("out 0 Hz,")
        if fails:
            parts.append(f"{fails} failed ({', '.join(f'{k} x{v}' for k, v in fail_kinds.items())}),")
        if drops:
            parts.append(f"{drops/span:.1f} Hz dropped (all connections busy),")
        if empty:
            parts.append(f"{empty/span:.1f} Hz zero-byte (upstream encoder failing),")

        self.get_logger().info(" ".join(parts).rstrip(","))


def main(args=None):
    rclpy.init(args=args)
    node = CameraApiSubscriber()
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
