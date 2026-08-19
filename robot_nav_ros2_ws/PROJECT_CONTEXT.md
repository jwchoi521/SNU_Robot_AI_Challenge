# Project Context

This workspace is for a ROS2 robot navigation stack.

## Goal

Use a front camera to detect objects, estimate object positions in the lidar
frame, map those objects into the map frame with timestamp-correct transforms,
and navigate a vehicle-like robot to a target-facing approach pose.

## Main Design

```text
lidar scan + odom
-> four_wall_localizer_node ray-casts ranges against the 4 known arena walls
-> robot pose in map frame, with square-symmetry candidates resolved by prior
camera detection bbox + original image timestamp
-> homography + RandomForest residual model
-> object x/y in lidar frame
-> tf2 lookup at image timestamp
-> object x/y in map frame
-> semantic_obstacle_cloud_node publishes PointCloud2
-> Nav2 obstacle_layer marks semantic objects in costmap
-> target-facing approach pose candidates
-> Nav2 Smac Hybrid-A* with REEDS_SHEPP
-> controller cmd_vel
-> wheel speed/PID motor command
```

Semantic object obstacles are modeled as about `8cm` diameter (`0.04m` radius)
and remain in the semantic cloud for `15s` after the last observation.
Repeated observations within `0.12m` are treated as the same obstacle and
merged with a smoothed position update before publishing the PointCloud2 cloud.

Robot geometry currently assumed:

```text
front/rear wheel spacing: 0.235m
left/right wheel spacing: 0.30m
wheel diameter: 0.066m
wheel radius: 0.033m
chassis length: 0.32m
chassis width: 0.33m
Nav2 footprint: x +/-0.16m, y +/-0.165m
```

## Coordinate Convention

- `lidar` frame: x forward, y left.
- `base_link` frame: robot body frame.
- `map` frame: fixed world frame.
- Object estimator output is lidar-frame `x, y`.
- `four_wall_localizer_node` estimates robot `base_link` pose in the `map`
  frame by matching LiDAR ranges to the four known arena walls.
- Final navigation goals are map-frame `x, y, yaw`.

## Square Arena Ambiguity

A perfectly square arena can make wall-only LiDAR matching ambiguous under
mirror and 90-degree rotation symmetries. The 4-wall localizer handles this by
generating the symmetry-equivalent pose candidates first, then choosing the
candidate closest to the initial/previous/odometry-predicted pose. This means
the robot should start with a roughly correct initial pose and keep using
encoder/IMU odometry between LiDAR updates.

## Important Rule

Never fuse a detection with the "current" robot pose just because YOLO finished
now. Use the original camera frame timestamp and lookup the transform at that
timestamp.

## Current Package

ROS2 package path:

```text
src/robot_nav_stack
```

The package is a scaffold intended to be copied into a ROS2/colcon workspace.
It contains node wrappers plus small core utilities. Nav2 still owns the real
global planning, costmaps, behavior tree, and controller in production.
