from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description() -> LaunchDescription:
    default_params = PathJoinSubstitution(
        [FindPackageShare("snu_mission_manager"), "config", "pick_place_mission.yaml"]
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument("params_file", default_value=default_params),
            Node(
                package="snu_mission_manager",
                executable="pick_place_mission_manager",
                name="pick_place_mission_manager",
                output="screen",
                parameters=[LaunchConfiguration("params_file")],
            ),
        ]
    )
