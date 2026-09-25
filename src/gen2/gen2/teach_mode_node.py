#!/usr/bin/env python3

import time

import rclpy
from rclpy.node import Node
from rclpy.executors import MultiThreadedExecutor
from rclpy.callback_groups import ReentrantCallbackGroup

from rcl_interfaces.msg import SetParametersResult

from hw_interface.srv import SetMotorGains


NUM_MOTORS = 8

# Defaults for the per-motor "normal_kp_<n>"/"normal_kd_<n>" ROS 2 parameters
# declared below (n = 1..NUM_MOTORS, matching send_gains()'s motor_ids) --
# not used directly once the node is up (self.normal_kp/self.normal_kd are),
# so a live `ros2 param set` on any single motor overrides these without a
# code change/restart.
DEFAULT_NORMAL_KP = [
    300.0,
    300.0,
    300.0,
    300.0,
    80.0,
    80.0,
    50.0,
    3.0,  # previous value 15 for gripper for vla
]

DEFAULT_NORMAL_KD = [
    3.0,
    3.0,
    3.0,
    3.0,
    1.0,
    1.0,
    1.0,
    0.5,
]

# NORMAL_KP = [
#     80.0,
#     80.0,
#     50.0,
#     50.0,
#     20.0,
#     20.0,
#     20.0,
#     5.0,
# ]

# NORMAL_KD = [
#     4.0,
#     4.0,
#     3.0,
#     3.0,
#     1.0,
#     1.0,
#     1.0,
#     0.5,
# ]

TEACH_KP = [0.0] * 8
TEACH_KD = [0.0] * 8

# How long to wait for both arms to confirm a gain update before giving up.
GAIN_CONFIRM_TIMEOUT_S = 2.0


class TeachModeNode(Node):

    def __init__(self):

        super().__init__("teach_mode_node")

        self.declare_parameter("teach_mode", False)

        for i in range(NUM_MOTORS):
            self.declare_parameter(f"normal_kp_{i + 1}", DEFAULT_NORMAL_KP[i])
            self.declare_parameter(f"normal_kd_{i + 1}", DEFAULT_NORMAL_KD[i])

        self.teach_mode = self.get_parameter(
            "teach_mode"
        ).value
        self.normal_kp = [
            self.get_parameter(f"normal_kp_{i + 1}").value
            for i in range(NUM_MOTORS)
        ]
        self.normal_kd = [
            self.get_parameter(f"normal_kd_{i + 1}").value
            for i in range(NUM_MOTORS)
        ]

        # These live on their own reentrant callback group so send_gains()
        # can block waiting on the responses without deadlocking the
        # (default-group) parameter callback that calls it. This only
        # works because main() spins with a MultiThreadedExecutor.
        self._client_cb_group = ReentrantCallbackGroup()

        self.left_client = self.create_client(
            SetMotorGains,
            "/LeftArmSystem/set_motor_gains",
            callback_group=self._client_cb_group,
        )

        self.right_client = self.create_client(
            SetMotorGains,
            "/RightArmSystem/set_motor_gains",
            callback_group=self._client_cb_group,
        )

        self.get_logger().info(
            "Waiting for motor gain services..."
        )

        self.left_client.wait_for_service()
        self.right_client.wait_for_service()

        self.get_logger().info(
            "Motor gain services connected."
        )

        self.add_on_set_parameters_callback(
            self.parameter_callback
        )

        # Apply initial mode
        if self.teach_mode:
            self.enable_teach_mode()
        else:
            self.disable_teach_mode()

    ############################################################

    def send_gains(self, kp, kd):
        """Requests new gains on both arms and blocks (bounded) until both
        confirm success, so callers know the hardware actually applied
        them before treating the mode switch as done. Safe to block here:
        the service clients run on a separate reentrant callback group
        from whatever calls this, under a MultiThreadedExecutor."""

        left = SetMotorGains.Request()

        left.motor_ids = [1, 2, 3, 4, 5, 6, 7, 8]
        left.kp = kp
        left.kd = kd

        right = SetMotorGains.Request()

        right.motor_ids = [1, 2, 3, 4, 5, 6, 7, 8]
        right.kp = kp
        right.kd = kd

        left_future = self.left_client.call_async(left)
        right_future = self.right_client.call_async(right)

        deadline = time.monotonic() + GAIN_CONFIRM_TIMEOUT_S

        while (
            (not left_future.done() or not right_future.done())
            and time.monotonic() < deadline
        ):
            time.sleep(0.005)

        left_result = left_future.result() if left_future.done() else None
        right_result = right_future.result() if right_future.done() else None

        left_ok = left_result is not None and left_result.success
        right_ok = right_result is not None and right_result.success

        if not left_ok:
            self.get_logger().error(
                "Left arm gain update did not confirm in time"
            )

        if not right_ok:
            self.get_logger().error(
                "Right arm gain update did not confirm in time"
            )

        return left_ok and right_ok

    ############################################################

    def enable_teach_mode(self):

        self.get_logger().info(
            "========== TEACH MODE ENABLED =========="
        )

        return self.send_gains(
            TEACH_KP,
            TEACH_KD
        )

    ############################################################

    def disable_teach_mode(self):

        self.get_logger().info(
            "========== TEACH MODE DISABLED =========="
        )

        return self.send_gains(
            self.normal_kp,
            self.normal_kd
        )

    ############################################################

    @staticmethod
    def _motor_gain_index(name):
        """0-based motor index for a "normal_kp_<n>"/"normal_kd_<n>"
        parameter name, or None if it isn't one of those."""

        for prefix in ("normal_kp_", "normal_kd_"):
            if not name.startswith(prefix):
                continue
            suffix = name[len(prefix):]
            if suffix.isdigit() and 1 <= int(suffix) <= NUM_MOTORS:
                return int(suffix) - 1

        return None

    ############################################################

    def parameter_callback(self, params):

        result = SetParametersResult()
        result.successful = True

        for param in params:

            if param.name == "teach_mode":

                if param.value == self.teach_mode:
                    continue

                requested = param.value

                ok = (
                    self.enable_teach_mode()
                    if requested
                    else self.disable_teach_mode()
                )

                if not ok:
                    result.successful = False
                    result.reason = "gain update did not confirm on hardware"
                    continue

                self.teach_mode = requested

            else:

                index = self._motor_gain_index(param.name)

                if index is None:
                    continue

                new_kp = list(self.normal_kp)
                new_kd = list(self.normal_kd)
                (new_kp if param.name.startswith("normal_kp_") else new_kd)[index] = \
                    float(param.value)

                # Stiffness/damping only needs to reach the hardware while
                # normal mode is actually the one in effect -- while
                # teaching, the arm's gains are deliberately zeroed, so this
                # just gets remembered for the next disable_teach_mode().
                if not self.teach_mode and not self.send_gains(new_kp, new_kd):
                    result.successful = False
                    result.reason = "gain update did not confirm on hardware"
                    continue

                self.normal_kp = new_kp
                self.normal_kd = new_kd

        return result


def main(args=None):

    rclpy.init(args=args)

    node = TeachModeNode()
    executor = MultiThreadedExecutor()
    executor.add_node(node)

    try:
        executor.spin()
    except KeyboardInterrupt:
        pass

    node.destroy_node()

    rclpy.shutdown()


if __name__ == "__main__":
    main()
