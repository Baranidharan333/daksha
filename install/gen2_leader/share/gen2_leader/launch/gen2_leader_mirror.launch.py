from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():

    return LaunchDescription([

        Node(
            package='gen2_leader',
            executable='leader_raw',
            name='leader_raw',
            output='screen'
        ),

        Node(
            package='gen2_leader',
            executable='leader_torque_toggle',
            name='leader_torque_toggle',
            output='screen'
        ),

        Node(
            package='gen2_leader',
            executable='leader_mirror',
            name='leader_mirror',
            output='screen'
        ),

    ])
