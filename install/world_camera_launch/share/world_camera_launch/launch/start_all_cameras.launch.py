from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():

    # ---------------- World Camera (D455) ----------------
    world = Node(
        package='realsense2_camera',
        executable='realsense2_camera_node',
        namespace='camera',
        name='world',
        parameters=[{
            'serial_no': '_313522301897',
            'depth_module.depth_profile': '640x480x15',
            'rgb_camera.color_profile': '640x480x30',
        }]
    )

    # ---------------- Right Arm Camera (D405) ----------------
    right = Node(
        package='realsense2_camera',
        executable='realsense2_camera_node',
        namespace='right',
        name='camera',
        parameters=[{
            'serial_no': '_260322273428',
            'depth_module.depth_profile': '640x480x30',
            'rgb_camera.color_profile': '640x480x30',
        }]
    )

    # ---------------- Left Arm Camera (D405) ----------------
    left = Node(
        package='realsense2_camera',
        executable='realsense2_camera_node',
        namespace='left',
        name='camera',
        parameters=[{
            'serial_no': '_260322274109',
            'depth_module.depth_profile': '640x480x30',
            'rgb_camera.color_profile': '640x480x30',
        }]
    )

    return LaunchDescription([
        world,
        right,
        left,
    ])
