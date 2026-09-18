from setuptools import find_packages
from setuptools import setup

setup(
    name='daksha_msgs',
    version='0.0.1',
    packages=find_packages(
        include=('daksha_msgs', 'daksha_msgs.*')),
)
