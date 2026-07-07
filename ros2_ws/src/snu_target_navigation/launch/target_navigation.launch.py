from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description() -> LaunchDescription:
    default_params = PathJoinSubstitution(
        [FindPackageShare("snu_target_navigation"), "config", "target_navigation.yaml"]
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument("params_file", default_value=default_params),
            DeclareLaunchArgument("enable_path_feedback", default_value="true"),
            Node(
                package="snu_target_navigation",
                executable="semantic_object_projector",
                name="semantic_object_projector",
                output="screen",
                parameters=[LaunchConfiguration("params_file")],
            ),
            Node(
                package="snu_target_navigation",
                executable="semantic_object_registry",
                name="semantic_object_registry",
                output="screen",
                parameters=[LaunchConfiguration("params_file")],
            ),
            Node(
                package="snu_target_navigation",
                executable="path_feedback_monitor",
                name="path_feedback_monitor",
                output="screen",
                parameters=[LaunchConfiguration("params_file")],
                condition=IfCondition(LaunchConfiguration("enable_path_feedback")),
            ),
        ]
    )
