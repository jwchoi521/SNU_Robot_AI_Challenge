from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description() -> LaunchDescription:
    default_params = PathJoinSubstitution(
        [FindPackageShare("snu_hardware_drivers"), "config", "esp32_serial.yaml"]
    )
    dry_run = ParameterValue(LaunchConfiguration("dry_run"), value_type=bool)

    return LaunchDescription(
        [
            DeclareLaunchArgument("params_file", default_value=default_params),
            DeclareLaunchArgument("dry_run", default_value="true"),
            DeclareLaunchArgument("serial_port", default_value="/dev/ttyUSB0"),
            DeclareLaunchArgument("enable_jog_test", default_value="false"),
            Node(
                package="snu_hardware_drivers",
                executable="esp32_serial_bridge",
                name="esp32_serial_bridge",
                output="screen",
                parameters=[
                    LaunchConfiguration("params_file"),
                    {
                        "dry_run": dry_run,
                        "serial_port": LaunchConfiguration("serial_port"),
                    },
                ],
            ),
            Node(
                package="snu_hardware_drivers",
                executable="wheel_jog_test",
                name="wheel_jog_test",
                output="screen",
                parameters=[LaunchConfiguration("params_file")],
                condition=IfCondition(LaunchConfiguration("enable_jog_test")),
            ),
        ]
    )
