from setuptools import find_packages, setup
from glob import glob

package_name = 'gen2_leader'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        (
            'share/ament_index/resource_index/packages',
            ['resource/' + package_name]
        ),
        (
            'share/' + package_name,
            ['package.xml']
        ),
        (
            'share/' + package_name + '/launch',
            glob('launch/*.py')
        ),
        (
            'share/' + package_name + '/config',
            glob('config/*.yaml')
        ),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='deeptech',
    maintainer_email='deeptech@todo.todo',
    description='Gen2 Leader Package',
    license='Apache-2.0',
    extras_require={
        'test': ['pytest'],
    },
    entry_points={
        'console_scripts': [

            'leader_raw = gen2_leader.Gen2Leader_raw:main',

            'leader_torque_toggle = gen2_leader.LeaderTorqueToggle:main',

            'leader_wifi = gen2_leader.main_with_service_wifi:main',

            'leader_mirror = gen2_leader.main_with_service_mirror_wifi:main',
            
            'leader_serial = gen2_leader.Gen2Leader_raw_serial:main',

        ],
    },
)