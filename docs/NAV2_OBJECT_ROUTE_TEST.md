# Nav2 object-to-route Jetson test

This test checks the exact pipeline used by `full_robot_stack.launch.py`:

`/object_pose_map` -> bbox approach goal + semantic obstacle cloud -> Nav2 `/plan`

## Tuned values

- Nav2 XY success tolerance: `0.05 m`
- Nav2 yaw success tolerance: `0.05 rad` (about `2.9 deg`)
- Object approach distance: `0.25 m`
- BBox navigator pre-check tolerance: `0.08 m`
- Object radius: `0.05 m`
- Inflation radius: `0.18 m`
- U-shaped footprint: `0.32 m x 0.33 m`, `0.16 m` opening

The approach goal stops the robot center 25 cm before the object.  Capturing the
object inside the U-shaped opening should be a separate low-speed final alignment
step using the camera or an IR/contact sensor.

## Rebuild on Jetson

```bash
cd ~/SNU_Robot_AI_Challenge/ros2_ws
source /opt/ros/humble/setup.bash
colcon build --symlink-install --packages-select robot_nav_stack snu_robot_bringup
source install/setup.bash
```

## Real-camera run

Use the normal full-stack command.  The important navigation arguments are:

```bash
ros2 launch snu_robot_bringup full_robot_stack.launch.py \
  enable_known_map_server:=true enable_slam:=false enable_nav2:=true \
  enable_bbox_goal_navigation:=true bbox_goal_send_nav2_goal:=true \
  bbox_goal_target_selection_mode:=nearest \
  bbox_goal_approach_distance_m:=0.25 \
  bbox_goal_reached_tolerance_m:=0.08 \
  enable_semantic_obstacle_cloud:=true \
  semantic_obstacle_topic:=/semantic_obstacle_cloud \
  semantic_obstacle_radius_m:=0.05
```

Do not repeat the same launch argument twice; the last value silently wins.

## RViz clicked-object test

Start the stack with the camera disabled, while keeping localization and Nav2
enabled:

```bash
ros2 launch snu_robot_bringup full_robot_stack.launch.py \
  enable_camera:=false enable_lidar_driver:=true \
  enable_sensor_tf:=true enable_known_map_server:=true enable_slam:=false \
  enable_nav2:=true enable_base_odometry:=true enable_ekf:=true \
  enable_bbox_goal_navigation:=true bbox_goal_send_nav2_goal:=true \
  bbox_goal_approach_distance_m:=0.25 bbox_goal_reached_tolerance_m:=0.08 \
  enable_semantic_obstacle_cloud:=true
```

In two more terminals:

```bash
cd ~/SNU_Robot_AI_Challenge
source ros2_ws/install/setup.bash
python3 tools/rviz_mock_object_publisher.py
```

```bash
source ~/SNU_Robot_AI_Challenge/ros2_ws/install/setup.bash
ros2 launch snu_robot_bringup rviz.launch.py
```

Select **Publish Point** in RViz and click inside the arena.  The yellow object
pose, green bbox approach goal, red semantic obstacle disk, and green global path
should all appear.

## Required checks

```bash
ros2 topic hz /object_pose_map
ros2 topic hz /semantic_obstacle_cloud
ros2 topic echo /bbox_goal_pose --once
ros2 topic echo /plan --once
ros2 topic echo /bbox_goal_navigator/status
ros2 topic info /semantic_obstacle_cloud -v
```

Expected `/semantic_obstacle_cloud` subscribers are both local and global
costmaps.  If no `/plan` is produced, first check TF (`map -> odom -> base_link`),
then check whether the approach goal lies inside an inflated obstacle.

After stopping the mock publisher, the object expires after 15 seconds.  The
semantic node requests both Nav2 clear-costmap services, and the current remaining
objects are marked again on the next cloud update.
