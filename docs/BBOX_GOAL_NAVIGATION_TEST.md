# BBox Goal Navigation Test Notes

This note covers the final bridge from bbox-localized object poses to robot
motion.

## What Was Added

`bbox_goal_navigator_node` subscribes to:

```text
/object_pose_map
/robot_pose_map
```

It publishes:

```text
/bbox_goal_pose
/bbox_goal_navigator/status
```

When enabled, it also sends Nav2 `NavigateToPose` goals to:

```text
navigate_to_pose
```

The goal is the object center by default because
`bbox_goal_approach_distance_m` defaults to `0.0`. Set it to a positive value
when you want the robot to stop in front of the object instead of driving into
the target point.

## Safe Bring-Up Order

1. Build and source the workspace.

```bash
cd ~/ros2_ws
colcon build --symlink-install
source install/setup.bash
```

2. Use the known 4 m x 4 m arena map before any object-chasing test.

The default 4x4 setup uses the center of the arena as the map origin:

```text
center of arena: x=0.0, y=0.0
left/right walls: x=-2.0, x=+2.0
bottom/top walls: y=-2.0, y=+2.0
```

Keep goal navigation disabled first and confirm robot/object coordinates:

```bash
ros2 launch snu_robot_bringup full_robot_stack.launch.py \
  enable_lidar_driver:=true \
  enable_known_map_server:=true \
  enable_slam:=false \
  enable_nav2:=false \
  enable_bbox_goal_navigation:=false \
  enable_sensor_tf:=false \
  publish_tf:=true \
  publish_lidar_tf:=true \
  arena_origin:=center \
  arena_width_m:=4.0 \
  arena_height_m:=4.0 \
  initial_x_m:=0.0 \
  initial_y_m:=0.0 \
  lidar_serial_port:=/dev/ttyUSB0 \
  shape_engine:=/home/jetson/models/shape_yolo_best_640.engine \
  classifier_engine:=/home/jetson/models/classifier_real_sz256_640.engine
```

In another terminal:

```bash
ros2 launch snu_robot_bringup rviz.launch.py
```

Confirm RViz shows the fixed `/map`, `/scan`, `/robot_pose_map`, and
`/object_pose_map`. In this mode the map is not built by SLAM; it is the known
4x4 field map from `snu_robot_bringup/maps/arena_4x4_center.yaml`.

Check the topics directly:

```bash
ros2 topic echo /robot_pose_map
ros2 topic echo /object_pose_map
ros2 topic echo /four_wall_localizer/status
```

3. Confirm bbox object poses land correctly on that map.

```bash
ros2 launch snu_robot_bringup full_robot_stack.launch.py \
  enable_lidar_driver:=true \
  enable_known_map_server:=true \
  enable_slam:=false \
  enable_nav2:=false \
  enable_bbox_goal_navigation:=false \
  arena_origin:=center \
  shape_engine:=/home/jetson/models/shape_yolo_best_640.engine \
  classifier_engine:=/home/jetson/models/classifier_real_sz256_640.engine
```

Keep one object visible and check these topics:

```bash
ros2 topic echo /shape_yolo/detections
ros2 topic echo /object_pose_map
ros2 topic echo /robot_pose_map
```

In RViz, add `/object_pose_map` as a Pose display. The pose should appear at
the real object location on the map. Fix localization/calibration before moving
on if this is wrong.

4. Enable goal computation without sending Nav2 action goals.

```bash
ros2 launch snu_robot_bringup full_robot_stack.launch.py \
  enable_bbox_goal_navigation:=true \
  bbox_goal_send_nav2_goal:=false \
  enable_known_map_server:=true \
  enable_slam:=false \
  enable_nav2:=false \
  enable_semantic_obstacle_cloud:=false \
  arena_origin:=center
```

Check `/bbox_goal_pose` in RViz. With the default center mode, the pose should
land on the object position. If `bbox_goal_approach_distance_m` is positive, it
should sit between the robot and the object.

5. Enable actual Nav2 goals only after the computed goal looks right.

This step needs a valid `map -> odom -> base_link` TF tree. Use
`wall_tf_mode:=map_to_odom`, enable EKF/base odometry, and use the static
`base_link -> lidar` transform from `sensor_tf.launch.py`.

```bash
ros2 launch snu_robot_bringup full_robot_stack.launch.py \
  enable_bbox_goal_navigation:=true \
  bbox_goal_send_nav2_goal:=true \
  enable_known_map_server:=true \
  enable_slam:=false \
  enable_semantic_obstacle_cloud:=false \
  enable_nav2:=true \
  enable_base_odometry:=true \
  enable_ekf:=true \
  enable_sensor_tf:=true \
  publish_tf:=true \
  wall_tf_mode:=map_to_odom \
  publish_lidar_tf:=false \
  odom_topic:=/odometry/filtered \
  arena_origin:=center
```

6. For real wheel motion through the U-shape ESP32 firmware, also enable the
command mapper and serial bridge. Use the ESP32 port that is not occupied by
the LiDAR.

```bash
ros2 launch snu_robot_bringup full_robot_stack.launch.py \
  enable_bbox_goal_navigation:=true \
  bbox_goal_send_nav2_goal:=true \
  bbox_goal_approach_distance_m:=0.0 \
  enable_known_map_server:=true \
  enable_slam:=false \
  enable_semantic_obstacle_cloud:=false \
  enable_nav2:=true \
  enable_base_odometry:=true \
  enable_ekf:=true \
  enable_sensor_tf:=true \
  publish_tf:=true \
  wall_tf_mode:=map_to_odom \
  publish_lidar_tf:=false \
  odom_topic:=/odometry/filtered \
  enable_wheel_command_mapper:=true \
  enable_esp32_serial_bridge:=true \
  esp32_dry_run:=false \
  esp32_protocol:=u_shape \
  esp32_serial_port:=/dev/ttyUSB1 \
  esp32_u_shape_pwm_max:=80 \
  esp32_max_power:=0.30 \
  arena_origin:=center \
  shape_engine:=/home/jetson/models/shape_yolo_best_640.engine \
  classifier_engine:=/home/jetson/models/classifier_real_sz256_640.engine
```

Upload this ESP32 firmware before running the real-motion test:

```text
firmware/esp32_u_shape_robot/esp32_u_shape_robot.ino
```

The ROS serial bridge talks to that firmware using:

```text
SET <front_left_pwm> <front_right_pwm> <back_left_pwm> <back_right_pwm>
ENC ON
```

## Parameters To Tune On The Robot

- `bbox_goal_approach_distance_m`: `0.0` means drive to the object center.
  Increase it if the robot should stop in front of the object.
- `bbox_goal_reached_tolerance_m`: Deadband around the approach distance.
  Increase it if goals keep firing when the target is already close.
- `bbox_goal_min_separation_m`: Minimum movement before sending a replacement
  Nav2 goal. Increase it if bbox jitter causes frequent replans.
- `bbox_goal_max_target_age_sec`: Maximum age for a target pose. Increase it if
  perception runs slowly, decrease it if stale goals are risky.
- `bbox_goal_target_lock_distance_m`: Once the selected target is within this
  distance, keep that target pose and ignore closer replacement targets or a
  target-to-obstacle reclassification until capture completes. The default is
  `0.30` m; set it to `0.0` to disable new target locking.
- `bbox_goal_margin_m`: Minimum distance from arena walls for the computed
  approach goal.
- `arena_width_m`, `arena_height_m`: Must match the real field, because goal
  clamping uses these values.
- `enable_semantic_obstacle_cloud`: Set this to `false` while driving to the
  exact object center, otherwise Nav2 may treat the object center as an
  obstacle.
- `esp32_u_shape_pwm_max`: Maximum absolute PWM sent to the U-shape Arduino
  firmware through `SET <fl> <fr> <bl> <br>`.
- `esp32_max_power`: Upstream normalized command level that maps to
  `esp32_u_shape_pwm_max`. Increase carefully if the robot does not move.

## Things To Verify

- `/object_pose_map` lands at the real object location in the map.
- `/robot_pose_map` matches the real robot position and heading.
- `/bbox_goal_pose` does not jump between multiple objects. For first tests,
  keep only one visible target. A later target selector should filter by fruit
  class before feeding this node.
- Nav2 accepts the goal and produces a path that does not cross arena walls or
  semantic obstacles.
- The robot reaches the intended target point. For a U-shaped intake, the best
  goal may be slightly past the object center after real driving tests.
