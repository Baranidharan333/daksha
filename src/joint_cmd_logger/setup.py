from setuptools import setup
from glob import glob

package_name = 'joint_cmd_logger'

setup(
    name=package_name,
    version='0.0.1',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
         ['resource/' + package_name]),

        ('share/' + package_name,
         ['package.xml']),

        ('share/' + package_name + '/launch',
         glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='baranidharan',
    maintainer_email='selvambharani100@gmail.com',
    description='Logs /joint_cmd and /jnt_cmt_to_ctrl JointState messages to timestamped CSV files.',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'joint_cmd_logger = joint_cmd_logger.joint_cmd_logger_node:main',
        ],
    },
)
