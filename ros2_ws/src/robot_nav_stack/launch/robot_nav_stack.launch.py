from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition, UnlessCondition
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
            DeclareLaunchArgument("object_pose_raw_topic", default_value="/object_pose_map_raw"),
            DeclareLaunchArgument(
                "object_pose_raw_json_topic",
                default_value="/object_pose_map_raw_json",
            ),
            # target은 목표점 토픽, obstacle은 costmap 입력 토픽으로 따로 보낸다.
            DeclareLaunchArgument("target_object_pose_topic", default_value="/target_object_pose_map"),
            DeclareLaunchArgument("obstacle_object_pose_topic", default_value="/obstacle_object_pose_map"),
            DeclareLaunchArgument(
                "target_object_pose_raw_topic",
                default_value="/target_object_pose_map_raw",
            ),
            DeclareLaunchArgument(
                "obstacle_object_pose_raw_topic",
                default_value="/obstacle_object_pose_map_raw",
            ),
            DeclareLaunchArgument("target_shape", default_value=""),
            DeclareLaunchArgument("target_fruit", default_value=""),
            DeclareLaunchArgument("no_fruit_class", default_value="none"),
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
            DeclareLaunchArgument("use_lidar_tf_extrinsics", default_value="false"),
            DeclareLaunchArgument("lidar_tf_timeout_sec", default_value="0.05"),
            DeclareLaunchArgument("enable_lidar_deskew", default_value="true"),
            DeclareLaunchArgument("motion_history_sec", default_value="3.0"),
            DeclareLaunchArgument("motion_max_extrapolation_sec", default_value="0.05"),
            DeclareLaunchArgument("use_odom_prior", default_value="true"),
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
            DeclareLaunchArgument("stabilize_objects", default_value="true"),
            DeclareLaunchArgument("object_association_radius_m", default_value="0.35"),
            DeclareLaunchArgument("object_update_alpha", default_value="0.4"),
            DeclareLaunchArgument("max_tracked_objects", default_value="20"),
            DeclareLaunchArgument("ignore_storage_objects", default_value="true"),
            DeclareLaunchArgument("enable_object_track_fusion", default_value="false"),
            DeclareLaunchArgument("object_track_status_topic", default_value="/object_track_fusion/status"),
            DeclareLaunchArgument("object_track_remove_pose_topic", default_value="/object_track_fusion/remove_pose"),
            DeclareLaunchArgument("object_track_mission_event_topic", default_value="/mission/event"),
            DeclareLaunchArgument("object_track_class_aware_association", default_value="false"),
            DeclareLaunchArgument("object_track_association_radius_m", default_value="0.30"),
            DeclareLaunchArgument(
                "object_track_use_dynamic_association_radius",
                default_value="true",
            ),
            DeclareLaunchArgument(
                "object_track_association_base_radius_m",
                default_value="0.30",
            ),
            DeclareLaunchArgument(
                "object_track_association_max_radius_m",
                default_value="0.42",
            ),
            DeclareLaunchArgument(
                "object_track_association_speed_gain",
                default_value="1.0",
            ),
            DeclareLaunchArgument(
                "object_track_association_yaw_gain_m_per_rad",
                default_value="0.12",
            ),
            DeclareLaunchArgument(
                "object_track_association_dt_cap_sec",
                default_value="1.0",
            ),
            DeclareLaunchArgument("object_track_smoothing_alpha", default_value="0.40"),
            DeclareLaunchArgument("object_track_confirm_observations", default_value="3"),
            DeclareLaunchArgument("object_track_candidate_max_age_sec", default_value="1.5"),
            DeclareLaunchArgument("object_track_confirmed_max_age_sec", default_value="1.5"),
            DeclareLaunchArgument("object_track_keep_confirmed_tracks", default_value="false"),
            DeclareLaunchArgument("object_track_max_publish_age_sec", default_value="1.5"),
            DeclareLaunchArgument("object_track_out_of_order_tolerance_sec", default_value="0.02"),
            DeclareLaunchArgument("object_track_publish_hz", default_value="10.0"),
            DeclareLaunchArgument("object_track_max_tracks", default_value="30"),
            DeclareLaunchArgument("object_track_remove_radius_m", default_value="0.40"),
            DeclareLaunchArgument("object_track_ignored_zones", default_value=""),
            DeclareLaunchArgument(
                "object_track_remove_event_names",
                default_value="object_captured,pickup_success,target_captured,target_reached",
            ),
            DeclareLaunchArgument("enable_distance_overlay", default_value="false"),
            DeclareLaunchArgument("enable_bbox_goal_navigation", default_value="false"),
            DeclareLaunchArgument("enable_semantic_obstacle_cloud", default_value="true"),
            DeclareLaunchArgument(
                "semantic_obstacle_topic",
                default_value="/semantic_obstacle_cloud",
            ),
            DeclareLaunchArgument("semantic_obstacle_radius_m", default_value="0.07"),
            DeclareLaunchArgument("semantic_obstacle_point_spacing_m", default_value="0.01"),
            DeclareLaunchArgument("semantic_obstacle_ttl_sec", default_value="15.0"),
            DeclareLaunchArgument("semantic_target_clear_radius_m", default_value="0.25"),
            DeclareLaunchArgument("semantic_clear_costmaps_on_target", default_value="true"),
            DeclareLaunchArgument(
                "semantic_obstacle_clear_costmaps_on_expiry",
                default_value="true",
            ),
            DeclareLaunchArgument("bbox_goal_target_topic", default_value="/target_object_pose_map"),
            DeclareLaunchArgument("bbox_goal_pose_topic", default_value="/bbox_goal_pose"),
            DeclareLaunchArgument(
                "bbox_goal_status_topic",
                default_value="/bbox_goal_navigator/status",
            ),
            DeclareLaunchArgument("bbox_goal_nav_action_name", default_value="navigate_to_pose"),
            DeclareLaunchArgument("bbox_goal_send_nav2_goal", default_value="true"),
            DeclareLaunchArgument("bbox_goal_publish_mission_events", default_value="true"),
            DeclareLaunchArgument(
                "bbox_goal_capture_event_names",
                default_value="object_captured,cargo_entry,pickup_success,target_captured",
            ),
            DeclareLaunchArgument("bbox_goal_control_gripper_gate", default_value="true"),
            DeclareLaunchArgument("bbox_goal_control_capture_arm", default_value="true"),
            DeclareLaunchArgument("gripper_command_topic", default_value="/gripper/command"),
            DeclareLaunchArgument("capture_arm_topic", default_value="/capture/arm"),
            DeclareLaunchArgument("bbox_goal_cmd_vel_topic", default_value="/cmd_vel"),
            DeclareLaunchArgument("bbox_goal_gate_open_distance_m", default_value="0.70"),
            # target 중심으로 들어가야 하므로 기본 접근 거리는 0m로 둔다.
            DeclareLaunchArgument("bbox_goal_approach_distance_m", default_value="0.0"),
            DeclareLaunchArgument("bbox_goal_reached_tolerance_m", default_value="0.05"),
            DeclareLaunchArgument("bbox_goal_min_separation_m", default_value="0.15"),
            DeclareLaunchArgument("bbox_goal_heading_offset_deg", default_value="0.0"),
            DeclareLaunchArgument("bbox_goal_max_target_age_sec", default_value="1.5"),
            DeclareLaunchArgument("bbox_goal_target_search_enabled", default_value="true"),
            DeclareLaunchArgument(
                "bbox_goal_target_search_missing_timeout_sec",
                default_value="2.0",
            ),
            DeclareLaunchArgument(
                "bbox_goal_target_search_radius_m",
                default_value="1.70",
            ),
            DeclareLaunchArgument(
                "bbox_goal_target_search_goal_timeout_sec",
                default_value="12.0",
            ),
            DeclareLaunchArgument(
                "bbox_goal_target_search_initial_spin_enabled",
                default_value="true",
            ),
            DeclareLaunchArgument(
                "bbox_goal_target_search_initial_spin_step_deg",
                default_value="60.0",
            ),
            DeclareLaunchArgument(
                "bbox_goal_target_search_dwell_sec",
                default_value="1.0",
            ),
            DeclareLaunchArgument(
                "bbox_goal_target_search_center_x_m",
                default_value="0.0",
            ),
            DeclareLaunchArgument(
                "bbox_goal_target_search_center_y_m",
                default_value="0.0",
            ),
            DeclareLaunchArgument("bbox_goal_capture_stop_hold_sec", default_value="0.8"),
            DeclareLaunchArgument("bbox_goal_capture_remove_radius_m", default_value="0.40"),
            DeclareLaunchArgument("bbox_goal_target_selection_mode", default_value="nearest"),
            DeclareLaunchArgument(
                "bbox_goal_target_association_radius_m",
                default_value="0.15",
            ),
            DeclareLaunchArgument("bbox_goal_target_lock_distance_m", default_value="0.30"),
            DeclareLaunchArgument("bbox_goal_max_tracked_targets", default_value="20"),
            DeclareLaunchArgument("bbox_goal_margin_m", default_value="0.20"),
            DeclareLaunchArgument(
                "bbox_goal_storage_dropoff_enabled",
                default_value="true",
            ),
            DeclareLaunchArgument(
                "bbox_goal_storage_trigger_count",
                default_value="3",
            ),
            DeclareLaunchArgument("bbox_goal_storage_min_x", default_value="-2.0"),
            DeclareLaunchArgument("bbox_goal_storage_max_x", default_value="-1.4"),
            DeclareLaunchArgument("bbox_goal_storage_min_y", default_value="-2.0"),
            DeclareLaunchArgument("bbox_goal_storage_max_y", default_value="-1.4"),
            DeclareLaunchArgument(
                "bbox_goal_storage_entry_mode",
                default_value="auto",
            ),
            DeclareLaunchArgument(
                "bbox_goal_storage_approach_clearance_m",
                default_value="0.05",
            ),
            DeclareLaunchArgument(
                "bbox_goal_robot_half_length_m",
                default_value="0.16",
            ),
            DeclareLaunchArgument(
                "bbox_goal_robot_half_width_m",
                default_value="0.165",
            ),
            DeclareLaunchArgument(
                "bbox_goal_storage_containment_margin_m",
                default_value="0.0",
            ),
            DeclareLaunchArgument(
                "bbox_goal_storage_heading_tolerance_deg",
                default_value="30.0",
            ),
            DeclareLaunchArgument(
                "bbox_goal_storage_verify_timeout_sec",
                default_value="3.0",
            ),
            DeclareLaunchArgument(
                "bbox_goal_storage_nav_max_retries",
                default_value="2",
            ),
            DeclareLaunchArgument(
                "bbox_goal_storage_open_gate_before_backup",
                default_value="true",
            ),
            DeclareLaunchArgument(
                "bbox_goal_storage_gate_open_wait_sec",
                default_value="2.0",
            ),
            DeclareLaunchArgument(
                "bbox_goal_storage_gate_close_wait_after_backup_sec",
                default_value="0.5",
            ),
            DeclareLaunchArgument(
                "bbox_goal_storage_backup_action_name",
                default_value="backup",
            ),
            DeclareLaunchArgument(
                "bbox_goal_storage_backup_distance_m",
                default_value="0.50",
            ),
            DeclareLaunchArgument(
                "bbox_goal_storage_backup_speed_mps",
                default_value="0.20",
            ),
            DeclareLaunchArgument(
                "bbox_goal_storage_backup_time_allowance_sec",
                default_value="4.0",
            ),
            DeclareLaunchArgument("enable_mapping_debug", default_value="true"),
            DeclareLaunchArgument("mapping_debug_period_sec", default_value="1.0"),
            DeclareLaunchArgument(
                "mapping_debug_topic",
                default_value="/robot_nav_stack/debug_state",
            ),
            DeclareLaunchArgument("publish_tf", default_value="true"),
            DeclareLaunchArgument("wall_tf_mode", default_value="map_to_base"),
            DeclareLaunchArgument("wall_tf_transform_tolerance_sec", default_value="0.20"),
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
                        "use_lidar_tf_extrinsics": _bool_arg(
                            "use_lidar_tf_extrinsics"
                        ),
                        "lidar_tf_timeout_sec": _float_arg("lidar_tf_timeout_sec"),
                        "enable_lidar_deskew": _bool_arg("enable_lidar_deskew"),
                        "motion_history_sec": _float_arg("motion_history_sec"),
                        "motion_max_extrapolation_sec": _float_arg(
                            "motion_max_extrapolation_sec"
                        ),
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
                        "use_odom_prior": _bool_arg("use_odom_prior"),
                        "use_imu_yaw_prior": _bool_arg("use_imu_yaw_prior"),
                        "max_imu_age_sec": _float_arg("max_imu_age_sec"),
                        "publish_tf": _bool_arg("publish_tf"),
                        "tf_mode": LaunchConfiguration("wall_tf_mode"),
                        "transform_tolerance_sec": _float_arg(
                            "wall_tf_transform_tolerance_sec"
                        ),
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
                        "classifications_topic": LaunchConfiguration("classifications_topic"),
                        "no_fruit_class": LaunchConfiguration("no_fruit_class"),
                    }
                ],
            ),
            Node(
                package="robot_nav_stack",
                executable="object_localizer_node",
                name="object_localizer_node",
                condition=UnlessCondition(LaunchConfiguration("enable_object_track_fusion")),
                parameters=[
                    {
                        "model_path": LaunchConfiguration("bbox_model_path"),
                        "detections_topic": LaunchConfiguration("detections_topic"),
                        "object_pose_topic": LaunchConfiguration("object_pose_topic"),
                        "target_object_pose_topic": LaunchConfiguration(
                            "target_object_pose_topic"
                        ),
                        "obstacle_object_pose_topic": LaunchConfiguration(
                            "obstacle_object_pose_topic"
                        ),
                        "target_shape": LaunchConfiguration("target_shape"),
                        "target_fruit": LaunchConfiguration("target_fruit"),
                        "no_fruit_class": LaunchConfiguration("no_fruit_class"),
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
                        "stabilize_objects": _bool_arg("stabilize_objects"),
                        "object_association_radius_m": _float_arg(
                            "object_association_radius_m"
                        ),
                        "object_update_alpha": _float_arg("object_update_alpha"),
                        "max_tracked_objects": _int_arg("max_tracked_objects"),
                        "target_lock_status_topic": LaunchConfiguration(
                            "bbox_goal_status_topic"
                        ),
                        "locked_target_radius_m": _float_arg(
                            "semantic_target_clear_radius_m"
                        ),
                        "ignore_storage_objects": _bool_arg("ignore_storage_objects"),
                        "storage_min_x": _float_arg("bbox_goal_storage_min_x"),
                        "storage_max_x": _float_arg("bbox_goal_storage_max_x"),
                        "storage_min_y": _float_arg("bbox_goal_storage_min_y"),
                        "storage_max_y": _float_arg("bbox_goal_storage_max_y"),
                    }
                ],
            ),
            Node(
                package="robot_nav_stack",
                executable="object_localizer_node",
                name="object_localizer_node",
                condition=IfCondition(LaunchConfiguration("enable_object_track_fusion")),
                parameters=[
                    {
                        "model_path": LaunchConfiguration("bbox_model_path"),
                        "detections_topic": LaunchConfiguration("detections_topic"),
                        "object_pose_topic": LaunchConfiguration("object_pose_raw_topic"),
                        "object_pose_json_topic": LaunchConfiguration(
                            "object_pose_raw_json_topic"
                        ),
                        "target_object_pose_topic": LaunchConfiguration(
                            "target_object_pose_raw_topic"
                        ),
                        # Obstacles bypass track fusion and go directly to the
                        # single semantic association/smoothing stage.
                        "obstacle_object_pose_topic": LaunchConfiguration(
                            "obstacle_object_pose_topic"
                        ),
                        "target_shape": LaunchConfiguration("target_shape"),
                        "target_fruit": LaunchConfiguration("target_fruit"),
                        "no_fruit_class": LaunchConfiguration("no_fruit_class"),
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
                        "stabilize_objects": False,
                        "object_association_radius_m": _float_arg(
                            "object_association_radius_m"
                        ),
                        "object_update_alpha": _float_arg("object_update_alpha"),
                        "max_tracked_objects": _int_arg("max_tracked_objects"),
                        "target_lock_status_topic": LaunchConfiguration(
                            "bbox_goal_status_topic"
                        ),
                        "locked_target_radius_m": _float_arg(
                            "semantic_target_clear_radius_m"
                        ),
                        "ignore_storage_objects": _bool_arg("ignore_storage_objects"),
                        "storage_min_x": _float_arg("bbox_goal_storage_min_x"),
                        "storage_max_x": _float_arg("bbox_goal_storage_max_x"),
                        "storage_min_y": _float_arg("bbox_goal_storage_min_y"),
                        "storage_max_y": _float_arg("bbox_goal_storage_max_y"),
                    }
                ],
            ),
            Node(
                package="robot_nav_stack",
                executable="object_track_fusion_node",
                name="object_track_fusion_node",
                condition=IfCondition(LaunchConfiguration("enable_object_track_fusion")),
                parameters=[
                    {
                        "input_topic": LaunchConfiguration("object_pose_raw_topic"),
                        "input_json_topic": LaunchConfiguration(
                            "object_pose_raw_json_topic"
                        ),
                        "output_topic": LaunchConfiguration("object_pose_topic"),
                        "target_output_topic": LaunchConfiguration(
                            "target_object_pose_topic"
                        ),
                        # Target/all-object fusion stays enabled; obstacles do not.
                        "obstacle_output_topic": "",
                        "status_topic": LaunchConfiguration("object_track_status_topic"),
                        "remove_pose_topic": LaunchConfiguration(
                            "object_track_remove_pose_topic"
                        ),
                        "mission_event_topic": LaunchConfiguration(
                            "object_track_mission_event_topic"
                        ),
                        "robot_pose_topic": LaunchConfiguration("robot_pose_topic"),
                        "frame_id": LaunchConfiguration("map_frame"),
                        "class_aware_association": _bool_arg(
                            "object_track_class_aware_association"
                        ),
                        "association_radius_m": _float_arg(
                            "object_track_association_radius_m"
                        ),
                        "use_dynamic_association_radius": _bool_arg(
                            "object_track_use_dynamic_association_radius"
                        ),
                        "association_base_radius_m": _float_arg(
                            "object_track_association_base_radius_m"
                        ),
                        "association_max_radius_m": _float_arg(
                            "object_track_association_max_radius_m"
                        ),
                        "association_speed_gain": _float_arg(
                            "object_track_association_speed_gain"
                        ),
                        "association_yaw_gain_m_per_rad": _float_arg(
                            "object_track_association_yaw_gain_m_per_rad"
                        ),
                        "association_dt_cap_sec": _float_arg(
                            "object_track_association_dt_cap_sec"
                        ),
                        "smoothing_alpha": _float_arg("object_track_smoothing_alpha"),
                        "confirm_observations": _int_arg(
                            "object_track_confirm_observations"
                        ),
                        "candidate_max_age_sec": _float_arg(
                            "object_track_candidate_max_age_sec"
                        ),
                        "confirmed_max_age_sec": _float_arg(
                            "object_track_confirmed_max_age_sec"
                        ),
                        "keep_confirmed_tracks": _bool_arg(
                            "object_track_keep_confirmed_tracks"
                        ),
                        "max_publish_age_sec": _float_arg(
                            "object_track_max_publish_age_sec"
                        ),
                        "out_of_order_tolerance_sec": _float_arg(
                            "object_track_out_of_order_tolerance_sec"
                        ),
                        "publish_hz": _float_arg("object_track_publish_hz"),
                        "max_tracks": _int_arg("object_track_max_tracks"),
                        "remove_radius_m": _float_arg("object_track_remove_radius_m"),
                        "ignored_zones": LaunchConfiguration("object_track_ignored_zones"),
                        "remove_event_names": LaunchConfiguration(
                            "object_track_remove_event_names"
                        ),
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
                        "no_fruit_class": LaunchConfiguration("no_fruit_class"),
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
                        "obstacle_pose_topic": LaunchConfiguration(
                            "obstacle_object_pose_topic"
                        ),
                        "robot_pose_topic": LaunchConfiguration("robot_pose_topic"),
                        "computed_goal_topic": LaunchConfiguration("bbox_goal_pose_topic"),
                        "status_topic": LaunchConfiguration("bbox_goal_status_topic"),
                        "nav_action_name": LaunchConfiguration("bbox_goal_nav_action_name"),
                        "map_frame": LaunchConfiguration("map_frame"),
                        "send_nav2_goal": _bool_arg("bbox_goal_send_nav2_goal"),
                        "publish_mission_events": _bool_arg(
                            "bbox_goal_publish_mission_events"
                        ),
                        "mission_event_topic": LaunchConfiguration(
                            "object_track_mission_event_topic"
                        ),
                        "capture_event_names": LaunchConfiguration(
                            "bbox_goal_capture_event_names"
                        ),
                        "control_gripper_gate": _bool_arg(
                            "bbox_goal_control_gripper_gate"
                        ),
                        "control_capture_arm": _bool_arg(
                            "bbox_goal_control_capture_arm"
                        ),
                        "gripper_command_topic": LaunchConfiguration(
                            "gripper_command_topic"
                        ),
                        "capture_arm_topic": LaunchConfiguration("capture_arm_topic"),
                        "cmd_vel_topic": LaunchConfiguration("bbox_goal_cmd_vel_topic"),
                        "gate_open_distance_m": _float_arg(
                            "bbox_goal_gate_open_distance_m"
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
                        "goal_heading_offset_deg": _float_arg(
                            "bbox_goal_heading_offset_deg"
                        ),
                        "max_target_age_sec": _float_arg(
                            "bbox_goal_max_target_age_sec"
                        ),
                        "target_search_enabled": _bool_arg(
                            "bbox_goal_target_search_enabled"
                        ),
                        "target_search_missing_timeout_sec": _float_arg(
                            "bbox_goal_target_search_missing_timeout_sec"
                        ),
                        "target_search_radius_m": _float_arg(
                            "bbox_goal_target_search_radius_m"
                        ),
                        "target_search_goal_timeout_sec": _float_arg(
                            "bbox_goal_target_search_goal_timeout_sec"
                        ),
                        "target_search_initial_spin_enabled": _bool_arg(
                            "bbox_goal_target_search_initial_spin_enabled"
                        ),
                        "target_search_initial_spin_step_deg": _float_arg(
                            "bbox_goal_target_search_initial_spin_step_deg"
                        ),
                        "target_search_dwell_sec": _float_arg(
                            "bbox_goal_target_search_dwell_sec"
                        ),
                        "target_search_center_x_m": _float_arg(
                            "bbox_goal_target_search_center_x_m"
                        ),
                        "target_search_center_y_m": _float_arg(
                            "bbox_goal_target_search_center_y_m"
                        ),
                        "capture_stop_hold_sec": _float_arg(
                            "bbox_goal_capture_stop_hold_sec"
                        ),
                        "capture_remove_radius_m": _float_arg(
                            "bbox_goal_capture_remove_radius_m"
                        ),
                        "target_selection_mode": LaunchConfiguration(
                            "bbox_goal_target_selection_mode"
                        ),
                        "target_association_radius_m": _float_arg(
                            "bbox_goal_target_association_radius_m"
                        ),
                        "target_lock_distance_m": _float_arg(
                            "bbox_goal_target_lock_distance_m"
                        ),
                        "reclassification_radius_m": _float_arg(
                            "semantic_target_clear_radius_m"
                        ),
                        "max_tracked_targets": _int_arg(
                            "bbox_goal_max_tracked_targets"
                        ),
                        "arena_width_m": _float_arg("arena_width_m"),
                        "arena_height_m": _float_arg("arena_height_m"),
                        "arena_origin": LaunchConfiguration("arena_origin"),
                        "goal_margin_m": _float_arg("bbox_goal_margin_m"),
                        "storage_dropoff_enabled": _bool_arg(
                            "bbox_goal_storage_dropoff_enabled"
                        ),
                        "storage_trigger_count": _int_arg(
                            "bbox_goal_storage_trigger_count"
                        ),
                        "storage_min_x": _float_arg("bbox_goal_storage_min_x"),
                        "storage_max_x": _float_arg("bbox_goal_storage_max_x"),
                        "storage_min_y": _float_arg("bbox_goal_storage_min_y"),
                        "storage_max_y": _float_arg("bbox_goal_storage_max_y"),
                        "storage_entry_mode": LaunchConfiguration(
                            "bbox_goal_storage_entry_mode"
                        ),
                        "storage_approach_clearance_m": _float_arg(
                            "bbox_goal_storage_approach_clearance_m"
                        ),
                        "robot_half_length_m": _float_arg(
                            "bbox_goal_robot_half_length_m"
                        ),
                        "robot_half_width_m": _float_arg(
                            "bbox_goal_robot_half_width_m"
                        ),
                        "storage_containment_margin_m": _float_arg(
                            "bbox_goal_storage_containment_margin_m"
                        ),
                        "storage_heading_tolerance_deg": _float_arg(
                            "bbox_goal_storage_heading_tolerance_deg"
                        ),
                        "storage_verify_timeout_sec": _float_arg(
                            "bbox_goal_storage_verify_timeout_sec"
                        ),
                        "storage_nav_max_retries": _int_arg(
                            "bbox_goal_storage_nav_max_retries"
                        ),
                        "storage_open_gate_before_backup": _bool_arg(
                            "bbox_goal_storage_open_gate_before_backup"
                        ),
                        "storage_gate_open_wait_sec": _float_arg(
                            "bbox_goal_storage_gate_open_wait_sec"
                        ),
                        "storage_gate_close_wait_after_backup_sec": _float_arg(
                            "bbox_goal_storage_gate_close_wait_after_backup_sec"
                        ),
                        "storage_backup_action_name": LaunchConfiguration(
                            "bbox_goal_storage_backup_action_name"
                        ),
                        "storage_backup_distance_m": _float_arg(
                            "bbox_goal_storage_backup_distance_m"
                        ),
                        "storage_backup_speed_mps": _float_arg(
                            "bbox_goal_storage_backup_speed_mps"
                        ),
                        "storage_backup_time_allowance_sec": _float_arg(
                            "bbox_goal_storage_backup_time_allowance_sec"
                        ),
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
                        # 선택된 target은 장애물 cloud에 넣지 않는다.
                        "input_topic": LaunchConfiguration("obstacle_object_pose_topic"),
                        "target_input_topic": LaunchConfiguration(
                            "target_object_pose_topic"
                        ),
                        "output_topic": LaunchConfiguration("semantic_obstacle_topic"),
                        "frame_id": LaunchConfiguration("map_frame"),
                        "obstacle_radius_m": _float_arg("semantic_obstacle_radius_m"),
                        "point_spacing_m": _float_arg("semantic_obstacle_point_spacing_m"),
                        "ttl_sec": _float_arg("semantic_obstacle_ttl_sec"),
                        "target_clear_radius_m": _float_arg(
                            "semantic_target_clear_radius_m"
                        ),
                        "target_lock_status_topic": LaunchConfiguration(
                            "bbox_goal_status_topic"
                        ),
                        "locked_target_radius_m": _float_arg(
                            "semantic_target_clear_radius_m"
                        ),
                        # Obstacle poses bypass ObjectLocalizer stabilization, so
                        # association and smoothing are applied exactly once here.
                        "association_radius_m": _float_arg(
                            "object_association_radius_m"
                        ),
                        "position_smoothing_alpha": _float_arg(
                            "object_update_alpha"
                        ),
                        "publish_hz": 10.0,
                        "clear_costmaps_on_expiry": _bool_arg(
                            "semantic_obstacle_clear_costmaps_on_expiry"
                        ),
                        "clear_costmaps_on_target": _bool_arg(
                            "semantic_clear_costmaps_on_target"
                        ),
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
                        "approach_goal_topic": LaunchConfiguration("bbox_goal_pose_topic"),
                        "semantic_cloud_topic": LaunchConfiguration(
                            "semantic_obstacle_topic"
                        ),
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
