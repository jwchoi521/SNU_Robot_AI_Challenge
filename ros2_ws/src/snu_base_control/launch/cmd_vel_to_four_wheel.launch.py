from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description() -> LaunchDescription:
    default_params = PathJoinSubstitution(
        [FindPackageShare("snu_base_control"), "config", "cmd_vel_to_four_wheel.yaml"]
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument("params_file", default_value=default_params),
            DeclareLaunchArgument(
                "startup_escape_active_topic",
                default_value="/startup_escape/active",
            ),
            DeclareLaunchArgument(
                "startup_escape_block_on_start",
                default_value="false",
            ),
            Node(
                package="snu_base_control",
                executable="cmd_vel_to_four_wheel",
                name="cmd_vel_to_four_wheel",
                output="screen",
                parameters=[
                    LaunchConfiguration("params_file"),
                    {
                        "startup_escape_active_topic": LaunchConfiguration(
                            "startup_escape_active_topic"
                        ),
                        "startup_escape_block_on_start": ParameterValue(
                            LaunchConfiguration("startup_escape_block_on_start"),
                            value_type=bool,
                        ),
                    },
                ],
            ),
        ]
    )
