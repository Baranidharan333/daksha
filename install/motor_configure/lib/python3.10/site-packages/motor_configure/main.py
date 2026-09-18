#!/usr/bin/env python3
import socket
import threading

import can
import rclpy
from rclpy.node import Node

from motor_configure.motor_web import app, state


class MotorConfigureNode(Node):
    """Opens the CAN bus and serves motor_web's Flask app in a background thread.

    Configuration is via ROS parameters (channel, host, port) so it can be set
    from a launch file or `--ros-args -p <name>:=<value>`. `port` is declared
    as an integer parameter (not string) because ROS infers an override's
    type from its value -- an unquoted numeric override like `-p port:=8455`
    (or a launch substitution that evaluates to "8455") is typed as INTEGER,
    and would be rejected against a STRING-typed declaration.
    """

    def __init__(self):
        super().__init__("motor_configure")

        self.declare_parameter("channel", "can0")
        self.declare_parameter("host", "0.0.0.0")
        self.declare_parameter("port", 8000)

        channel = self.get_parameter("channel").get_parameter_value().string_value
        host = self.get_parameter("host").get_parameter_value().string_value
        port = self.get_parameter("port").get_parameter_value().integer_value

        state["channel"] = channel
        state["bus"] = can.interface.Bus(channel=channel, interface="socketcan")

        self._server_thread = threading.Thread(
            target=app.run,
            kwargs={"host": host, "port": port, "debug": False, "use_reloader": False},
            daemon=True,
        )
        self._server_thread.start()

        # "0.0.0.0" (bind-all) isn't a reachable address -- print the
        # machine's own hostname there instead, so the logged link is
        # actually something you can open from another device on the LAN.
        display_host = socket.gethostname() if host in ("0.0.0.0", "::") else host
        self.get_logger().info(f"Motor web UI: http://{display_host}:{port}  (channel={channel})")

    def destroy_node(self):
        bus = state.get("bus")
        if bus is not None:
            bus.shutdown()
            state["bus"] = None
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = MotorConfigureNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
