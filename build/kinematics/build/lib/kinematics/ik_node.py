"""ROS2 node wrapping ArmIKSolver for single-arm or dual-arm teleop.

Which arm(s) run is controlled by the 'arms' parameter, e.g.:
    ros2 run kinematics ik_node --ros-args -p arms:="['left']"        # single arm
    ros2 run kinematics ik_node --ros-args -p arms:="['left','right']"  # dual arm (default)
"""

from __future__ import annotations

import math
import os
import threading

import numpy as np
import placo
import rclpy
from ament_index_python.packages import get_package_share_directory
from rclpy.callback_groups import MutuallyExclusiveCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from placo_utils.visualization import robot_viz, frame_viz
from scipy.spatial.transform import Rotation as R
from geometry_msgs.msg import PoseStamped
from rcl_interfaces.msg import SetParametersResult
from sensor_msgs.msg import JointState, Joy

from kinematics.arm_ik_solver import ArmIKSolver, RobotConfig

DAKSHA_URDF_PATH = os.path.join(
    get_package_share_directory("daksha_description_full_body"), "urdf", "robot.urdf"
)

DAKSHA_LEFT_CONFIG = RobotConfig(
    urdf_path=DAKSHA_URDF_PATH,
    tcp_frame="left_tcp",
    joint_names=[f"left_joint_{i}" for i in range(1, 8)],
    base_offset=np.array([0.0, 0.0, 0.0]),
    gripper_joint=None,
)

DAKSHA_RIGHT_CONFIG = RobotConfig(
    urdf_path=DAKSHA_URDF_PATH,
    tcp_frame="right_tcp",
    joint_names=[f"right_joint_{i}" for i in range(1, 8)],
    base_offset=np.array([0.0, 0.0, 0.0]),
    gripper_joint=None,
)

ARM_CONFIGS = {"left": DAKSHA_LEFT_CONFIG, "right": DAKSHA_RIGHT_CONFIG}

REAL_JOINT_NAMES = {
    "left": DAKSHA_LEFT_CONFIG.joint_names,
    "right": DAKSHA_RIGHT_CONFIG.joint_names,
}


def _quat_multiply(q1, q2):
    x1, y1, z1, w1 = q1
    x2, y2, z2, w2 = q2

    return [
        w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
        w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
        w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2,
        w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2,
    ]


def _build_correction_quaternion() -> list[float]:
    """Fixed Quest -> ROS frame correction: +90 deg about X, +180 deg about Z."""
    qx_90 = [math.sin(math.pi / 4), 0.0, 0.0, math.cos(math.pi / 4)]
    qz_180 = [0.0, 0.0, math.sin(math.pi / 2), math.cos(math.pi / 2)]
    return _quat_multiply(qz_180, qx_90)


def _build_offset_quaternion() -> list[float]:
    angle_x = math.radians(-90.0)
    angle_y = math.radians(90.0)
    angle_z = math.radians(0.0)

    x_offset = [math.sin(angle_x / 2), 0.0, 0.0, math.cos(angle_x / 2)]
    y_offset = [0.0, math.sin(angle_y / 2), 0.0, math.cos(angle_y / 2)]
    z_offset = [0.0, 0.0, math.sin(angle_z / 2), math.cos(angle_z / 2)]
    return _quat_multiply(z_offset, _quat_multiply(y_offset, x_offset))


Q_CORRECTION = _build_correction_quaternion()
Q_OFFSET = _build_offset_quaternion()

# Per-arm orientation trim defaults: offset (deg) added to each axis, and a
# direction multiplier (1.0 = clockwise/as-received, -1.0 = anticlockwise/inverted).
# Edit left/right independently here.
ARM_ORIENTATION_DEFAULTS = {
    "left": {
        "roll_offset_deg": 0.0,
        "pitch_offset_deg": 0.0,
        "yaw_offset_deg": -90.0,
        "roll_dir": -1.0,
        "pitch_dir": 1.0,
        "yaw_dir": -1.0,
    },
    "right": {
        "roll_offset_deg": 0.0,
        "pitch_offset_deg": 0.0,
        "yaw_offset_deg": 90.0,
        "roll_dir": 1.0,
        "pitch_dir": -1.0,
        "yaw_dir": -1.0,
    },
}


class _ArmContext:
    """Per-arm ROS wiring: solver instance + subscriptions + gripper state.

    Each arm gets its own MutuallyExclusiveCallbackGroup so, combined with a
    MultiThreadedExecutor, both arms' pose/joy callbacks run concurrently on
    separate threads instead of serializing behind one another.
    """

    def __init__(self, node: "DualArmIK", arm: str):
        self.arm = arm
        self.config = ARM_CONFIGS[arm]
        if node.collision_urdf_path:
            # Same kinematics, primitive collision geometry. Swapped in only
            # for the solver: the visualiser keeps the mesh URDF, so nothing
            # on screen changes.
            self.config = RobotConfig(
                urdf_path=node.collision_urdf_path,
                tcp_frame=self.config.tcp_frame,
                joint_names=self.config.joint_names,
                base_offset=self.config.base_offset,
                gripper_joint=self.config.gripper_joint,
            )
        self.solver = ArmIKSolver(
            self.config,
            collision_pairs_path=node.collision_pairs_path,
            self_collision_margin=node.self_collision_margin,
            self_collision_trigger=node.self_collision_trigger,
        )
        self.enabled = False
        self.gripper = 0.1

        # Per-arm orientation trim, hardcoded in ARM_ORIENTATION_DEFAULTS above.
        defaults = ARM_ORIENTATION_DEFAULTS[arm]
        self.roll_offset_deg = defaults["roll_offset_deg"]
        self.pitch_offset_deg = defaults["pitch_offset_deg"]
        self.yaw_offset_deg = defaults["yaw_offset_deg"]
        self.roll_dir = defaults["roll_dir"]
        self.pitch_dir = defaults["pitch_dir"]
        self.yaw_dir = defaults["yaw_dir"]

        callback_group = MutuallyExclusiveCallbackGroup()

        node.create_subscription(
            PoseStamped, f"/{arm}/pose",
            lambda msg, ctx=self: node.pose_cb(ctx, msg), 10,
            callback_group=callback_group,
        )
        node.create_subscription(
            Joy, f"/quest/{arm}/joy",
            lambda msg, ctx=self: node.joy_cb(ctx, msg), 10,
            callback_group=callback_group,
        )

    def correct_orientation(self, orientation_xyzw, swap_roll_pitch: bool) -> list[float]:
        """Quest -> robot axis correction for this arm: roll/pitch swap + per-axis direction/trim, then fixed remap."""
        yaw_in, pitch_in, roll_in = R.from_quat(orientation_xyzw).as_euler("zyx", degrees=False)

        if swap_roll_pitch:
            roll_in, pitch_in = pitch_in, roll_in

        yaw = self.yaw_dir * yaw_in + math.radians(self.yaw_offset_deg)
        pitch = self.pitch_dir * pitch_in + math.radians(self.pitch_offset_deg)
        roll = self.roll_dir * roll_in + math.radians(self.roll_offset_deg)

        quat = R.from_euler("zyx", [yaw, pitch, roll], degrees=False).as_quat()

        q_corr = _quat_multiply(Q_CORRECTION, list(quat))
        return _quat_multiply(Q_OFFSET, q_corr)


class DualArmIK(Node):
    """Single-arm or dual-arm IK node (arm count set by the 'arms' parameter)."""

    def __init__(self):
        super().__init__('dual_arm_ik')

        self.declare_parameter('real_arm', True)
        self.real_arm = self.get_parameter('real_arm').get_parameter_value().bool_value

        self.declare_parameter('arms', ['left', 'right'])
        requested_arms = self.get_parameter('arms').get_parameter_value().string_array_value
        arms = [arm for arm in requested_arms if arm in ARM_CONFIGS] or ['left', 'right']

        self.declare_parameter('swap_roll_pitch', True)
        self.swap_roll_pitch = self.get_parameter('swap_roll_pitch').get_parameter_value().bool_value

        # Self-collision avoidance. Needs two generated artifacts, both of
        # which must come from the SAME geometry or the pair list will
        # describe a model the solver isn't using:
        #   robot_collision.urdf  - gen_collision_primitives.py
        #   collision_pairs.json  - gen_collision_pairs.py (an allowlist)
        # Fitting collision geometry to the visual meshes instead costs
        # ~133 ms/solve (~8 Hz); primitives bring it to well under a
        # millisecond.
        self.declare_parameter('collision_avoidance', True)
        self.declare_parameter('collision_pairs_file', '')
        self.declare_parameter('collision_urdf_file', '')
        self.declare_parameter('self_collision_margin', 0.02)
        self.declare_parameter('self_collision_trigger', 0.05)

        self.self_collision_margin = self.get_parameter(
            'self_collision_margin').get_parameter_value().double_value
        self.self_collision_trigger = self.get_parameter(
            'self_collision_trigger').get_parameter_value().double_value

        self.collision_pairs_path = None
        self.collision_urdf_path = None
        if self.get_parameter('collision_avoidance').get_parameter_value().bool_value:
            pairs = self.get_parameter(
                'collision_pairs_file').get_parameter_value().string_value
            if not pairs:
                pairs = os.path.join(
                    get_package_share_directory("kinematics"),
                    "config", "collision_pairs.json",
                )
            urdf = self.get_parameter(
                'collision_urdf_file').get_parameter_value().string_value
            if not urdf:
                urdf = os.path.join(
                    get_package_share_directory("daksha_description_full_body"),
                    "urdf", "robot_collision.urdf",
                )

            missing = [p for p in (pairs, urdf) if not os.path.exists(p)]
            if missing:
                # Refuse rather than silently fall back to the mesh URDF:
                # that path runs at ~8 Hz and the arm visibly lags, which is
                # far more confusing than an explicit error.
                self.get_logger().error(
                    f"[collision] collision_avoidance is on but missing: {missing}. "
                    f"Running WITHOUT it. Regenerate with "
                    f"kinematics/scripts/gen_collision_primitives.py and "
                    f"gen_collision_pairs.py --urdf <robot_collision.urdf>"
                )
            else:
                self.collision_pairs_path = pairs
                self.collision_urdf_path = urdf
                self.get_logger().info(
                    "[collision] self-collision avoidance ON (primitive geometry)"
                )
        else:
            self.get_logger().info("[collision] self-collision avoidance OFF")

        self.alpha_grip = 0.2
        self.pos_offset = np.zeros(3)

        self.arm_ctx = {arm: _ArmContext(self, arm) for arm in arms}
        self._publish_lock = threading.Lock()

        viz_config = ARM_CONFIGS[arms[0]]
        self.viz_robot = placo.RobotWrapper(viz_config.urdf_path)
        self.viz = robot_viz(self.viz_robot, "dual_arm_final")

        self.pub_all = self.create_publisher(JointState, "/joint_states", 10)
        self.pub_joint_cmd = self.create_publisher(JointState, "/joint_cmd", 10)

        self.declare_parameter('posture_enabled', True)
        self.posture_enabled = self.get_parameter('posture_enabled').get_parameter_value().bool_value
        for ctx in self.arm_ctx.values():
            ctx.solver.set_posture_enabled(self.posture_enabled)

        self.declare_parameter('collision_enabled', self.collision_pairs_path is not None)
        self.collision_enabled = self.get_parameter('collision_enabled').get_parameter_value().bool_value
        for ctx in self.arm_ctx.values():
            ctx.solver.set_collision_avoidance_enabled(self.collision_enabled)

        self.add_on_set_parameters_callback(self.dynamic_parameter_cb)

        print(f"IK STARTED for arms: {arms}")

    # -----------------------
    def dynamic_parameter_cb(self, params):
        for p in params:

            if p.name == 'posture_enabled':
                self.posture_enabled = p.value
                for ctx in self.arm_ctx.values():
                    ctx.solver.set_posture_enabled(p.value)

                state = "enabled" if p.value else "disabled"
                self.get_logger().info(f"[DEBUG] posture bias -> {state}")

            elif p.name == 'collision_enabled':
                if p.value and self.collision_pairs_path is None:
                    return SetParametersResult(
                        successful=False,
                        reason="collision avoidance unavailable: no pair allowlist "
                               "was loaded at startup (missing generated artifacts)",
                    )

                applied = all(
                    ctx.solver.set_collision_avoidance_enabled(p.value)
                    for ctx in self.arm_ctx.values()
                )
                if not applied:
                    return SetParametersResult(successful=False, reason="collision toggle failed")

                self.collision_enabled = p.value
                state = "enabled" if p.value else "disabled"
                self.get_logger().info(f"[DEBUG] self-collision avoidance -> {state}")

        return SetParametersResult(successful=True)

    # -----------------------
    def joy_cb(self, ctx: _ArmContext, msg):
        trigger = msg.axes[2]
        if trigger < 0:
            trigger = (trigger + 1) / 2

        target = 0.1 * (1 - trigger)
        ctx.gripper = (1 - self.alpha_grip) * ctx.gripper + self.alpha_grip * target

        was_enabled = ctx.enabled
        ctx.enabled = len(msg.axes) > 3 and msg.axes[3] > 0.5
        if ctx.enabled != was_enabled:
            self.get_logger().info(f"[DEBUG] {ctx.arm} enabled -> {ctx.enabled}  axes={list(msg.axes)}")
        self.publish()

    def pose_cb(self, ctx: _ArmContext, msg):
        if not ctx.enabled:
            return   # STOP IK

        position = [msg.pose.position.x, msg.pose.position.y, msg.pose.position.z]
        orientation = [
            msg.pose.orientation.x,
            msg.pose.orientation.y,
            msg.pose.orientation.z,
            msg.pose.orientation.w,
        ]
        corrected_orientation = ctx.correct_orientation(orientation, self.swap_roll_pitch)

        self._mirror_other_arms(ctx)

        try:
            _, _, _, T, fk_pose = ctx.solver.process(position, corrected_orientation, self.pos_offset)
        except RuntimeError as exc:
            self.get_logger().warn(f"{ctx.arm} IK solve failed, skipping frame: {exc}")
            return

        self._visualize_target_frames(ctx.arm, T, fk_pose)

        self.publish()

    # -----------------------
    def _visualize_target_frames(self, arm: str, desired_pose: np.ndarray, fk_pose: np.ndarray) -> None:
        for suffix, pose in ("target", desired_pose), ("fk", fk_pose):
            try:
                frame_viz(f"{arm}_{suffix}", pose)
            except Exception as exc:
                self.get_logger().warn(
                    f"{arm} {suffix} frame visualization failed: {exc}"
                )

    def _mirror_other_arms(self, ctx: _ArmContext) -> None:
        """Write the other arms' current joint values into this arm's model.

        Each _ArmContext owns a separate placo RobotWrapper. They all load
        the same full-body URDF, so the opposite arm's geometry exists in
        every model - but only the arm a given solver drives is ever
        updated. The others sit at their load-time defaults forever.

        For the end-effector task that is harmless. For self-collision it is
        not: the left solver would steer around a right arm parked wherever
        the URDF left it, which is worse than no protection because it looks
        like protection while avoiding a phantom. Only needed when the
        constraint is active, so the no-collision path stays exactly as fast
        as before.
        """
        if not ctx.solver.kin.collision_avoidance:
            return

        robot = ctx.solver.kin.robot
        for other_arm, other in self.arm_ctx.items():
            if other_arm == ctx.arm:
                continue
            for i, name in enumerate(other.solver.kin.joint_names):
                robot.set_joint(name, float(np.deg2rad(other.solver.q[i])))

    def _sync_viz_robot(self) -> None:
        for name in self.viz_robot.joint_names():
            for ctx in self.arm_ctx.values():
                if name in ctx.solver.kin.joint_names:
                    idx = ctx.solver.kin.joint_names.index(name)
                    self.viz_robot.set_joint(name, np.deg2rad(ctx.solver.q[idx]))
                    break
        self.viz_robot.update_kinematics()

    # -----------------------
    def publish(self):
        with self._publish_lock:
            now = self.get_clock().now().to_msg()
            self._sync_viz_robot()

            all_names: list[str] = []
            all_positions: list[float] = []

            for arm, ctx in self.arm_ctx.items():
                js = JointState()
                js.header.stamp = now

                if self.real_arm:
                    js.name = REAL_JOINT_NAMES[arm]
                    positions = list(np.deg2rad(ctx.solver.q))
                    if ctx.config.gripper_joint:
                        positions.append(float(ctx.gripper))
                else:
                    # SIMULATION MODE
                    js.name = [str(n) for n in ctx.solver.kin.joint_names]
                    positions = list(np.deg2rad(ctx.solver.q))

                js.position = positions

                all_names += js.name
                all_positions += js.position

            js_all = JointState()
            js_all.header.stamp = now
            js_all.name = all_names
            js_all.position = all_positions
            self.pub_all.publish(js_all)
            self.pub_joint_cmd.publish(js_all)

            # VISUALIZATION
            self.viz.display(self.viz_robot.state.q)


def main():
    rclpy.init()
    node = DualArmIK()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
