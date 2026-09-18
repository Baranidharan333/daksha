#!/usr/bin/env python3
"""
Subscribes to the global /joint_cmd topic and forwards each message to
the Daksha API as a joint_cmd event, so the commanded joint targets show
up on the live dashboard/websocket alongside joint_states.
"""

import threading
import time
from concurrent.futures import ThreadPoolExecutor

import requests
from requests.adapters import HTTPAdapter
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState


class JointCmdApiSubscriber(Node):

    def __init__(self):
        super().__init__("joint_cmd_api_subscriber")

        self.declare_parameter("api_url", "https://daksha-v1.onrender.com")
        self.declare_parameter("robot_id", "s1")
        self.declare_parameter("username", "ihub")
        self.declare_parameter("password", "ihub_ihr")
        self.declare_parameter("rate_limit_hz", 100.0)
        # Requests in flight at once. A single sequential POST is capped at
        # 1/RTT (e.g. ~3 Hz if the server takes 300ms); overlapping several
        # in-flight requests lets the achieved rate exceed that, up to
        # max_inflight/RTT. Tune this based on the measured RTT logged
        # below rather than guessing.
        self.declare_parameter("max_inflight", 16)

        self.api_url = self.get_parameter("api_url").get_parameter_value().string_value.rstrip("/")
        self.robot_id = self.get_parameter("robot_id").get_parameter_value().string_value
        self.username = self.get_parameter("username").get_parameter_value().string_value
        self.password = self.get_parameter("password").get_parameter_value().string_value
        self.max_inflight = self.get_parameter("max_inflight").get_parameter_value().integer_value

        rate_limit_hz = self.get_parameter("rate_limit_hz").get_parameter_value().double_value
        self.min_interval = 1.0 / rate_limit_hz if rate_limit_hz > 0.0 else 0.0
        self.last_sent = 0.0

        # Reuse HTTP connections (keep-alive) instead of a new TCP/TLS
        # handshake per request. Pool sized to match max_inflight so
        # concurrent sends don't queue up waiting for a free connection.
        self.session = requests.Session()
        adapter = HTTPAdapter(pool_connections=self.max_inflight, pool_maxsize=self.max_inflight)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

        self.token = None
        self._login_lock = threading.Lock()
        self._login()

        # Rolling POST latency/throughput stats, logged periodically so the
        # actual server RTT is visible instead of guessed at - see
        # _record_post_stat().
        self._stats_lock = threading.Lock()
        self._stats_count = 0
        self._stats_latency_sum = 0.0
        self._stats_last_log = time.monotonic()

        # A dispatcher thread paces sends at rate_limit_hz and hands each
        # payload to a thread pool instead of sending synchronously, so the
        # send rate is not capped by one HTTP round trip. Only the latest
        # payload is kept between dispatches; if the sender falls behind,
        # stale in-between messages are dropped instead of queuing up and
        # adding latency.
        self._executor = ThreadPoolExecutor(max_workers=self.max_inflight)
        self._inflight = threading.Semaphore(self.max_inflight)
        self._pending_payload = None
        self._lock = threading.Lock()
        self._new_data = threading.Event()
        threading.Thread(target=self._sender_loop, daemon=True).start()

        # Global topic name (leading slash) so this node picks up /joint_cmd
        # regardless of the namespace it is launched under.
        self.create_subscription(JointState, "/joint_cmd", self._on_joint_cmd, 10)

        self.get_logger().info(
            f"Forwarding /joint_cmd -> {self.api_url}/daksha/{self.robot_id}/joint_cmd"
        )

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

    def _on_joint_cmd(self, msg):
        payload = {
            "name": list(msg.name),
            "position": list(msg.position),
            "velocity": list(msg.velocity),
            "effort": list(msg.effort),
        }

        with self._lock:
            self._pending_payload = payload
        self._new_data.set()

    def _sender_loop(self):
        while rclpy.ok():
            self._new_data.wait()

            with self._lock:
                payload = self._pending_payload
                self._pending_payload = None
                self._new_data.clear()

            if payload is None:
                continue

            # All max_inflight connections are already busy sending older
            # payloads - drop this one instead of queuing (queuing would
            # just mean sending increasingly stale data with growing
            # delay). A newer payload will be along by the next dispatch.
            if not self._inflight.acquire(blocking=False):
                continue

            if self.min_interval:
                wait = self.min_interval - (time.monotonic() - self.last_sent)
                if wait > 0:
                    time.sleep(wait)
            self.last_sent = time.monotonic()

            # Hand off to the thread pool and immediately loop back for the
            # next payload rather than waiting for this request to
            # complete - this is what lets the send rate exceed 1/RTT.
            future = self._executor.submit(self._post, payload, True)
            future.add_done_callback(lambda _f: self._inflight.release())

    def _post(self, payload, retry_on_auth_error):
        start = time.monotonic()
        try:
            resp = self.session.post(
                f"{self.api_url}/daksha/{self.robot_id}/joint_cmd",
                json=payload,
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=5,
            )
        except requests.RequestException as e:
            self.get_logger().warn(f"[post] joint_cmd failed: {e}")
            return
        finally:
            self._record_post_stat(time.monotonic() - start)

        if resp.status_code == 401 and retry_on_auth_error:
            self.get_logger().info("[post] token expired, re-logging in")
            self._login()
            self._post(payload, retry_on_auth_error=False)
            return

        if resp.status_code != 200:
            self.get_logger().warn(f"[post] joint_cmd -> {resp.status_code}: {resp.text}")

    def _record_post_stat(self, elapsed):
        # Surfaces the real server RTT and achieved send rate every 2s, so
        # max_inflight can be tuned from measured numbers instead of
        # guesswork - throughput ceiling is roughly max_inflight / RTT.
        with self._stats_lock:
            self._stats_count += 1
            self._stats_latency_sum += elapsed
            now = time.monotonic()
            span = now - self._stats_last_log
            if span >= 2.0:
                avg_latency = self._stats_latency_sum / self._stats_count
                hz = self._stats_count / span
                self.get_logger().info(
                    f"[post] {hz:.1f} req/s, avg latency {avg_latency*1000:.0f}ms "
                    f"(ceiling ~{self.max_inflight / avg_latency:.1f} Hz at max_inflight={self.max_inflight})"
                )
                self._stats_count = 0
                self._stats_latency_sum = 0.0
                self._stats_last_log = now


def main(args=None):
    rclpy.init(args=args)
    node = JointCmdApiSubscriber()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
