from setuptools import setup, find_packages

package_name = 'gesture_management'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/srv', [
            'srv/StartRecording.srv',
            'srv/ReplayRecording.srv',
            'srv/PlayRecording.srv',
            'srv/PlaySequence.srv',
            'srv/SaveSequence.srv',
            'srv/DeleteSequence.srv',
            'srv/ListSequences.srv',
            'srv/GetReplayStatus.srv',
        ]),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='karthika',
    maintainer_email='karthika@todo.todo',
    description='Joint parquet recorder and replay system',
    license='Apache License 2.0',
    entry_points={
        'console_scripts': [
            'recorder_server = gesture_management.recorder_server:main',
            'replay_server = gesture_management.replay_server:main',
            'gesture_management = gesture_management.gesture_management_app:main',
        ],
    },
)