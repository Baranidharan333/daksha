from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    collision_padding_arg = DeclareLaunchArgument(
        "collision_padding",
        default_value="0.0",
        description="Uniform link padding (metres) MoveIt applies to every collision object before checking contact",
    )

    moveit_collision_guard_node = Node(
        package="moveit_collision_management",
        executable="moveit_collision_guard_node",
        name="moveit_collision_guard_node",
        output="screen",
        parameters=[
            {
                "collision_padding": LaunchConfiguration("collision_padding"),
            }
        ],
    )

    return LaunchDescription([
        collision_padding_arg,
        moveit_collision_guard_node,
    ])
