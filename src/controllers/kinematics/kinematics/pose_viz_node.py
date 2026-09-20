"""Draws /left/pose and /right/pose in the placo (meshcat) viewer, nothing else.

No IK, no orientation correction, no solver: whatever quest_tf_to_pose
publishes is what gets drawn. That is the point - it isolates the incoming
pose from everything ik_node does to it, so you can confirm the controller
frames are right before blaming the solver.

Run it alongside the VR stack, with ik_node stopped or running:

    ros2 run kinematics pose_viz

then open the viewer URL it prints (meshcat, usually http://127.0.0.1:7000).
The robot is drawn from /joint_states for spatial reference; set show_robot
to false for frames on their own.
"""

from __future__ import annotations

import numpy as np
import placo
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from placo_utils.visualization import frame_viz, get_viewer, robot_viz
from scipy.spatial.transform import Rotation as R
from geometry_msgs.msg import PoseStamped
from sensor_msgs.msg import JointState

from kinematics.ik_node import ARM_CONFIGS, DAKSHA_URDF_PATH


class PoseViz(Node):
    """Mirrors the incoming target poses into meshcat as coordinate frames."""

    def __init__(self):
        super().__init__("pose_viz")

        requested = self.declare_parameter("arms", ["left", "right"]).value
        self.arms = [arm for arm in requested if arm in ARM_CONFIGS] or ["left", "right"]

        self.show_robot = self.declare_parameter("show_robot", True).value
        self.frame_scale = self.declare_parameter("frame_scale", 1.0).value
        self.log_period_sec = self.declare_parameter("log_period_sec", 1.0).value
        draw_rate = self.declare_parameter("draw_rate", 30.0).value

        # Latest pose per arm as a 4x4, redrawn on a timer rather than on every
        # message: the poses arrive at 100 Hz and each frame is three meshcat
        # transforms, which the viewer does not need to see that often.
        self.poses: dict[str, np.ndarray] = {}
        self._last_log = 0.0

        get_viewer()

        self.viz = None
        self.robot = None
        if self.show_robot:
            self.robot = placo.RobotWrapper(DAKSHA_URDF_PATH)
            self.viz = robot_viz(self.robot, "pose_viz_robot")
            self.create_subscription(JointState, "/joint_states", self.joint_cb, 10)

        for arm in self.arms:
            self.create_subscription(
                PoseStamped, f"/{arm}/pose",
                lambda msg, a=arm: self.pose_cb(a, msg), 10,
            )

        self.create_timer(1.0 / draw_rate, self.draw_cb)

        self.get_logger().info(
            f"pose_viz drawing {', '.join(f'/{a}/pose' for a in self.arms)} "
            f"(robot {'shown' if self.show_robot else 'hidden'})"
        )

    # -----------------------
    def pose_cb(self, arm: str, msg: PoseStamped) -> None:
        T = np.eye(4)
        T[:3, :3] = R.from_quat([
            msg.pose.orientation.x,
            msg.pose.orientation.y,
            msg.pose.orientation.z,
            msg.pose.orientation.w,
        ]).as_matrix()
        T[:3, 3] = [msg.pose.position.x, msg.pose.position.y, msg.pose.position.z]
        self.poses[arm] = T

    def joint_cb(self, msg: JointState) -> None:
        model_joints = set(self.robot.joint_names())
        for name, position in zip(msg.name, msg.position):
            if name in model_joints:
                self.robot.set_joint(name, float(position))
        self.robot.update_kinematics()

    # -----------------------
    def draw_cb(self) -> None:
        for arm, T in self.poses.items():
            frame_viz(f"{arm}_target", T, scale=self.frame_scale)

        if self.viz is not None:
            self.viz.display(self.robot.state.q)

        self._log_poses()

    def _log_poses(self) -> None:
        if self.log_period_sec <= 0.0:
            return

        now = self.get_clock().now().nanoseconds * 1e-9
        if now - self._last_log < self.log_period_sec:
            return
        self._last_log = now

        if not self.poses:
            self.get_logger().warn(
                "no poses received yet on "
                f"{', '.join(f'/{a}/pose' for a in self.arms)}",
                throttle_duration_sec=5.0,
            )
            return

        for arm, T in sorted(self.poses.items()):
            rpy = R.from_matrix(T[:3, :3]).as_euler("xyz", degrees=True)
            self.get_logger().info(
                f"{arm}  xyz={np.array2string(T[:3, 3], precision=3, suppress_small=True)}"
                f"  rpy={np.array2string(rpy, precision=1, suppress_small=True)}"
            )


def main():
    rclpy.init()
    node = PoseViz()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
