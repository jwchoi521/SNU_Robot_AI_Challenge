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
    fps = LaunchConfiguration("fps")
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
            DeclareLaunchArgument("fps", default_value="30.0"),
            DeclareLaunchArgument("frame_width", default_value="640"),
            DeclareLaunchArgument("frame_height", default_value="480"),
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
                        "fps": ParameterValue(fps, value_type=float),
                        "frame_width": ParameterValue(frame_width, value_type=int),
                        "frame_height": ParameterValue(frame_height, value_type=int),
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
                        "nms_iou_threshold": 0.7,
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
                        "classifications_topic": "/cube_fruit/classifications",
                        "annotated_topic": "/cube_fruit/annotated_image",
                        "input_width": ParameterValue(classifier_input_size, value_type=int),
                        "input_height": ParameterValue(classifier_input_size, value_type=int),
                        "cube_class_id": 0,
                        "threshold": 0.7,
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
