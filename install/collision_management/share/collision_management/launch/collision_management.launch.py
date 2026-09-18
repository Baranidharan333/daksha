from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    protective_margin_arg = DeclareLaunchArgument(
        "protective_margin",
        default_value="0.005",
        description="Self-collision distance threshold (metres) for the protective (geometric) guard",
    )

    reactive_effort_threshold_arg = DeclareLaunchArgument(
        "reactive_effort_threshold",
        default_value="5.0",
        description="Measured-vs-commanded effort mismatch threshold (N*m) for the reactive guard",
    )

    collision_guard_node = Node(
        package="collision_management",
        executable="collision_guard_node.py",
        name="collision_guard_node",
        output="screen",
        parameters=[
            {
                "protective_margin": LaunchConfiguration("protective_margin"),
                "reactive_effort_threshold": LaunchConfiguration("reactive_effort_threshold"),
            }
        ],
    )

    return LaunchDescription([
        protective_margin_arg,
        reactive_effort_threshold_arg,
        collision_guard_node,
    ])
