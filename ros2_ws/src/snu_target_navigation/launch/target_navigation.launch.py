from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description() -> LaunchDescription:
    default_params = PathJoinSubstitution(
        [FindPackageShare("snu_target_navigation"), "config", "target_navigation.yaml"]
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument("params_file", default_value=default_params),
            Node(
                package="snu_target_navigation",
                executable="target_pose_projector",
                name="target_pose_projector",
                output="screen",
                parameters=[LaunchConfiguration("params_file")],
            ),
        ]
    )
