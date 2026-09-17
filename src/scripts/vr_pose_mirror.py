#!/usr/bin/env python3

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import PoseStamped
from std_srvs.srv import SetBool

from message_filters import Subscriber, ApproximateTimeSynchronizer

# =====================================================
# CONFIG
# =====================================================

# ---------- MIRROR CONFIG ----------
MIRROR_CONTROLS = True   # True: each controller drives the opposite arm, mirrored
MIRROR_AXIS = "x"        # "x" / "y" / "z"

# =====================================================
# HELPERS
# =====================================================

def mirror_position(x, y, z, axis):
    if axis == "x":
        return (-x, y, z)
    if axis == "y":
        return (x, -y, z)
    if axis == "z":
        return (x, y, -z)
    raise ValueError(f"Unsupported mirror axis: {axis}")


def mirror_quaternion(qx, qy, qz, qw, axis):
    """
    Mirror an orientation across one Cartesian axis.

    Assumes the incoming pose is already expressed in the robot/world frame.
    For the default ROS convention (x forward, y left, z up), mirroring
    left/right motion is a reflection across the y axis.

    These are the closed form of R_out = M @ R_in @ M with M the reflection
    matrix for that axis: negate the two quaternion vector components other
    than the mirror axis, leaving that component and w alone.
    """
    if axis == "x":
        return (qx, -qy, -qz, qw)
    if axis == "y":
        return (-qx, qy, -qz, qw)
    if axis == "z":
        return (-qx, -qy, qz, qw)
    raise ValueError(f"Unsupported mirror axis: {axis}")


# =====================================================
# NODE
# =====================================================

class PoseRelay(Node):
    def __init__(self):
        super().__init__("pose_relay")

        self.enabled = True

        self.mirror_controls = MIRROR_CONTROLS
        self.mirror_axis = MIRROR_AXIS

        if self.mirror_axis not in ("x", "y", "z"):
            raise ValueError(f"Unsupported mirror axis: {self.mirror_axis}")

        # Publishers
        self.left_pub = self.create_publisher(
            PoseStamped,
            "/left/pose",
            10,
        )

        self.right_pub = self.create_publisher(
            PoseStamped,
            "/right/pose",
            10,
        )

        # Subscribers
        self.left_sub = Subscriber(
            self,
            PoseStamped,
            "/quest/left/pose",
        )

        self.right_sub = Subscriber(
            self,
            PoseStamped,
            "/quest/right/pose",
        )

        # Synchronizer
        self.sync = ApproximateTimeSynchronizer(
            [self.left_sub, self.right_sub],
            queue_size=10,
            slop=0.02,
        )

        self.sync.registerCallback(self.pose_callback)

        # Enable/Disable service
        self.srv = self.create_service(
            SetBool,
            "/vr_enable",
            self.enable_callback,
        )

        control_mode = "mirrored" if self.mirror_controls else "direct"
        self.get_logger().info(
            f"Pose relay started. Mode: {control_mode}, "
            f"mirror_axis={self.mirror_axis}."
        )

    def enable_callback(self, request, response):
        self.enabled = request.data

        response.success = True

        if self.enabled:
            response.message = "VR relay enabled"
            self.get_logger().info("VR relay ENABLED")
        else:
            response.message = "VR relay disabled"
            self.get_logger().info("VR relay DISABLED")

        return response

    def get_controller_side(self, arm_side: str) -> str:
        if not self.mirror_controls:
            return arm_side
        return "right" if arm_side == "left" else "left"

    def mirror_pose(self, msg: PoseStamped) -> PoseStamped:
        mirrored = PoseStamped()
        mirrored.header = msg.header

        p = msg.pose.position
        px, py, pz = mirror_position(p.x, p.y, p.z, self.mirror_axis)
        mirrored.pose.position.x = px
        mirrored.pose.position.y = py
        mirrored.pose.position.z = pz

        r = msg.pose.orientation
        qx, qy, qz, qw = mirror_quaternion(r.x, r.y, r.z, r.w, self.mirror_axis)
        mirrored.pose.orientation.x = qx
        mirrored.pose.orientation.y = qy
        mirrored.pose.orientation.z = qz
        mirrored.pose.orientation.w = qw

        return mirrored

    def pose_callback(self, left_msg, right_msg):
        if not self.enabled:
            return

        incoming = {"left": left_msg, "right": right_msg}

        for arm_side, pub in (("left", self.left_pub), ("right", self.right_pub)):
            controller_side = self.get_controller_side(arm_side)
            msg = incoming[controller_side]

            if self.mirror_controls:
                pub.publish(self.mirror_pose(msg))
            else:
                pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)

    node = PoseRelay()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass

    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()

#ros2 service call /vr_enable std_srvs/srv/SetBool "{data: true}"

#ros2 service call /vr_enable std_srvs/srv/SetBool "{data: false}"
