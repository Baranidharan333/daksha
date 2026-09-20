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
                executable="quest_tf_switch",
                emulate_tty=True,
                parameters=[{"mirror": False}],
            ),
            Node(
                package="vr_teleop",
                executable="quest_tf_to_pose",
                emulate_tty=True,
            ),
            # quest_tf is deliberately not started here: it broadcasts the same
            # world -> quest_head/quest_left/quest_right frames as
            # quest_tf_switch, so running both puts two sources on /tf for the
            # same frames. They agree today, but the moment mirror is enabled on
            # the switch, tf2 interleaves mirrored and un-mirrored transforms.
        ]
    )
