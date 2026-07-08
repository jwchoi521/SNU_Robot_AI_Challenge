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

The workspace now includes the TensorRT YOLO ROS2 package and the SLAMTEC
RPLIDAR C1 driver package at:

```text
src/robot_object_detector_ros
src/sllidar_ros2
```

The RPLIDAR C1 is expected on `/dev/ttyUSB0`. If the driver cannot open the
port, add your user to the `dialout` group, then log out and back in:

```bash
sudo usermod -a -G dialout $USER
```

The easiest runtime entry point starts the TensorRT detector, RPLIDAR C1
driver, and navigation stack:

```bash
ros2 launch snu_robot_bringup full_robot_stack.launch.py \
  shape_engine:=models/shape_yolo_best_640.engine \
  shape_input_size:=640 \
  classifier_engine:=models/classifier_real_sz256_640.engine \
  classifier_input_size:=640 \
  camera_index:=0 \
  frame_width:=1280 \
  frame_height:=720 \
  enable_lidar_driver:=true \
  lidar_serial_port:=/dev/ttyUSB0 \
  lidar_serial_baudrate:=460800 \
  lidar_scan_mode:=Standard \
  lidar_frame:=lidar \
  scan_topic:=/scan \
  odom_topic:=/odom \
  arena_origin:=center \
  arena_width_m:=4.0 \
  arena_height_m:=4.0
```

`full_robot_stack.launch.py` forwards the engine/camera arguments into
`jetson_shape_fruit.launch.py` once and the LiDAR arguments into
`sllidar_c1_launch.py` once. Do not start those launch files separately when
using the full stack, because that would launch duplicate camera or LiDAR
pipelines.

With the full stack, `/cube_fruit/annotated_image` is published by
`distance_annotator_node`: it redraws the YOLO/classifier bbox labels and adds
the bbox model distance estimate, for example `apple 0.92 0.77m`. The raw
classifier-only overlay is still available on `/cube_fruit/classifier_annotated_image`.

To let a bbox-localized object drive the robot through Nav2, enable the
optional goal bridge:

```bash
ros2 launch snu_robot_bringup full_robot_stack.launch.py \
  enable_bbox_goal_navigation:=true \
  bbox_goal_target_topic:=/object_pose_map \
  bbox_goal_approach_distance_m:=0.0 \
  enable_known_map_server:=true \
  arena_origin:=center \
  enable_semantic_obstacle_cloud:=false
```

Leave `enable_bbox_goal_navigation` false while validating perception and
localization, because setting it true sends `NavigateToPose` goals whenever a
fresh `/object_pose_map` target is available.
See `docs/BBOX_GOAL_NAVIGATION_TEST.md` for the safe bring-up checklist and
robot-side tuning parameters.

If you want to debug the LiDAR alone:

```bash
ros2 launch sllidar_ros2 sllidar_c1_launch.py \
  serial_port:=/dev/ttyUSB0 \
  serial_baudrate:=460800 \
  frame_id:=lidar
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
  arena_origin:=center \
  arena_width_m:=4.0 \
  arena_height_m:=4.0 \
  initial_x_m:=0.0 \
  initial_y_m:=0.0 \
  initial_yaw_deg:=0.0 \
  lidar_x_m:=0.0 \
  lidar_y_m:=0.0 \
  lidar_yaw_deg:=0.0
```

Set `lidar_x_m`, `lidar_y_m`, and `lidar_yaw_deg` to the LiDAR pose relative
to `base_link`. By default the 4-wall localizer publishes `map -> base_link`
and `map -> lidar`, so `object_localizer_node` can transform object detections
from the learned LiDAR frame into `map`.
The default 4x4 arena origin is the field center, so the walls are at
`x=-2`, `x=+2`, `y=-2`, and `y=+2`. Set `arena_origin:=corner` only if you
want the older `x=0..4`, `y=0..4` convention.
For Nav2 driving with wheel odometry/EKF, use `wall_tf_mode:=map_to_odom`,
`enable_sensor_tf:=true`, and `publish_lidar_tf:=false` so the TF tree is
`map -> odom -> base_link -> lidar`.

## Nodes

- `four_wall_localizer_node`
  - Input: `/scan` (`sensor_msgs/LaserScan`), `/odom` (`nav_msgs/Odometry`)
  - Output: `/robot_pose_map` (`geometry_msgs/PoseStamped`)
  - Status: `/four_wall_localizer/status` (`std_msgs/String` JSON)
  - Assumes the LiDAR mainly sees the 4 known arena walls.
  - Can publish either direct localization TF (`map -> base_link`) or Nav2
    localization TF (`map -> odom`) through `wall_tf_mode`.
  - For each robot pose candidate, ray-casts every LiDAR beam to the first
    intersected wall. With the default centered 4x4 arena, those walls are
    `x=-2`, `x=+2`, `y=-2`, and `y=+2`,
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
  - Looks up `map -> object_source_frame` at the original detection stamp.
    If that stamp is newer than the latest localization TF, the node queues
    the detection and retries exact TF lookup for `pending_detection_timeout_sec`
    instead of projecting with the latest TF.

- `distance_annotator_node`
  - Input: `/camera/image_raw`, `/shape_yolo/detections`,
    `/cube_fruit/classifications`
  - Output: `/cube_fruit/annotated_image_distance` by default, or
    `/cube_fruit/annotated_image` when launched through `full_robot_stack`.
  - Uses the same homography + residual bbox model and overlays the estimated
    object distance in meters next to the fruit/shape label.

- `bbox_goal_navigator_node`
  - Input: `/object_pose_map` (`geometry_msgs/PoseStamped`),
    `/robot_pose_map` (`geometry_msgs/PoseStamped`)
  - Output: `/bbox_goal_pose` (`geometry_msgs/PoseStamped`),
    `/bbox_goal_navigator/status` (`std_msgs/String` JSON)
  - Optional action output: Nav2 `NavigateToPose` on `navigate_to_pose`.
  - Computes either the bbox-localized object center
    (`bbox_goal_approach_distance_m=0.0`) or a target-facing approach pose,
    clamps it inside the configured arena, and sends a new Nav2 goal only when
    the goal moves enough to matter.
  - Key tuning parameters:
    `bbox_goal_approach_distance_m`, `bbox_goal_min_separation_m`,
    `bbox_goal_max_target_age_sec`, `bbox_goal_margin_m`.

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
