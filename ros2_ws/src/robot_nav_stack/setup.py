from setuptools import setup


package_name = "robot_nav_stack"

setup(
    name=package_name,
    version="0.1.0",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        ("share/" + package_name + "/config", ["config/nav2_smac_reeds_shepp.yaml"]),
        ("share/" + package_name + "/launch", ["launch/robot_nav_stack.launch.py"]),
        (
            "share/" + package_name + "/models",
            [
                "models/bbox_pose_anchor033.joblib",
                "models/bbox_pose_anchor033.cppbin",
            ],
        ),
    ],
    install_requires=[
        "setuptools",
        "joblib",
        "numpy",
        "pandas",
        "scikit-learn",
    ],
    zip_safe=True,
    maintainer="TODO",
    maintainer_email="todo@example.com",
    description="Camera/lidar object localization and navigation helpers.",
    license="MIT",
    entry_points={
        "console_scripts": [
            "four_wall_localizer_node = robot_nav_stack.four_wall_localizer_node:main",
            "rect_wall_localizer_node = robot_nav_stack.rect_wall_localizer_node:main",
            "yolo_detection_adapter_node = robot_nav_stack.yolo_detection_adapter_node:main",
            "object_localizer_node = robot_nav_stack.object_localizer_node:main",
            "object_track_fusion_node = robot_nav_stack.object_track_fusion_node:main",
            "distance_annotator_node = robot_nav_stack.distance_annotator_node:main",
            "bbox_goal_navigator_node = robot_nav_stack.bbox_goal_navigator_node:main",
            "semantic_obstacle_cloud_node = robot_nav_stack.semantic_obstacle_cloud_node:main",
            "mapping_debug_monitor_node = robot_nav_stack.mapping_debug_monitor_node:main",
            "nav2_startup_gate_node = robot_nav_stack.nav2_startup_gate_node:main",
            "direct_goal_controller_node = robot_nav_stack.direct_goal_controller_node:main",
            "approach_goal_node = robot_nav_stack.approach_goal_node:main",
            "pure_pursuit_node = robot_nav_stack.pure_pursuit_node:main",
            "wheel_controller_node = robot_nav_stack.wheel_controller_node:main",
        ],
    },
)
