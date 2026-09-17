from setuptools import setup

package_name = 'daksha_api_bridge_follower'

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
         ['config/send_cameras.yaml']),

        ('share/' + package_name + '/launch',
         ['launch/follower_bridge.launch.py',
          'launch/camera_bridge.launch.py']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='baranidharan',
    maintainer_email='baranidharan@example.com',
    description='Follower-side Daksha API bridge: reports local camera feeds and /joint_states to the cloud dashboard and receives dashboard-issued joint_cmd events.',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            "joint_cmd_api_subscriber = daksha_api_bridge_follower.joint_cmd_api_publish:main",
            "joint_states_api_publisher = daksha_api_bridge_follower.joint_states_api_suscriber:main",
            "camera_publisher = daksha_api_bridge_follower.camera_suscriber:main",
        ],
    },
)
