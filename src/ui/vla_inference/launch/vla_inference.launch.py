"""Bring up the VLA inference command console.

Reads this package's own ROS parameter file from its share/, so the console
launches without any other package being built. The node's settings live
under `vla_inference.*`:

    ros2 param get /vla_inference vla_inference.port
    ros2 param get /vla_inference vla_inference.instruction_topic

ROS_DOMAIN_ID cannot be a ROS parameter - DDS reads it during rclpy.init(),
before any node exists to hold one - so this file reads that single key out of
the YAML itself and exports it before the node starts.
"""

import os

import yaml
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, SetEnvironmentVariable
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

DEFAULT_CONFIG = os.path.join(
    get_package_share_directory("vla_inference"), "config", "vla_inference.yaml"
)


def _domain_id(config_path: str, default: str = "33") -> str:
    """ros.domain_id out of the parameter file, for the environment variable."""
    try:
        with open(config_path) as f:
            document = yaml.safe_load(f) or {}
        return str(document["/**"]["ros__parameters"]["ros"]["domain_id"])
    except Exception as exc:
        print(f"[vla_inference.launch] could not read ros.domain_id from "
              f"{config_path} ({exc}); falling back to {default}")
        return default


def generate_launch_description():
    config_arg = DeclareLaunchArgument(
        "config_file",
        default_value=DEFAULT_CONFIG,
        description="ROS parameter file to configure the console with.",
    )
    config_file = LaunchConfiguration("config_file")

    console = Node(
        package="vla_inference",
        executable="vla_inference_app.py",
        name="vla_inference",
        output="screen",
        parameters=[config_file],
    )

    return LaunchDescription([
        config_arg,
        # Always from the default file: a launch argument is not resolvable at
        # this point, so overriding config_file changes the node's parameters
        # but not the domain. Set ROS_DOMAIN_ID yourself if you need both.
        SetEnvironmentVariable("ROS_DOMAIN_ID", _domain_id(DEFAULT_CONFIG)),
        console,
    ])
