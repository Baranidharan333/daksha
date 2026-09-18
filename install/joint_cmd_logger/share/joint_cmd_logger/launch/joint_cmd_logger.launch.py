import os

from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration


def generate_launch_description():

    log_dir_arg = DeclareLaunchArgument(
        "log_dir",
        default_value=os.path.expanduser("~/.ros/joint_cmd_logger_logs"),
        description="Directory to write the /joint_cmd and /jnt_cmt_to_ctrl CSV logs into",
    )

    logger_node = Node(
        package="joint_cmd_logger",
        executable="joint_cmd_logger",
        name="joint_cmd_logger",
        output="screen",
        parameters=[{"log_dir": LaunchConfiguration("log_dir")}],
    )

    return LaunchDescription([
        log_dir_arg,
        logger_node,
    ])
