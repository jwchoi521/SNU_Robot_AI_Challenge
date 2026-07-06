from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def _bool_arg(name: str) -> ParameterValue:
    return ParameterValue(LaunchConfiguration(name), value_type=bool)


def _float_arg(name: str) -> ParameterValue:
    return ParameterValue(LaunchConfiguration(name), value_type=float)


def _int_arg(name: str) -> ParameterValue:
    return ParameterValue(LaunchConfiguration(name), value_type=int)


def generate_launch_description():
    return LaunchDescription(
        [
            DeclareLaunchArgument("scan_topic", default_value="/scan"),
            DeclareLaunchArgument("odom_topic", default_value="/odom"),
            DeclareLaunchArgument("detections_topic", default_value="/detections_json"),
            DeclareLaunchArgument("robot_pose_topic", default_value="/robot_pose_map"),
            DeclareLaunchArgument("object_pose_topic", default_value="/object_pose_map"),
            DeclareLaunchArgument("map_frame", default_value="map"),
            DeclareLaunchArgument("base_frame", default_value="base_link"),
            DeclareLaunchArgument("lidar_frame", default_value="lidar"),
            DeclareLaunchArgument("arena_width_m", default_value="4.0"),
            DeclareLaunchArgument("arena_height_m", default_value="4.0"),
            DeclareLaunchArgument("initial_x_m", default_value="2.0"),
            DeclareLaunchArgument("initial_y_m", default_value="2.0"),
            DeclareLaunchArgument("initial_yaw_deg", default_value="0.0"),
            DeclareLaunchArgument("lidar_x_m", default_value="0.0"),
            DeclareLaunchArgument("lidar_y_m", default_value="0.0"),
            DeclareLaunchArgument("lidar_yaw_deg", default_value="0.0"),
            DeclareLaunchArgument("min_visible_walls", default_value="2"),
            DeclareLaunchArgument("min_rays_per_wall", default_value="10"),
            DeclareLaunchArgument("publish_tf", default_value="true"),
            DeclareLaunchArgument("publish_lidar_tf", default_value="true"),
            DeclareLaunchArgument(
                "bbox_model_path",
                default_value=PathJoinSubstitution(
                    [
                        FindPackageShare("robot_nav_stack"),
                        "models",
                        "bbox_pose_anchor033.joblib",
                    ]
                ),
            ),
            Node(
                package="robot_nav_stack",
                executable="four_wall_localizer_node",
                name="four_wall_localizer_node",
                parameters=[
                    {
                        "scan_topic": LaunchConfiguration("scan_topic"),
                        "odom_topic": LaunchConfiguration("odom_topic"),
                        "pose_topic": LaunchConfiguration("robot_pose_topic"),
                        "status_topic": "/four_wall_localizer/status",
                        "map_frame": LaunchConfiguration("map_frame"),
                        "base_frame": LaunchConfiguration("base_frame"),
                        "lidar_frame": LaunchConfiguration("lidar_frame"),
                        "arena_width_m": _float_arg("arena_width_m"),
                        "arena_height_m": _float_arg("arena_height_m"),
                        "initial_x_m": _float_arg("initial_x_m"),
                        "initial_y_m": _float_arg("initial_y_m"),
                        "initial_yaw_deg": _float_arg("initial_yaw_deg"),
                        "lidar_x_m": _float_arg("lidar_x_m"),
                        "lidar_y_m": _float_arg("lidar_y_m"),
                        "lidar_yaw_deg": _float_arg("lidar_yaw_deg"),
                        "min_visible_walls": _int_arg("min_visible_walls"),
                        "min_rays_per_wall": _int_arg("min_rays_per_wall"),
                        "use_odom_prior": True,
                        "publish_tf": _bool_arg("publish_tf"),
                        "publish_lidar_tf": _bool_arg("publish_lidar_tf"),
                    }
                ],
            ),
            Node(
                package="robot_nav_stack",
                executable="object_localizer_node",
                name="object_localizer_node",
                parameters=[
                    {
                        "model_path": LaunchConfiguration("bbox_model_path"),
                        "detections_topic": LaunchConfiguration("detections_topic"),
                        "object_pose_topic": LaunchConfiguration("object_pose_topic"),
                        "target_frame": LaunchConfiguration("map_frame"),
                        "lidar_frame": LaunchConfiguration("lidar_frame"),
                        "tf_lookup_timeout_sec": 0.08,
                    }
                ],
            ),
            Node(
                package="robot_nav_stack",
                executable="approach_goal_node",
                name="approach_goal_node",
                parameters=[
                    {
                        "approach_radius_m": 0.9,
                        "angle_step_deg": 15.0,
                    }
                ],
            ),
            Node(
                package="robot_nav_stack",
                executable="semantic_obstacle_cloud_node",
                name="semantic_obstacle_cloud_node",
                parameters=[
                    {
                        "input_topic": LaunchConfiguration("object_pose_topic"),
                        "output_topic": "/semantic_obstacle_cloud",
                        "frame_id": LaunchConfiguration("map_frame"),
                        "obstacle_radius_m": 0.04,
                        "point_spacing_m": 0.02,
                        "ttl_sec": 15.0,
                        "association_radius_m": 0.12,
                        "position_smoothing_alpha": 0.35,
                        "publish_hz": 10.0,
                    }
                ],
            ),
            Node(
                package="robot_nav_stack",
                executable="wheel_controller_node",
                name="wheel_controller_node",
                parameters=[
                    {
                        "wheel_radius_m": 0.033,
                        "track_width_m": 0.30,
                    }
                ],
            ),
        ]
    )
