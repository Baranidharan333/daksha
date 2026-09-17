from setuptools import setup
from glob import glob

package_name = 'gen2'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
         ['resource/' + package_name]),

        ('share/' + package_name,
         ['package.xml']),

        ('share/' + package_name + '/launch',
         glob('launch/*.launch.py')),
        ('share/' + package_name + '/config',
         glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='baranidharan',
    maintainer_email='baranidharan@example.com',
    description='Gen2 bringup package',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            "joint_cmd = gen2.joint_cmd:main",
            "joint_cmd_web_ui = gen2.joint_cmd_web_ui:main",
            "GravityToJointCmd = gen2.GravityToJointCmd:main",
            "joint_cmd_publisher_from_joint_sates = gen2.joint_cmd_publisher_from_joint_sates:main",
            "teach_mode_node = gen2.teach_mode_node:main",
            "gravity_scale_setter = gen2.gravity_scale_setter:main",
            "gravity_ff_tuner = gen2.gravity_ff_tuner:main",
            "mode_toggler = gen2.mode_toggler:main",
            "vcan_bridge = gen2.vcan_bridge:main",
            "leader_controller_ui = gen2.leader_controller_ui:main",
            "battery_info = gen2.battery_info:main",
            "HomeMoveService = gen2.HomeMoveService:main",
            "arm_recovery_watchdog = gen2.arm_recovery_watchdog:main",
            ],
    },
)