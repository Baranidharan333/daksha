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


# Orientation pipeline stages, cheapest first. See config/orientation.yaml.
#   passthrough - incoming quaternion used as the target rotation, unchanged
#   fixed       - one explicit rotation: R_corr * R_in
#   trim        - roll/pitch swap + per-axis direction/offset, then the
#                 correction and offset rotations
ORIENTATION_MODES = ("passthrough", "fixed", "trim")

# Fallbacks for everything in config/orientation.yaml, used when the node runs
# without that params file. Keep the two in sync.
ORIENTATION_DEFAULTS = {
    "mode": "passthrough",
    "swap_roll_pitch": True,
    "fixed.rotation_deg": [90.0, 0.0, 180.0],
    "fixed.sequence": "xyz",
    "trim.correction_deg": [90.0, 0.0, 180.0],
    "trim.offset_deg": [-90.0, 90.0, 0.0],
}

# Per-arm trim defaults: offset (deg) added to each axis, and a direction
# multiplier (1.0 = as received, -1.0 = inverted). Overridden per arm by
# orientation.<arm>.* in config/orientation.yaml.
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

TRIM_KEYS = tuple(ARM_ORIENTATION_DEFAULTS["left"].keys())


class _OrientationConfig:
    """The node-wide half of the orientation pipeline, as live ROS parameters.

    Everything here can be changed with `ros2 param set` while the node runs -
    the fixed rotations are rebuilt on each change so the next incoming pose
    uses them. Per-arm trim lives on _ArmContext instead.
    """

    def __init__(self, node: Node) -> None:
        d = ORIENTATION_DEFAULTS
        self.mode = node.declare_parameter('orientation.mode', d["mode"]).value
        self.swap_roll_pitch = node.declare_parameter(
            'orientation.swap_roll_pitch', d["swap_roll_pitch"]).value
        self.fixed_rotation_deg = list(node.declare_parameter(
            'orientation.fixed.rotation_deg', d["fixed.rotation_deg"]).value)
        self.fixed_sequence = node.declare_parameter(
            'orientation.fixed.sequence', d["fixed.sequence"]).value
        self.correction_deg = list(node.declare_parameter(
            'orientation.trim.correction_deg', d["trim.correction_deg"]).value)
        self.offset_deg = list(node.declare_parameter(
            'orientation.trim.offset_deg', d["trim.offset_deg"]).value)

        if self.mode not in ORIENTATION_MODES:
            node.get_logger().error(
                f"[orientation] unknown mode '{self.mode}', falling back to "
                f"'{d['mode']}' (valid: {', '.join(ORIENTATION_MODES)})"
            )
            self.mode = d["mode"]

        self.rebuild()

    def rebuild(self) -> None:
        """Recompute the fixed rotations from the current angle parameters."""
        self.r_fixed = R.from_euler(self.fixed_sequence, self.fixed_rotation_deg, degrees=True)
        # Extrinsic xyz, i.e. Rz @ Ry @ Rx - the convention the previously
        # hardcoded Q_CORRECTION / Q_OFFSET quaternions were built in.
        r_correction = R.from_euler("xyz", self.correction_deg, degrees=True)
        r_offset = R.from_euler("xyz", self.offset_deg, degrees=True)
        # Applied as offset * correction * q_trimmed.
        self.r_trim_post = r_offset * r_correction

    def apply(self, name: str, value) -> str | None:
        """Apply one orientation.* parameter. Returns an error message, or None on success."""
        # Snapshot so a value that only fails inside rebuild() (a bad Euler
        # sequence, say) leaves the node on its previous, working settings.
        previous = (
            self.mode, self.swap_roll_pitch, list(self.fixed_rotation_deg),
            self.fixed_sequence, list(self.correction_deg), list(self.offset_deg),
        )

        if name == 'orientation.mode':
            if value not in ORIENTATION_MODES:
                return f"orientation.mode must be one of {', '.join(ORIENTATION_MODES)}"
            self.mode = value
        elif name == 'orientation.swap_roll_pitch':
            self.swap_roll_pitch = value
        elif name == 'orientation.fixed.rotation_deg':
            if len(value) != 3:
                return "orientation.fixed.rotation_deg needs 3 angles"
            self.fixed_rotation_deg = list(value)
        elif name == 'orientation.fixed.sequence':
            self.fixed_sequence = value
        elif name == 'orientation.trim.correction_deg':
            if len(value) != 3:
                return "orientation.trim.correction_deg needs 3 angles"
            self.correction_deg = list(value)
        elif name == 'orientation.trim.offset_deg':
            if len(value) != 3:
                return "orientation.trim.offset_deg needs 3 angles"
            self.offset_deg = list(value)
        else:
            return f"unknown orientation parameter '{name}'"

        try:
            self.rebuild()
        except ValueError as exc:
            (self.mode, self.swap_roll_pitch, self.fixed_rotation_deg,
             self.fixed_sequence, self.correction_deg, self.offset_deg) = previous
            self.rebuild()
            return f"invalid rotation ({exc})"
        return None


class _ArmContext:
    """Per-arm ROS wiring: solver instance + subscriptions + gripper state.

    Each arm gets its own MutuallyExclusiveCallbackGroup so, combined with a
    MultiThreadedExecutor, both arms' pose/joy callbacks run concurrently on
    separate threads instead of serializing behind one another.
    """

    def __init__(self, node: "DualArmIK", arm: str):
        self.node = node
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
            orientation_weight=node.orientation_weight,
            alpha_pos=node.alpha_pos,
            alpha_rot=node.alpha_rot,
            use_ref_rot=node.apply_ref_rot,
            collision_pairs_path=node.collision_pairs_path,
            self_collision_margin=node.self_collision_margin,
            self_collision_trigger=node.self_collision_trigger,
        )
        self.enabled = False
        self.gripper = 0.1

        # Per-arm orientation trim: live parameters orientation.<arm>.<key>,
        # defaulting to ARM_ORIENTATION_DEFAULTS when no params file is given.
        for key, default in ARM_ORIENTATION_DEFAULTS[arm].items():
            value = node.declare_parameter(f'orientation.{arm}.{key}', default).value
            setattr(self, key, value)

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

    def set_trim(self, key: str, value: float) -> str | None:
        """Apply one orientation.<arm>.* parameter. Returns an error message, or None."""
        if key not in TRIM_KEYS:
            return f"unknown orientation trim '{key}' (valid: {', '.join(TRIM_KEYS)})"
        setattr(self, key, value)
        return None

    def correct_orientation(self, orientation_xyzw) -> list[float]:
        """Quest -> robot orientation conversion for this arm.

        Which transformations run is set by orientation.mode: 'passthrough'
        applies none, 'fixed' applies a single explicit rotation, 'trim' runs
        the full per-axis trim plus correction/offset rotations. See
        config/orientation.yaml.
        """
        orient = self.node.orient
        # from_quat normalizes, so passthrough still returns a unit quaternion.
        r_in = R.from_quat(orientation_xyzw)

        if orient.mode == "passthrough":
            return r_in.as_quat().tolist()

        if orient.mode == "fixed":
            return (orient.r_fixed * r_in).as_quat().tolist()

        yaw_in, pitch_in, roll_in = r_in.as_euler("zyx", degrees=False)

        if orient.swap_roll_pitch:
            roll_in, pitch_in = pitch_in, roll_in

        yaw = self.yaw_dir * yaw_in + math.radians(self.yaw_offset_deg)
        pitch = self.pitch_dir * pitch_in + math.radians(self.pitch_offset_deg)
        roll = self.roll_dir * roll_in + math.radians(self.roll_offset_deg)

        r_trim = R.from_euler("zyx", [yaw, pitch, roll], degrees=False)
        return (orient.r_trim_post * r_trim).as_quat().tolist()


class DualArmIK(Node):
    """Single-arm or dual-arm IK node (arm count set by the 'arms' parameter)."""

    def __init__(self):
        super().__init__('dual_arm_ik')

        self.declare_parameter('real_arm', True)
        self.real_arm = self.get_parameter('real_arm').get_parameter_value().bool_value

        self.declare_parameter('arms', ['left', 'right'])
        requested_arms = self.get_parameter('arms').get_parameter_value().string_array_value
        arms = [arm for arm in requested_arms if arm in ARM_CONFIGS] or ['left', 'right']

        # Orientation pipeline + solver tuning. Defaults here match
        # config/orientation.yaml; pass that file to override them, and
        # `ros2 param set` to retune any of it while the node runs.
        self.orient = _OrientationConfig(self)

        self.apply_ref_rot = self.declare_parameter('solver.apply_ref_rot', False).value
        self.alpha_pos = self.declare_parameter('solver.alpha_pos', 0.8).value
        self.alpha_rot = self.declare_parameter('solver.alpha_rot', 0.3).value
        self.orientation_weight = self.declare_parameter('solver.orientation_weight', 1.0).value

        self.debug_euler = self.declare_parameter('debug.log_euler', False).value
        self.debug_period = self.declare_parameter('debug.log_period_sec', 0.5).value
        self._last_debug_log: dict[str, float] = {}

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

            if p.name.startswith('orientation.'):
                error = self._apply_orientation_param(p)
                if error:
                    return SetParametersResult(successful=False, reason=error)
                self.get_logger().info(f"[DEBUG] {p.name} -> {p.value}")

            elif p.name.startswith('solver.'):
                error = self._apply_solver_param(p)
                if error:
                    return SetParametersResult(successful=False, reason=error)
                self.get_logger().info(f"[DEBUG] {p.name} -> {p.value}")

            elif p.name == 'debug.log_euler':
                self.debug_euler = p.value

            elif p.name == 'debug.log_period_sec':
                self.debug_period = p.value

            elif p.name == 'posture_enabled':
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

    def _apply_orientation_param(self, p) -> str | None:
        """Route one orientation.* parameter to the node config or to an arm's trim."""
        _, section, *rest = p.name.split('.')

        if section in ARM_CONFIGS:
            ctx = self.arm_ctx.get(section)
            if ctx is None:
                # Trim for an arm this node isn't running: accept and ignore,
                # so one params file can serve single- and dual-arm setups.
                return None
            return ctx.set_trim('.'.join(rest), p.value)

        return self.orient.apply(p.name, p.value)

    def _apply_solver_param(self, p) -> str | None:
        """Route one solver.* parameter to every arm's solver."""
        attribute = {
            'solver.apply_ref_rot': 'use_ref_rot',
            'solver.alpha_pos': 'alpha_pos',
            'solver.alpha_rot': 'alpha_rot',
            'solver.orientation_weight': 'orientation_weight',
        }.get(p.name)

        if attribute is None:
            return f"unknown solver parameter '{p.name}'"

        setattr(self, p.name.split('.', 1)[1], p.value)
        for ctx in self.arm_ctx.values():
            setattr(ctx.solver, attribute, p.value)
        return None

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
        corrected_orientation = ctx.correct_orientation(orientation)

        self._mirror_other_arms(ctx)

        try:
            _, _, _, T, fk_pose = ctx.solver.process(position, corrected_orientation, self.pos_offset)
        except RuntimeError as exc:
            self.get_logger().warn(f"{ctx.arm} IK solve failed, skipping frame: {exc}")
            return

        self._log_orientation_debug(ctx, orientation, corrected_orientation, T)
        self._visualize_target_frames(ctx.arm, T, fk_pose)

        self.publish()

    # -----------------------
    def _log_orientation_debug(self, ctx: _ArmContext, raw, corrected, T: np.ndarray) -> None:
        """Print RAW / CORRECTED / TARGET Euler angles for one arm, rate-limited.

        The three stages of the pipeline side by side: what the controller
        sent, what correct_orientation made of it, and what the solver was
        actually asked to reach (which includes ref_rot and the slerp).
        """
        if not self.debug_euler:
            return

        now = self.get_clock().now().nanoseconds * 1e-9
        if now - self._last_debug_log.get(ctx.arm, 0.0) < self.debug_period:
            return
        self._last_debug_log[ctx.arm] = now

        def euler(rotation) -> str:
            return np.array2string(
                rotation.as_euler("xyz", degrees=True), precision=1, suppress_small=True
            )

        self.get_logger().info(
            f"[orientation:{self.orient.mode}] {ctx.arm} "
            f"RAW={euler(R.from_quat(raw))} "
            f"CORRECTED={euler(R.from_quat(corrected))} "
            f"TARGET={euler(R.from_matrix(T[:3, :3]))}"
        )

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
