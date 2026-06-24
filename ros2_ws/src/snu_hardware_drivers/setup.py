from glob import glob
from setuptools import setup


package_name = "snu_hardware_drivers"

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
    test_suite="test",
    maintainer="SNU Robot AI Challenge Team",
    maintainer_email="team@example.com",
    description="Jetson hardware drivers and bringup tests for SNU Robot AI Challenge.",
    license="MIT",
    entry_points={
        "console_scripts": [
            "esp32_serial_bridge = snu_hardware_drivers.esp32_serial_bridge:main",
            "gpio_encoder_joint_state = snu_hardware_drivers.gpio_encoder_joint_state:main",
            "gpio_four_wheel_driver = snu_hardware_drivers.gpio_four_wheel_driver:main",
            "wheel_jog_test = snu_hardware_drivers.wheel_jog_test:main",
        ],
    },
)
