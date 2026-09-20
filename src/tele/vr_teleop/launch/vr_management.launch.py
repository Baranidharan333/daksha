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
            # vr_pose_relay is deliberately not started here: it published the
            # raw, unconverted /quest/*/pose straight onto /left/pose and
            # /right/pose, the same topics quest_tf_to_pose owns, so ik_node saw
            # Unity and ROS coordinate conventions interleaved. quest_tf_to_pose
            # supersedes it and now carries the /vr_enable service too.
            Node(
                package="vr_teleop",
                executable="vr_gripper_ctrl",
                emulate_tty=True,
            ),
            Node(
                package="vr_teleop",
                executable="vr_management_ui",
                emulate_tty=True,
            ),
            # Node(
            #     package="kinematics",
            #     executable="ik_node",
            #     output="screen",
            # )
        ]
    )
