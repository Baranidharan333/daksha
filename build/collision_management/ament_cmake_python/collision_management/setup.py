from setuptools import find_packages
from setuptools import setup

setup(
    name='collision_management',
    version='0.0.1',
    packages=find_packages(
        include=('collision_management', 'collision_management.*')),
)
