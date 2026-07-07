from setuptools import find_packages
from setuptools import setup

setup(
    name='snu_robot_interfaces',
    version='0.1.0',
    packages=find_packages(
        include=('snu_robot_interfaces', 'snu_robot_interfaces.*')),
)
