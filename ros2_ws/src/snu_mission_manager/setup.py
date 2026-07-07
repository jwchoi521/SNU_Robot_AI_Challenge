from glob import glob
from setuptools import setup


package_name = "snu_mission_manager"

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
    description="Mission state machines for target pickup and drop-off.",
    license="MIT",
    entry_points={
        "console_scripts": [
            "pick_place_mission_manager = snu_mission_manager.pick_place_mission_manager:main",
        ],
    },
)
