#!/usr/bin/env python3

import rclpy
from rclpy.node import Node

from rcl_interfaces.msg import SetParametersResult
from sensor_msgs.msg import Joy, JointState


# =====================================================
# CONFIG
# =====================================================

# Joint names must match joint_command_limiter's map (gen2/joint_cmd.py),
# which is the node that turns /joint_cmd into controller trajectories.
# Anything else is dropped there with "Unknown joint: <name>".
# The second joint of each gripper (left_gripper_right_joint /
# right_gripper_left_joint) mimics these in the URDF, so only these two
# are commanded.
LEFT_GRIPPER_JOINT = "left_gripper_left_joint"
RIGHT_GRIPPER_JOINT = "right_gripper_right_joint"

# The two grippers have OPPOSITE sign conventions in robot.urdf:
#   left_gripper_left_joint     lower=-0.044  upper= 0.0
#   right_gripper_right_joint   lower= 0.0    upper= 0.044
# so a single shared GRIPPER_OPEN would drive the right gripper outside
# its limits.
GRIPPER_CLOSED = 0.0
LEFT_GRIPPER_OPEN = -0.044
RIGHT_GRIPPER_OPEN = 0.044

CONTROL_HZ = 100.0
DT = 1.0 / CONTROL_HZ

MAX_GRIPPER_VEL = 0.10      # meters/sec
KP = 10.0

TRIGGER_DEADBAND = 0.01


# =====================================================
# NODE
# =====================================================

class VRGripperServo(Node):

    def __init__(self):
        super().__init__("vr_gripper_servo")

        # ----------------------------
        # Trigger values (0~1)
        # ----------------------------
        self.left_trigger = 0.0
        self.right_trigger = 0.0

        # ----------------------------
        # Current gripper positions
        # ----------------------------
        self.left_q = GRIPPER_CLOSED
        self.right_q = GRIPPER_CLOSED

        # ----------------------------
        # Publisher
        # ----------------------------
        self.pub = self.create_publisher(
            JointState,
            "/joint_cmd",
            10,
        )

        # ----------------------------
        # Publish enable/disable
        # ----------------------------
        self.declare_parameter('publish_enabled', False)
        self.publish_enabled = self.get_parameter('publish_enabled').get_parameter_value().bool_value

        self.add_on_set_parameters_callback(self.dynamic_parameter_cb)

        # ----------------------------
        # Joy subscribers
        # ----------------------------
        self.create_subscription(
            Joy,
            "/quest/left/joy",
            self.left_joy_cb,
            10,
        )

        self.create_subscription(
            Joy,
            "/quest/right/joy",
            self.right_joy_cb,
            10,
        )

        # ----------------------------
        # Timer
        # ----------------------------
        self.create_timer(DT, self.control_loop)

        self.get_logger().info("VR Gripper Servo Started")

    # =================================================
    # Publish toggle
    # =================================================

    def dynamic_parameter_cb(self, params):

        for p in params:

            if p.name == 'publish_enabled':
                self.publish_enabled = p.value

                state = "enabled" if p.value else "disabled"
                self.get_logger().info(f"[DEBUG] gripper /joint_cmd publish -> {state}")

        return SetParametersResult(successful=True)

    # =================================================
    # Left Controller
    # =================================================

    def left_joy_cb(self, msg: Joy):

        if len(msg.axes) < 3:
            return

        trigger = msg.axes[2]

        # Quest trigger:
        # released -> 1
        # pressed  -> 0

        trigger = 1.0 - trigger

        trigger = max(0.0, min(1.0, trigger))

        if abs(trigger - self.left_trigger) < TRIGGER_DEADBAND:
            return

        self.left_trigger = trigger

    # =================================================
    # Right Controller
    # =================================================

    def right_joy_cb(self, msg: Joy):

        if len(msg.axes) < 3:
            return

        trigger = msg.axes[2]

        trigger = 1.0 - trigger

        trigger = max(0.0, min(1.0, trigger))

        if abs(trigger - self.right_trigger) < TRIGGER_DEADBAND:
            return

        self.right_trigger = trigger

    # =================================================
    # Velocity limited servo
    # =================================================

    def update_gripper(self, current, trigger, gripper_open):

        target = (
            GRIPPER_CLOSED +
            trigger * (gripper_open - GRIPPER_CLOSED)
        )

        vel = KP * (target - current)

        vel = max(
            -MAX_GRIPPER_VEL,
            min(MAX_GRIPPER_VEL, vel),
        )

        current += vel * DT

        # Clamped with min/max of the two endpoints rather than assuming an
        # order, since gripper_open is negative for the left gripper and
        # positive for the right.
        current = max(
            min(current, max(GRIPPER_CLOSED, gripper_open)),
            min(GRIPPER_CLOSED, gripper_open),
        )

        return current

    # =================================================
    # Control loop
    # =================================================

    def control_loop(self):

        self.left_q = self.update_gripper(
            self.left_q,
            self.left_trigger,
            LEFT_GRIPPER_OPEN,
        )

        self.right_q = self.update_gripper(
            self.right_q,
            self.right_trigger,
            RIGHT_GRIPPER_OPEN,
        )

        if not self.publish_enabled:
            return

        msg = JointState()

        msg.header.stamp = self.get_clock().now().to_msg()

        msg.name = [
            LEFT_GRIPPER_JOINT,
            RIGHT_GRIPPER_JOINT,
        ]

        msg.position = [
            self.left_q,
            self.right_q,
        ]

        self.pub.publish(msg)


# =====================================================
# MAIN
# =====================================================

def main(args=None):

    rclpy.init(args=args)

    node = VRGripperServo()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass

    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()