import os

import yaml
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node

# Resolution order: the installed share/ dir (the normal case) -> a
# source-tree path relative to this file, so editing config/cameras.yaml
# takes effect immediately on a symlink-install without a rebuild.
try:
    CAMERAS_YAML = os.path.join(
        get_package_share_directory('camera_launch'), 'config', 'cameras.yaml'
    )
except Exception:
    CAMERAS_YAML = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), '..', 'config', 'cameras.yaml'
    )
CAMERAS_YAML = os.path.normpath(CAMERAS_YAML)

# Stream toggles nothing downstream in this workspace subscribes to (raw
# infra, point cloud, aligned depth, extra tf) -- default false per camera in
# cameras.yaml to cut USB bandwidth and CPU load. gyro/accel default false
# too: rs-enumerate-devices confirmed the world D455 and left D405 are both
# stuck on a USB 2.1 port (see lsusb -t), and the Motion Module's IIO sysfs
# nodes need udev rules this box didn't have installed, which was
# crashing/restarting the node (see rs_node_setup.cpp "Failed to open
# scan_element ... Permission denied"). Flip a camera's copy back on in
# cameras.yaml once src/camera/librealsense/scripts/setup_udev_rules.sh has
# been run and the cameras replugged.
STREAM_TOGGLE_KEYS = (
    'enable_depth', 'enable_infra1', 'enable_infra2', 'enable_gyro', 'enable_accel',
    'pointcloud.enable', 'align_depth.enable', 'publish_tf',
)


def generate_launch_description():
    with open(CAMERAS_YAML) as f:
        config = yaml.safe_load(f) or {}

    nodes = []
    for cam_id, cam in (config.get('cameras') or {}).items():
        if not cam.get('enabled', True):
            continue
        color_profile = f"{cam.get('color_resolution', '640x480')}x{cam.get('color_fps', 15)}"
        depth_profile = f"{cam.get('depth_resolution', '640x480')}x{cam.get('depth_fps', 15)}"
        stream_toggles = {key: cam.get(key, False) for key in STREAM_TOGGLE_KEYS}
        node_name = cam.get('name', 'camera')

        # image_transport advertises raw/compressed/compressedDepth/theora for
        # every image topic by default. The only way to drop the ones you
        # don't want is its own allowlist parameter, "<resolved topic, node
        # name and slashes replaced with dots>.enable_pub_plugins" (verified
        # against image_transport's publisher.cpp upstream) -- restricting it
        # to color_pub_plugins below (["compressed"] by default) removes raw,
        # compressedDepth and theora, leaving only .../color/image_raw/compressed.
        # camera_info and metadata for color are unconditional publishers in
        # realsense2_camera tied to enable_color itself (verified in
        # rs_node_setup.cpp) -- there's no parameter to drop just those two.
        color_pub_plugins_param = f"{node_name}.color.image_raw.enable_pub_plugins"

        nodes.append(Node(
            package='realsense2_camera',
            executable='realsense2_camera_node',
            namespace=cam.get('namespace', cam_id),
            name=node_name,
            parameters=[{
                **stream_toggles,
                'serial_no': cam['serial_no'],
                'depth_module.depth_profile': depth_profile,
                'rgb_camera.color_profile': color_profile,
                color_pub_plugins_param: cam.get('color_pub_plugins', ['image_transport/compressed']),
            }],
        ))

    return LaunchDescription(nodes)
