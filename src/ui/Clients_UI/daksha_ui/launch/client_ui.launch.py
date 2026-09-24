"""Bring up the daksha_ui Flask apps with the shared ROS parameters.

The instruction console that used to launch here now lives in its own
package: ros2 launch vla_inference vla_inference.launch.py

Settings come from this package's own ROS 2 parameter file, installed at
share/daksha_ui/config/daksha_ui.yaml. It is self-contained; nothing else is
loaded. Each app reads its settings as ordinary ROS parameters:

    ros2 param list /daksha_dashboard
    ros2 param get  /daksha_dashboard network.daksha_ui_port

ROS_DOMAIN_ID is the exception. DDS reads it during rclpy.init(), before any
node exists to hold a parameter, so it cannot be applied as one. This file
reads that single key out of the YAML itself and exports it with
SetEnvironmentVariable before the nodes start - which is why the nodes end up
on the robot's domain without any of them hardcoding it.
"""

import os

import yaml
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import SetEnvironmentVariable
from launch_ros.actions import Node

CONFIG = os.path.join(
    get_package_share_directory("daksha_ui"), "config", "daksha_ui.yaml"
)


def _domain_id(config_path: str, default: str = "33") -> str:
    """ros.domain_id out of the parameter file, for the environment variable."""
    try:
        with open(config_path) as f:
            document = yaml.safe_load(f) or {}
        value = document["/**"]["ros__parameters"]["ros"]["domain_id"]
        return str(value)
    except Exception as exc:
        print(f"[client_ui.launch] could not read ros.domain_id from "
              f"{config_path} ({exc}); falling back to {default}")
        return default


def generate_launch_description():
    # config_file points at daksha_ui.yaml because that is where
    # joint_calibration lives, and the dashboard's calibration editor writes
    # its changes back to that file.
    parameters = [CONFIG, {"config_file": CONFIG}]

    dashboard_node = Node(
        package="daksha_ui",
        executable="dashboard_app.py",
        name="daksha_dashboard",
        output="screen",
        parameters=parameters,
    )

    viveka_camera_node = Node(
        package="daksha_ui",
        executable="viveka_camera_ui.py",
        name="daksha_viveka_camera_ui",
        output="screen",
        # --ros is what makes it subscribe to the camera topics (and read its
        # parameters) instead of proxying the TriView gateway.
        arguments=["--ros"],
        parameters=parameters,
    )

    return LaunchDescription([
        SetEnvironmentVariable("ROS_DOMAIN_ID", _domain_id(CONFIG)),
        dashboard_node,
        viveka_camera_node,
    ])
