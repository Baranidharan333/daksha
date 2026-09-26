from launch import LaunchDescription
from launch.actions import SetEnvironmentVariable
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        # All UI actions and service nodes communicate on the Data Collection domain.
        SetEnvironmentVariable('ROS_DOMAIN_ID', '55'),
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
            # No `name=` here: this executable hosts several rclpy Node
            # objects in one process (the UI controller plus one
            # CameraDisplayNode per active domain). Passing `name=` makes
            # launch_ros inject a global `-r __node:=...` remap, which
            # forces every one of those nodes to the same runtime name --
            # producing "nodes share an exact name" collisions in the
            # graph. Leaving it unset lets each node keep its own
            # code-defined name (data_management_ui_controller,
            # camera_display_node, camera_display_node_domain<id>, ...).
            output='screen',
            respawn=True
        ),
        # teleop_mux removed: it was forwarding live leader→follower commands
        # causing jerking whenever the UI started. The UI is a data-collection
        # tool only — it never controls the robot directly.
    ])
