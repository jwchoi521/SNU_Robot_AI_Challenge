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
    u_shape_pwm_max = ParameterValue(
        LaunchConfiguration("u_shape_pwm_max"), value_type=int
    )
    log_serial_writes = ParameterValue(
        LaunchConfiguration("log_serial_writes"), value_type=bool
    )
    close_gate_on_start = ParameterValue(
        LaunchConfiguration("close_gate_on_start"), value_type=bool
    )
    publish_imu = ParameterValue(LaunchConfiguration("publish_imu"), value_type=bool)
    imu_yaw_offset_deg = ParameterValue(
        LaunchConfiguration("imu_yaw_offset_deg"), value_type=float
    )
    imu_enable_retry_sec = ParameterValue(
        LaunchConfiguration("imu_enable_retry_sec"), value_type=float
    )
    imu_enable_retry_max_attempts = ParameterValue(
        LaunchConfiguration("imu_enable_retry_max_attempts"), value_type=int
    )
    max_wheel_velocity_rad_s = ParameterValue(
        LaunchConfiguration("max_wheel_velocity_rad_s"), value_type=float
    )
    encoder_counts_per_revolution = ParameterValue(
        LaunchConfiguration("encoder_counts_per_revolution"), value_type=float
    )
    front_left_motor_sign = ParameterValue(
        LaunchConfiguration("front_left_motor_sign"), value_type=float
    )
    front_right_motor_sign = ParameterValue(
        LaunchConfiguration("front_right_motor_sign"), value_type=float
    )
    rear_left_motor_sign = ParameterValue(
        LaunchConfiguration("rear_left_motor_sign"), value_type=float
    )
    rear_right_motor_sign = ParameterValue(
        LaunchConfiguration("rear_right_motor_sign"), value_type=float
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument("params_file", default_value=default_params),
            DeclareLaunchArgument("dry_run", default_value="true"),
            DeclareLaunchArgument("serial_port", default_value="/dev/ttyUSB1"),
            DeclareLaunchArgument("baud_rate", default_value="115200"),
            DeclareLaunchArgument("serial_reset_wait_sec", default_value="2.0"),
            DeclareLaunchArgument("esp32_protocol", default_value="u_shape"),
            DeclareLaunchArgument("esp32_command_mode", default_value="encoder_velocity"),
            DeclareLaunchArgument("max_power", default_value="0.35"),
            DeclareLaunchArgument("u_shape_pwm_max", default_value="120"),
            DeclareLaunchArgument("log_serial_writes", default_value="false"),
            DeclareLaunchArgument("gripper_command_topic", default_value="/gripper/command"),
            DeclareLaunchArgument("close_gate_on_start", default_value="true"),
            DeclareLaunchArgument("publish_imu", default_value="true"),
            DeclareLaunchArgument("imu_topic", default_value="/imu"),
            DeclareLaunchArgument("imu_frame", default_value="base_link"),
            DeclareLaunchArgument("imu_yaw_offset_deg", default_value="0.0"),
            DeclareLaunchArgument("imu_enable_retry_sec", default_value="1.0"),
            DeclareLaunchArgument("imu_enable_retry_max_attempts", default_value="0"),
            DeclareLaunchArgument("max_wheel_velocity_rad_s", default_value="50.0"),
            DeclareLaunchArgument("encoder_counts_per_revolution", default_value="890.3"),
            DeclareLaunchArgument("front_left_motor_sign", default_value="1.0"),
            DeclareLaunchArgument("front_right_motor_sign", default_value="1.0"),
            DeclareLaunchArgument("rear_left_motor_sign", default_value="1.0"),
            DeclareLaunchArgument("rear_right_motor_sign", default_value="1.0"),
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
                        "esp32_protocol": LaunchConfiguration("esp32_protocol"),
                        "esp32_command_mode": LaunchConfiguration("esp32_command_mode"),
                        "max_power": max_power,
                        "u_shape_pwm_max": u_shape_pwm_max,
                        "log_serial_writes": log_serial_writes,
                        "gripper_command_topic": LaunchConfiguration(
                            "gripper_command_topic"
                        ),
                        "close_gate_on_start": close_gate_on_start,
                        "publish_imu": publish_imu,
                        "imu_topic": LaunchConfiguration("imu_topic"),
                        "imu_frame": LaunchConfiguration("imu_frame"),
                        "imu_yaw_offset_deg": imu_yaw_offset_deg,
                        "imu_enable_retry_sec": imu_enable_retry_sec,
                        "imu_enable_retry_max_attempts": imu_enable_retry_max_attempts,
                        "max_wheel_velocity_rad_s": max_wheel_velocity_rad_s,
                        "encoder_counts_per_revolution": encoder_counts_per_revolution,
                        "front_left_motor_sign": front_left_motor_sign,
                        "front_right_motor_sign": front_right_motor_sign,
                        "rear_left_motor_sign": rear_left_motor_sign,
                        "rear_right_motor_sign": rear_right_motor_sign,
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
