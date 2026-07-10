from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
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
            DeclareLaunchArgument("odom_topic", default_value="/odometry/filtered"),
            DeclareLaunchArgument("imu_topic", default_value="/imu"),
            DeclareLaunchArgument("image_topic", default_value="/camera/image_raw"),
            DeclareLaunchArgument("yolo_detections_topic", default_value="/shape_yolo/detections"),
            DeclareLaunchArgument("detections_topic", default_value="/detections_json"),
            DeclareLaunchArgument(
                "classifications_topic",
                default_value="/cube_fruit/classifications",
            ),
            DeclareLaunchArgument(
                "distance_annotated_topic",
                default_value="/cube_fruit/annotated_image_distance",
            ),
            DeclareLaunchArgument("robot_pose_topic", default_value="/robot_pose_map"),
            DeclareLaunchArgument("object_pose_topic", default_value="/object_pose_map"),
            DeclareLaunchArgument("map_frame", default_value="map"),
            DeclareLaunchArgument("odom_frame", default_value="odom"),
            DeclareLaunchArgument("base_frame", default_value="base_link"),
            DeclareLaunchArgument("lidar_frame", default_value="lidar"),
            DeclareLaunchArgument("object_source_frame", default_value="base_link"),
            DeclareLaunchArgument("arena_width_m", default_value="4.0"),
            DeclareLaunchArgument("arena_height_m", default_value="4.0"),
            DeclareLaunchArgument("arena_origin", default_value="center"),
            DeclareLaunchArgument("initial_x_m", default_value="1.8"),
            DeclareLaunchArgument("initial_y_m", default_value="-1.8"),
            DeclareLaunchArgument("initial_yaw_deg", default_value="90.0"),
            DeclareLaunchArgument("lidar_x_m", default_value="0.0"),
            DeclareLaunchArgument("lidar_y_m", default_value="0.0"),
            DeclareLaunchArgument("lidar_yaw_deg", default_value="0.0"),
            DeclareLaunchArgument("use_imu_yaw_prior", default_value="true"),
            DeclareLaunchArgument("max_imu_age_sec", default_value="0.5"),
            DeclareLaunchArgument("max_rays", default_value="60"),
            DeclareLaunchArgument("min_rays", default_value="40"),
            DeclareLaunchArgument("opt_iterations", default_value="1"),
            DeclareLaunchArgument("min_visible_walls", default_value="2"),
            DeclareLaunchArgument("min_rays_per_wall", default_value="10"),
            DeclareLaunchArgument("use_global_seed_search_on_first_scan", default_value="false"),
            DeclareLaunchArgument("use_symmetry_seeds", default_value="false"),
            DeclareLaunchArgument("global_seed_step_m", default_value="0.75"),
            DeclareLaunchArgument("global_seed_yaw_step_deg", default_value="90.0"),
            DeclareLaunchArgument("adapter_min_confidence", default_value="0.8"),
            DeclareLaunchArgument("adapter_max_detections_per_frame", default_value="1"),
            DeclareLaunchArgument("adapter_max_output_hz", default_value="2.0"),
            DeclareLaunchArgument("detection_stamp_mode", default_value="header"),
            DeclareLaunchArgument("max_header_stamp_offset_sec", default_value="2.0"),
            DeclareLaunchArgument("tf_lookup_timeout_sec", default_value="0.0"),
            DeclareLaunchArgument("fallback_to_latest_tf", default_value="false"),
            DeclareLaunchArgument("latest_tf_max_extrapolation_sec", default_value="3.0"),
            DeclareLaunchArgument("pending_detection_timeout_sec", default_value="0.2"),
            DeclareLaunchArgument("max_pending_detections", default_value="3"),
            DeclareLaunchArgument("enable_distance_overlay", default_value="false"),
            DeclareLaunchArgument("enable_bbox_goal_navigation", default_value="false"),
            DeclareLaunchArgument("enable_semantic_obstacle_cloud", default_value="true"),
            DeclareLaunchArgument("semantic_obstacle_ttl_sec", default_value="0.75"),
            DeclareLaunchArgument(
                "semantic_obstacle_association_radius_m",
                default_value="0.12",
            ),
            DeclareLaunchArgument("bbox_goal_target_topic", default_value="/object_pose_map"),
            DeclareLaunchArgument("bbox_goal_pose_topic", default_value="/bbox_goal_pose"),
            DeclareLaunchArgument(
                "bbox_goal_status_topic",
                default_value="/bbox_goal_navigator/status",
            ),
            DeclareLaunchArgument("bbox_goal_nav_action_name", default_value="navigate_to_pose"),
            DeclareLaunchArgument("bbox_goal_send_nav2_goal", default_value="true"),
            DeclareLaunchArgument("bbox_goal_publish_mission_events", default_value="true"),
            DeclareLaunchArgument("bbox_goal_approach_distance_m", default_value="0.0"),
            DeclareLaunchArgument("bbox_goal_reached_tolerance_m", default_value="0.12"),
            DeclareLaunchArgument("bbox_goal_min_separation_m", default_value="0.15"),
            DeclareLaunchArgument("bbox_goal_max_target_age_sec", default_value="1.5"),
            DeclareLaunchArgument("bbox_goal_target_selection_mode", default_value="nearest"),
            DeclareLaunchArgument(
                "bbox_goal_target_association_radius_m",
                default_value="0.15",
            ),
            DeclareLaunchArgument("bbox_goal_max_tracked_targets", default_value="20"),
            DeclareLaunchArgument("bbox_goal_margin_m", default_value="0.20"),
            DeclareLaunchArgument("enable_mapping_debug", default_value="true"),
            DeclareLaunchArgument("mapping_debug_period_sec", default_value="1.0"),
            DeclareLaunchArgument(
                "mapping_debug_topic",
                default_value="/robot_nav_stack/debug_state",
            ),
            DeclareLaunchArgument("publish_tf", default_value="true"),
            DeclareLaunchArgument("wall_tf_mode", default_value="map_to_base"),
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
                        "imu_topic": LaunchConfiguration("imu_topic"),
                        "pose_topic": LaunchConfiguration("robot_pose_topic"),
                        "status_topic": "/four_wall_localizer/status",
                        "map_frame": LaunchConfiguration("map_frame"),
                        "odom_frame": LaunchConfiguration("odom_frame"),
                        "base_frame": LaunchConfiguration("base_frame"),
                        "lidar_frame": LaunchConfiguration("lidar_frame"),
                        "arena_width_m": _float_arg("arena_width_m"),
                        "arena_height_m": _float_arg("arena_height_m"),
                        "arena_origin": LaunchConfiguration("arena_origin"),
                        "initial_x_m": _float_arg("initial_x_m"),
                        "initial_y_m": _float_arg("initial_y_m"),
                        "initial_yaw_deg": _float_arg("initial_yaw_deg"),
                        "lidar_x_m": _float_arg("lidar_x_m"),
                        "lidar_y_m": _float_arg("lidar_y_m"),
                        "lidar_yaw_deg": _float_arg("lidar_yaw_deg"),
                        "max_rays": _int_arg("max_rays"),
                        "min_rays": _int_arg("min_rays"),
                        "opt_iterations": _int_arg("opt_iterations"),
                        "min_visible_walls": _int_arg("min_visible_walls"),
                        "min_rays_per_wall": _int_arg("min_rays_per_wall"),
                        "use_global_seed_search_on_first_scan": _bool_arg(
                            "use_global_seed_search_on_first_scan"
                        ),
                        "use_symmetry_seeds": _bool_arg("use_symmetry_seeds"),
                        "global_seed_step_m": _float_arg("global_seed_step_m"),
                        "global_seed_yaw_step_deg": _float_arg("global_seed_yaw_step_deg"),
                        "use_odom_prior": True,
                        "use_imu_yaw_prior": _bool_arg("use_imu_yaw_prior"),
                        "max_imu_age_sec": _float_arg("max_imu_age_sec"),
                        "publish_tf": _bool_arg("publish_tf"),
                        "tf_mode": LaunchConfiguration("wall_tf_mode"),
                        "publish_lidar_tf": _bool_arg("publish_lidar_tf"),
                    }
                ],
            ),
            Node(
                package="robot_nav_stack",
                executable="yolo_detection_adapter_node",
                name="yolo_detection_adapter_node",
                parameters=[
                    {
                        "input_topic": LaunchConfiguration("yolo_detections_topic"),
                        "output_topic": LaunchConfiguration("detections_topic"),
                        "min_confidence": _float_arg("adapter_min_confidence"),
                        "max_detections_per_frame": _int_arg(
                            "adapter_max_detections_per_frame"
                        ),
                        "max_output_hz": _float_arg("adapter_max_output_hz"),
                        "use_current_time_when_stamp_zero": True,
                        "stamp_mode": LaunchConfiguration("detection_stamp_mode"),
                        "max_header_stamp_offset_sec": _float_arg("max_header_stamp_offset_sec"),
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
                        "source_frame": LaunchConfiguration("object_source_frame"),
                        "lidar_frame": LaunchConfiguration("lidar_frame"),
                        "tf_lookup_timeout_sec": _float_arg("tf_lookup_timeout_sec"),
                        "fallback_to_latest_tf": _bool_arg("fallback_to_latest_tf"),
                        "latest_tf_max_extrapolation_sec": _float_arg(
                            "latest_tf_max_extrapolation_sec"
                        ),
                        "pending_detection_timeout_sec": _float_arg(
                            "pending_detection_timeout_sec"
                        ),
                        "max_pending_detections": _int_arg("max_pending_detections"),
                    }
                ],
            ),
            Node(
                package="robot_nav_stack",
                executable="distance_annotator_node",
                name="distance_annotator_node",
                condition=IfCondition(LaunchConfiguration("enable_distance_overlay")),
                parameters=[
                    {
                        "model_path": LaunchConfiguration("bbox_model_path"),
                        "image_topic": LaunchConfiguration("image_topic"),
                        "detections_topic": LaunchConfiguration("yolo_detections_topic"),
                        "classifications_topic": LaunchConfiguration("classifications_topic"),
                        "annotated_topic": LaunchConfiguration("distance_annotated_topic"),
                        "cube_class_id": 0,
                        "no_fruit_class": "none",
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
                executable="bbox_goal_navigator_node",
                name="bbox_goal_navigator_node",
                condition=IfCondition(LaunchConfiguration("enable_bbox_goal_navigation")),
                parameters=[
                    {
                        "target_pose_topic": LaunchConfiguration("bbox_goal_target_topic"),
                        "robot_pose_topic": LaunchConfiguration("robot_pose_topic"),
                        "computed_goal_topic": LaunchConfiguration("bbox_goal_pose_topic"),
                        "status_topic": LaunchConfiguration("bbox_goal_status_topic"),
                        "nav_action_name": LaunchConfiguration("bbox_goal_nav_action_name"),
                        "map_frame": LaunchConfiguration("map_frame"),
                        "send_nav2_goal": _bool_arg("bbox_goal_send_nav2_goal"),
                        "publish_mission_events": _bool_arg(
                            "bbox_goal_publish_mission_events"
                        ),
                        "approach_distance_m": _float_arg(
                            "bbox_goal_approach_distance_m"
                        ),
                        "goal_reached_tolerance_m": _float_arg(
                            "bbox_goal_reached_tolerance_m"
                        ),
                        "min_goal_separation_m": _float_arg(
                            "bbox_goal_min_separation_m"
                        ),
                        "max_target_age_sec": _float_arg(
                            "bbox_goal_max_target_age_sec"
                        ),
                        "target_selection_mode": LaunchConfiguration(
                            "bbox_goal_target_selection_mode"
                        ),
                        "target_association_radius_m": _float_arg(
                            "bbox_goal_target_association_radius_m"
                        ),
                        "max_tracked_targets": _int_arg(
                            "bbox_goal_max_tracked_targets"
                        ),
                        "arena_width_m": _float_arg("arena_width_m"),
                        "arena_height_m": _float_arg("arena_height_m"),
                        "arena_origin": LaunchConfiguration("arena_origin"),
                        "goal_margin_m": _float_arg("bbox_goal_margin_m"),
                    }
                ],
            ),
            Node(
                package="robot_nav_stack",
                executable="semantic_obstacle_cloud_node",
                name="semantic_obstacle_cloud_node",
                condition=IfCondition(LaunchConfiguration("enable_semantic_obstacle_cloud")),
                parameters=[
                    {
                        "input_topic": LaunchConfiguration("object_pose_topic"),
                        "output_topic": "/semantic_obstacles",
                        "frame_id": LaunchConfiguration("map_frame"),
                        "obstacle_radius_m": 0.04,
                        "point_spacing_m": 0.02,
                        "ttl_sec": _float_arg("semantic_obstacle_ttl_sec"),
                        "association_radius_m": _float_arg(
                            "semantic_obstacle_association_radius_m"
                        ),
                        "position_smoothing_alpha": 0.35,
                        "publish_hz": 10.0,
                    }
                ],
            ),
            Node(
                package="robot_nav_stack",
                executable="mapping_debug_monitor_node",
                name="mapping_debug_monitor_node",
                condition=IfCondition(LaunchConfiguration("enable_mapping_debug")),
                parameters=[
                    {
                        "robot_pose_topic": LaunchConfiguration("robot_pose_topic"),
                        "object_pose_topic": LaunchConfiguration("object_pose_topic"),
                        "approach_goal_topic": "/approach_goal",
                        "semantic_cloud_topic": "/semantic_obstacles",
                        "localizer_status_topic": "/four_wall_localizer/status",
                        "detections_topic": LaunchConfiguration("detections_topic"),
                        "debug_topic": LaunchConfiguration("mapping_debug_topic"),
                        "log_period_sec": _float_arg("mapping_debug_period_sec"),
                        "stale_after_sec": 2.0,
                        "print_to_console": True,
                        "publish_debug_json": True,
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
