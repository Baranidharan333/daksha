from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from ament_index_python.packages import get_package_share_directory



import os


def generate_launch_description():

    # realpath (not abspath): with --symlink-install this launch file is a
    # symlink back to the source tree, so this still resolves to the real
    # gesture_management/recordings dir either way -- same reasoning as
    # gesture_management_app.py's _default_recordings_dir().
    default_recordings_dir = os.path.normpath(os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "..", "recordings",
    ))

    recordings_dir_arg = DeclareLaunchArgument(
        "recordings_dir",
        default_value=os.environ.get("GESTURE_RECORDINGS_DIR", default_recordings_dir),
        description="Directory containing parquet recordings",
    )

    params_file = os.path.join(
        get_package_share_directory("gesture_management"),
        "config",
        "gesture_management_params.yaml",
    )

    gesture_node = Node(
        package="gesture_management",
        executable="gesture_management_app.py",
        name="gesture_management",
        output="screen",
        parameters=[
            params_file,
            {
                "recordings_dir": LaunchConfiguration("recordings_dir"),
            },
        ],
    )

    replay_server = Node(
        package="gesture_management",
        executable="replay_server.py",
        name="replay_server",
        output="screen",
        parameters=[
            {
                "recordings_dir": LaunchConfiguration("recordings_dir"),
            }
        ],
    )

    return LaunchDescription([
        recordings_dir_arg,
        gesture_node,
        replay_server,
    ])