#!/usr/bin/env python3

import math
import os

import yaml

import rclpy
from ament_index_python.packages import get_package_share_directory
from rcl_interfaces.msg import SetParametersResult
from rclpy.callback_groups import MutuallyExclusiveCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from rclpy.parameter import Parameter
from rclpy.qos import (
    QoSDurabilityPolicy,
    QoSHistoryPolicy,
    QoSProfile,
    QoSReliabilityPolicy,
)

from sensor_msgs.msg import JointState
from std_srvs.srv import SetBool
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from builtin_interfaces.msg import Duration


def load_joint_limits(yaml_path):
    """name -> (lower, upper), loaded from arm_limit.yaml.

    That file groups joints per arm controller (see
    gen2/config/arm_limit.yaml: left_arm_mit_controller/right_arm_mit_controller,
    each with a ros__parameters block mapping joint name -> {lower, upper}).
    This just flattens both arms into a single name -> (lower, upper) map."""
    with open(yaml_path) as f:
        data = yaml.safe_load(f) or {}

    limits = {}
    for controller in data.values():
        for name, bounds in controller.get("ros__parameters", {}).items():
            limits[name] = (float(bounds["lower"]), float(bounds["upper"]))
    return limits


# Mimic joints (see daksha_description_full_body/urdf/robot.urdf): each
# gripper's second finger joint mirrors the driven joint via the URDF
# <mimic> tag and isn't commanded independently. Full joint-state sources
# (e.g. joint_state_publisher_gui) publish these too, so they show up here
# but shouldn't be logged as a genuine "unknown joint" problem.
MIMIC_JOINT_NAMES = {"left_gripper_right_joint", "right_gripper_left_joint"}


class JointCommandLimiter(Node):

    def __init__(self):
        super().__init__("joint_command_limiter")

        # -------- Parameters --------
        self.declare_parameter("max_velocity", 1.0)       # rad/s
        self.declare_parameter("max_acceleration", 2.0)   # rad/s^2
        self.declare_parameter("publish_rate", 500.0)    # Hz
        self.declare_parameter("joint_limits_path", "")
        self.declare_parameter("enforce_joint_limits", False)

        self.enforce_joint_limits = self.get_parameter(
            "enforce_joint_limits").get_parameter_value().bool_value

        self.max_vel = self.get_parameter(
            "max_velocity").get_parameter_value().double_value

        self.max_acc = self.get_parameter(
            "max_acceleration").get_parameter_value().double_value

        self.rate = self.get_parameter(
            "publish_rate").get_parameter_value().double_value

        self.dt = 1.0 / self.rate

        joint_limits_path = self.get_parameter(
            "joint_limits_path").get_parameter_value().string_value
        if not joint_limits_path:
            joint_limits_path = os.path.join(
                get_package_share_directory("gen2"),
                "config", "arm_limit.yaml")

        self.joint_limits = load_joint_limits(joint_limits_path)

        self.add_on_set_parameters_callback(self.dynamic_parameter_cb)

        # Keeps the high-rate /joint_cmd, /joint_states and timer callbacks
        # off the node's default callback group, which is where rclpy's
        # built-in parameter get/set services run. Without this, those
        # topic/timer callbacks (up to publish_rate Hz, plus one extra
        # update() call per /joint_cmd message) can keep a single-threaded
        # executor busy long enough that `ros2 param get/set` requests from
        # leader_controller_ui time out. Paired with the MultiThreadedExecutor
        # in main() so the two groups can actually run concurrently.
        self._io_cbg = MutuallyExclusiveCallbackGroup()

        # -------- State --------
        # 14 arm joints (left + right) followed by left_gripper, right_gripper.
        self.num_joints = 16
        self.target_pos = [0.0] * self.num_joints
        self.target_effort = [0.0] * self.num_joints
        self.gravity_effort = [0.0] * self.num_joints
        self.current_pos = [0.0] * self.num_joints
        self.current_vel = [0.0] * self.num_joints
        self.initialized = False
        self._seeded_joints = set()
        self._last_update_time = None

        # -------- ROS --------
        self.create_subscription(
            JointState,
            "/joint_states",
            self.joint_state_callback,
            10,
            callback_group=self._io_cbg)

        # /joint_cmd is a live teleop stream at up to the update() rate: only
        # the newest command matters, and blocking on a dropped/late one just
        # adds latency to tracking. BEST_EFFORT + KEEP_LAST(1) discards stale
        # commands instead of queuing/retrying them.
        joint_cmd_qos = QoSProfile(
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            durability=QoSDurabilityPolicy.VOLATILE,
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=1,
        )

        self.create_subscription(
            JointState,
            "/joint_cmd",
            self.cmd_callback,
            joint_cmd_qos,
            callback_group=self._io_cbg)

        # Gravity compensation feedforward torque, added on top of
        # target_effort. Joints not present in the latest message keep
        # contributing zero.
        self.create_subscription(
            JointState,
            "/gravity_torque_temp",
            self.gravity_effort_callback,
            10,
            callback_group=self._io_cbg)

        self.left_pub = self.create_publisher(
            JointTrajectory,
            "/left_arm_mit_controller/joint_trajectory",
            10)

        self.right_pub = self.create_publisher(
            JointTrajectory,
            "/right_arm_mit_controller/joint_trajectory",
            10)

        self.left_gripper_pub = self.create_publisher(
            JointTrajectory,
            "/left_gripper_mit_controller/joint_trajectory",
            10)

        self.right_gripper_pub = self.create_publisher(
            JointTrajectory,
            "/right_gripper_mit_controller/joint_trajectory",
            10)

        self.debug_pub = self.create_publisher(
            JointState,
            "/jnt_cmt_to_ctrl",
            10)

        # Lets an operator turn URDF joint-limit enforcement on/off at
        # runtime (e.g. teach mode briefly driving a joint past its
        # nominal limit) without restarting the node.
        self.create_service(
            SetBool,
            "~/set_joint_limit_enforcement",
            self.set_joint_limit_enforcement_cb)

        self.timer = self.create_timer(
            self.dt, self.update, callback_group=self._io_cbg)

        self.left_names = [
            "left_joint_1",
            "left_joint_2",
            "left_joint_3",
            "left_joint_4",
            "left_joint_5",
            "left_joint_6",
            "left_joint_7",
        ]

        self.right_names = [
            "right_joint_1",
            "right_joint_2",
            "right_joint_3",
            "right_joint_4",
            "right_joint_5",
            "right_joint_6",
            "right_joint_7",
        ]

        self.left_gripper_names = ["left_gripper_left_joint"]
        self.right_gripper_names = ["right_gripper_right_joint"]

        self.joint_map = {
            name: i
            for i, name in enumerate(
                self.left_names
                + self.right_names
                + self.left_gripper_names
                + self.right_gripper_names
            )
        }

    def dynamic_parameter_cb(self, params):

        for p in params:

            if p.name == "max_velocity":
                self.max_vel = p.value
                self.get_logger().info(f"[DEBUG] max_velocity -> {p.value} rad/s")

            elif p.name == "max_acceleration":
                self.max_acc = p.value
                self.get_logger().info(f"[DEBUG] max_acceleration -> {p.value} rad/s^2")

            elif p.name == "enforce_joint_limits":
                self.enforce_joint_limits = p.value
                self.get_logger().info(f"[DEBUG] enforce_joint_limits -> {p.value}")

        return SetParametersResult(successful=True)

    def set_joint_limit_enforcement_cb(self, request, response):

        # Routed through set_parameters (-> dynamic_parameter_cb) rather
        # than set directly, so the "enforce_joint_limits" parameter
        # stays in sync and `ros2 param get` reflects the service-driven
        # state too.
        self.set_parameters(
            [Parameter(
                "enforce_joint_limits",
                Parameter.Type.BOOL,
                request.data)])

        state = "enabled" if request.data else "disabled"
        self.get_logger().info(f"URDF joint limit enforcement {state}")

        response.success = True
        response.message = f"joint limit enforcement {state}"

        return response

    def joint_state_callback(self, msg):

        # Seed each joint's starting position the first time it shows up in
        # /joint_states, whichever message that is - some joints (e.g. a
        # gripper whose controller fails to activate) may never appear at
        # all, and others may arrive on a later message than the first one
        # received. A joint already seeded is left alone from then on: this
        # node owns current_pos/target_pos going forward, it's not meant to
        # keep tracking live feedback.
        for i, name in enumerate(msg.name):

            if name not in self.joint_map:
                continue

            idx = self.joint_map[name]

            if i >= len(msg.position):
                continue

            if name in self._seeded_joints:
                continue

            self.current_pos[idx] = msg.position[i]
            self.target_pos[idx] = msg.position[i]
            self._seeded_joints.add(name)

        if not self.initialized and self._seeded_joints:
            self.initialized = True

    def cmd_callback(self, msg):

        for i, name in enumerate(msg.name):

            if name not in self.joint_map:
                if name not in MIMIC_JOINT_NAMES:
                    self.get_logger().warn(f"Unknown joint: {name}")
                continue

            idx = self.joint_map[name]

            if i < len(msg.position):
                pos = msg.position[i]
                limit = self.joint_limits.get(name)
                if (not self.enforce_joint_limits) or limit is None or (
                        limit[0] <= pos <= limit[1]):
                    self.target_pos[idx] = pos
                else:
                    self.get_logger().warn(
                        f"{name}: commanded position {pos:.4f} outside URDF "
                        f"limit [{limit[0]:.4f}, {limit[1]:.4f}] - ignored"
                    )

            if i < len(msg.effort):
                self.target_effort[idx] = msg.effort[i]

        # update() only ran on the self.timer tick, so every /joint_cmd value
        # sat queued for up to one full publish period (1/publish_rate) before
        # current_pos/current_vel picked it up and /jnt_cmt_to_ctrl reflected
        # it - the actual lag being reported. Publish on receipt instead of
        # only polling; the timer keeps running underneath to re-publish the
        # held target (e.g. for effort/gravity-comp updates) even when no new
        # position command arrives.
        self.update()

    def gravity_effort_callback(self, msg):

        self.gravity_effort = [0.0] * self.num_joints

        for i, name in enumerate(msg.name):

            if name not in self.joint_map:
                if name not in MIMIC_JOINT_NAMES:
                    self.get_logger().warn(f"Unknown joint: {name}")
                continue

            idx = self.joint_map[name]

            if i < len(msg.effort):
                self.gravity_effort[idx] = msg.effort[i]

    def update(self):

        if not self.initialized:
            return

        # update() is called both by the self.timer tick (every self.dt) and,
        # for lower latency, directly from cmd_callback on every /joint_cmd
        # message. Upstream publishers (e.g. teach-mode's joint_states echo,
        # VR/leader teleop) can exceed the timer's rate, so the velocity/
        # acceleration integration below MUST use the real elapsed wall-clock
        # time rather than assume exactly self.dt happened - otherwise, at
        # 2x the assumed call rate the arm moves at ~2x the configured
        # max_vel in real time (each extra call double-counts the same
        # instant), and this compounds with call rate.
        now = self.get_clock().now()
        if self._last_update_time is None:
            self._last_update_time = now
            return

        dt = (now - self._last_update_time).nanoseconds * 1e-9
        self._last_update_time = now

        if dt <= 0.0:
            return
        # Clamp so a stall (e.g. a scheduling hiccup) followed by a resume
        # doesn't integrate one huge catch-up step instead.
        dt = min(dt, 2.0 * self.dt)

        for i in range(self.num_joints):

            error = self.target_pos[i] - self.current_pos[i]

            # Cap speed so the arm can still brake to zero velocity
            # exactly at the target given max_acc (v^2 = 2*a*d).
            brake_limited_vel = math.sqrt(2 * self.max_acc * abs(error))

            desired_vel = math.copysign(
                min(self.max_vel, brake_limited_vel),
                error
            )

            # Acceleration clamp
            dv = desired_vel - self.current_vel[i]

            max_dv = self.max_acc * dt

            dv = max(-max_dv, min(max_dv, dv))

            self.current_vel[i] += dv

            self.current_pos[i] += self.current_vel[i] * dt

        self.publish()

    def publish(self):

        effort = [
            self.target_effort[i] + self.gravity_effort[i]
            for i in range(self.num_joints)
        ]

        left = JointTrajectory()
        left.joint_names = self.left_names

        p = JointTrajectoryPoint()
        p.positions = self.current_pos[:7]
        p.velocities = self.current_vel[:7]
        p.effort = effort[:7]
        p.time_from_start = Duration(sec=0, nanosec=int(self.dt * 1e9))

        left.points.append(p)

        self.left_pub.publish(left)

        right = JointTrajectory()
        right.joint_names = self.right_names

        p = JointTrajectoryPoint()
        p.positions = self.current_pos[7:14]
        p.velocities = self.current_vel[7:14]
        p.effort = effort[7:14]
        p.time_from_start = Duration(sec=0, nanosec=int(self.dt * 1e9))

        right.points.append(p)

        self.right_pub.publish(right)

        left_gripper = JointTrajectory()
        left_gripper.joint_names = self.left_gripper_names

        p = JointTrajectoryPoint()
        p.positions = self.current_pos[14:15]
        p.velocities = self.current_vel[14:15]
        p.effort = effort[14:15]
        p.time_from_start = Duration(sec=0, nanosec=int(self.dt * 1e9))

        left_gripper.points.append(p)

        self.left_gripper_pub.publish(left_gripper)

        right_gripper = JointTrajectory()
        right_gripper.joint_names = self.right_gripper_names

        p = JointTrajectoryPoint()
        p.positions = self.current_pos[15:16]
        p.velocities = self.current_vel[15:16]
        p.effort = effort[15:16]
        p.time_from_start = Duration(sec=0, nanosec=int(self.dt * 1e9))

        right_gripper.points.append(p)

        self.right_gripper_pub.publish(right_gripper)

        debug = JointState()
        debug.header.stamp = self.get_clock().now().to_msg()
        debug.name = (
            self.left_names
            + self.right_names
            + self.left_gripper_names
            + self.right_gripper_names
        )
        debug.position = self.current_pos
        debug.velocity = self.current_vel
        debug.effort = effort

        self.debug_pub.publish(debug)


def main(args=None):

    rclpy.init(args=args)

    node = JointCommandLimiter()

    # 2 threads: one keeps servicing the high-rate /joint_cmd, /joint_states
    # and timer callbacks (self._io_cbg), the other stays free for the
    # default callback group, which is where rclpy's built-in parameter
    # get/set services (used by leader_controller_ui) run.
    executor = MultiThreadedExecutor(num_threads=2)
    executor.add_node(node)

    try:
        executor.spin()
    finally:
        executor.shutdown()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()