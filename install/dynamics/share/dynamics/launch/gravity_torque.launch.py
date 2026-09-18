import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    urdf_path_arg = DeclareLaunchArgument(
        "urdf_path",
        default_value=os.path.join(
            get_package_share_directory("daksha_description_full_body"),
            "urdf",
            "robot.urdf",
        ),
    )
    root_link_arg = DeclareLaunchArgument("root_link", default_value="base_link")
    right_leaf_link_arg = DeclareLaunchArgument("right_leaf_link", default_value="right_link_8")
    left_leaf_link_arg = DeclareLaunchArgument("left_leaf_link", default_value="left_link_8")

    gravity_torque_node = Node(
        package="dynamics",
        executable="gravity_torque_node",
        name="gravity_torque_node",
        output="screen",
        parameters=[
            {
                "urdf_path": LaunchConfiguration("urdf_path"),
                "root_link": LaunchConfiguration("root_link"),
                "right_leaf_link": LaunchConfiguration("right_leaf_link"),
                "left_leaf_link": LaunchConfiguration("left_leaf_link"),
            }
        ],
    )

    return LaunchDescription([
        urdf_path_arg,
        root_link_arg,
        right_leaf_link_arg,
        left_leaf_link_arg,
        gravity_torque_node,
    ])
