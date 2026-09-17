from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='daksha_data_collection',
            executable='ros2_topic_recorder',
            name='ros2_topic_recorder',
            output='screen',
            respawn=True
        ),
        Node(
            package='daksha_data_collection',
            executable='ros2_topic_replay',
            name='ros2_topic_replay',
            output='screen',
            respawn=True
        ),
        Node(
            package='daksha_data_collection',
            executable='web_data_management_ui',
            name='web_data_management_ui',
            output='screen',
            respawn=True
        ),
        # teleop_mux removed: it was forwarding live leader→follower commands
        # causing jerking whenever the UI started. The UI is a data-collection
        # tool only — it never controls the robot directly.
    ])
