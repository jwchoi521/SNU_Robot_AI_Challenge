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
    baud_rate = ParameterValue(LaunchConfiguration("baud_rate"), value_type=int)
    serial_reset_wait_sec = ParameterValue(
        LaunchConfiguration("serial_reset_wait_sec"), value_type=float
    )
    max_power = ParameterValue(LaunchConfiguration("max_power"), value_type=float)

    return LaunchDescription(
        [
            DeclareLaunchArgument("params_file", default_value=default_params),
            DeclareLaunchArgument("dry_run", default_value="true"),
            DeclareLaunchArgument("serial_port", default_value="/dev/ttyUSB0"),
            DeclareLaunchArgument("baud_rate", default_value="115200"),
            DeclareLaunchArgument("serial_reset_wait_sec", default_value="2.0"),
            DeclareLaunchArgument("max_power", default_value="0.12"),
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
                        "baud_rate": baud_rate,
                        "serial_reset_wait_sec": serial_reset_wait_sec,
                        "max_power": max_power,
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
