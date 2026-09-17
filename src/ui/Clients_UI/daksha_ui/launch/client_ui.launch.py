from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():

    dashboard_node = Node(
        package="daksha_ui",
        executable="dashboard_app.py",
        name="daksha_dashboard",
        output="screen",
    )

    subui_node = Node(
        package="daksha_ui",
        executable="subui_app.py",
        name="daksha_subui",
        output="screen",
    )

    viveka_camera_node = Node(
        package="daksha_ui",
        executable="viveka_camera_ui",
        name="daksha_viveka_camera_ui",
        output="screen",
    )

    return LaunchDescription([
        dashboard_node,
        subui_node,
        viveka_camera_node,
    ])
