from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():

    web_nav_site_node = Node(
        package="web_nav_site",
        executable="server.py",
        name="web_nav_site",
        output="screen",
        # Without this, ros2 launch pipes the process's stdout through a
        # pipe instead of a pty, which Python treats as non-interactive and
        # fully buffers -- the "Serving ... at http://..." line then never
        # reaches this terminal until the process exits.
        emulate_tty=True,
    )

    return LaunchDescription([
        web_nav_site_node,
    ])
