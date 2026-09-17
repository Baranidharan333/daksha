from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():

    power_monitor_node = Node(
        package="vajara",
        executable="power_monitor_node",
        name="vajara_power_monitor_node",
        output="screen",
        parameters=[
            {
                "serial_port": "/dev/ttyACM0",
                "baud_rate": 115200,
                "web_port": 8080,
            }
        ],
    )

    return LaunchDescription([
        power_monitor_node,
    ])
