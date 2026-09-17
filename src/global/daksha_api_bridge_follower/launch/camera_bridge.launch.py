"""
Launches one camera bridge PROCESS per camera in send_cameras.yaml.

The camera node can handle every camera in a single process (its threads
are already isolated per camera), but one process each buys three things
that threads inside one interpreter cannot:

  * No shared GIL. Envelope framing and TLS writes for one camera never
    wait behind another's.
  * Independent failure. A camera whose driver dies, or whose node hits
    an exception, does not take the other feeds down with it.
  * Independent restart and tuning. Each process takes its own
    rate_limit_hz / max_inflight / wire_format, so a heavy ZED stream and
    a light wrist stream can be paced differently.

The cost is one login and one HTTPS connection pool per camera instead of
one shared set.

Cameras are read from the same send_cameras.yaml the node itself reads,
so commenting an entry out there removes its process from this launch too
- no second list to keep in sync.

    ros2 launch daksha_api_bridge_follower camera_bridge.launch.py
    ros2 launch daksha_api_bridge_follower camera_bridge.launch.py rate_limit_hz:=5.0
"""

import os

import yaml
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def _camera_ids():
    config_path = os.path.join(
        get_package_share_directory("daksha_api_bridge_follower"),
        "config", "send_cameras.yaml",
    )
    with open(config_path) as f:
        data = yaml.safe_load(f) or {}
    cameras = data.get("cameras") or []
    if not cameras:
        raise RuntimeError(f"No cameras defined in {config_path}")
    return [cam["id"] for cam in cameras]


def generate_launch_description():
    common_params = {
        "api_url": LaunchConfiguration("api_url"),
        "robot_id": LaunchConfiguration("robot_id"),
        "username": LaunchConfiguration("username"),
        "password": LaunchConfiguration("password"),
        "rate_limit_hz": LaunchConfiguration("rate_limit_hz"),
        "max_inflight": LaunchConfiguration("max_inflight"),
        "wire_format": LaunchConfiguration("wire_format"),
        "stats_period_sec": LaunchConfiguration("stats_period_sec"),
        "jpeg_quality": LaunchConfiguration("jpeg_quality"),
        "max_width": LaunchConfiguration("max_width"),
    }

    nodes = [
        # name= overrides the node name, so the four processes do not all
        # register as "camera_subscriber" - which would make ros2 node
        # list, logs and parameter sets ambiguous between them.
        Node(
            package="daksha_api_bridge_follower",
            executable="camera_publisher",
            name=f"camera_bridge_{camera_id}",
            parameters=[common_params, {"camera_id": camera_id}],
            output="screen",
        )
        for camera_id in _camera_ids()
    ]

    return LaunchDescription([
        DeclareLaunchArgument("api_url", default_value="https://daksha-v1.onrender.com"),
        DeclareLaunchArgument("robot_id", default_value="s1"),
        DeclareLaunchArgument("username", default_value="ihub"),
        DeclareLaunchArgument("password", default_value="ihub_ihr"),
        DeclareLaunchArgument("rate_limit_hz", default_value="10.0"),
        DeclareLaunchArgument("max_inflight", default_value="4"),
        DeclareLaunchArgument(
            "wire_format", default_value="base85",
            description="base85 survives a send_text() backend; binary is 25% smaller",
        ),
        DeclareLaunchArgument("stats_period_sec", default_value="1.0"),
        DeclareLaunchArgument(
            "jpeg_quality", default_value="0",
            description="0 forwards the camera's own JPEG untouched; 1-100 re-encodes",
        ),
        DeclareLaunchArgument(
            "max_width", default_value="0",
            description="0 keeps the source size; e.g. 640 downscales before re-encoding",
        ),
        *nodes,
    ])
