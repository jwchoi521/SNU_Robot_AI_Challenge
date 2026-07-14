from glob import glob
from setuptools import setup


package_name = "snu_yaw_calibration"

setup(
    name=package_name,
    version="0.1.0",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml"]),
        (f"share/{package_name}", glob("*.md")),
        (f"share/{package_name}/launch", glob("launch/*.launch.py")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    test_suite="test",
    maintainer="SNU Robot AI Challenge Team",
    maintainer_email="team@example.com",
    description="Yaw-rate response calibration tools for the SNU four-wheel base.",
    license="MIT",
    entry_points={
        "console_scripts": [
            "yaw_calibration_collector = snu_yaw_calibration.collector_node:main",
            "train_yaw_response_model = snu_yaw_calibration.train_yaw_response_model:main",
            "yaw_cmd_compensator = snu_yaw_calibration.yaw_cmd_compensator_node:main",
        ],
    },
)
