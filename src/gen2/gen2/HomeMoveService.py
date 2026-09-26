#!/usr/bin/env python3

import rclpy
import numpy as np
import time

from rclpy.node import Node
from sensor_msgs.msg import JointState
from std_srvs.srv import Trigger
from gen2_msgs.srv import SetHomePosition


# Fallback for the "reset to default" case in set_home_position_cb -- not
# used directly once the node is up (self.home_position is), so /move_home
# always drives to whatever was last set there, not this constant.
DEFAULT_HOME_POSITION = np.array([
    # # LEFT ARM
    # 0.0,
    # 0.0,
    # 0.0,
    # 0.0,
    # 0.0,
    # 0.0,
    # 0.0 ,
    # 0.0,

    # # RIGHT ARM
    # -0.34,
    # 0.0,
    # 0.0,
    # 1.45,
    # 1.53,
    # 0.0,
    # 0.7,
    # 0.0,
    
    # LEFT ARM
    0.0,
    0.0,
    0.0,
    0.0,
    0.0,
    0.0,
    0.0 ,
    0.0,

    # RIGHT ARM
    0.0,
    0.0,
    0.0,
    0.0,
    0.0,
    0.0,
    0.0 ,
    0.0,
], dtype=float)


class HomeMoveService(Node):

    def __init__(self):
        super().__init__("home_move_service")

        self.right_state = None
        self.left_state = None

        self.create_subscription(
            JointState,
            "/RightArmSystem_ordered_joint_states",
            self.right_cb,
            10
        )

        self.create_subscription(
            JointState,
            "/LeftArmSystem_ordered_joint_states",
            self.left_cb,
            10
        )

        self.pub = self.create_publisher(
            JointState,
            "/joint_cmd",
            10
        )

        self.create_service(
            Trigger,
            "/move_home",
            self.move_home_cb
        )

        # Separate from /move_home on purpose: /move_home is a bare Trigger
        # already called (as std_srvs/Trigger, no request fields) from
        # leader_controller_ui.py, dashboard_app.py and launch_control_app.py
        # -- changing its type would break all three. This just updates what
        # "home" currently means; /move_home still does the actual move.
        self.create_service(
            SetHomePosition,
            "/set_home_position",
            self.set_home_position_cb
        )

        self.home_position = np.array(DEFAULT_HOME_POSITION, dtype=float)

    def right_cb(self, msg):
        self.right_state = msg

    def left_cb(self, msg):
        self.left_state = msg

    def move_home_cb(self, request, response):

        if self.right_state is None or self.left_state is None:
            response.success = False
            response.message = "Joint states not received"
            return response

        current = np.array(
            list(self.left_state.position) +
            list(self.right_state.position),
            dtype=float
        )

        joint_names = (
            list(self.left_state.name) +
            list(self.right_state.name)
        )

        joint_count = len(self.home_position)

        if len(current) < joint_count:
            response.success = False
            response.message = (
                f"Expected {joint_count} ordered joints, received {len(current)}"
            )
            return response

        start = current[:joint_count]
        target = self.home_position

        rate_hz = 30.0
        steps = 500

        self.get_logger().info(
            f"Moving home in {steps} steps"
        )

        for i in range(steps + 1):

            t = i / steps
            alpha = t * t * (3.0 - 2.0 * t)

            q = start + alpha * (target - start)

            msg = JointState()
            msg.header.stamp = self.get_clock().now().to_msg()
            msg.name = joint_names[:joint_count]
            msg.position = q.tolist()

            self.pub.publish(msg)

            time.sleep(1.0 / rate_hz)

        response.success = True
        response.message = "Reached home"

        return response

    def set_home_position_cb(self, request, response):
        """Updates self.home_position -- doesn't move anything itself.
        An empty position resets to DEFAULT_HOME_POSITION; otherwise it must
        supply exactly one value per joint (left arm then right arm, same
        order /move_home already uses)."""

        joint_count = len(DEFAULT_HOME_POSITION)

        if len(request.position) == 0:
            self.home_position = np.array(DEFAULT_HOME_POSITION, dtype=float)
            response.success = True
            response.message = "Home position reset to default"
            return response

        if len(request.position) != joint_count:
            response.success = False
            response.message = (
                f"Expected {joint_count} positions (left arm then right "
                f"arm), received {len(request.position)}"
            )
            return response

        self.home_position = np.array(request.position, dtype=float)

        self.get_logger().info(
            f"Home position set to {self.home_position.tolist()}"
        )

        response.success = True
        response.message = "Home position updated"

        return response


def main():
    rclpy.init()

    node = HomeMoveService()

    rclpy.spin(node)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
