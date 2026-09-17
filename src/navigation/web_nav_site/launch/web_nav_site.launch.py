from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():

    web_nav_site_node = Node(
        package="web_nav_site",
        executable="server.py",
        name="web_nav_site",
        output="screen",
    )

    return LaunchDescription([
        web_nav_site_node,
    ])
