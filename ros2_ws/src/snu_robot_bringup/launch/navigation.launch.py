from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from nav2_common.launch import RewrittenYaml
from launch_ros.substitutions import FindPackageShare


def generate_launch_description() -> LaunchDescription:
    default_params = PathJoinSubstitution(
        [FindPackageShare("snu_robot_bringup"), "config", "nav2_params.yaml"]
    )
    nav2_launch = PathJoinSubstitution(
        [FindPackageShare("nav2_bringup"), "launch", "navigation_launch.py"]
    )
    # nav2_params.yaml의 inflation_radius를 launch 옵션으로 덮어쓴다.
    configured_params = RewrittenYaml(
        source_file=LaunchConfiguration("params_file"),
        root_key="",
        param_rewrites={
            "inflation_radius": LaunchConfiguration("nav2_inflation_radius"),
        },
        convert_types=True,
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument("use_sim_time", default_value="false"),
            DeclareLaunchArgument("autostart", default_value="true"),
            DeclareLaunchArgument("params_file", default_value=default_params),
            DeclareLaunchArgument("nav2_inflation_radius", default_value="0.16"),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(nav2_launch),
                launch_arguments={
                    "use_sim_time": LaunchConfiguration("use_sim_time"),
                    "autostart": LaunchConfiguration("autostart"),
                    "params_file": configured_params,
                }.items(),
            ),
        ]
    )
