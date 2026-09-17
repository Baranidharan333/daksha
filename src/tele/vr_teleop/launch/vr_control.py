from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription(
        [
            Node(
                package="vr_teleop",
                executable="default_server_endpoint",
                emulate_tty=True,
                parameters=[{"ROS_IP": "0.0.0.0"}, {"ROS_TCP_PORT": 10000}],
            ),
            Node(
                package="vr_teleop",
                executable="quest_tf",
                emulate_tty=True,
            ),
            Node(
                package="vr_teleop",
                executable="quest_tf_to_pose",
                emulate_tty=True,
            ),
        ]
    )
