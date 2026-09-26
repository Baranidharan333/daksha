from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():

    dashboard_node = Node(
        package="daksha_ui",
        executable="dashboard_app.py",
        name="daksha_dashboard",
        output="screen",
    )

    viveka_camera_node = Node(
        package="daksha_ui",
        executable="viveka_camera_ui.py",
        name="daksha_viveka_camera_ui",
        output="screen",
    )

    return LaunchDescription([
        dashboard_node,
        viveka_camera_node,
    ])
