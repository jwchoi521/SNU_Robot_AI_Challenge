from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def _include_launch(package_name: str, launch_file: str, arguments: dict):
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
        launch_arguments=arguments.items(),
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
        "fps": LaunchConfiguration("fps"),
        "frame_width": LaunchConfiguration("frame_width"),
        "frame_height": LaunchConfiguration("frame_height"),
    }

    nav_arguments = {
        "scan_topic": LaunchConfiguration("scan_topic"),
        "odom_topic": LaunchConfiguration("odom_topic"),
        "yolo_detections_topic": LaunchConfiguration("yolo_detections_topic"),
        "detections_topic": LaunchConfiguration("detections_topic"),
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
        "publish_tf": LaunchConfiguration("publish_tf"),
        "publish_lidar_tf": LaunchConfiguration("publish_lidar_tf"),
        "bbox_model_path": LaunchConfiguration("bbox_model_path"),
    }

    return LaunchDescription(
        [
            DeclareLaunchArgument("shape_engine", default_value="models/shape_yolo_best_640.engine"),
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
            DeclareLaunchArgument("publish_tf", default_value="true"),
            DeclareLaunchArgument("publish_lidar_tf", default_value="true"),
            DeclareLaunchArgument("bbox_model_path", default_value=bbox_model_default),
            _include_launch(
                "robot_object_detector_ros",
                "jetson_shape_fruit.launch.py",
                detector_arguments,
            ),
            _include_launch(
                "robot_nav_stack",
                "robot_nav_stack.launch.py",
                nav_arguments,
            ),
        ]
    )
