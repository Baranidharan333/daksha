from setuptools import setup

package_name = 'daksha_api_bridge_leader'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
         ['resource/' + package_name]),

        ('share/' + package_name,
         ['package.xml']),

        ('share/' + package_name + '/config',
         ['config/receive_cameras.yaml']),

        ('share/' + package_name + '/launch',
         ['launch/leader_bridge.launch.py']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='baranidharan',
    maintainer_email='baranidharan@example.com',
    description='Leader-side Daksha API bridge: reports local /joint_cmd to the cloud dashboard and receives dashboard-issued camera and joint_states events.',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            "joint_cmd_api_publisher = daksha_api_bridge_leader.joint_cmd_api_suscriber:main",
            "joint_states_api_subscriber = daksha_api_bridge_leader.joint_states_api_publisher:main",
            "camera_subscriber = daksha_api_bridge_leader.camera_publisher:main",
        ],
    },
)
