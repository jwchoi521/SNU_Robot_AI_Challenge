from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    shape_engine = LaunchConfiguration("shape_engine")
    shape_input_size = LaunchConfiguration("shape_input_size")
    classifier_engine = LaunchConfiguration("classifier_engine")
    classifier_input_size = LaunchConfiguration("classifier_input_size")
    camera_index = LaunchConfiguration("camera_index")
    camera_pipeline = LaunchConfiguration("camera_pipeline")
    camera_topic = LaunchConfiguration("camera_topic")
    camera_frame = LaunchConfiguration("camera_frame")
    camera_buffer_size = LaunchConfiguration("camera_buffer_size")
    camera_timestamp_mode = LaunchConfiguration("camera_timestamp_mode")
    camera_timestamp_offset_sec = LaunchConfiguration("camera_timestamp_offset_sec")
    classifications_topic = LaunchConfiguration("classifications_topic")
    classifier_annotated_topic = LaunchConfiguration("classifier_annotated_topic")
    fps = LaunchConfiguration("fps")
    inference_fps = LaunchConfiguration("inference_fps")
    shape_nms_iou_threshold = LaunchConfiguration("shape_nms_iou_threshold")
    shape_class_agnostic_nms = LaunchConfiguration("shape_class_agnostic_nms")
    frame_width = LaunchConfiguration("frame_width")
    frame_height = LaunchConfiguration("frame_height")

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "shape_engine",
                default_value="models/shape_yolo_best_640.engine",
                description="Path to the YOLO TensorRT engine.",
            ),
            DeclareLaunchArgument(
                "shape_input_size",
                default_value="640",
                description="Square input size used when the YOLO engine was exported.",
            ),
            DeclareLaunchArgument(
                "classifier_engine",
                default_value="models/classifier_real_sz256_640.engine",
                description="Path to the cube fruit classifier TensorRT engine.",
            ),
            DeclareLaunchArgument(
                "classifier_input_size",
                default_value="640",
                description="Square input size used when the classifier engine was exported.",
            ),
            DeclareLaunchArgument("camera_index", default_value="0"),
            DeclareLaunchArgument(
                "camera_pipeline",
                default_value="",
                description="Optional OpenCV GStreamer pipeline. If set, camera_index is ignored.",
            ),
            DeclareLaunchArgument("camera_topic", default_value="/camera/image_raw"),
            DeclareLaunchArgument("camera_frame", default_value="camera_frame"),
            DeclareLaunchArgument("camera_buffer_size", default_value="1"),
            DeclareLaunchArgument("camera_timestamp_mode", default_value="midpoint"),
            DeclareLaunchArgument(
                "camera_timestamp_offset_sec", default_value="0.0"
            ),
            DeclareLaunchArgument(
                "classifications_topic",
                default_value="/cube_fruit/classifications",
            ),
            DeclareLaunchArgument(
                "classifier_annotated_topic",
                default_value="/cube_fruit/annotated_image",
            ),
            DeclareLaunchArgument("fps", default_value="30.0"),
            DeclareLaunchArgument(
                "inference_fps",
                default_value="0.0",
                description="Maximum YOLO inference rate in Hz. 0 means infer every camera frame.",
            ),
            DeclareLaunchArgument(
                "shape_nms_iou_threshold",
                default_value="0.8",
                description="IoU threshold used by YOLO NMS.",
            ),
            DeclareLaunchArgument(
                "shape_class_agnostic_nms",
                default_value="true",
                description="Suppress overlapping YOLO boxes across different shape classes.",
            ),
            DeclareLaunchArgument("frame_width", default_value="1280"),
            DeclareLaunchArgument("frame_height", default_value="720"),
            Node(
                package="robot_object_detector_ros",
                executable="opencv_camera_node",
                name="opencv_camera_node",
                output="screen",
                parameters=[
                    {
                        "image_topic": camera_topic,
                        "camera_index": ParameterValue(camera_index, value_type=int),
                        "camera_pipeline": camera_pipeline,
                        "frame_id": camera_frame,
                        "fps": ParameterValue(fps, value_type=float),
                        "frame_width": ParameterValue(frame_width, value_type=int),
                        "frame_height": ParameterValue(frame_height, value_type=int),
                        "buffer_size": ParameterValue(camera_buffer_size, value_type=int),
                        "timestamp_mode": camera_timestamp_mode,
                        "timestamp_offset_sec": ParameterValue(
                            camera_timestamp_offset_sec, value_type=float
                        ),
                    }
                ],
            ),
            Node(
                package="robot_object_detector_ros",
                executable="shape_yolo_node",
                name="shape_yolo_node",
                output="screen",
                parameters=[
                    {
                        "engine_path": shape_engine,
                        "image_topic": camera_topic,
                        "detections_topic": "/shape_yolo/detections",
                        "annotated_topic": "/shape_yolo/annotated_image",
                        "input_width": ParameterValue(shape_input_size, value_type=int),
                        "input_height": ParameterValue(shape_input_size, value_type=int),
                        "num_classes": 4,
                        "class_names": [
                            "cube_any",
                            "octahedron",
                            "dodecahedron",
                            "icosahedron",
                        ],
                        "conf_threshold": 0.25,
                        "nms_iou_threshold": ParameterValue(
                            shape_nms_iou_threshold, value_type=float
                        ),
                        "class_agnostic_nms": ParameterValue(
                            shape_class_agnostic_nms, value_type=bool
                        ),
                        "inference_fps": ParameterValue(inference_fps, value_type=float),
                    }
                ],
            ),
            Node(
                package="robot_object_detector_ros",
                executable="cube_fruit_classifier_node",
                name="cube_fruit_classifier_node",
                output="screen",
                parameters=[
                    {
                        "engine_path": classifier_engine,
                        "image_topic": camera_topic,
                        "detections_topic": "/shape_yolo/detections",
                        "classifications_topic": classifications_topic,
                        "annotated_topic": classifier_annotated_topic,
                        "input_width": ParameterValue(classifier_input_size, value_type=int),
                        "input_height": ParameterValue(classifier_input_size, value_type=int),
                        "cube_class_id": 0,
                        "threshold": 0.2,
                        "class_names": [
                            "apple",
                            "orange",
                            "banana",
                            "pineapple",
                            "none",
                        ],
                        "no_fruit_class": "none",
                    }
                ],
            ),
        ]
    )
