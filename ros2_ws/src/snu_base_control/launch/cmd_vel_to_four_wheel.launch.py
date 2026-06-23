from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description() -> LaunchDescription:
    default_params = PathJoinSubstitution(
        [FindPackageShare("snu_base_control"), "config", "cmd_vel_to_four_wheel.yaml"]
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument("params_file", default_value=default_params),
            Node(
                package="snu_base_control",
                executable="cmd_vel_to_four_wheel",
                name="cmd_vel_to_four_wheel",
                output="screen",
                parameters=[LaunchConfiguration("params_file")],
            ),
        ]
    )
