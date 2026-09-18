from setuptools import find_packages
from setuptools import setup

setup(
    name='gesture_management',
    version='0.0.1',
    packages=find_packages(
        include=('gesture_management', 'gesture_management.*')),
)
