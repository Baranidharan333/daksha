from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    common_params = {
        "api_url": LaunchConfiguration("api_url"),
        "robot_id": LaunchConfiguration("robot_id"),
        "username": LaunchConfiguration("username"),
        "password": LaunchConfiguration("password"),
    }

    return LaunchDescription([
        DeclareLaunchArgument("api_url", default_value="https://daksha-v1.onrender.com"),
        DeclareLaunchArgument("robot_id", default_value="s1"),
        DeclareLaunchArgument("username", default_value="ihub"),
        DeclareLaunchArgument("password", default_value="ihub_ihr"),

        # Leader -> API: forwards local /joint_cmd to the dashboard.
        Node(
            package="daksha_api_bridge_leader",
            executable="joint_cmd_api_publisher",
            parameters=[common_params],
            output="screen",
        ),
        # API -> Leader: republishes dashboard-issued joint_states events.
        Node(
            package="daksha_api_bridge_leader",
            executable="joint_states_api_subscriber",
            parameters=[common_params],
            output="screen",
        ),
        # API -> Leader: republishes dashboard-issued camera frames.
        Node(
            package="daksha_api_bridge_leader",
            executable="camera_subscriber",
            parameters=[common_params],
            output="screen",
        ),
    ])
