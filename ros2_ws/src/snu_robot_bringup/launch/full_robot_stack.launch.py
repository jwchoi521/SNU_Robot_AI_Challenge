from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.actions import OpaqueFunction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def _include_launch(package_name: str, launch_file: str, arguments: dict, condition=None):
    include_kwargs = {"launch_arguments": arguments.items()}
    if condition is not None:
        include_kwargs["condition"] = condition

    return IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [
                    FindPackageShare(package_name),
                    "launch",
                    launch_file,
                ]
            )
        ),
        **include_kwargs,
    )


def _launch_bool(context, name: str) -> bool:
    value = LaunchConfiguration(name).perform(context).strip().lower()
    if value in ("1", "true", "yes", "on"):
        return True
    if value in ("0", "false", "no", "off"):
        return False
    raise RuntimeError(f"launch argument {name} must be boolean, got {value!r}")


def _validate_tf_configuration(context):
    mode = LaunchConfiguration("wall_tf_mode").perform(context).strip().lower()
    direct_mode = mode in ("map_to_base", "map_base", "direct")
    map_to_odom_mode = mode in ("map_to_odom", "map_odom")
    if not direct_mode and not map_to_odom_mode:
        raise RuntimeError(
            "wall_tf_mode must be map_to_base or map_to_odom, "
            f"got {mode!r}"
        )

    publish_tf = _launch_bool(context, "publish_tf")
    enable_ekf = _launch_bool(context, "enable_ekf")
    enable_slam = _launch_bool(context, "enable_slam")
    enable_sensor_tf = _launch_bool(context, "enable_sensor_tf")
    publish_lidar_tf = _launch_bool(context, "publish_lidar_tf")
    errors = []
    if publish_tf and enable_ekf and direct_mode:
        errors.append(
            "EKF publishes odom->base_link, so wall_tf_mode must be map_to_odom"
        )
    if publish_tf and enable_slam:
        errors.append(
            "SLAM Toolbox publishes map->odom; set publish_tf:=false or "
            "enable_slam:=false so map->odom has exactly one publisher"
        )
    if publish_tf and enable_sensor_tf and publish_lidar_tf and direct_mode:
        errors.append(
            "sensor_tf publishes base_link->lidar; set publish_lidar_tf:=false "
            "to avoid giving lidar two TF parents"
        )
    if errors:
        raise RuntimeError("Invalid TF configuration: " + "; ".join(errors))
    return []


def generate_launch_description():
    bbox_model_default = PathJoinSubstitution(
        [
            FindPackageShare("robot_nav_stack"),
            "models",
            "bbox_pose_anchor033.joblib",
        ]
    )
    nav2_params_default = PathJoinSubstitution(
        [
            FindPackageShare("snu_robot_bringup"),
            "config",
            "nav2_params.yaml",
        ]
    )
    known_map_default = PathJoinSubstitution(
        [
            FindPackageShare("snu_robot_bringup"),
            "maps",
            "arena_4x4_center.yaml",
        ]
    )
    slam_params_default = PathJoinSubstitution(
        [
            FindPackageShare("snu_robot_bringup"),
            "config",
            "slam_toolbox_online_async.yaml",
        ]
    )
    ekf_params_default = PathJoinSubstitution(
        [
            FindPackageShare("snu_robot_bringup"),
            "config",
            "ekf.yaml",
        ]
    )

    detector_arguments = {
        "shape_engine": LaunchConfiguration("shape_engine"),
        "shape_input_size": LaunchConfiguration("shape_input_size"),
        "classifier_engine": LaunchConfiguration("classifier_engine"),
        "classifier_input_size": LaunchConfiguration("classifier_input_size"),
        "camera_index": LaunchConfiguration("camera_index"),
        "camera_pipeline": LaunchConfiguration("camera_pipeline"),
        "camera_topic": LaunchConfiguration("camera_topic"),
        "camera_frame": LaunchConfiguration("camera_frame"),
        "camera_buffer_size": LaunchConfiguration("camera_buffer_size"),
        "camera_timestamp_mode": LaunchConfiguration("camera_timestamp_mode"),
        "camera_timestamp_offset_sec": LaunchConfiguration(
            "camera_timestamp_offset_sec"
        ),
        "classifications_topic": LaunchConfiguration("classifications_topic"),
        "classifier_annotated_topic": LaunchConfiguration("classifier_annotated_topic"),
        "fps": LaunchConfiguration("fps"),
        "inference_fps": LaunchConfiguration("inference_fps"),
        "shape_nms_iou_threshold": LaunchConfiguration("shape_nms_iou_threshold"),
        "shape_class_agnostic_nms": LaunchConfiguration("shape_class_agnostic_nms"),
        "frame_width": LaunchConfiguration("frame_width"),
        "frame_height": LaunchConfiguration("frame_height"),
    }

    nav_arguments = {
        "scan_topic": LaunchConfiguration("scan_topic"),
        "odom_topic": LaunchConfiguration("odom_topic"),
        "imu_topic": LaunchConfiguration("imu_topic"),
        "image_topic": LaunchConfiguration("camera_topic"),
        "yolo_detections_topic": LaunchConfiguration("yolo_detections_topic"),
        "detections_topic": LaunchConfiguration("detections_topic"),
        "classifications_topic": LaunchConfiguration("classifications_topic"),
        "distance_annotated_topic": LaunchConfiguration("distance_annotated_topic"),
        "robot_pose_topic": LaunchConfiguration("robot_pose_topic"),
        "object_pose_topic": LaunchConfiguration("object_pose_topic"),
        "object_pose_raw_topic": LaunchConfiguration("object_pose_raw_topic"),
        "object_pose_raw_json_topic": LaunchConfiguration("object_pose_raw_json_topic"),
        "target_object_pose_topic": LaunchConfiguration("target_object_pose_topic"),
        "obstacle_object_pose_topic": LaunchConfiguration("obstacle_object_pose_topic"),
        "target_object_pose_raw_topic": LaunchConfiguration(
            "target_object_pose_raw_topic"
        ),
        "obstacle_object_pose_raw_topic": LaunchConfiguration(
            "obstacle_object_pose_raw_topic"
        ),
        "target_shape": LaunchConfiguration("target_shape"),
        "target_fruit": LaunchConfiguration("target_fruit"),
        "no_fruit_class": LaunchConfiguration("no_fruit_class"),
        "map_frame": LaunchConfiguration("map_frame"),
        "odom_frame": LaunchConfiguration("odom_frame"),
        "base_frame": LaunchConfiguration("base_frame"),
        "lidar_frame": LaunchConfiguration("lidar_frame"),
        "object_source_frame": LaunchConfiguration("object_source_frame"),
        "arena_width_m": LaunchConfiguration("arena_width_m"),
        "arena_height_m": LaunchConfiguration("arena_height_m"),
        "arena_origin": LaunchConfiguration("arena_origin"),
        "initial_x_m": LaunchConfiguration("initial_x_m"),
        "initial_y_m": LaunchConfiguration("initial_y_m"),
        "initial_yaw_deg": LaunchConfiguration("initial_yaw_deg"),
        "lidar_x_m": LaunchConfiguration("lidar_x_m"),
        "lidar_y_m": LaunchConfiguration("lidar_y_m"),
        "lidar_yaw_deg": LaunchConfiguration("lidar_yaw_deg"),
        "use_lidar_tf_extrinsics": LaunchConfiguration("enable_sensor_tf"),
        "lidar_tf_timeout_sec": LaunchConfiguration("lidar_tf_timeout_sec"),
        "enable_lidar_deskew": LaunchConfiguration("enable_lidar_deskew"),
        "motion_history_sec": LaunchConfiguration("motion_history_sec"),
        "motion_max_extrapolation_sec": LaunchConfiguration(
            "motion_max_extrapolation_sec"
        ),
        "use_odom_prior": LaunchConfiguration("use_odom_prior"),
        "use_imu_yaw_prior": LaunchConfiguration("use_imu_yaw_prior"),
        "max_imu_age_sec": LaunchConfiguration("max_imu_age_sec"),
        "max_rays": LaunchConfiguration("max_rays"),
        "min_rays": LaunchConfiguration("min_rays"),
        "opt_iterations": LaunchConfiguration("opt_iterations"),
        "min_visible_walls": LaunchConfiguration("min_visible_walls"),
        "min_rays_per_wall": LaunchConfiguration("min_rays_per_wall"),
        "use_global_seed_search_on_first_scan": LaunchConfiguration(
            "use_global_seed_search_on_first_scan"
        ),
        "use_symmetry_seeds": LaunchConfiguration("use_symmetry_seeds"),
        "global_seed_step_m": LaunchConfiguration("global_seed_step_m"),
        "global_seed_yaw_step_deg": LaunchConfiguration("global_seed_yaw_step_deg"),
        "adapter_min_confidence": LaunchConfiguration("adapter_min_confidence"),
        "adapter_max_detections_per_frame": LaunchConfiguration(
            "adapter_max_detections_per_frame"
        ),
        "adapter_max_output_hz": LaunchConfiguration("adapter_max_output_hz"),
        "detection_stamp_mode": LaunchConfiguration("detection_stamp_mode"),
        "max_header_stamp_offset_sec": LaunchConfiguration("max_header_stamp_offset_sec"),
        "tf_lookup_timeout_sec": LaunchConfiguration("tf_lookup_timeout_sec"),
        "fallback_to_latest_tf": LaunchConfiguration("fallback_to_latest_tf"),
        "latest_tf_max_extrapolation_sec": LaunchConfiguration(
            "latest_tf_max_extrapolation_sec"
        ),
        "pending_detection_timeout_sec": LaunchConfiguration("pending_detection_timeout_sec"),
        "max_pending_detections": LaunchConfiguration("max_pending_detections"),
        "stabilize_objects": LaunchConfiguration("stabilize_objects"),
        "object_association_radius_m": LaunchConfiguration("object_association_radius_m"),
        "object_update_alpha": LaunchConfiguration("object_update_alpha"),
        "max_tracked_objects": LaunchConfiguration("max_tracked_objects"),
        "enable_object_track_fusion": LaunchConfiguration("enable_object_track_fusion"),
        "object_track_status_topic": LaunchConfiguration("object_track_status_topic"),
        "object_track_remove_pose_topic": LaunchConfiguration(
            "object_track_remove_pose_topic"
        ),
        "object_track_mission_event_topic": LaunchConfiguration(
            "object_track_mission_event_topic"
        ),
        "object_track_class_aware_association": LaunchConfiguration(
            "object_track_class_aware_association"
        ),
        "object_track_association_radius_m": LaunchConfiguration(
            "object_track_association_radius_m"
        ),
        "object_track_use_dynamic_association_radius": LaunchConfiguration(
            "object_track_use_dynamic_association_radius"
        ),
        "object_track_association_base_radius_m": LaunchConfiguration(
            "object_track_association_base_radius_m"
        ),
        "object_track_association_max_radius_m": LaunchConfiguration(
            "object_track_association_max_radius_m"
        ),
        "object_track_association_speed_gain": LaunchConfiguration(
            "object_track_association_speed_gain"
        ),
        "object_track_association_yaw_gain_m_per_rad": LaunchConfiguration(
            "object_track_association_yaw_gain_m_per_rad"
        ),
        "object_track_association_dt_cap_sec": LaunchConfiguration(
            "object_track_association_dt_cap_sec"
        ),
        "object_track_smoothing_alpha": LaunchConfiguration(
            "object_track_smoothing_alpha"
        ),
        "object_track_confirm_observations": LaunchConfiguration(
            "object_track_confirm_observations"
        ),
        "object_track_candidate_max_age_sec": LaunchConfiguration(
            "object_track_candidate_max_age_sec"
        ),
        "object_track_confirmed_max_age_sec": LaunchConfiguration(
            "object_track_confirmed_max_age_sec"
        ),
        "object_track_keep_confirmed_tracks": LaunchConfiguration(
            "object_track_keep_confirmed_tracks"
        ),
        "object_track_max_publish_age_sec": LaunchConfiguration(
            "object_track_max_publish_age_sec"
        ),
        "object_track_out_of_order_tolerance_sec": LaunchConfiguration(
            "object_track_out_of_order_tolerance_sec"
        ),
        "object_track_publish_hz": LaunchConfiguration("object_track_publish_hz"),
        "object_track_max_tracks": LaunchConfiguration("object_track_max_tracks"),
        "object_track_remove_radius_m": LaunchConfiguration(
            "object_track_remove_radius_m"
        ),
        "object_track_ignored_zones": LaunchConfiguration("object_track_ignored_zones"),
        "object_track_remove_event_names": LaunchConfiguration(
            "object_track_remove_event_names"
        ),
        "enable_distance_overlay": LaunchConfiguration("enable_distance_overlay"),
        "enable_bbox_goal_navigation": LaunchConfiguration("enable_bbox_goal_navigation"),
        "enable_semantic_obstacle_cloud": LaunchConfiguration(
            "enable_semantic_obstacle_cloud"
        ),
        "semantic_obstacle_topic": LaunchConfiguration("semantic_obstacle_topic"),
        "semantic_obstacle_radius_m": LaunchConfiguration(
            "semantic_obstacle_radius_m"
        ),
        "semantic_obstacle_point_spacing_m": LaunchConfiguration(
            "semantic_obstacle_point_spacing_m"
        ),
        "semantic_obstacle_ttl_sec": LaunchConfiguration("semantic_obstacle_ttl_sec"),
        "semantic_target_clear_radius_m": LaunchConfiguration(
            "semantic_target_clear_radius_m"
        ),
        "semantic_clear_costmaps_on_target": LaunchConfiguration(
            "semantic_clear_costmaps_on_target"
        ),
        "semantic_obstacle_clear_costmaps_on_expiry": LaunchConfiguration(
            "semantic_obstacle_clear_costmaps_on_expiry"
        ),
        "bbox_goal_target_topic": LaunchConfiguration("bbox_goal_target_topic"),
        "bbox_goal_pose_topic": LaunchConfiguration("bbox_goal_pose_topic"),
        "bbox_goal_status_topic": LaunchConfiguration("bbox_goal_status_topic"),
        "bbox_goal_nav_action_name": LaunchConfiguration("bbox_goal_nav_action_name"),
        "bbox_goal_send_nav2_goal": LaunchConfiguration("bbox_goal_send_nav2_goal"),
        "bbox_goal_publish_mission_events": LaunchConfiguration(
            "bbox_goal_publish_mission_events"
        ),
        "bbox_goal_capture_event_names": LaunchConfiguration(
            "bbox_goal_capture_event_names"
        ),
        "bbox_goal_control_gripper_gate": LaunchConfiguration(
            "bbox_goal_control_gripper_gate"
        ),
        "bbox_goal_control_capture_arm": LaunchConfiguration(
            "bbox_goal_control_capture_arm"
        ),
        "gripper_command_topic": LaunchConfiguration("gripper_command_topic"),
        "capture_arm_topic": LaunchConfiguration("capture_arm_topic"),
        "bbox_goal_cmd_vel_topic": LaunchConfiguration("bbox_goal_cmd_vel_topic"),
        "bbox_goal_gate_open_distance_m": LaunchConfiguration(
            "bbox_goal_gate_open_distance_m"
        ),
        "bbox_goal_approach_distance_m": LaunchConfiguration(
            "bbox_goal_approach_distance_m"
        ),
        "bbox_goal_reached_tolerance_m": LaunchConfiguration(
            "bbox_goal_reached_tolerance_m"
        ),
        "bbox_goal_min_separation_m": LaunchConfiguration(
            "bbox_goal_min_separation_m"
        ),
        "bbox_goal_heading_offset_deg": LaunchConfiguration(
            "bbox_goal_heading_offset_deg"
        ),
        "bbox_goal_max_target_age_sec": LaunchConfiguration(
            "bbox_goal_max_target_age_sec"
        ),
        "bbox_goal_target_search_enabled": LaunchConfiguration(
            "bbox_goal_target_search_enabled"
        ),
        "bbox_goal_target_search_missing_timeout_sec": LaunchConfiguration(
            "bbox_goal_target_search_missing_timeout_sec"
        ),
        "bbox_goal_target_search_radius_m": LaunchConfiguration(
            "bbox_goal_target_search_radius_m"
        ),
        "bbox_goal_target_search_goal_timeout_sec": LaunchConfiguration(
            "bbox_goal_target_search_goal_timeout_sec"
        ),
        "bbox_goal_target_search_center_x_m": LaunchConfiguration(
            "bbox_goal_target_search_center_x_m"
        ),
        "bbox_goal_target_search_center_y_m": LaunchConfiguration(
            "bbox_goal_target_search_center_y_m"
        ),
        "bbox_goal_capture_stop_hold_sec": LaunchConfiguration(
            "bbox_goal_capture_stop_hold_sec"
        ),
        "bbox_goal_capture_remove_radius_m": LaunchConfiguration(
            "bbox_goal_capture_remove_radius_m"
        ),
        "bbox_goal_target_selection_mode": LaunchConfiguration(
            "bbox_goal_target_selection_mode"
        ),
        "bbox_goal_target_association_radius_m": LaunchConfiguration(
            "bbox_goal_target_association_radius_m"
        ),
        "bbox_goal_target_lock_distance_m": LaunchConfiguration(
            "bbox_goal_target_lock_distance_m"
        ),
        "bbox_goal_max_tracked_targets": LaunchConfiguration(
            "bbox_goal_max_tracked_targets"
        ),
        "bbox_goal_margin_m": LaunchConfiguration("bbox_goal_margin_m"),
        "ignore_storage_objects": LaunchConfiguration("ignore_storage_objects"),
        "bbox_goal_storage_dropoff_enabled": LaunchConfiguration(
            "bbox_goal_storage_dropoff_enabled"
        ),
        "bbox_goal_storage_trigger_count": LaunchConfiguration(
            "bbox_goal_storage_trigger_count"
        ),
        "bbox_goal_storage_min_x": LaunchConfiguration(
            "bbox_goal_storage_min_x"
        ),
        "bbox_goal_storage_max_x": LaunchConfiguration(
            "bbox_goal_storage_max_x"
        ),
        "bbox_goal_storage_min_y": LaunchConfiguration(
            "bbox_goal_storage_min_y"
        ),
        "bbox_goal_storage_max_y": LaunchConfiguration(
            "bbox_goal_storage_max_y"
        ),
        "bbox_goal_storage_entry_mode": LaunchConfiguration(
            "bbox_goal_storage_entry_mode"
        ),
        "bbox_goal_storage_approach_clearance_m": LaunchConfiguration(
            "bbox_goal_storage_approach_clearance_m"
        ),
        "bbox_goal_robot_half_length_m": LaunchConfiguration(
            "bbox_goal_robot_half_length_m"
        ),
        "bbox_goal_robot_half_width_m": LaunchConfiguration(
            "bbox_goal_robot_half_width_m"
        ),
        "bbox_goal_storage_containment_margin_m": LaunchConfiguration(
            "bbox_goal_storage_containment_margin_m"
        ),
        "bbox_goal_storage_heading_tolerance_deg": LaunchConfiguration(
            "bbox_goal_storage_heading_tolerance_deg"
        ),
        "bbox_goal_storage_verify_timeout_sec": LaunchConfiguration(
            "bbox_goal_storage_verify_timeout_sec"
        ),
        "bbox_goal_storage_nav_max_retries": LaunchConfiguration(
            "bbox_goal_storage_nav_max_retries"
        ),
        "bbox_goal_storage_gate_open_wait_sec": LaunchConfiguration(
            "bbox_goal_storage_gate_open_wait_sec"
        ),
        "bbox_goal_storage_backup_action_name": LaunchConfiguration(
            "bbox_goal_storage_backup_action_name"
        ),
        "bbox_goal_storage_backup_distance_m": LaunchConfiguration(
            "bbox_goal_storage_backup_distance_m"
        ),
        "bbox_goal_storage_backup_speed_mps": LaunchConfiguration(
            "bbox_goal_storage_backup_speed_mps"
        ),
        "bbox_goal_storage_backup_time_allowance_sec": LaunchConfiguration(
            "bbox_goal_storage_backup_time_allowance_sec"
        ),
        "enable_mapping_debug": LaunchConfiguration("enable_mapping_debug"),
        "mapping_debug_period_sec": LaunchConfiguration("mapping_debug_period_sec"),
        "mapping_debug_topic": LaunchConfiguration("mapping_debug_topic"),
        "publish_tf": LaunchConfiguration("publish_tf"),
        "wall_tf_mode": LaunchConfiguration("wall_tf_mode"),
        "publish_lidar_tf": LaunchConfiguration("publish_lidar_tf"),
        "bbox_model_path": LaunchConfiguration("bbox_model_path"),
    }

    lidar_arguments = {
        "channel_type": "serial",
        "serial_port": LaunchConfiguration("lidar_serial_port"),
        "serial_baudrate": LaunchConfiguration("lidar_serial_baudrate"),
        "frame_id": LaunchConfiguration("lidar_frame"),
        "inverted": LaunchConfiguration("lidar_inverted"),
        "angle_compensate": LaunchConfiguration("lidar_angle_compensate"),
        "scan_mode": LaunchConfiguration("lidar_scan_mode"),
    }

    sensor_tf_arguments = {
        "base_frame": LaunchConfiguration("base_frame"),
        "laser_frame": LaunchConfiguration("lidar_frame"),
        "camera_frame": LaunchConfiguration("camera_frame"),
        "laser_x": LaunchConfiguration("laser_x"),
        "laser_y": LaunchConfiguration("laser_y"),
        "laser_z": LaunchConfiguration("laser_z"),
        "laser_roll": LaunchConfiguration("laser_roll"),
        "laser_pitch": LaunchConfiguration("laser_pitch"),
        "laser_yaw": LaunchConfiguration("laser_yaw"),
        "camera_x": LaunchConfiguration("camera_x"),
        "camera_y": LaunchConfiguration("camera_y"),
        "camera_z": LaunchConfiguration("camera_z"),
        "camera_roll": LaunchConfiguration("camera_roll"),
        "camera_pitch": LaunchConfiguration("camera_pitch"),
        "camera_yaw": LaunchConfiguration("camera_yaw"),
    }

    nav2_arguments = {
        "use_sim_time": LaunchConfiguration("use_sim_time"),
        "autostart": LaunchConfiguration("nav2_autostart"),
        "params_file": LaunchConfiguration("nav2_params_file"),
        "nav2_inflation_radius": LaunchConfiguration("nav2_inflation_radius"),
        "nav2_behavior_max_rotational_vel": LaunchConfiguration(
            "nav2_behavior_max_rotational_vel"
        ),
    }
    known_map_arguments = {
        "use_sim_time": LaunchConfiguration("use_sim_time"),
        "autostart": LaunchConfiguration("nav2_autostart"),
        "map": LaunchConfiguration("known_map"),
    }

    slam_arguments = {
        "use_sim_time": LaunchConfiguration("use_sim_time"),
        "scan_topic": LaunchConfiguration("scan_topic"),
        "params_file": LaunchConfiguration("slam_params_file"),
    }

    ekf_arguments = {
        "use_sim_time": LaunchConfiguration("use_sim_time"),
        "params_file": LaunchConfiguration("ekf_params_file"),
    }

    esp32_arguments = {
        "dry_run": LaunchConfiguration("esp32_dry_run"),
        "serial_port": LaunchConfiguration("esp32_serial_port"),
        "baud_rate": LaunchConfiguration("esp32_baud_rate"),
        "serial_reset_wait_sec": LaunchConfiguration("esp32_serial_reset_wait_sec"),
        "esp32_protocol": LaunchConfiguration("esp32_protocol"),
        "esp32_command_mode": LaunchConfiguration("esp32_command_mode"),
        "max_power": LaunchConfiguration("esp32_max_power"),
        "max_wheel_velocity_rad_s": LaunchConfiguration(
            "esp32_max_wheel_velocity_rad_s"
        ),
        "encoder_counts_per_revolution": LaunchConfiguration(
            "esp32_encoder_counts_per_revolution"
        ),
        "u_shape_pwm_max": LaunchConfiguration("esp32_u_shape_pwm_max"),
        "log_serial_writes": LaunchConfiguration("esp32_log_serial_writes"),
        "gripper_command_topic": LaunchConfiguration("gripper_command_topic"),
        "capture_arm_topic": LaunchConfiguration("capture_arm_topic"),
        "close_gate_on_start": LaunchConfiguration("esp32_close_gate_on_start"),
        "disarm_capture_on_start": LaunchConfiguration(
            "esp32_disarm_capture_on_start"
        ),
        "mission_event_topic": LaunchConfiguration("object_track_mission_event_topic"),
        "publish_cargo_events": LaunchConfiguration("esp32_publish_cargo_events"),
        "cargo_entry_event_name": LaunchConfiguration("esp32_cargo_entry_event_name"),
        "publish_imu": LaunchConfiguration("esp32_publish_imu"),
        "imu_topic": LaunchConfiguration("esp32_imu_topic"),
        "imu_frame": LaunchConfiguration("esp32_imu_frame"),
        "imu_yaw_offset_deg": LaunchConfiguration("esp32_imu_yaw_offset_deg"),
        "imu_enable_retry_sec": LaunchConfiguration("esp32_imu_enable_retry_sec"),
        "imu_enable_retry_max_attempts": LaunchConfiguration(
            "esp32_imu_enable_retry_max_attempts"
        ),
    }

    return LaunchDescription(
        [
            DeclareLaunchArgument("use_sim_time", default_value="false"),
            DeclareLaunchArgument(
                "shape_engine",
                default_value="models/shape_yolo_best_640.engine",
            ),
            DeclareLaunchArgument("shape_input_size", default_value="640"),
            DeclareLaunchArgument(
                "classifier_engine",
                default_value="models/classifier_real_sz256_640.engine",
            ),
            DeclareLaunchArgument("classifier_input_size", default_value="640"),
            DeclareLaunchArgument("camera_index", default_value="0"),
            DeclareLaunchArgument("camera_pipeline", default_value=""),
            DeclareLaunchArgument("camera_topic", default_value="/camera/image_raw"),
            DeclareLaunchArgument("camera_buffer_size", default_value="1"),
            DeclareLaunchArgument("camera_timestamp_mode", default_value="midpoint"),
            DeclareLaunchArgument(
                "camera_timestamp_offset_sec", default_value="0.0"
            ),
            DeclareLaunchArgument("fps", default_value="30.0"),
            DeclareLaunchArgument("inference_fps", default_value="0.0"),
            DeclareLaunchArgument("shape_nms_iou_threshold", default_value="0.8"),
            DeclareLaunchArgument("shape_class_agnostic_nms", default_value="true"),
            DeclareLaunchArgument("frame_width", default_value="1280"),
            DeclareLaunchArgument("frame_height", default_value="720"),
            DeclareLaunchArgument(
                "classifications_topic",
                default_value="/cube_fruit/classifications",
            ),
            DeclareLaunchArgument(
                "classifier_annotated_topic",
                default_value="/cube_fruit/classifier_annotated_image",
            ),
            DeclareLaunchArgument(
                "distance_annotated_topic",
                default_value="/cube_fruit/annotated_image",
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
            DeclareLaunchArgument(
                "bbox_goal_control_capture_arm",
                default_value="true",
            ),
            DeclareLaunchArgument("gripper_command_topic", default_value="/gripper/command"),
            DeclareLaunchArgument("capture_arm_topic", default_value="/capture/arm"),
            DeclareLaunchArgument("bbox_goal_cmd_vel_topic", default_value="/cmd_vel"),
            DeclareLaunchArgument("bbox_goal_gate_open_distance_m", default_value="0.70"),
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
            DeclareLaunchArgument("ignore_storage_objects", default_value="true"),
            DeclareLaunchArgument(
                "bbox_goal_storage_dropoff_enabled",
                default_value="true",
            ),
            DeclareLaunchArgument(
                "bbox_goal_storage_trigger_count",
                default_value="3",
            ),
            DeclareLaunchArgument("bbox_goal_storage_min_x", default_value="-2.0"),
            DeclareLaunchArgument("bbox_goal_storage_max_x", default_value="-1.6"),
            DeclareLaunchArgument("bbox_goal_storage_min_y", default_value="-2.0"),
            DeclareLaunchArgument("bbox_goal_storage_max_y", default_value="-1.6"),
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
                default_value="10.0",
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
                "bbox_goal_storage_gate_open_wait_sec",
                default_value="1.0",
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
                default_value="0.50",
            ),
            DeclareLaunchArgument(
                "bbox_goal_storage_backup_time_allowance_sec",
                default_value="1.0",
            ),
            DeclareLaunchArgument("enable_nav2", default_value="false"),
            DeclareLaunchArgument("enable_slam", default_value="false"),
            DeclareLaunchArgument("enable_base_odometry", default_value="false"),
            DeclareLaunchArgument("enable_ekf", default_value="false"),
            DeclareLaunchArgument("enable_camera", default_value="true"),
            DeclareLaunchArgument("nav2_autostart", default_value="true"),
            DeclareLaunchArgument("nav2_params_file", default_value=nav2_params_default),
            # 실험 중 장애물 회피 여유를 launch 옵션으로 바로 조절한다.
            DeclareLaunchArgument("nav2_inflation_radius", default_value="0.16"),
            DeclareLaunchArgument(
                "nav2_behavior_max_rotational_vel",
                default_value="0.5",
            ),
            DeclareLaunchArgument("enable_known_map_server", default_value="false"),
            DeclareLaunchArgument("known_map", default_value=known_map_default),
            DeclareLaunchArgument("slam_params_file", default_value=slam_params_default),
            DeclareLaunchArgument("ekf_params_file", default_value=ekf_params_default),
            DeclareLaunchArgument("enable_wheel_command_mapper", default_value="false"),
            DeclareLaunchArgument("enable_esp32_serial_bridge", default_value="false"),
            DeclareLaunchArgument("esp32_dry_run", default_value="true"),
            DeclareLaunchArgument("esp32_serial_port", default_value="/dev/ttyUSB1"),
            DeclareLaunchArgument("esp32_baud_rate", default_value="115200"),
            DeclareLaunchArgument("esp32_serial_reset_wait_sec", default_value="2.0"),
            DeclareLaunchArgument("esp32_protocol", default_value="u_shape"),
            DeclareLaunchArgument("esp32_command_mode", default_value="encoder_velocity"),
            DeclareLaunchArgument("esp32_max_power", default_value="0.35"),
            DeclareLaunchArgument("esp32_max_wheel_velocity_rad_s", default_value="50.0"),
            DeclareLaunchArgument("esp32_encoder_counts_per_revolution", default_value="684.8"),
            DeclareLaunchArgument("esp32_u_shape_pwm_max", default_value="120"),
            DeclareLaunchArgument("esp32_log_serial_writes", default_value="false"),
            DeclareLaunchArgument("esp32_close_gate_on_start", default_value="true"),
            DeclareLaunchArgument("esp32_disarm_capture_on_start", default_value="true"),
            DeclareLaunchArgument("esp32_publish_cargo_events", default_value="true"),
            DeclareLaunchArgument("esp32_cargo_entry_event_name", default_value="object_captured"),
            DeclareLaunchArgument("esp32_publish_imu", default_value="true"),
            DeclareLaunchArgument("esp32_imu_topic", default_value="/imu"),
            DeclareLaunchArgument("esp32_imu_frame", default_value="base_link"),
            DeclareLaunchArgument("esp32_imu_yaw_offset_deg", default_value="0.0"),
            DeclareLaunchArgument("esp32_imu_enable_retry_sec", default_value="1.0"),
            DeclareLaunchArgument("esp32_imu_enable_retry_max_attempts", default_value="0"),
            DeclareLaunchArgument("enable_sensor_tf", default_value="false"),
            DeclareLaunchArgument("enable_lidar_driver", default_value="true"),
            DeclareLaunchArgument("lidar_serial_port", default_value="/dev/ttyUSB0"),
            DeclareLaunchArgument("lidar_serial_baudrate", default_value="460800"),
            DeclareLaunchArgument("lidar_scan_mode", default_value="Standard"),
            DeclareLaunchArgument("lidar_inverted", default_value="false"),
            DeclareLaunchArgument("lidar_angle_compensate", default_value="true"),
            DeclareLaunchArgument("scan_topic", default_value="/scan"),
            DeclareLaunchArgument("odom_topic", default_value="/odometry/filtered"),
            DeclareLaunchArgument("imu_topic", default_value="/imu"),
            DeclareLaunchArgument("yolo_detections_topic", default_value="/shape_yolo/detections"),
            DeclareLaunchArgument("detections_topic", default_value="/detections_json"),
            DeclareLaunchArgument("robot_pose_topic", default_value="/robot_pose_map"),
            DeclareLaunchArgument("object_pose_topic", default_value="/object_pose_map"),
            DeclareLaunchArgument("object_pose_raw_topic", default_value="/object_pose_map_raw"),
            DeclareLaunchArgument(
                "object_pose_raw_json_topic",
                default_value="/object_pose_map_raw_json",
            ),
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
            # 예: target_shape:=cube_any target_fruit:=apple 이면 apple cube만 목표로 본다.
            DeclareLaunchArgument("target_shape", default_value=""),
            DeclareLaunchArgument("target_fruit", default_value=""),
            DeclareLaunchArgument("no_fruit_class", default_value="none"),
            DeclareLaunchArgument("map_frame", default_value="map"),
            DeclareLaunchArgument("odom_frame", default_value="odom"),
            DeclareLaunchArgument("base_frame", default_value="base_link"),
            DeclareLaunchArgument("lidar_frame", default_value="lidar"),
            DeclareLaunchArgument("object_source_frame", default_value="base_link"),
            DeclareLaunchArgument("camera_frame", default_value="camera_frame"),
            DeclareLaunchArgument("laser_x", default_value="0.0"),
            DeclareLaunchArgument("laser_y", default_value="0.0"),
            DeclareLaunchArgument("laser_z", default_value="0.0"),
            DeclareLaunchArgument("laser_roll", default_value="0.0"),
            DeclareLaunchArgument("laser_pitch", default_value="0.0"),
            DeclareLaunchArgument("laser_yaw", default_value="0.0"),
            DeclareLaunchArgument("camera_x", default_value="0.0"),
            DeclareLaunchArgument("camera_y", default_value="0.0"),
            DeclareLaunchArgument("camera_z", default_value="0.0"),
            DeclareLaunchArgument("camera_roll", default_value="0.0"),
            DeclareLaunchArgument("camera_pitch", default_value="0.0"),
            DeclareLaunchArgument("camera_yaw", default_value="0.0"),
            DeclareLaunchArgument("arena_width_m", default_value="4.0"),
            DeclareLaunchArgument("arena_height_m", default_value="4.0"),
            DeclareLaunchArgument("arena_origin", default_value="center"),
            DeclareLaunchArgument("initial_x_m", default_value="1.8"),
            DeclareLaunchArgument("initial_y_m", default_value="-1.8"),
            DeclareLaunchArgument("initial_yaw_deg", default_value="90.0"),
            DeclareLaunchArgument("lidar_x_m", default_value="0.0"),
            DeclareLaunchArgument("lidar_y_m", default_value="0.0"),
            DeclareLaunchArgument("lidar_yaw_deg", default_value="0.0"),
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
            DeclareLaunchArgument("enable_object_track_fusion", default_value="false"),
            DeclareLaunchArgument(
                "object_track_status_topic",
                default_value="/object_track_fusion/status",
            ),
            DeclareLaunchArgument(
                "object_track_remove_pose_topic",
                default_value="/object_track_fusion/remove_pose",
            ),
            DeclareLaunchArgument(
                "object_track_mission_event_topic",
                default_value="/mission/event",
            ),
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
            DeclareLaunchArgument(
                "object_track_candidate_max_age_sec",
                default_value="1.5",
            ),
            DeclareLaunchArgument(
                "object_track_confirmed_max_age_sec",
                default_value="1.5",
            ),
            DeclareLaunchArgument(
                "object_track_keep_confirmed_tracks",
                default_value="false",
            ),
            DeclareLaunchArgument(
                "object_track_max_publish_age_sec",
                default_value="1.5",
            ),
            DeclareLaunchArgument(
                "object_track_out_of_order_tolerance_sec",
                default_value="0.02",
            ),
            DeclareLaunchArgument("object_track_publish_hz", default_value="10.0"),
            DeclareLaunchArgument("object_track_max_tracks", default_value="30"),
            DeclareLaunchArgument("object_track_remove_radius_m", default_value="0.40"),
            DeclareLaunchArgument("object_track_ignored_zones", default_value=""),
            DeclareLaunchArgument(
                "object_track_remove_event_names",
                default_value="object_captured,pickup_success,target_captured,target_reached",
            ),
            DeclareLaunchArgument("enable_mapping_debug", default_value="true"),
            DeclareLaunchArgument("mapping_debug_period_sec", default_value="1.0"),
            DeclareLaunchArgument(
                "mapping_debug_topic",
                default_value="/robot_nav_stack/debug_state",
            ),
            DeclareLaunchArgument("publish_tf", default_value="true"),
            DeclareLaunchArgument("wall_tf_mode", default_value="map_to_base"),
            DeclareLaunchArgument("publish_lidar_tf", default_value="true"),
            DeclareLaunchArgument("bbox_model_path", default_value=bbox_model_default),
            OpaqueFunction(function=_validate_tf_configuration),
            _include_launch(
                "robot_object_detector_ros",
                "jetson_shape_fruit.launch.py",
                detector_arguments,
                condition=IfCondition(LaunchConfiguration("enable_camera")),
            ),
            _include_launch(
                "sllidar_ros2",
                "sllidar_c1_launch.py",
                lidar_arguments,
                condition=IfCondition(LaunchConfiguration("enable_lidar_driver")),
            ),
            _include_launch(
                "snu_robot_bringup",
                "sensor_tf.launch.py",
                sensor_tf_arguments,
                condition=IfCondition(LaunchConfiguration("enable_sensor_tf")),
            ),
            _include_launch(
                "snu_base_control",
                "four_wheel_odometry.launch.py",
                {},
                condition=IfCondition(LaunchConfiguration("enable_base_odometry")),
            ),
            _include_launch(
                "snu_robot_bringup",
                "ekf.launch.py",
                ekf_arguments,
                condition=IfCondition(LaunchConfiguration("enable_ekf")),
            ),
            _include_launch(
                "snu_robot_bringup",
                "slam.launch.py",
                slam_arguments,
                condition=IfCondition(LaunchConfiguration("enable_slam")),
            ),
            _include_launch(
                "snu_robot_bringup",
                "known_map_server.launch.py",
                known_map_arguments,
                condition=IfCondition(LaunchConfiguration("enable_known_map_server")),
            ),
            _include_launch(
                "snu_robot_bringup",
                "navigation.launch.py",
                nav2_arguments,
                condition=IfCondition(LaunchConfiguration("enable_nav2")),
            ),
            _include_launch(
                "snu_base_control",
                "cmd_vel_to_four_wheel.launch.py",
                {},
                condition=IfCondition(
                    LaunchConfiguration("enable_wheel_command_mapper")
                ),
            ),
            _include_launch(
                "snu_hardware_drivers",
                "esp32_serial_hardware.launch.py",
                esp32_arguments,
                condition=IfCondition(
                    LaunchConfiguration("enable_esp32_serial_bridge")
                ),
            ),
            _include_launch(
                "robot_nav_stack",
                "robot_nav_stack.launch.py",
                nav_arguments,
            ),
        ]
    )
