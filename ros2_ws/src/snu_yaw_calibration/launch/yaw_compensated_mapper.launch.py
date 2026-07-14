from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description() -> LaunchDescription:
    max_abs_yaw_cmd_rad_s = ParameterValue(
        LaunchConfiguration("max_abs_yaw_cmd_rad_s"), value_type=float
    )
    wheel_radius_m = ParameterValue(
        LaunchConfiguration("wheel_radius_m"), value_type=float
    )
    track_width_m = ParameterValue(
        LaunchConfiguration("track_width_m"), value_type=float
    )
    wheelbase_m = ParameterValue(LaunchConfiguration("wheelbase_m"), value_type=float)
    max_wheel_velocity_rad_s = ParameterValue(
        LaunchConfiguration("max_wheel_velocity_rad_s"), value_type=float
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "model_path",
                default_value="/home/cho/yaw_calibration/yaw_response_model.json",
            ),
            DeclareLaunchArgument("input_cmd_vel_topic", default_value="/cmd_vel"),
            DeclareLaunchArgument(
                "output_cmd_vel_topic", default_value="/cmd_vel_calibrated"
            ),
            DeclareLaunchArgument("wheel_command_topic", default_value="/wheel_commands"),
            DeclareLaunchArgument("max_abs_yaw_cmd_rad_s", default_value="4.0"),
            DeclareLaunchArgument("wheel_radius_m", default_value="0.033"),
            DeclareLaunchArgument("track_width_m", default_value="0.30"),
            DeclareLaunchArgument("wheelbase_m", default_value="0.235"),
            DeclareLaunchArgument("max_wheel_velocity_rad_s", default_value="50.0"),
            Node(
                package="snu_yaw_calibration",
                executable="yaw_cmd_compensator",
                name="yaw_cmd_compensator",
                output="screen",
                parameters=[
                    {
                        "model_path": LaunchConfiguration("model_path"),
                        "input_cmd_vel_topic": LaunchConfiguration("input_cmd_vel_topic"),
                        "output_cmd_vel_topic": LaunchConfiguration("output_cmd_vel_topic"),
                        "max_abs_yaw_cmd_rad_s": max_abs_yaw_cmd_rad_s,
                    }
                ],
            ),
            Node(
                package="snu_base_control",
                executable="cmd_vel_to_four_wheel",
                name="cmd_vel_to_four_wheel_calibrated",
                output="screen",
                parameters=[
                    {
                        "cmd_vel_topic": LaunchConfiguration("output_cmd_vel_topic"),
                        "wheel_command_topic": LaunchConfiguration("wheel_command_topic"),
                        "drive_model": "skid_steer",
                        "command_mode": "velocity",
                        "wheel_radius_m": wheel_radius_m,
                        "track_width_m": track_width_m,
                        "wheelbase_m": wheelbase_m,
                        "max_wheel_velocity_rad_s": max_wheel_velocity_rad_s,
                    }
                ],
            ),
        ]
    )
