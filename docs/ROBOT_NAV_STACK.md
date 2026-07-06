# robot_nav_ros2_ws

ROS2 scaffold for the current robot navigation plan.

## Jetson Orin Nano Setup

Copy this workspace folder to the Jetson as a ROS2 colcon workspace, then run:

```bash
cd ~/robot_nav_ros2_ws
python3 -m pip install -r requirements-jetson.txt
rosdep install --from-paths src -y --ignore-src
colcon build --symlink-install
source install/setup.bash
```

The workspace now includes the TensorRT YOLO ROS2 package at:

```text
src/robot_object_detector_ros
```

The easiest runtime entry point starts both the TensorRT detector and the
navigation stack:

```bash
ros2 launch snu_robot_bringup full_robot_stack.launch.py \
  shape_engine:=models/shape_yolo_best_640.engine \
  classifier_engine:=models/classifier_real_sz256_640.engine \
  scan_topic:=/scan \
  odom_topic:=/odom \
  arena_width_m:=4.0 \
  arena_height_m:=4.0
```

If you want to debug perception alone, start only the detector, using the
engine paths that exist on the Jetson:

```bash
ros2 launch robot_object_detector_ros jetson_shape_fruit.launch.py \
  shape_engine:=models/shape_yolo_best_640.engine \
  classifier_engine:=models/classifier_real_sz256_640.engine
```

The trained homography + residual-learning model is packaged at:

```text
src/robot_nav_stack/models/bbox_pose_anchor033.joblib
```

The packaged model is the batch2-only model trained with the new 1280x720
homography and `anchor_y = bbox_cy + 0.33 * bbox_h`.

The default launch file uses that model automatically after `colcon build`.
Because the model is a `joblib`/scikit-learn artifact, keep the Jetson Python
packages close to `requirements-jetson.txt` unless the model is retrained or
re-exported on the Jetson.
Run the full stack with your real topics and measured LiDAR offset:

```bash
ros2 launch robot_nav_stack robot_nav_stack.launch.py \
  scan_topic:=/scan \
  odom_topic:=/odom \
  yolo_detections_topic:=/shape_yolo/detections \
  detections_topic:=/detections_json \
  arena_width_m:=4.0 \
  arena_height_m:=4.0 \
  initial_x_m:=2.0 \
  initial_y_m:=2.0 \
  initial_yaw_deg:=0.0 \
  lidar_x_m:=0.0 \
  lidar_y_m:=0.0 \
  lidar_yaw_deg:=0.0
```

Set `lidar_x_m`, `lidar_y_m`, and `lidar_yaw_deg` to the LiDAR pose relative
to `base_link`. By default the 4-wall localizer publishes `map -> base_link`
and `map -> lidar`, so `object_localizer_node` can transform object detections
from the learned LiDAR frame into `map`.

## Nodes

- `four_wall_localizer_node`
  - Input: `/scan` (`sensor_msgs/LaserScan`), `/odom` (`nav_msgs/Odometry`)
  - Output: `/robot_pose_map` (`geometry_msgs/PoseStamped`)
  - Status: `/four_wall_localizer/status` (`std_msgs/String` JSON)
  - Assumes the LiDAR mainly sees the 4 known arena walls.
  - For each robot pose candidate, ray-casts every LiDAR beam to the first
    intersected wall among `x=0`, `x=arena_width`, `y=0`, `y=arena_height`,
    then minimizes the robust range residual.
  - For a square arena, wall-only matching has mirror/rotation ambiguity. The
    node explicitly tests symmetry-equivalent pose candidates, then uses the
    configured initial pose, previous pose, and odometry delta as a prior to
    choose the physically continuous candidate.
  - The status JSON includes per-wall ray counts, `ambiguous_without_prior`,
    and `symmetry_resolved_by_prior`.

- `rect_wall_localizer_node`
  - Alternative wall localizer that fits transformed LiDAR points to the nearest
    rectangular boundary. Use `four_wall_localizer_node` first when the LiDAR
    mostly sees the walls cleanly.

- `object_localizer_node`
  - Input: `/detections_json` (`std_msgs/String`)
  - Output: `/object_pose_map` (`geometry_msgs/PoseStamped`)
  - Uses homography + residual model from `bbox_pose_ml.py`.

- `yolo_detection_adapter_node`
  - Input: `/shape_yolo/detections`
    (`robot_object_detector_ros/Detection2DArray`)
  - Output: `/detections_json` (`std_msgs/String`)
  - Converts TensorRT YOLO `x1,y1,x2,y2` pixel boxes into the
    `cx,cy,w,h` format expected by `object_localizer_node`.
  - Preserves the original image timestamp from the detection message header.

- `approach_goal_node`
  - Input: `/target_pose_map`, `/robot_pose_map`
  - Output: `/approach_goal` (`geometry_msgs/PoseStamped`)
  - Generates target-facing approach poses.

- `semantic_obstacle_cloud_node`
  - Input: `/object_pose_map` (`geometry_msgs/PoseStamped`)
  - Output: `/semantic_obstacle_cloud` (`sensor_msgs/PointCloud2`)
  - Expands each object pose into a small disk of points so Nav2's obstacle
    layer can mark it in the costmap.
  - Default object disk radius is `0.04m`, matching an obstacle diameter of
    about `8cm`; Nav2 inflation adds robot clearance separately.
  - Object poses within `0.12m` are associated as the same obstacle and merged
    with smoothing to reduce camera/localization jitter.
    Increase this if one object appears as several nearby obstacles; decrease it
    if two nearby objects are being merged.

- `pure_pursuit_node`
  - Input: `/planned_path`, `/robot_pose_map`
  - Output: `/cmd_vel`
  - Simple fallback controller. In production, prefer Nav2 controller server.

- `wheel_controller_node`
  - Input: `/cmd_vel`, `/wheel_speed_measured`
  - Output: `/motor_voltage_cmd`
  - Converts velocity commands to wheel PID voltage/PWM commands.

## Expected Detection JSON

```json
{
  "stamp": 123.456,
  "bbox": {"cx": 322.0, "cy": 241.0, "w": 100.0, "h": 135.0},
  "object_type": "cube_any",
  "confidence": 0.91
}
```

Use the original image timestamp for `stamp`.
The current model was trained with these object classes:
`cube_any`, `octahedron`, `dodecahedron`, `icosahedron`.

## Nav2

See:

```text
src/robot_nav_stack/config/nav2_smac_reeds_shepp.yaml
```

This config uses:

```text
Smac Hybrid-A*
REEDS_SHEPP
reverse_penalty
goal tolerance
robot footprint/inflation
semantic object PointCloud2 obstacle source
semantic obstacle association radius: 0.12m
```

## Robot Geometry Assumption

```text
front/rear wheel spacing: 0.235m
left/right wheel spacing: 0.30m
wheel diameter: 0.066m
wheel radius: 0.033m
chassis length: 0.32m
chassis width: 0.33m
Nav2 footprint: x +/-0.16m, y +/-0.165m
```
