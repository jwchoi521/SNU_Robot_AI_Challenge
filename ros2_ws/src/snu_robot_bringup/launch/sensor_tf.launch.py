from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def _static_tf_node(
    *,
    name: str,
    condition_arg: str,
    parent_frame: str,
    child_frame: str,
    prefix: str,
) -> Node:
    return Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        name=name,
        arguments=[
            "--x",
            LaunchConfiguration(f"{prefix}_x"),
            "--y",
            LaunchConfiguration(f"{prefix}_y"),
            "--z",
            LaunchConfiguration(f"{prefix}_z"),
            "--roll",
            LaunchConfiguration(f"{prefix}_roll"),
            "--pitch",
            LaunchConfiguration(f"{prefix}_pitch"),
            "--yaw",
            LaunchConfiguration(f"{prefix}_yaw"),
            "--frame-id",
            parent_frame,
            "--child-frame-id",
            child_frame,
        ],
        condition=IfCondition(LaunchConfiguration(condition_arg)),
    )


def generate_launch_description() -> LaunchDescription:
    return LaunchDescription(
        [
            DeclareLaunchArgument("publish_laser_tf", default_value="true"),
            DeclareLaunchArgument("publish_camera_tf", default_value="true"),
            DeclareLaunchArgument("base_frame", default_value="base_link"),
            DeclareLaunchArgument("laser_frame", default_value="laser_frame"),
            DeclareLaunchArgument("camera_frame", default_value="camera_frame"),
            DeclareLaunchArgument("laser_x", default_value="0.15"),
            DeclareLaunchArgument("laser_y", default_value="0.0"),
            DeclareLaunchArgument("laser_z", default_value="0.12"),
            DeclareLaunchArgument("laser_roll", default_value="0.0"),
            DeclareLaunchArgument("laser_pitch", default_value="0.0"),
            DeclareLaunchArgument("laser_yaw", default_value="0.0"),
            DeclareLaunchArgument("camera_x", default_value="0.12"),
            DeclareLaunchArgument("camera_y", default_value="0.0"),
            DeclareLaunchArgument("camera_z", default_value="0.18"),
            DeclareLaunchArgument("camera_roll", default_value="0.0"),
            DeclareLaunchArgument("camera_pitch", default_value="0.0"),
            DeclareLaunchArgument("camera_yaw", default_value="0.0"),
            _static_tf_node(
                name="laser_static_transform_publisher",
                condition_arg="publish_laser_tf",
                parent_frame=LaunchConfiguration("base_frame"),
                child_frame=LaunchConfiguration("laser_frame"),
                prefix="laser",
            ),
            _static_tf_node(
                name="camera_static_transform_publisher",
                condition_arg="publish_camera_tf",
                parent_frame=LaunchConfiguration("base_frame"),
                child_frame=LaunchConfiguration("camera_frame"),
                prefix="camera",
            ),
        ]
    )
