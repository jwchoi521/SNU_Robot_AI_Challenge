from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description() -> LaunchDescription:
    default_params = PathJoinSubstitution(
        [FindPackageShare("snu_robot_bringup"), "config", "nav2_params.yaml"]
    )
    localization_launch = PathJoinSubstitution(
        [FindPackageShare("nav2_bringup"), "launch", "localization_launch.py"]
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument("use_sim_time", default_value="false"),
            DeclareLaunchArgument("autostart", default_value="true"),
            DeclareLaunchArgument("map", default_value=""),
            DeclareLaunchArgument("params_file", default_value=default_params),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(localization_launch),
                launch_arguments={
                    "use_sim_time": LaunchConfiguration("use_sim_time"),
                    "autostart": LaunchConfiguration("autostart"),
                    "map": LaunchConfiguration("map"),
                    "params_file": LaunchConfiguration("params_file"),
                }.items(),
            ),
        ]
    )
