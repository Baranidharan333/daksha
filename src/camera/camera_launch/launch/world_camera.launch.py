from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='realsense2_camera',
            executable='realsense2_camera_node',
            namespace='camera',
            name='world',

            parameters=[{
                'serial_no': '_313522301897',
                'depth_module.depth_profile': '640x480x15',
                'rgb_camera.color_profile': '640x480x30',
            }],

            remappings=[
                # Left camera
                ('infra1/image_rect_raw', 'left/image_raw'),
                ('infra1/camera_info', 'left/camera_info'),

                # Right camera
                ('color/image_raw', 'right/image_raw'),
                ('color/camera_info', 'right/camera_info'),
            ],
        )
    ])
