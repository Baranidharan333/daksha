#!/usr/bin/env python3
"""HTTP server that also bridges ROS data to the browser."""

# Method signatures below annotate params/returns with ROS message types
# (TFMessage, OccupancyGrid, ...) that only exist when the optional rclpy
# import block below succeeds. Deferring annotation evaluation (PEP 563)
# keeps RosStateBridge importable -- and this file runnable in its
# degraded, ROS-less mode -- even when those types were never imported.
from __future__ import annotations

import argparse
import json
import math
import os
import socket
import threading
import time
from http.server import SimpleHTTPRequestHandler
from pathlib import Path
from socketserver import TCPServer
from typing import Dict, List, Optional

try:
    import rclpy
    from action_msgs.msg import GoalStatus
    from diagnostic_msgs.msg import DiagnosticArray
    from geometry_msgs.msg import PoseStamped, PoseWithCovarianceStamped, Twist
    from nav2_msgs.action import NavigateToPose
    from nav2_msgs.msg import ParticleCloud
    from nav_msgs.msg import OccupancyGrid, Odometry
    # Aliased: this file already imports pathlib.Path for filesystem paths
    # (config/waypoints.json, the URDF/mesh routes, etc) -- nav_msgs.msg.Path
    # would silently shadow it otherwise.
    from nav_msgs.msg import Path as RosPath
    from rclpy.action import ActionClient
    from rclpy.executors import MultiThreadedExecutor
    from rclpy.node import Node
    from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy, qos_profile_sensor_data
    from sensor_msgs.msg import BatteryState, Imu, JointState, LaserScan
    from std_msgs.msg import Bool
    from tf2_msgs.msg import TFMessage
except ImportError:  # pragma: no cover
    rclpy = None
    # RosStateBridge(Node) is defined unconditionally below (only
    # start_ros_bridge() checks `rclpy is None` before instantiating it), so
    # Node must still name something or that class statement itself crashes
    # the whole server at import time.
    Node = object

ROS_BRIDGE = None
ROS_EXECUTOR = None
ROS_THREAD = None

# Overridable via --max-linear / --max-angular; clamps every /api/teleop
# request server-side so a stray large value from the browser (or a bug in
# it) can't command a speed beyond what's safe for this robot.
TELEOP_MAX_LINEAR = 0.5
TELEOP_MAX_ANGULAR = 1.0

# Docking is a real feature in this workspace's nav_bringup package
# (custom_docking_server.py, using opennav_docking_msgs/action/DockRobot),
# but that message package isn't installed in this environment -- attempting
# the import would crash this whole server at startup over one optional
# feature. Guarded the same way the rest of this file treats optional ROS
# pieces: degrade to an honest "not available" response instead.
try:
    from opennav_docking_msgs.action import DockRobot, UndockRobot  # noqa: F401
    DOCKING_AVAILABLE = True
except ImportError:
    DOCKING_AVAILABLE = False

# The 3D view's "spawn my URDF" model is read straight from the
# daksha_description_full_body package's installed share/ directory (URDF +
# meshes) instead of duplicating those files into this package -- so it
# always matches whatever description is actually built, with no separate
# copy to keep in sync. Same honest-degrade pattern as DOCKING_AVAILABLE
# above: if that package isn't built/sourced, the /robot_model/* routes
# just report unavailable instead of crashing this server at startup.
DESCRIPTION_PKG = 'daksha_description_full_body'
ROBOT_URDF_PATH: Optional[Path] = None
ROBOT_MESHES_DIR: Optional[Path] = None
try:
    from ament_index_python.packages import get_package_share_directory
    _description_share = Path(get_package_share_directory(DESCRIPTION_PKG))
    _urdf_candidate = _description_share / 'urdf' / 'robot.urdf'
    _meshes_candidate = _description_share / 'meshes'
    if _urdf_candidate.is_file():
        ROBOT_URDF_PATH = _urdf_candidate
    if _meshes_candidate.is_dir():
        ROBOT_MESHES_DIR = _meshes_candidate
except Exception:
    pass


def quaternion_to_yaw(rotation):
    siny_cosp = 2 * (rotation.w * rotation.z + rotation.x * rotation.y)
    cosy_cosp = 1 - 2 * (rotation.y * rotation.y + rotation.z * rotation.z)
    return math.atan2(siny_cosp, cosy_cosp)


class RosStateBridge(Node):
    def __init__(self):
        super().__init__('web_nav_state_bridge')
        self._pose_lock = threading.Lock()
        self._map_lock = threading.Lock()
        self._feedback_lock = threading.Lock()
        self._localization_lock = threading.Lock()
        self._battery_lock = threading.Lock()
        self._diag_lock = threading.Lock()
        self._scan_lock = threading.Lock()
        self._nav_lock = threading.Lock()
        self._odom_lock = threading.Lock()
        self._imu_lock = threading.Lock()
        self._joint_lock = threading.Lock()
        self._local_costmap_lock = threading.Lock()
        self._global_costmap_lock = threading.Lock()
        self._local_plan_lock = threading.Lock()
        self._global_plan_lock = threading.Lock()
        self._particle_cloud_lock = threading.Lock()

        self._current_pose = {'x': 0.0, 'y': 0.0, 'yaw': 0.0}
        self._map: Optional[Dict] = None
        self._feedback: Dict = {}
        self._amcl_pose: Optional[Dict] = None
        self._localization_confidence = 'unknown'
        self._localization_spread = None
        self._last_amcl_ns = 0
        self._battery: Optional[Dict] = None
        self._last_battery_ns = 0
        self._diagnostics: List[Dict] = []
        self._last_diag_ns = 0
        self._scan: Optional[Dict] = None
        self._last_scan_ns = 0
        self._odom: Optional[Dict] = None
        self._last_odom_ns = 0
        self._imu: Optional[Dict] = None
        self._last_imu_ns = 0
        self._joint_positions: Dict[str, float] = {}
        self._last_joint_ns = 0
        self._local_costmap: Optional[Dict] = None
        self._global_costmap: Optional[Dict] = None
        self._local_plan: List[Dict] = []
        self._last_local_plan_ns = 0
        self._global_plan: List[Dict] = []
        self._last_global_plan_ns = 0
        self._particles: List[Dict] = []
        self._last_particle_ns = 0

        # Navigation state machine, driven by the navigate_to_pose action
        # client below -- gives real Idle/Planning/Navigating/Reached/Failed
        # states and a real Cancel, which a bare /goal_pose topic publish
        # can't provide (no goal handle to cancel, no result/status).
        self._nav_state = 'idle'
        self._nav_goal_handle = None
        self._nav_distance_remaining = None
        self._nav_current_goal = None
        self._nav_error = None
        self._start_time_s = time.time()

        self._goal_pub = self.create_publisher(PoseStamped, '/goal_pose', 10)
        self._initialpose_pub = self.create_publisher(PoseWithCovarianceStamped, '/initialpose', 10)
        self._motors_enable_pub = self.create_publisher(Bool, '/motors_enable', 10)
        self._cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self._nav_action_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')

        self._last_teleop_ns = 0
        # Deadman timer: if the browser stops sending teleop commands (tab
        # closed, network drop, joystick released without a final zero
        # reaching the server) the robot must not keep driving on the last
        # velocity it heard. Re-publishes zero once, then goes quiet again --
        # doesn't fight a *different* velocity source (e.g. nav2) that may
        # be publishing to the same topic between teleop sessions.
        self._teleop_zeroed = True
        self.create_timer(0.3, self._teleop_deadman)

        self.create_subscription(TFMessage, '/tf', self._tf_callback, 10)
        # nav2's map_server publishes /map with TRANSIENT_LOCAL durability
        # specifically so a late-joining subscriber still gets the last
        # published map instead of only future updates. The default
        # (VOLATILE) subscription QoS is incompatible with that publisher --
        # they simply never match, so /api/map silently stays empty forever
        # with no error on either side. Must mirror the publisher's QoS
        # (same profile amcl itself subscribes with) to actually receive it.
        map_qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            depth=1,
        )
        self.create_subscription(OccupancyGrid, '/map', self._map_callback, map_qos)
        self.create_subscription(PoseWithCovarianceStamped, '/amcl_pose', self._amcl_pose_callback, 10)
        self.create_subscription(BatteryState, '/battery_state', self._battery_callback, 10)
        self.create_subscription(DiagnosticArray, '/diagnostics', self._diagnostics_callback, 10)
        self.create_subscription(LaserScan, '/scan_filtered', self._scan_callback, qos_profile_sensor_data)
        self.create_subscription(Odometry, '/odom', self._odom_callback, 10)
        self.create_subscription(Imu, '/imu/data', self._imu_callback, qos_profile_sensor_data)
        # Drives the 3D view's URDF model, the same way robot_state_publisher
        # drives RViz2's RobotModel display -- if this robot's controllers
        # aren't up, the 3D model just falls back to its neutral URDF pose.
        self.create_subscription(JointState, '/joint_states', self._joint_states_callback, 10)
        # RViz2-equivalent layers: local/global costmaps (same TRANSIENT_LOCAL
        # QoS as /map, for the same reason -- see map_qos above), the
        # planner's global path and the controller's local trajectory, and
        # AMCL's live particle cloud. All degrade to "unavailable" the same
        # way the rest of this bridge does if the full nav2 stack (not just
        # localization_launch.py) isn't up.
        self.create_subscription(OccupancyGrid, '/local_costmap/costmap', self._local_costmap_callback, map_qos)
        self.create_subscription(OccupancyGrid, '/global_costmap/costmap', self._global_costmap_callback, map_qos)
        self.create_subscription(RosPath, '/local_plan', self._local_plan_callback, 10)
        self.create_subscription(RosPath, '/received_global_plan', self._global_plan_callback, 10)
        # amcl publishes this BEST_EFFORT; the default (RELIABLE) subscriber
        # QoS is incompatible with that -- same class of silent-empty-forever
        # bug as /map's durability mismatch above, caught this time via the
        # "incompatible QoS" warning rclpy logs on mismatch.
        self.create_subscription(
            ParticleCloud, '/particle_cloud', self._particle_cloud_callback, qos_profile_sensor_data
        )
        # Passive observation of whichever client's goal is active (ours via
        # the action client below, or e.g. rviz2's) -- kept as a fallback
        # distance-remaining source for goals sent through the legacy
        # /goal_pose topic path (see send_nav_goal's fallback branch).
        try:
            from nav2_msgs.action import NavigateToPose_FeedbackMessage
            self.create_subscription(
                NavigateToPose_FeedbackMessage,
                '/navigate_to_pose/_action/feedback',
                self._feedback_callback,
                10
            )
        except (ImportError, AttributeError):
            pass

    # ── pose / map ───────────────────────────────────────────────────────

    def _tf_callback(self, msg: TFMessage):
        # On this robot base_link is only ever on /tf_static (a fixed
        # z-offset above base_footprint, published once at startup) --
        # base_footprint is the frame that actually moves on the live /tf
        # topic. Matching only 'base_link' meant this callback never fired
        # at all, leaving _current_pose stuck at its __init__ default
        # forever, even while the robot was actively driving (confirmed via
        # tf2_echo showing map->base_link changing live). base_footprint's
        # x/y/yaw are the same as base_link's by ROS convention (it's
        # base_link's ground projection), so this is correct for a top-down
        # nav UI either way -- also still matches robots (like this
        # workspace's own daksha URDF) that publish base_link directly with
        # no footprint frame at all.
        for transform in msg.transforms:
            if transform.child_frame_id in ('base_footprint', 'base_link'):
                translation = transform.transform.translation
                rotation = transform.transform.rotation
                with self._pose_lock:
                    self._current_pose = {
                        'x': translation.x,
                        'y': translation.y,
                        'yaw': quaternion_to_yaw(rotation)
                    }
                break

    def _map_callback(self, msg: OccupancyGrid):
        info = msg.info
        with self._map_lock:
            self._map = {
                'resolution': info.resolution,
                'width': info.width,
                'height': info.height,
                'origin': {
                    'x': info.origin.position.x,
                    'y': info.origin.position.y,
                    'yaw': quaternion_to_yaw(info.origin.orientation)
                },
                'data': list(msg.data)
            }

    def get_pose(self) -> Dict:
        with self._pose_lock:
            return dict(self._current_pose)

    def get_map(self) -> Optional[Dict]:
        with self._map_lock:
            return dict(self._map) if self._map is not None else None

    # ── localization (AMCL) ──────────────────────────────────────────────

    def _amcl_pose_callback(self, msg: PoseWithCovarianceStamped):
        yaw = quaternion_to_yaw(msg.pose.pose.orientation)
        cov = msg.pose.covariance
        # Confidence heuristic from position covariance trace (xx + yy, m^2):
        # a well scan-matched AMCL sits well under 0.05 in practice; a
        # freshly-reset or poorly-matched one sits at 0.25+ (AMCL's own
        # default initial spread) or keeps growing between scan matches.
        spread = cov[0] + cov[7]
        if spread < 0.05:
            confidence = 'high'
        elif spread < 0.25:
            confidence = 'medium'
        else:
            confidence = 'low'
        with self._localization_lock:
            self._amcl_pose = {
                'x': msg.pose.pose.position.x,
                'y': msg.pose.pose.position.y,
                'yaw': yaw,
            }
            self._localization_confidence = confidence
            self._localization_spread = spread
            self._last_amcl_ns = self.get_clock().now().nanoseconds

    def get_localization(self) -> Dict:
        with self._localization_lock:
            if self._amcl_pose is None:
                return {'available': False}
            age_s = (self.get_clock().now().nanoseconds - self._last_amcl_ns) / 1e9
            return {
                'available': True,
                'pose': dict(self._amcl_pose),
                'confidence': self._localization_confidence,
                'covariance_spread': self._localization_spread,
                'age_s': age_s,
            }

    def publish_initial_pose(self, x: float, y: float, yaw: float):
        msg = PoseWithCovarianceStamped()
        msg.header.frame_id = 'map'
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.pose.pose.position.x = x
        msg.pose.pose.position.y = y
        msg.pose.pose.orientation.z = math.sin(yaw / 2.0)
        msg.pose.pose.orientation.w = math.cos(yaw / 2.0)
        # Modest default spread (AMCL narrows it via subsequent scan
        # matches) -- same order of magnitude as rviz2's "2D Pose Estimate"
        # tool default.
        msg.pose.covariance[0] = 0.25
        msg.pose.covariance[7] = 0.25
        msg.pose.covariance[35] = 0.06853891945200942
        self._initialpose_pub.publish(msg)

    # ── battery ──────────────────────────────────────────────────────────

    def _battery_callback(self, msg: BatteryState):
        with self._battery_lock:
            self._battery = {
                'percentage': msg.percentage,
                'voltage': msg.voltage,
                'current': msg.current,
                'power_supply_status': int(msg.power_supply_status),
            }
            self._last_battery_ns = self.get_clock().now().nanoseconds

    def get_battery(self) -> Dict:
        with self._battery_lock:
            if self._battery is None:
                return {'available': False}
            age_s = (self.get_clock().now().nanoseconds - self._last_battery_ns) / 1e9
            return {'available': True, 'age_s': age_s, **self._battery}

    # ── diagnostics ──────────────────────────────────────────────────────

    def _diagnostics_callback(self, msg: DiagnosticArray):
        entries = [
            {
                'name': s.name,
                'level': int.from_bytes(s.level, 'little') if isinstance(s.level, bytes) else int(s.level),
                'message': s.message,
                'hardware_id': s.hardware_id,
            }
            for s in msg.status
        ]
        with self._diag_lock:
            self._diagnostics = entries
            self._last_diag_ns = self.get_clock().now().nanoseconds

    def get_diagnostics(self) -> Dict:
        with self._diag_lock:
            age_s = None
            if self._last_diag_ns:
                age_s = (self.get_clock().now().nanoseconds - self._last_diag_ns) / 1e9
            return {'entries': list(self._diagnostics), 'age_s': age_s}

    # ── lidar scan (freshness + polar-plot data for the Sensors card) ─────

    def _scan_callback(self, msg: LaserScan):
        with self._scan_lock:
            self._scan = {
                'angle_min': msg.angle_min,
                'angle_increment': msg.angle_increment,
                'range_max': msg.range_max,
                'ranges': list(msg.ranges),
            }
            self._last_scan_ns = self.get_clock().now().nanoseconds

    def get_scan(self) -> Dict:
        with self._scan_lock:
            if self._scan is None:
                return {'available': False}
            age_s = (self.get_clock().now().nanoseconds - self._last_scan_ns) / 1e9
            return {'available': True, 'age_s': age_s, **self._scan}

    # ── odometry ─────────────────────────────────────────────────────────

    def _odom_callback(self, msg: Odometry):
        with self._odom_lock:
            self._odom = {
                'x': msg.pose.pose.position.x,
                'y': msg.pose.pose.position.y,
                'yaw': quaternion_to_yaw(msg.pose.pose.orientation),
                'linear_x': msg.twist.twist.linear.x,
                'angular_z': msg.twist.twist.angular.z,
            }
            self._last_odom_ns = self.get_clock().now().nanoseconds

    def get_odometry(self) -> Dict:
        with self._odom_lock:
            if self._odom is None:
                return {'available': False}
            age_s = (self.get_clock().now().nanoseconds - self._last_odom_ns) / 1e9
            return {'available': True, 'age_s': age_s, **self._odom}

    # ── IMU ──────────────────────────────────────────────────────────────

    def _imu_callback(self, msg: Imu):
        with self._imu_lock:
            self._imu = {
                'angular_velocity': {
                    'x': msg.angular_velocity.x,
                    'y': msg.angular_velocity.y,
                    'z': msg.angular_velocity.z,
                },
                'linear_acceleration': {
                    'x': msg.linear_acceleration.x,
                    'y': msg.linear_acceleration.y,
                    'z': msg.linear_acceleration.z,
                },
            }
            self._last_imu_ns = self.get_clock().now().nanoseconds

    def get_imu(self) -> Dict:
        with self._imu_lock:
            if self._imu is None:
                return {'available': False}
            age_s = (self.get_clock().now().nanoseconds - self._last_imu_ns) / 1e9
            return {'available': True, 'age_s': age_s, **self._imu}

    # ── joint states (drives the 3D view's URDF pose) ──────────────────────

    def _joint_states_callback(self, msg: JointState):
        with self._joint_lock:
            self._joint_positions = dict(zip(msg.name, msg.position))
            self._last_joint_ns = self.get_clock().now().nanoseconds

    def get_joint_states(self) -> Dict:
        with self._joint_lock:
            if not self._joint_positions:
                return {'available': False}
            age_s = (self.get_clock().now().nanoseconds - self._last_joint_ns) / 1e9
            return {'available': True, 'age_s': age_s, 'positions': dict(self._joint_positions)}

    # ── costmaps (RViz2 "Global/Local Costmap" layers) ──────────────────────

    @staticmethod
    def _occupancy_grid_to_dict(msg: OccupancyGrid) -> Dict:
        info = msg.info
        return {
            'resolution': info.resolution,
            'width': info.width,
            'height': info.height,
            'origin': {
                'x': info.origin.position.x,
                'y': info.origin.position.y,
                'yaw': quaternion_to_yaw(info.origin.orientation),
            },
            'data': list(msg.data),
        }

    def _local_costmap_callback(self, msg: OccupancyGrid):
        with self._local_costmap_lock:
            self._local_costmap = self._occupancy_grid_to_dict(msg)

    def get_local_costmap(self) -> Dict:
        with self._local_costmap_lock:
            if self._local_costmap is None:
                return {'available': False}
            return {'available': True, **self._local_costmap}

    def _global_costmap_callback(self, msg: OccupancyGrid):
        with self._global_costmap_lock:
            self._global_costmap = self._occupancy_grid_to_dict(msg)

    def get_global_costmap(self) -> Dict:
        with self._global_costmap_lock:
            if self._global_costmap is None:
                return {'available': False}
            return {'available': True, **self._global_costmap}

    # ── planned paths (RViz2 "Global/Local Plan" lines) ─────────────────────

    @staticmethod
    def _path_to_points(msg: RosPath) -> List[Dict]:
        return [{'x': p.pose.position.x, 'y': p.pose.position.y} for p in msg.poses]

    def _local_plan_callback(self, msg: RosPath):
        with self._local_plan_lock:
            self._local_plan = self._path_to_points(msg)
            self._last_local_plan_ns = self.get_clock().now().nanoseconds

    def get_local_plan(self) -> Dict:
        with self._local_plan_lock:
            if not self._local_plan:
                return {'available': False}
            age_s = (self.get_clock().now().nanoseconds - self._last_local_plan_ns) / 1e9
            return {'available': True, 'age_s': age_s, 'points': list(self._local_plan)}

    def _global_plan_callback(self, msg: RosPath):
        with self._global_plan_lock:
            self._global_plan = self._path_to_points(msg)
            self._last_global_plan_ns = self.get_clock().now().nanoseconds

    def get_global_plan(self) -> Dict:
        with self._global_plan_lock:
            if not self._global_plan:
                return {'available': False}
            age_s = (self.get_clock().now().nanoseconds - self._last_global_plan_ns) / 1e9
            return {'available': True, 'age_s': age_s, 'points': list(self._global_plan)}

    # ── AMCL particle cloud (RViz2 "Particle Cloud" display) ─────────────────

    def _particle_cloud_callback(self, msg: ParticleCloud):
        with self._particle_cloud_lock:
            self._particles = [
                {
                    'x': p.pose.position.x,
                    'y': p.pose.position.y,
                    'yaw': quaternion_to_yaw(p.pose.orientation),
                    'weight': p.weight,
                }
                for p in msg.particles
            ]
            self._last_particle_ns = self.get_clock().now().nanoseconds

    def get_particle_cloud(self) -> Dict:
        with self._particle_cloud_lock:
            if not self._particles:
                return {'available': False}
            age_s = (self.get_clock().now().nanoseconds - self._last_particle_ns) / 1e9
            return {'available': True, 'age_s': age_s, 'particles': list(self._particles)}

    # ── navigation (NavigateToPose action: real status + cancel) ──────────

    def send_nav_goal(self, x: float, y: float, yaw: float, label: Optional[str] = None):
        goal_msg = NavigateToPose.Goal()
        goal_msg.pose.header.frame_id = 'map'
        goal_msg.pose.header.stamp = self.get_clock().now().to_msg()
        goal_msg.pose.pose.position.x = x
        goal_msg.pose.pose.position.y = y
        goal_msg.pose.pose.orientation.z = math.sin(yaw / 2.0)
        goal_msg.pose.pose.orientation.w = math.cos(yaw / 2.0)

        if not self._nav_action_client.server_is_ready():
            # bt_navigator isn't up (e.g. only localization_launch.py is
            # running, not the full navigation_launch.py) -- fall back to
            # the bare topic publish so "set goal" still does *something*.
            # No cancel/granular status is possible for a goal sent this way.
            self._goal_pub.publish(goal_msg.pose)
            with self._nav_lock:
                self._nav_state = 'idle'
                self._nav_current_goal = label
                self._nav_error = (
                    'navigate_to_pose action server not available -- sent via '
                    '/goal_pose topic instead (no cancel/live status for this goal)'
                )
            return

        with self._nav_lock:
            self._nav_state = 'planning'
            self._nav_current_goal = label
            self._nav_error = None
            self._nav_distance_remaining = None

        send_future = self._nav_action_client.send_goal_async(goal_msg, feedback_callback=self._nav_feedback_cb)
        send_future.add_done_callback(self._nav_goal_response_cb)

    def _nav_goal_response_cb(self, future):
        try:
            goal_handle = future.result()
        except Exception as exc:  # noqa: BLE001 - surface any rclpy-side failure to the UI
            with self._nav_lock:
                self._nav_state = 'failed'
                self._nav_error = f'Failed to send goal: {exc}'
            return
        if not goal_handle.accepted:
            with self._nav_lock:
                self._nav_state = 'failed'
                self._nav_error = 'Goal rejected by navigate_to_pose'
            return
        with self._nav_lock:
            self._nav_goal_handle = goal_handle
            self._nav_state = 'navigating'
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self._nav_result_cb)

    def _nav_feedback_cb(self, feedback_msg):
        fb = feedback_msg.feedback
        with self._nav_lock:
            self._nav_distance_remaining = fb.distance_remaining

    def _nav_result_cb(self, future):
        try:
            result = future.result()
            status = result.status
        except Exception as exc:  # noqa: BLE001
            with self._nav_lock:
                self._nav_goal_handle = None
                self._nav_state = 'failed'
                self._nav_error = f'Result error: {exc}'
            return
        with self._nav_lock:
            self._nav_goal_handle = None
            if status == GoalStatus.STATUS_SUCCEEDED:
                self._nav_state = 'goal_reached'
            elif status == GoalStatus.STATUS_CANCELED:
                self._nav_state = 'canceled'
            else:
                self._nav_state = 'failed'
                self._nav_error = f'navigate_to_pose finished with status {status}'

    def cancel_nav_goal(self) -> bool:
        with self._nav_lock:
            goal_handle = self._nav_goal_handle
        if goal_handle is None:
            return False
        goal_handle.cancel_goal_async()
        return True

    def get_nav_status(self) -> Dict:
        with self._nav_lock:
            return {
                'state': self._nav_state,
                'current_goal': self._nav_current_goal,
                'distance_remaining': self._nav_distance_remaining,
                'error': self._nav_error,
                'action_server_available': self._nav_action_client.server_is_ready(),
            }

    # ── system status (node/topic liveness for the Diagnostics card) ──────

    def get_system_status(self) -> Dict:
        return {
            'hostname': socket.gethostname(),
            'ros_domain_id': os.environ.get('ROS_DOMAIN_ID', '0'),
            'uptime_s': time.time() - self._start_time_s,
            'map_server': self.count_publishers('/map') > 0,
            'amcl': self.count_publishers('/amcl_pose') > 0,
            'nav2_bt_navigator': self._nav_action_client.server_is_ready(),
            'lidar': self.count_publishers('/scan_filtered') > 0,
            'battery_topic': self.count_publishers('/battery_state') > 0,
            'odom': self.count_publishers('/odom') > 0,
            'imu': self.count_publishers('/imu/data') > 0,
            'camera': self.count_publishers('/camera/image_raw') > 0,
            'local_costmap': self.count_publishers('/local_costmap/costmap') > 0,
            'global_costmap': self.count_publishers('/global_costmap/costmap') > 0,
            'docking_msgs_installed': DOCKING_AVAILABLE,
        }

    # ── manual control ───────────────────────────────────────────────────

    def publish_cmd_vel(self, linear: float, angular: float):
        twist = Twist()
        twist.linear.x = linear
        twist.angular.z = angular
        self._cmd_vel_pub.publish(twist)
        self._last_teleop_ns = self.get_clock().now().nanoseconds
        self._teleop_zeroed = (linear == 0.0 and angular == 0.0)

    def _teleop_deadman(self):
        if self._teleop_zeroed:
            return
        elapsed_s = (self.get_clock().now().nanoseconds - self._last_teleop_ns) / 1e9
        if elapsed_s > 0.5:
            self._cmd_vel_pub.publish(Twist())
            self._teleop_zeroed = True
            self.get_logger().warn('Teleop deadman: no /api/teleop update in 0.5s, publishing zero cmd_vel.')

    def set_motors_enabled(self, enabled: bool):
        # Best-effort: no motor-enable service is known to exist for this
        # mobile base in this workspace, so this just publishes a Bool on a
        # conventional topic name. Callers should treat the HTTP response as
        # "command sent", not "motors confirmed enabled" -- there is no
        # feedback path to confirm the base actually acted on it.
        msg = Bool()
        msg.data = enabled
        self._motors_enable_pub.publish(msg)

    def get_feedback(self) -> Dict:
        with self._feedback_lock:
            return dict(self._feedback)

    def _feedback_callback(self, msg):
        feedback = getattr(msg, 'feedback', None)
        if not feedback:
            return
        distance = getattr(feedback, 'distance_remaining', 0.0)
        with self._feedback_lock:
            self._feedback = {
                'distance_remaining': distance,
                'goal_reached': distance <= 0.05,
            }


class NavHTTPHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, static_dir=None, config_dir=None, **kwargs):
        self.static_dir = static_dir
        self.config_dir = config_dir
        super().__init__(*args, directory=str(static_dir), **kwargs)

    def log_message(self, format, *args):
        # Suppress BaseHTTPRequestHandler's default per-request access log
        # line. The browser polls several status endpoints a few times a
        # second, so left on this drowns the console in "GET /api/pose 200"
        # noise with nothing actionable in it.
        pass

    def _set_json_headers(self, response_code=200):
        self.send_response(response_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

    def _write_json(self, payload, response_code=200):
        self._set_json_headers(response_code)
        self.wfile.write(json.dumps(payload).encode())

    def _require_bridge(self):
        if ROS_BRIDGE is None:
            self._write_json({'error': 'ROS bridge not available'}, 503)
            return None
        return ROS_BRIDGE

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        # /robot_model/meshes/<file>.stl carries a variable filename, so it
        # can't sit in the exact-match routes dict below like the other
        # endpoints -- handled as a prefix check instead.
        if self.path.startswith('/robot_model/meshes/'):
            self._handle_robot_mesh_get()
            return
        routes = {
            '/api/waypoints': self._handle_waypoints_get,
            '/api/missions': self._handle_missions_get,
            '/api/pose': self._handle_pose_get,
            '/api/map': self._handle_map_get,
            '/api/feedback': self._handle_feedback_get,
            '/api/localization': self._handle_localization_get,
            '/api/battery': self._handle_battery_get,
            '/api/diagnostics': self._handle_diagnostics_get,
            '/api/scan': self._handle_scan_get,
            '/api/odometry': self._handle_odometry_get,
            '/api/imu': self._handle_imu_get,
            '/api/joint_states': self._handle_joint_states_get,
            '/api/local_costmap': self._handle_local_costmap_get,
            '/api/global_costmap': self._handle_global_costmap_get,
            '/api/local_plan': self._handle_local_plan_get,
            '/api/global_plan': self._handle_global_plan_get,
            '/api/particle_cloud': self._handle_particle_cloud_get,
            '/api/nav_status': self._handle_nav_status_get,
            '/api/system_status': self._handle_system_status_get,
            '/robot_model/urdf': self._handle_robot_urdf_get,
        }
        handler = routes.get(self.path)
        if handler:
            handler()
        else:
            super().do_GET()

    def do_POST(self):
        routes = {
            '/api/waypoints': self._handle_waypoints_post,
            '/api/missions': self._handle_missions_post,
            '/api/command': self._handle_command_post,
            '/api/teleop': self._handle_teleop_post,
            '/api/log': self._handle_log_post,
            '/api/initial_pose': self._handle_initial_pose_post,
            '/api/cancel_goal': self._handle_cancel_goal_post,
            '/api/motors': self._handle_motors_post,
            '/api/dock': self._handle_dock_post,
            '/api/undock': self._handle_undock_post,
        }
        handler = routes.get(self.path)
        if handler:
            handler()
        else:
            self.send_error(404, 'Resource not found')

    # ── waypoints ────────────────────────────────────────────────────────

    def _handle_waypoints_get(self):
        file_path = self.config_dir / 'waypoints.json'
        if not file_path.exists():
            self._write_json({'error': 'waypoints not found'}, 404)
            return
        with file_path.open('r') as handler:
            data = json.load(handler)
        self._write_json(data)

    def _handle_waypoints_post(self):
        length = int(self.headers.get('Content-Length', 0))
        payload = self.rfile.read(length)
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            self._write_json({'error': 'invalid JSON'}, 400)
            return
        file_path = self.config_dir / 'waypoints.json'
        with file_path.open('w') as handler:
            json.dump(data, handler, indent=4)
        self._write_json({'ok': True}, 201)

    # ── missions (ordered waypoint sequences; run client-side) ─────────────

    def _handle_missions_get(self):
        file_path = self.config_dir / 'missions.json'
        if not file_path.exists():
            self._write_json({'missions': []})
            return
        with file_path.open('r') as handler:
            data = json.load(handler)
        self._write_json(data)

    def _handle_missions_post(self):
        length = int(self.headers.get('Content-Length', 0))
        payload = self.rfile.read(length)
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            self._write_json({'error': 'invalid JSON'}, 400)
            return
        file_path = self.config_dir / 'missions.json'
        with file_path.open('w') as handler:
            json.dump(data, handler, indent=4)
        self._write_json({'ok': True}, 201)

    # ── navigation ───────────────────────────────────────────────────────

    def _handle_command_post(self):
        bridge = self._require_bridge()
        if bridge is None:
            return
        length = int(self.headers.get('Content-Length', 0))
        payload = self.rfile.read(length)
        try:
            data = json.loads(payload)
            x = float(data['x'])
            y = float(data['y'])
            yaw = float(data.get('yaw', 0.0))
            label = data.get('label')
        except (ValueError, KeyError, json.JSONDecodeError):
            self._write_json({'error': 'invalid command payload'}, 400)
            return
        bridge.send_nav_goal(x, y, yaw, label=label)
        self._write_json({'ok': True})

    def _handle_initial_pose_post(self):
        bridge = self._require_bridge()
        if bridge is None:
            return
        length = int(self.headers.get('Content-Length', 0))
        payload = self.rfile.read(length)
        try:
            data = json.loads(payload)
            x = float(data['x'])
            y = float(data['y'])
            yaw = float(data.get('yaw', 0.0))
        except (ValueError, KeyError, json.JSONDecodeError):
            self._write_json({'error': 'invalid pose payload'}, 400)
            return
        bridge.publish_initial_pose(x, y, yaw)
        self._write_json({'ok': True})

    def _handle_cancel_goal_post(self):
        bridge = self._require_bridge()
        if bridge is None:
            return
        canceled = bridge.cancel_nav_goal()
        if canceled:
            self._write_json({'ok': True, 'message': 'Cancel requested'})
        else:
            self._write_json({'ok': False, 'message': 'No active goal to cancel'}, 409)

    def _handle_nav_status_get(self):
        bridge = self._require_bridge()
        if bridge is None:
            return
        self._write_json(bridge.get_nav_status())

    # ── teleop / motors ──────────────────────────────────────────────────

    def _handle_teleop_post(self):
        bridge = self._require_bridge()
        if bridge is None:
            return
        length = int(self.headers.get('Content-Length', 0))
        payload = self.rfile.read(length)
        try:
            data = json.loads(payload)
            linear = max(-TELEOP_MAX_LINEAR, min(TELEOP_MAX_LINEAR, float(data.get('linear', 0.0))))
            angular = max(-TELEOP_MAX_ANGULAR, min(TELEOP_MAX_ANGULAR, float(data.get('angular', 0.0))))
        except (ValueError, TypeError, json.JSONDecodeError):
            self._write_json({'error': 'invalid teleop payload'}, 400)
            return
        bridge.publish_cmd_vel(linear, angular)
        self._write_json({'ok': True})

    def _handle_motors_post(self):
        bridge = self._require_bridge()
        if bridge is None:
            return
        length = int(self.headers.get('Content-Length', 0))
        payload = self.rfile.read(length)
        try:
            data = json.loads(payload)
            enabled = bool(data.get('enabled', False))
        except json.JSONDecodeError:
            self._write_json({'error': 'invalid motors payload'}, 400)
            return
        bridge.set_motors_enabled(enabled)
        self._write_json({
            'ok': True,
            'message': f"Best-effort {'enable' if enabled else 'disable'} command published to /motors_enable "
                       "(no confirmation topic/service is known for this base -- verify on the robot).",
        })

    # ── docking (honest stub -- opennav_docking_msgs isn't installed) ──────

    def _docking_unavailable_response(self):
        self._write_json({
            'ok': False,
            'error': (
                'Docking action interface not available: opennav_docking_msgs is not installed '
                'in this environment (sudo apt install ros-humble-opennav-docking-msgs), so '
                'nav_bringup\'s custom_docking_server.py cannot run either.'
            ),
        }, 503)

    def _handle_dock_post(self):
        self._docking_unavailable_response()

    def _handle_undock_post(self):
        self._docking_unavailable_response()

    # ── read-only status endpoints ───────────────────────────────────────

    def _handle_pose_get(self):
        bridge = self._require_bridge()
        if bridge is None:
            return
        self._write_json(bridge.get_pose())

    def _handle_map_get(self):
        bridge = self._require_bridge()
        if bridge is None:
            return
        map_payload = bridge.get_map()
        if not map_payload:
            self._write_json({}, 204)
            return
        self._write_json(map_payload)

    def _handle_feedback_get(self):
        bridge = self._require_bridge()
        if bridge is None:
            return
        self._write_json(bridge.get_feedback())

    def _handle_localization_get(self):
        bridge = self._require_bridge()
        if bridge is None:
            return
        self._write_json(bridge.get_localization())

    def _handle_battery_get(self):
        bridge = self._require_bridge()
        if bridge is None:
            return
        self._write_json(bridge.get_battery())

    def _handle_diagnostics_get(self):
        bridge = self._require_bridge()
        if bridge is None:
            return
        self._write_json(bridge.get_diagnostics())

    def _handle_scan_get(self):
        bridge = self._require_bridge()
        if bridge is None:
            return
        self._write_json(bridge.get_scan())

    def _handle_odometry_get(self):
        bridge = self._require_bridge()
        if bridge is None:
            return
        self._write_json(bridge.get_odometry())

    def _handle_imu_get(self):
        bridge = self._require_bridge()
        if bridge is None:
            return
        self._write_json(bridge.get_imu())

    def _handle_joint_states_get(self):
        bridge = self._require_bridge()
        if bridge is None:
            return
        self._write_json(bridge.get_joint_states())

    def _handle_local_costmap_get(self):
        bridge = self._require_bridge()
        if bridge is None:
            return
        self._write_json(bridge.get_local_costmap())

    def _handle_global_costmap_get(self):
        bridge = self._require_bridge()
        if bridge is None:
            return
        self._write_json(bridge.get_global_costmap())

    def _handle_local_plan_get(self):
        bridge = self._require_bridge()
        if bridge is None:
            return
        self._write_json(bridge.get_local_plan())

    def _handle_global_plan_get(self):
        bridge = self._require_bridge()
        if bridge is None:
            return
        self._write_json(bridge.get_global_plan())

    def _handle_particle_cloud_get(self):
        bridge = self._require_bridge()
        if bridge is None:
            return
        self._write_json(bridge.get_particle_cloud())

    def _handle_system_status_get(self):
        bridge = self._require_bridge()
        if bridge is None:
            return
        self._write_json(bridge.get_system_status())

    # ── 3D robot model (URDF + meshes, read from daksha_description_full_body) ──

    def _handle_robot_urdf_get(self):
        if ROBOT_URDF_PATH is None:
            self._write_json(
                {'error': f'{DESCRIPTION_PKG} URDF not found -- is it built and sourced?'}, 503
            )
            return
        body = ROBOT_URDF_PATH.read_bytes()
        self.send_response(200)
        self.send_header('Content-Type', 'application/xml')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _handle_robot_mesh_get(self):
        if ROBOT_MESHES_DIR is None:
            self.send_error(503, f'{DESCRIPTION_PKG} meshes not found')
            return
        # .name strips any directory components the client sent, so this can
        # only ever resolve to a file directly inside ROBOT_MESHES_DIR --
        # no path-traversal outside it via ../ segments.
        requested = Path(self.path[len('/robot_model/meshes/'):]).name
        mesh_path = ROBOT_MESHES_DIR / requested
        if not requested or not mesh_path.is_file():
            self.send_error(404, 'Mesh not found')
            return
        body = mesh_path.read_bytes()
        self.send_response(200)
        self.send_header('Content-Type', 'application/octet-stream')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _handle_log_post(self):
        length = int(self.headers.get('Content-Length', 0))
        payload = self.rfile.read(length)
        try:
            entry = json.loads(payload)
            level = entry.get('level', 'info')
            msg = entry.get('message', '')
        except json.JSONDecodeError:
            level, msg = 'error', 'Invalid log payload'
        print(f'[WEBLOG {level.upper()}] {msg}')
        self._write_json({'ok': True})


class ReusableTCPServer(TCPServer):
    # Plain socketserver.TCPServer (unlike http.server.HTTPServer, which
    # sets this itself) defaults allow_reuse_address to False, so the
    # listening socket sits in TIME_WAIT for up to 60s after this process
    # exits -- any relaunch within that window fails with "Address already
    # in use" even though no process is actually holding the port anymore.
    allow_reuse_address = True


def start_ros_bridge():
    global ROS_BRIDGE, ROS_EXECUTOR, ROS_THREAD
    if rclpy is None:
        print('rclpy not available, ROS bridge disabled')
        return
    rclpy.init()
    ROS_BRIDGE = RosStateBridge()
    ROS_EXECUTOR = MultiThreadedExecutor()
    ROS_EXECUTOR.add_node(ROS_BRIDGE)
    ROS_THREAD = threading.Thread(target=ROS_EXECUTOR.spin, daemon=True)
    ROS_THREAD.start()


def main() -> None:
    global TELEOP_MAX_LINEAR, TELEOP_MAX_ANGULAR
    parser = argparse.ArgumentParser(description='Serve the static web_nav_site directory.')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind the HTTP server to.')
    parser.add_argument('-p', '--port', type=int, default=8000, help='Port to listen on.')
    parser.add_argument('--directory', default='static', help='Static directory relative to the script.')
    parser.add_argument('--config', default='config', help='Config directory relative to the script.')
    parser.add_argument('--max-linear', type=float, default=TELEOP_MAX_LINEAR,
                         help='Max linear speed (m/s) the joystick/WASD teleop can command.')
    parser.add_argument('--max-angular', type=float, default=TELEOP_MAX_ANGULAR,
                         help='Max angular speed (rad/s) the joystick/WASD teleop can command.')
    # parse_known_args (not parse_args): ros2 launch's Node action always
    # appends --ros-args -r __node:=... to the invocation, which this
    # argparse setup doesn't define -- parse_args() would reject it as an
    # unrecognized argument and crash on startup under `ros2 launch`/`ros2 run`.
    args, _ = parser.parse_known_args()

    TELEOP_MAX_LINEAR = args.max_linear
    TELEOP_MAX_ANGULAR = args.max_angular

    root = Path(__file__).resolve().parent
    static_dir = root / args.directory
    config_dir = root / args.config
    if not static_dir.is_dir():
        raise FileNotFoundError(f"Static directory not found: {static_dir}")
    if not config_dir.is_dir():
        raise FileNotFoundError(f"Config directory not found: {config_dir}")

    start_ros_bridge()

    handler_factory = lambda *handler_args, **handler_kwargs: NavHTTPHandler(
        *handler_args,
        static_dir=static_dir,
        config_dir=config_dir,
        **handler_kwargs
    )

    with ReusableTCPServer((args.host, args.port), handler_factory) as httpd:
        # args.host is "0.0.0.0" by default (binds every interface, already
        # reachable from any machine on the network) -- print the real
        # hostname instead, since "0.0.0.0" isn't an address anyone else can
        # actually type into a browser to reach this machine.
        display_host = f"{socket.gethostname().lower()}.local" if args.host in ("0.0.0.0", "::") else args.host
        # flush=True: stdout is fully (not line-) buffered once it's piped
        # to `ros2 launch` instead of a real terminal, so without this the
        # port never actually reaches the terminal until the process exits.
        print(f"Serving {static_dir} with config {config_dir} at http://{display_host}:{args.port}", flush=True)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print('\nServer interrupted, exiting.')
        finally:
            if ROS_EXECUTOR and ROS_BRIDGE:
                ROS_EXECUTOR.shutdown()
                ROS_BRIDGE.destroy_node()
                rclpy.shutdown()


if __name__ == '__main__':
    main()
