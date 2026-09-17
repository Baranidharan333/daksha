import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'daksha_data_collection'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='physicalai',
    maintainer_email='physicalai@todo.todo',
    description='ROS 2 dataset recording and replaying package',
    license='MIT',
    entry_points={
        'console_scripts': [
            'ros2_topic_recorder = daksha_data_collection.ros2_topic_recorder:main',
            'ros2_topic_replay = daksha_data_collection.ros2_topic_replay:main',
            'web_data_management_ui = daksha_data_collection.web_data_management_ui:main',
            'delete_episode = daksha_data_collection.delete_episode:main',
        ],
    },
)
