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

        # API -> Follower: republishes dashboard-issued joint_cmd events.
        Node(
            package="daksha_api_bridge_follower",
            executable="joint_cmd_api_subscriber",
            parameters=[common_params],
            output="screen",
        ),
        # Follower -> API: forwards local /joint_states to the dashboard.
        Node(
            package="daksha_api_bridge_follower",
            executable="joint_states_api_publisher",
            parameters=[common_params],
            output="screen",
        ),
        # Follower -> API: forwards local camera feed(s) to the dashboard.
        Node(
            package="daksha_api_bridge_follower",
            executable="camera_publisher",
            parameters=[common_params],
            output="screen",
        ),
    ])
