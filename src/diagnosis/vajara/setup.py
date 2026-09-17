from setuptools import setup
from glob import glob

package_name = 'vajara'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    package_data={package_name: ['index.html']},
    include_package_data=True,
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch',
            glob('launch/*.launch.py')),
        ('share/' + package_name + '/firmware',
            glob('firmware/*.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='fxyas',
    maintainer_email='ihrphysicalai@gmail.com',
    description='Vajara power monitor bridge node (serial telemetry -> ROS 2 topic + web UI)',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'power_monitor_node = vajara.power_monitor_node:main',
        ],
    },
)
