#!/usr/bin/env python3
"""
power_monitor_node.py - ROS 2 Humble Bridge Node & Web UI Server for Vajara Power Monitor
Reads serial JSON from STM32 (/dev/ttyACM0), publishes to ROS 2 topic (/vajra/power_telemetry),
and serves the Web UI Dashboard at http://localhost:8080.
"""

import os
import sys
import time
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import serial

# Try importing ROS 2 rclpy and std_msgs
try:
    import rclpy
    from rclpy.node import Node
    from std_msgs.msg import String
    ROS2_AVAILABLE = True
except ImportError:
    ROS2_AVAILABLE = False


# Global thread-safe telemetry cache
latest_telemetry_lock = threading.Lock()
latest_telemetry = {
    "connected": False,
    "up": 0,
    "rec": 0,
    "ports": [
        {"n": "24V Port 1", "a": 64, "rail": 24, "on": False, "v": 0.0, "i": 0.0, "p": 0.0, "lim": 20.0, "warn": 16.0, "th": False, "e": 0},
        {"n": "24V Port 2", "a": 65, "rail": 24, "on": False, "v": 0.0, "i": 0.0, "p": 0.0, "lim": 20.0, "warn": 16.0, "th": False, "e": 0},
        {"n": "24V Port 3", "a": 66, "rail": 24, "on": False, "v": 0.0, "i": 0.0, "p": 0.0, "lim": 20.0, "warn": 16.0, "th": False, "e": 0},
        {"n": "24V Port 4", "a": 67, "rail": 24, "on": False, "v": 0.0, "i": 0.0, "p": 0.0, "lim": 20.0, "warn": 16.0, "th": False, "e": 0},
        {"n": "12V Port",   "a": 68, "rail": 12, "on": False, "v": 0.0, "i": 0.0, "p": 0.0, "lim": 5.0,  "warn": 3.0,  "th": True,  "e": 0},
    ],
    "tot": {"p": 0.0, "i24": 0.0, "i12": 0.0, "on": 0, "of": 5}
}

HTML_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")


class WebUIRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            try:
                with open(HTML_PATH, "rb") as f:
                    self.wfile.write(f.read())
            except Exception as e:
                self.wfile.write(f"<h1>Error loading index.html: {e}</h1>".encode("utf-8"))

        elif self.path == "/api/data":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()

            with latest_telemetry_lock:
                data_bytes = json.dumps(latest_telemetry).encode("utf-8")
            self.wfile.write(data_bytes)

        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"404 Not Found")

    def log_message(self, format, *args):
        # Suppress noisy HTTP GET logging
        pass


def run_web_server(host="0.0.0.0", port=8080):
    server = HTTPServer((host, port), WebUIRequestHandler)
    print(f"[WEB UI] Dashboard server running at http://localhost:{port}")
    server.serve_forever()


def _publish_diag(ros_node, connected: bool):
    if ros_node is None or not ROS2_AVAILABLE:
        return
    msg = String()
    msg.data = "vajira_diagnosis_emb connected" if connected else "vajira_diagnosis_emb not connected"
    ros_node.diag_publisher_.publish(msg)


def serial_reader_thread(port="/dev/ttyACM0", baud=115200, ros_node=None):
    global latest_telemetry
    print(f"[SERIAL] Opening serial port {port} at {baud} baud...")
    disconnect_warned = False

    while True:
        try:
            with serial.Serial(port, baud, timeout=1.5) as ser:
                print(f"[SERIAL] Connected to STM32 on {port}")
                with latest_telemetry_lock:
                    latest_telemetry["connected"] = True
                if disconnect_warned:
                    _publish_diag(ros_node, connected=True)
                    disconnect_warned = False
                while True:
                    line = ser.readline().decode("utf-8", errors="ignore").strip()
                    if not line:
                        continue

                    # Attempt to parse JSON telemetry line
                    if line.startswith("{") and line.endswith("}"):
                        try:
                            data = json.loads(line)
                            if "ports" in data and "tot" in data:
                                data["connected"] = True
                                with latest_telemetry_lock:
                                    latest_telemetry = data

                                # Publish to ROS 2 topic if node available
                                if ros_node is not None and ROS2_AVAILABLE:
                                    msg = String()
                                    msg.data = line
                                    ros_node.publisher_.publish(msg)
                        except Exception:
                            pass
                    else:
                        # Non-JSON console output from STM32 boot
                        print(f"[STM32 LOG] {line}")
        except Exception as e:
            with latest_telemetry_lock:
                latest_telemetry["connected"] = False
            if not disconnect_warned:
                print(f"[SERIAL ERROR] Not connected — retrying {port} in 2 seconds ({e})...")
                _publish_diag(ros_node, connected=False)
                disconnect_warned = True
            time.sleep(2.0)


if ROS2_AVAILABLE:
    class VajaraPowerMonitorNode(Node):
        def __init__(self):
            super().__init__("vajara_power_monitor_node")
            self.declare_parameter("serial_port", "/dev/ttyACM0")
            self.declare_parameter("baud_rate", 115200)
            self.declare_parameter("web_port", 8080)

            serial_port = self.get_parameter("serial_port").get_parameter_value().string_value
            baud_rate = self.get_parameter("baud_rate").get_parameter_value().integer_value
            web_port = self.get_parameter("web_port").get_parameter_value().integer_value

            self.publisher_ = self.create_publisher(String, "/vajra/power_telemetry", 10)
            self.diag_publisher_ = self.create_publisher(String, "vajira_diagnosis_emb", 10)
            self.get_logger().info(f"ROS 2 Node started. Publishing to topic: /vajra/power_telemetry")

            # Start Web Server thread
            web_thread = threading.Thread(target=run_web_server, args=("0.0.0.0", web_port), daemon=True)
            web_thread.start()

            # Start Serial Reader thread
            reader_thread = threading.Thread(target=serial_reader_thread, args=(serial_port, baud_rate, self), daemon=True)
            reader_thread.start()


def main(args=None):
    if ROS2_AVAILABLE:
        rclpy.init(args=args)
        node = VajaraPowerMonitorNode()
        try:
            rclpy.spin(node)
        except KeyboardInterrupt:
            pass
        finally:
            node.destroy_node()
            rclpy.shutdown()
    else:
        print("[WARNING] rclpy / ROS 2 not detected in current environment.")
        print("[INFO] Running in Standalone Bridge Mode (Serial -> Web UI Dashboard)...")
        
        # Start Web Server thread
        web_thread = threading.Thread(target=run_web_server, args=("0.0.0.0", 8080), daemon=True)
        web_thread.start()

        # Run Serial Reader in main thread
        serial_reader_thread(port="/dev/ttyACM0", baud=115200, ros_node=None)


if __name__ == "__main__":
    main()
