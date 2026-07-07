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
        "image_topic": LaunchConfiguration("camera_topic"),
        "yolo_detections_topic": LaunchConfiguration("yolo_detections_topic"),
        "detections_topic": LaunchConfiguration("detections_topic"),
        "classifications_topic": LaunchConfiguration("classifications_topic"),
        "distance_annotated_topic": LaunchConfiguration("distance_annotated_topic"),
        "robot_pose_topic": LaunchConfiguration("robot_pose_topic"),
        "object_pose_topic": LaunchConfiguration("object_pose_topic"),
        "map_frame": LaunchConfiguration("map_frame"),
        "base_frame": LaunchConfiguration("base_frame"),
        "lidar_frame": LaunchConfiguration("lidar_frame"),
        "arena_width_m": LaunchConfiguration("arena_width_m"),
        "arena_height_m": LaunchConfiguration("arena_height_m"),
        "initial_x_m": LaunchConfiguration("initial_x_m"),
        "initial_y_m": LaunchConfiguration("initial_y_m"),
        "initial_yaw_deg": LaunchConfiguration("initial_yaw_deg"),
        "lidar_x_m": LaunchConfiguration("lidar_x_m"),
        "lidar_y_m": LaunchConfiguration("lidar_y_m"),
        "lidar_yaw_deg": LaunchConfiguration("lidar_yaw_deg"),
        "min_visible_walls": LaunchConfiguration("min_visible_walls"),
        "min_rays_per_wall": LaunchConfiguration("min_rays_per_wall"),
        "adapter_min_confidence": LaunchConfiguration("adapter_min_confidence"),
        "detection_stamp_mode": LaunchConfiguration("detection_stamp_mode"),
        "max_header_stamp_offset_sec": LaunchConfiguration("max_header_stamp_offset_sec"),
        "fallback_to_latest_tf": LaunchConfiguration("fallback_to_latest_tf"),
        "enable_distance_overlay": LaunchConfiguration("enable_distance_overlay"),
        "enable_mapping_debug": LaunchConfiguration("enable_mapping_debug"),
        "mapping_debug_period_sec": LaunchConfiguration("mapping_debug_period_sec"),
        "mapping_debug_topic": LaunchConfiguration("mapping_debug_topic"),
        "publish_tf": LaunchConfiguration("publish_tf"),
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

    return LaunchDescription(
        [
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
            DeclareLaunchArgument("enable_distance_overlay", default_value="true"),
            DeclareLaunchArgument("enable_lidar_driver", default_value="true"),
            DeclareLaunchArgument("lidar_serial_port", default_value="/dev/ttyUSB0"),
            DeclareLaunchArgument("lidar_serial_baudrate", default_value="460800"),
            DeclareLaunchArgument("lidar_scan_mode", default_value="Standard"),
            DeclareLaunchArgument("lidar_inverted", default_value="false"),
            DeclareLaunchArgument("lidar_angle_compensate", default_value="true"),
            DeclareLaunchArgument("scan_topic", default_value="/scan"),
            DeclareLaunchArgument("odom_topic", default_value="/odom"),
            DeclareLaunchArgument("yolo_detections_topic", default_value="/shape_yolo/detections"),
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
            DeclareLaunchArgument("adapter_min_confidence", default_value="0.0"),
            DeclareLaunchArgument("detection_stamp_mode", default_value="auto"),
            DeclareLaunchArgument("max_header_stamp_offset_sec", default_value="2.0"),
            DeclareLaunchArgument("fallback_to_latest_tf", default_value="true"),
            DeclareLaunchArgument("enable_mapping_debug", default_value="true"),
            DeclareLaunchArgument("mapping_debug_period_sec", default_value="1.0"),
            DeclareLaunchArgument(
                "mapping_debug_topic",
                default_value="/robot_nav_stack/debug_state",
            ),
            DeclareLaunchArgument("publish_tf", default_value="true"),
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
                "robot_nav_stack",
                "robot_nav_stack.launch.py",
                nav_arguments,
            ),
        ]
    )
