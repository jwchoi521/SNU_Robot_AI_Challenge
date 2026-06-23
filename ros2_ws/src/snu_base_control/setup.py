from glob import glob
from setuptools import setup


package_name = "snu_base_control"

setup(
    name=package_name,
    version="0.1.0",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml"]),
        (f"share/{package_name}/config", glob("config/*.yaml")),
        (f"share/{package_name}/launch", glob("launch/*.launch.py")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="SNU Robot AI Challenge Team",
    maintainer_email="team@example.com",
    description="Four-wheel base kinematics and odometry helpers.",
    license="MIT",
    entry_points={
        "console_scripts": [
            "cmd_vel_to_four_wheel = snu_base_control.cmd_vel_to_four_wheel:main",
            "four_wheel_odometry = snu_base_control.four_wheel_odometry:main",
        ],
    },
)
