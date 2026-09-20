"""Per-arm IK solver (pure Python, no ROS dependency).

Wraps placo-based kinematics with pose filtering, escape search, and
velocity/acceleration limiting for a single arm. Instantiate one of these
for a single-arm setup, or two (e.g. left/right) for a dual-arm setup.
"""

from __future__ import annotations

import math

import numpy as np
import placo
from scipy.spatial.transform import Rotation as R


class RobotConfig:
    """Configuration bundle that encapsulates URDF/tcp/joint metadata."""

    def __init__(
        self,
        urdf_path: str,
        tcp_frame: str,
        joint_names: list[str],
        base_offset: np.ndarray,
        gripper_joint: str | None = None,
    ) -> None:
        self.urdf_path = urdf_path
        self.tcp_frame = tcp_frame
        self.joint_names = joint_names
        self.base_offset = base_offset
        self.gripper_joint = gripper_joint


class RobotKinematics:
    """Robot kinematics using placo library for forward and inverse kinematics."""

    def __init__(
        self,
        urdf_path: str,
        target_frame_name: str = "gripper_frame_link",
        joint_names: list[str] | None = None,
        posture_joints_deg: np.ndarray | None = None,
        posture_weight: float = 0.01,
        collision_pairs_path: str | None = None,
        self_collision_margin: float = 0.02,
        self_collision_trigger: float = 0.05,
    ):
        """
        Initialize placo-based kinematics solver.

        Args:
            urdf_path (str): Path to the robot URDF file
            target_frame_name (str): Name of the end-effector frame in the URDF
            joint_names (list[str] | None): List of joint names to use for the kinematics solver
            posture_joints_deg (np.ndarray | None): Neutral/human-like joint angles (degrees) that
                the redundant DOFs relax toward when the EE task doesn't fully constrain them.
                Defaults to the zero configuration.
            posture_weight (float): Weight of the posture task relative to the EE frame task's
                weight of 1.0. Kept small so posture never fights the EE target.
        """
        self.robot = placo.RobotWrapper(urdf_path)

        # Must run before the solver is built: load_collision_pairs replaces
        # the model's entire pair set (it is an ALLOWLIST, not a list of
        # exclusions), and the constraint reads that set when it is added.
        # Without it placo checks all 268 pairs of this model - including
        # parent/child links, which overlap at their shared joint by
        # construction and would make the constraint unsatisfiable.
        self.collision_avoidance = False
        self.self_collision_constraint = None
        # Whether the pair allowlist got loaded, i.e. whether the constraint
        # can be (re)added at all. The allowlist itself isn't reloadable, so
        # this stays fixed for the solver's lifetime even as the constraint
        # is toggled on/off.
        self._collision_pairs_available = bool(collision_pairs_path)
        self._self_collision_margin = self_collision_margin
        self._self_collision_trigger = self_collision_trigger
        if collision_pairs_path:
            self.robot.load_collision_pairs(collision_pairs_path)

        self.solver = placo.KinematicsSolver(self.robot)
        self.solver.mask_fbase(True)

        # Free, and correct regardless of collision avoidance: keeps the
        # solver inside the URDF's joint limits instead of returning poses
        # the hardware cannot reach.
        self.solver.enable_joint_limits(True)

        if collision_pairs_path:
            self._add_self_collision_constraint()
            self.collision_avoidance = True

        self.target_frame_name = target_frame_name
        self.joint_names = list(self.robot.joint_names()) if joint_names is None else joint_names

        self.tip_frame = self.solver.add_frame_task(self.target_frame_name, np.eye(4))
        self.tip_frame.configure(self.target_frame_name, "soft", 1.0, 0.0)

        posture_rad = (
            np.zeros(len(self.joint_names))
            if posture_joints_deg is None
            else np.deg2rad(posture_joints_deg[: len(self.joint_names)])
        )
        self.posture_task = self.solver.add_joints_task()
        self.posture_task.set_joints(
            {name: posture_rad[i] for i, name in enumerate(self.joint_names)}
        )
        self.posture_task.configure("posture", "soft", posture_weight)

    def set_posture_weight(self, weight: float) -> None:
        """Reconfigure the posture task's weight at runtime (0.0 disables it)."""
        self.posture_task.configure("posture", "soft", weight)

    def _add_self_collision_constraint(self) -> None:
        self.self_collision_constraint = self.solver.add_avoid_self_collisions_constraint()
        # margin  - separation the constraint drives pairs toward
        # trigger - distance at which it starts acting at all
        self.self_collision_constraint.self_collisions_margin = self._self_collision_margin
        self.self_collision_constraint.self_collisions_trigger = self._self_collision_trigger

    def set_collision_avoidance_enabled(self, enabled: bool) -> bool:
        """Toggle the self-collision constraint on/off at runtime.

        Requires the pair allowlist to have been loaded at construction
        (collision_pairs_path given) - that part isn't reloadable, only the
        constraint enforcing it can be added/removed. Returns whether the
        request could be applied.
        """
        if not self._collision_pairs_available:
            return False

        if enabled == self.collision_avoidance:
            return True

        if enabled:
            self._add_self_collision_constraint()
        else:
            self.solver.remove_constraint(self.self_collision_constraint)
            self.self_collision_constraint = None

        self.collision_avoidance = enabled
        return True

    def forward_kinematics(self, joint_pos_deg: np.ndarray) -> np.ndarray:
        """Compute forward kinematics for the configured target frame."""

        joint_pos_rad = np.deg2rad(joint_pos_deg[: len(self.joint_names)])

        for i, joint_name in enumerate(self.joint_names):
            self.robot.set_joint(joint_name, joint_pos_rad[i])

        self.robot.update_kinematics()

        return self.robot.get_T_world_frame(self.target_frame_name)

    def inverse_kinematics(
        self,
        current_joint_pos: np.ndarray,
        desired_ee_pose: np.ndarray,
        position_weight: float = 1.0,
        orientation_weight: float = 0.01,
    ) -> np.ndarray:
        """Solve for joint positions that reach `desired_ee_pose` using Placo."""

        current_joint_rad = np.deg2rad(current_joint_pos[: len(self.joint_names)])

        for i, joint_name in enumerate(self.joint_names):
            self.robot.set_joint(joint_name, current_joint_rad[i])

        self.tip_frame.T_world_frame = desired_ee_pose
        self.tip_frame.configure(
            self.target_frame_name,
            "soft",
            position_weight,
            orientation_weight,
        )

        self.solver.solve(True)
        self.robot.update_kinematics()

        joint_pos_rad = np.array(
            [self.robot.get_joint(name) for name in self.joint_names]
        )

        joint_pos_deg = np.rad2deg(joint_pos_rad)

        if len(current_joint_pos) > len(self.joint_names):
            result = current_joint_pos.copy()
            result[: len(self.joint_names)] = joint_pos_deg
            return result

        return joint_pos_deg


class ArmIKSolver:
    """Solves IK for a single arm described by a RobotConfig."""

    def __init__(
        self,
        config: RobotConfig,
        orientation_weight: float = 0.02,
        error_threshold: float = 0.05,
        escape_attempts: int = 20,
        max_vel: float = 10.0,
        max_acc: float = 2.0,
        alpha_pos: float = 0.8,
        alpha_rot: float = 0.3,
        use_ref_rot: bool = True,
        posture_joints_deg: np.ndarray | None = None,
        posture_weight: float = 0.01,
        collision_pairs_path: str | None = None,
        self_collision_margin: float = 0.02,
        self_collision_trigger: float = 0.05,
    ) -> None:
        self.config = config
        self.kin = RobotKinematics(
            config.urdf_path,
            config.tcp_frame,
            config.joint_names,
            posture_joints_deg=posture_joints_deg,
            posture_weight=posture_weight,
            collision_pairs_path=collision_pairs_path,
            self_collision_margin=self_collision_margin,
            self_collision_trigger=self_collision_trigger,
        )
        self.robot = self.kin.robot

        self._posture_weight = posture_weight
        self.set_posture_enabled(True)

        self.orientation_weight = orientation_weight
        self.error_threshold = error_threshold
        self.escape_attempts = escape_attempts
        self.max_vel = max_vel
        self.max_acc = max_acc
        self.alpha_pos = alpha_pos
        self.alpha_rot = alpha_rot

        # When False the incoming orientation is used as the target rotation
        # directly. When True it is pre-multiplied by `ref_rot`, the TCP
        # orientation at the zero-joint configuration - an extra rotation on
        # top of whatever the controller sends, so it is worth turning off
        # while working out the correct frame conversion.
        self.use_ref_rot = use_ref_rot

        self.base_offset = config.base_offset.copy()

        self.q = np.zeros(len(self.kin.joint_names))
        self.prev_dq = np.zeros_like(self.q)
        self.filt_pos = np.zeros(3)
        self.filtered_quat = np.array([0.0, 0.0, 0.0, 1.0])

        T0 = self.kin.forward_kinematics(self.q)
        self.ref_rot = T0[:3, :3]

    # -----------------------
    def set_posture_enabled(self, enabled: bool) -> None:
        """Toggle the human-like posture bias on/off.

        Disabled: redundant joints are left purely to the IK solver (whatever
        configuration it converges to). Enabled: redundant joints relax toward
        `posture_joints_deg`, changing the arm's pose while keeping the same
        end-effector target.
        """
        self.posture_enabled = enabled
        self.kin.set_posture_weight(self._posture_weight if enabled else 0.0)

    def set_collision_avoidance_enabled(self, enabled: bool) -> bool:
        """Toggle self-collision avoidance on/off. Returns False if unavailable
        (pair allowlist was never loaded, e.g. generated artifacts were missing
        at startup)."""
        return self.kin.set_collision_avoidance_enabled(enabled)

    def solve_ik(self, T: np.ndarray):
        q_new = self.q.copy()
        for _ in range(5):
            q_new = self.kin.inverse_kinematics(
                current_joint_pos=q_new,
                desired_ee_pose=T,
                position_weight=1.0,
                orientation_weight=self.orientation_weight,
            )

        for i, name in enumerate(self.kin.joint_names):
            self.robot.set_joint(name, np.deg2rad(q_new[i]))
        self.robot.update_kinematics()
        current = self.robot.get_T_world_frame(self.config.tcp_frame)

        err = np.linalg.norm(T[:3, 3] - current[:3, 3])
        return q_new, err

    def solve_escape(self, T: np.ndarray):
        best_q = self.q.copy()
        best_err = 1e9

        for _ in range(self.escape_attempts):
            q_try = self.q + np.random.uniform(-60, 60, len(self.q))

            for _ in range(10):
                q_try = self.kin.inverse_kinematics(
                    current_joint_pos=q_try,
                    desired_ee_pose=T,
                    position_weight=1.0,
                    orientation_weight=self.orientation_weight,
                )

            for i, name in enumerate(self.kin.joint_names):
                self.robot.set_joint(name, np.deg2rad(q_try[i]))
            self.robot.update_kinematics()
            current = self.robot.get_T_world_frame(self.config.tcp_frame)

            err = np.linalg.norm(T[:3, 3] - current[:3, 3])
            if err < best_err:
                best_err = err
                best_q = q_try

        return best_q

    def vel_acc_limit(self, q_target: np.ndarray):
        dq = q_target - self.q

        num_joints = len(dq)
        max_v = np.max(np.abs(dq[:num_joints]))
        if max_v > self.max_vel:
            dq[:num_joints] *= self.max_vel / max_v

        ddq = dq - self.prev_dq
        max_a = np.max(np.abs(ddq[:num_joints]))
        if max_a > self.max_acc:
            ddq[:num_joints] *= self.max_acc / max_a
            dq = self.prev_dq + ddq

        return self.q + dq, dq

    def process(self, position_xyz, orientation_xyzw, pos_offset: np.ndarray | None = None):
        """Solve IK for one incoming, already axis-corrected target pose and advance internal state.

        The caller is expected to have already remapped the raw controller pose onto
        the robot's axis convention; this only applies smoothing and solves IK.

        Args:
            position_xyz: target position [x, y, z] in world frame.
            orientation_xyzw: target orientation quaternion [x, y, z, w].
            pos_offset: optional extra world-frame offset applied before the arm base offset.

        Returns:
            (q_final_deg, dq_deg, err, T_target, fk_pose)
        """

        offset = np.zeros(3) if pos_offset is None else pos_offset
        world = np.array(position_xyz) + offset
        raw = world - self.base_offset

        self.filt_pos = (1 - self.alpha_pos) * self.filt_pos + self.alpha_pos * raw

        quat = self._normalize_quat(np.array(orientation_xyzw))
        quat = self._match_quaternion_sign(self.filtered_quat, quat)
        self.filtered_quat = self._quat_slerp(self.filtered_quat, quat, self.alpha_rot)

        rot = R.from_quat(self.filtered_quat).as_matrix()
        target_rot = self.ref_rot @ rot if self.use_ref_rot else rot

        T = np.eye(4)
        T[:3, :3] = target_rot
        T[:3, 3] = self.filt_pos

        q_new, err = self.solve_ik(T)
        if err > self.error_threshold:
            q_new = self.solve_escape(T)

        q_final, dq = self.vel_acc_limit(q_new)

        for i, name in enumerate(self.kin.joint_names):
            self.robot.set_joint(name, np.deg2rad(q_final[i]))
        self.robot.update_kinematics()
        fk_pose = self.robot.get_T_world_frame(self.config.tcp_frame)

        self.q = q_final
        self.prev_dq = dq

        return q_final, dq, err, T, fk_pose

    # -----------------------
    @staticmethod
    def _normalize_quat(quat: np.ndarray) -> np.ndarray:
        norm = np.linalg.norm(quat)
        return quat / norm if norm > 1e-9 else np.array([0.0, 0.0, 0.0, 1.0])

    @staticmethod
    def _match_quaternion_sign(reference: np.ndarray, quat: np.ndarray) -> np.ndarray:
        return -quat if np.dot(reference, quat) < 0.0 else quat

    def _quat_slerp(self, qa: np.ndarray, qb: np.ndarray, t: float) -> np.ndarray:
        dot = np.dot(qa, qb)
        if dot < 0.0:
            qb = -qb
            dot = -dot

        if dot > 0.9995:
            result = qa + t * (qb - qa)
            return self._normalize_quat(result)

        theta0 = math.acos(np.clip(dot, -1.0, 1.0))
        theta = theta0 * t
        sin_theta = math.sin(theta)
        sin_theta0 = math.sin(theta0)

        if abs(sin_theta0) < 1e-6:
            return qa

        s0 = math.cos(theta) - dot * sin_theta / sin_theta0
        s1 = sin_theta / sin_theta0

        return self._normalize_quat(s0 * qa + s1 * qb)
