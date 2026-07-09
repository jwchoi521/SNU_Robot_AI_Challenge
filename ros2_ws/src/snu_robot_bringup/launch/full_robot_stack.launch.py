from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
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

    detector_arguments = {
        "shape_engine": LaunchConfiguration("shape_engine"),
        "shape_input_size": LaunchConfiguration("shape_input_size"),
        "classifier_engine": LaunchConfiguration("classifier_engine"),
        "classifier_input_size": LaunchConfiguration("classifier_input_size"),
        "camera_index": LaunchConfiguration("camera_index"),
        "camera_pipeline": LaunchConfiguration("camera_pipeline"),
        "camera_topic": LaunchConfiguration("camera_topic"),
        "classifications_topic": LaunchConfiguration("classifications_topic"),
        "classifier_annotated_topic": LaunchConfiguration("classifier_annotated_topic"),
        "fps": LaunchConfiguration("fps"),
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
        "enable_distance_overlay": LaunchConfiguration("enable_distance_overlay"),
        "enable_bbox_goal_navigation": LaunchConfiguration("enable_bbox_goal_navigation"),
        "enable_semantic_obstacle_cloud": LaunchConfiguration(
            "enable_semantic_obstacle_cloud"
        ),
        "bbox_goal_target_topic": LaunchConfiguration("bbox_goal_target_topic"),
        "bbox_goal_pose_topic": LaunchConfiguration("bbox_goal_pose_topic"),
        "bbox_goal_status_topic": LaunchConfiguration("bbox_goal_status_topic"),
        "bbox_goal_nav_action_name": LaunchConfiguration("bbox_goal_nav_action_name"),
        "bbox_goal_send_nav2_goal": LaunchConfiguration("bbox_goal_send_nav2_goal"),
        "bbox_goal_publish_mission_events": LaunchConfiguration(
            "bbox_goal_publish_mission_events"
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
        "bbox_goal_max_target_age_sec": LaunchConfiguration(
            "bbox_goal_max_target_age_sec"
        ),
        "bbox_goal_target_selection_mode": LaunchConfiguration(
            "bbox_goal_target_selection_mode"
        ),
        "bbox_goal_target_association_radius_m": LaunchConfiguration(
            "bbox_goal_target_association_radius_m"
        ),
        "bbox_goal_max_tracked_targets": LaunchConfiguration(
            "bbox_goal_max_tracked_targets"
        ),
        "bbox_goal_margin_m": LaunchConfiguration("bbox_goal_margin_m"),
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
        "publish_imu": LaunchConfiguration("esp32_publish_imu"),
        "imu_topic": LaunchConfiguration("esp32_imu_topic"),
        "imu_frame": LaunchConfiguration("esp32_imu_frame"),
        "imu_yaw_offset_deg": LaunchConfiguration("esp32_imu_yaw_offset_deg"),
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
            DeclareLaunchArgument("fps", default_value="30.0"),
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
            DeclareLaunchArgument("enable_nav2", default_value="false"),
            DeclareLaunchArgument("enable_slam", default_value="false"),
            DeclareLaunchArgument("enable_base_odometry", default_value="false"),
            DeclareLaunchArgument("enable_ekf", default_value="false"),
            DeclareLaunchArgument("nav2_autostart", default_value="true"),
            DeclareLaunchArgument("nav2_params_file", default_value=nav2_params_default),
            DeclareLaunchArgument("enable_known_map_server", default_value="false"),
            DeclareLaunchArgument("known_map", default_value=known_map_default),
            DeclareLaunchArgument("slam_params_file", default_value=slam_params_default),
            DeclareLaunchArgument("enable_wheel_command_mapper", default_value="false"),
            DeclareLaunchArgument("enable_esp32_serial_bridge", default_value="false"),
            DeclareLaunchArgument("esp32_dry_run", default_value="true"),
            DeclareLaunchArgument("esp32_serial_port", default_value="/dev/ttyUSB1"),
            DeclareLaunchArgument("esp32_baud_rate", default_value="115200"),
            DeclareLaunchArgument("esp32_serial_reset_wait_sec", default_value="2.0"),
            DeclareLaunchArgument("esp32_protocol", default_value="u_shape"),
            DeclareLaunchArgument("esp32_command_mode", default_value="encoder_velocity"),
            DeclareLaunchArgument("esp32_max_power", default_value="0.35"),
            DeclareLaunchArgument("esp32_max_wheel_velocity_rad_s", default_value="20.0"),
            DeclareLaunchArgument("esp32_encoder_counts_per_revolution", default_value="890.3"),
            DeclareLaunchArgument("esp32_u_shape_pwm_max", default_value="120"),
            DeclareLaunchArgument("esp32_log_serial_writes", default_value="false"),
            DeclareLaunchArgument("esp32_publish_imu", default_value="true"),
            DeclareLaunchArgument("esp32_imu_topic", default_value="/imu"),
            DeclareLaunchArgument("esp32_imu_frame", default_value="base_link"),
            DeclareLaunchArgument("esp32_imu_yaw_offset_deg", default_value="0.0"),
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
            _include_launch(
                "robot_object_detector_ros",
                "jetson_shape_fruit.launch.py",
                detector_arguments,
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
