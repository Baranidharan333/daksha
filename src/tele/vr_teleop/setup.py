import os

from setuptools import setup

package_name = "vr_teleop"
share_dir = os.path.join("share", package_name)

setup(
    name=package_name,
    version="0.0.1",
    packages=[
        package_name,
        package_name + ".main_scripts",
        package_name + ".bridge_nodes",
    ],
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        (share_dir, ["package.xml"]),
        (os.path.join(share_dir, "launch"), [
            "launch/endpoint.py",
            "launch/vr_control.py",
            "launch/vr_control_mirror.py",
            "launch/vr_control_switch.py",
        ]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Unity Robotics",
    maintainer_email="unity-robotics@unity3d.com",
    description="ROS TCP Endpoint Unity Integration (ROS2 version)",
    license="Apache 2.0",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "default_server_endpoint = vr_teleop.bridge_nodes.default_server_endpoint:main",
            "quest_tf = vr_teleop.main_scripts.quest_tf:main",
            "quest_tf_mirror = vr_teleop.main_scripts.quest_tf_mirror:main",
            "quest_tf_switch = vr_teleop.main_scripts.quest_tf_switch:main",
            "quest_tf_to_pose = vr_teleop.main_scripts.quest_tf_to_pose:main",
            "vr_pose_relay = vr_teleop.main_scripts.vr_pose_relay:main",
            "vr_gripper_ctrl = vr_teleop.main_scripts.vr_gripper_ctrl:main",
            "vr_management_ui = vr_teleop.main_scripts.vr_management_ui:main",
        ]
    },
)
