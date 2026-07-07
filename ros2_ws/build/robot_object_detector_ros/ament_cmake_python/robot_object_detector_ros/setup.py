from setuptools import find_packages
from setuptools import setup

setup(
    name='robot_object_detector_ros',
    version='0.1.0',
    packages=find_packages(
        include=('robot_object_detector_ros', 'robot_object_detector_ros.*')),
)
