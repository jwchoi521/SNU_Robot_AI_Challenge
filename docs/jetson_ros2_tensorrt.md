# Jetson ROS2 TensorRT Pipeline

This pipeline runs three ROS2 C++ nodes on Jetson Orin Nano:

```text
opencv_camera_node
  /camera/image_raw
        -> shape_yolo_node
             /shape_yolo/detections
             /shape_yolo/annotated_image
        -> cube_fruit_classifier_node
             /cube_fruit/classifications
             /cube_fruit/annotated_image
```

`shape_yolo_node` detects shapes with a YOLO TensorRT engine. For detections
where `class_id == 0`, `cube_fruit_classifier_node` crops the cube bbox from the
same camera frame and classifies it as `apple`, `orange`, `banana`,
`pineapple`, or `none`.

## 1. Install ROS2 Dependencies

On Jetson, use the ROS2 distro that is installed with your JetPack setup.

```bash
sudo apt update
sudo apt install -y \
  ros-$ROS_DISTRO-cv-bridge \
  ros-$ROS_DISTRO-message-filters \
  ros-$ROS_DISTRO-rqt-image-view \
  python3-colcon-common-extensions
```

TensorRT and CUDA should come from JetPack. Check:

```bash
trtexec --version
python3 - <<'PY'
import tensorrt as trt
print(trt.__version__)
PY
```

If TensorRT headers or plugins are missing during `colcon build`, install the
JetPack TensorRT development packages:

```bash
sudo apt install -y libnvinfer-dev libnvinfer-plugin-dev
```

## 2. Build The ROS2 Package

The package is already included in the integrated workspace:

```bash
cd ~/robot_nav_ros2_ws
source /opt/ros/$ROS_DISTRO/setup.bash
colcon build --symlink-install --packages-select robot_object_detector_ros
source install/setup.bash
```

## 3. Prepare TensorRT Engines

Create the model directory:

```bash
cd ~/robot_object_detector
mkdir -p models
```

### YOLO Shape Engine

Copy your trained shape YOLO checkpoint to Jetson, for example:

```text
models/shape_yolo_best.pt
```

Export the TensorRT engine on Jetson:

```bash
python3 src/export_engine.py \
  --model models/shape_yolo_best.pt \
  --imgsz 640 \
  --half \
  --device 0 \
  --output models/shape_yolo_best_640.engine
```

The expected output is:

```text
models/shape_yolo_best_640.engine
```

`src/export_engine.py --output` strips the Ultralytics metadata prefix and writes
a raw TensorRT plan. The C++ node performs confidence filtering and NMS itself.

### Fruit Classifier Engine

Copy your trained classifier checkpoint to Jetson, for example:

```text
models/classifier_real_sz256.pt
```

Export ONNX:

```bash
python3 -m pip install onnx onnxscript
python3 scripts/export_fruit_classifier_onnx.py \
  --model models/classifier_real_sz256.pt \
  --output models/classifier_real_sz256_640.onnx \
  --imgsz 640 \
  --device cpu
```

Build the TensorRT engine on Jetson:

```bash
trtexec \
  --onnx=models/classifier_real_sz256_640.onnx \
  --saveEngine=models/classifier_real_sz256_640.engine \
  --fp16
```

Repeat with `--imgsz 960` and `--imgsz 1280` if you want the larger classifier
engine variants. The classifier engine expects `1x3x{imgsz}x{imgsz}` RGB input
normalized with
`mean=(0.5, 0.5, 0.5)` and `std=(0.5, 0.5, 0.5)`.

## 4. Run The Pipeline

USB camera:

```bash
cd ~/robot_object_detector
source /opt/ros/$ROS_DISTRO/setup.bash
source ~/ros2_ws/install/setup.bash

ros2 launch robot_object_detector_ros jetson_shape_fruit.launch.py \
  shape_engine:=models/shape_yolo_best_640.engine \
  shape_input_size:=640 \
  classifier_engine:=models/classifier_real_sz256_640.engine \
  classifier_input_size:=640 \
  camera_index:=0
```

CSI camera example:

```bash
ros2 launch robot_object_detector_ros jetson_shape_fruit.launch.py \
  shape_engine:=models/shape_yolo_best_640.engine \
  shape_input_size:=640 \
  classifier_engine:=models/classifier_real_sz256_640.engine \
  classifier_input_size:=640 \
  camera_pipeline:='nvarguscamerasrc ! video/x-raw(memory:NVMM), width=1280, height=720, framerate=30/1 ! nvvidconv ! video/x-raw, format=BGRx ! videoconvert ! video/x-raw, format=BGR ! appsink'
```

View the overlay:

```bash
rqt_image_view /cube_fruit/annotated_image
```

Print final cube fruit classifications:

```bash
ros2 topic echo /cube_fruit/classifications
```

## 5. Topics

Published by `shape_yolo_node`:

```text
/shape_yolo/detections        robot_object_detector_ros/msg/Detection2DArray
/shape_yolo/annotated_image   sensor_msgs/msg/Image
```

Published by `cube_fruit_classifier_node`:

```text
/cube_fruit/classifications   robot_object_detector_ros/msg/FruitClassificationArray
/cube_fruit/annotated_image   sensor_msgs/msg/Image
```

`FruitClassification.pick_allowed` is `false` when the classifier result is
`none`. This matches the current rule that a lone cube is `unknown_cube` and is
not pickable.

## 6. Important Parameters

```text
shape_yolo_node.conf_threshold        default 0.25
shape_yolo_node.nms_iou_threshold     default 0.7
cube_fruit_classifier_node.threshold  default 0.7
```

Lower `cube_fruit_classifier_node.threshold` only if the classifier is too
conservative. A value such as `0.5` will classify more cubes as fruit, but also
increases false positives.
