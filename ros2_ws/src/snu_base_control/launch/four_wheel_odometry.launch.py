from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description() -> LaunchDescription:
    default_params = PathJoinSubstitution(
        [FindPackageShare("snu_base_control"), "config", "four_wheel_odometry.yaml"]
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument("params_file", default_value=default_params),
            Node(
                package="snu_base_control",
                executable="four_wheel_odometry",
                name="four_wheel_odometry",
                output="screen",
                parameters=[LaunchConfiguration("params_file")],
            ),
        ]
    )
