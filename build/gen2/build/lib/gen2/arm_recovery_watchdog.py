#!/usr/bin/env python3

import rclpy

from rclpy.node import Node

from std_srvs.srv import Trigger

from hw_interface.msg import MotorStatusArray
from sensor_msgs.msg import JointState


class SingleArmWatchdog:
    """Fault detection + recovery trigger for one arm's motor_status/arm_recover
    pair, isolated from the other arm so a fault on one never blocks or delays
    recovery on the other."""

    FAULT_NAMES = ("Communication Lost", "Disabled")
    RETRIGGER_COOLDOWN_SEC = 3.0

    def __init__(self, node: Node, arm_name: str, on_recovery_triggered):
        self.node = node
        self.arm_name = arm_name
        self.on_recovery_triggered = on_recovery_triggered

        self.recovery_in_progress = False
        self.last_trigger_time = node.get_clock().now()

        # motor id -> number of times recovery was triggered because this
        # motor faulted. Published (across both arms) on
        # /arm_recovery/recovery_counts as a JointState.
        self.recovery_counts = {}

        self.subscription = node.create_subscription(
            MotorStatusArray,
            f"/{arm_name}/motor_status",
            self.status_callback,
            10,
        )

        self.client = node.create_client(
            Trigger,
            f"/{arm_name}/arm_recover",
        )

    def status_callback(self, msg):

        if self.recovery_in_progress:
            return

        for motor in msg.motors:

            if motor.error_name in self.FAULT_NAMES:

                now = self.node.get_clock().now()

                dt = (now - self.last_trigger_time).nanoseconds / 1e9

                # prevent spam
                if dt < self.RETRIGGER_COOLDOWN_SEC:
                    return

                self.node.get_logger().warn(
                    f"[{self.arm_name}] motor {motor.id} fault: "
                    f"{motor.error_name}"
                )

                self.recovery_counts[motor.id] = (
                    self.recovery_counts.get(motor.id, 0) + 1
                )
                self.on_recovery_triggered()

                self.call_recovery()

                self.last_trigger_time = now

                return

    def call_recovery(self):

        if not self.client.wait_for_service(timeout_sec=1.0):

            self.node.get_logger().error(
                f"[{self.arm_name}] recovery service unavailable"
            )

            return

        self.recovery_in_progress = True

        request = Trigger.Request()

        future = self.client.call_async(request)

        future.add_done_callback(self.recovery_response_callback)

    def recovery_response_callback(self, future):

        self.recovery_in_progress = False

        try:

            response = future.result()

            if response.success:

                self.node.get_logger().info(
                    f"[{self.arm_name}] recovery success: "
                    f"{response.message}"
                )

            else:

                self.node.get_logger().error(
                    f"[{self.arm_name}] recovery failed: "
                    f"{response.message}"
                )

        except Exception as e:

            self.node.get_logger().error(
                f"[{self.arm_name}] service call failed: {str(e)}"
            )


class ArmRecoveryWatchdog(Node):

    def __init__(self):

        super().__init__('arm_recovery_watchdog')

        self.declare_parameter('right_arm_name', 'RightArmSystem')
        self.declare_parameter('left_arm_name', 'LeftArmSystem')

        right_arm_name = self.get_parameter(
            'right_arm_name').get_parameter_value().string_value
        left_arm_name = self.get_parameter(
            'left_arm_name').get_parameter_value().string_value

        # How many times recovery has been triggered for each joint (motor),
        # across both arms -- one name/position entry per motor that has
        # ever faulted. Consumed by automation's launch_control_app.py UI.
        self.recovery_count_pub = self.create_publisher(
            JointState, '/arm_recovery/recovery_counts', 10)

        self.right_arm = SingleArmWatchdog(
            self, right_arm_name, self._publish_recovery_counts)
        self.left_arm = SingleArmWatchdog(
            self, left_arm_name, self._publish_recovery_counts)

        self.get_logger().info(
            f"watching /{right_arm_name}/motor_status and "
            f"/{left_arm_name}/motor_status independently"
        )

    def _publish_recovery_counts(self):
        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()
        for arm in (self.right_arm, self.left_arm):
            for motor_id, count in sorted(arm.recovery_counts.items()):
                msg.name.append(f"{arm.arm_name}_motor_{motor_id}")
                msg.position.append(float(count))
        self.recovery_count_pub.publish(msg)


def main(args=None):

    rclpy.init(args=args)

    node = ArmRecoveryWatchdog()

    rclpy.spin(node)

    node.destroy_node()

    rclpy.shutdown()


if __name__ == '__main__':
    main()
