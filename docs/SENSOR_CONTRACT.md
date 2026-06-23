# Sensor Contract

This document is the interface contract between hardware bringup, SLAM/Nav2,
and perception.

## Required Topics

| Topic | Type | Producer | Consumer | Notes |
| --- | --- | --- | --- | --- |
| `/scan` | `sensor_msgs/LaserScan` | LiDAR driver | `slam_toolbox`, Nav2 costmaps | Used for mapping and obstacle updates only |
| `/wheel/odom` | `nav_msgs/Odometry` | Motor/base driver | `robot_localization` | Raw wheel odometry |
| `/imu` | `sensor_msgs/Imu` | IMU driver | `robot_localization` | Optional but recommended |
| `/odometry/filtered` | `nav_msgs/Odometry` | `robot_localization` | Nav2 | Smoothed local odometry |
| `/map` | `nav_msgs/OccupancyGrid` | SLAM or map server | Nav2 global costmap | Static/global environment |
| `/cmd_vel` | `geometry_msgs/Twist` | Nav2 controller | Motor/base driver | Velocity command |
| `/perception/targets` | `snu_robot_interfaces/DetectedTargetArray` | YOLO + IR bridge | target navigation | Camera bearing plus IR distance |
| `/target_pose_base` | `geometry_msgs/PoseStamped` | target navigation | higher-level mission logic | Target point in `base_link` frame |

## Required Frames

| Frame | Owner | Meaning |
| --- | --- | --- |
| `map` | SLAM/localization | Global map frame |
| `odom` | odometry/EKF | Smooth local frame |
| `base_link` | robot base | Robot body frame, x forward, y left |
| `laser_frame` | static TF | LiDAR optical/mechanical frame |
| `camera_frame` | static TF | Camera-aligned frame used by target projection |

Expected TF chain:

```text
map -> odom -> base_link -> laser_frame
                         -> camera_frame
```

## Perception Message Semantics

`DetectedTarget.bearing_deg` follows the current YOLO code convention:

- `0` means image center.
- Positive values mean the target is to the right side of the image.

`snu_target_navigation` converts that to ROS base-frame y using the
`bearing_positive_is_left` parameter, which defaults to `false`.

`distance_m` must come from the infrared sensor or another target-distance
provider. LiDAR is reserved for SLAM and obstacle avoidance.

## Hardware Values To Measure

Before field tuning, measure and update launch arguments or URDF/static TF:

| Transform | Default placeholder | Needs measurement |
| --- | --- | --- |
| `base_link -> laser_frame` | x `0.15`, y `0.0`, z `0.12` | yes |
| `base_link -> camera_frame` | x `0.12`, y `0.0`, z `0.18` | yes |
| Robot footprint | radius `0.18` m in Nav2 params | yes |
| Max linear speed | `0.25` m/s in Nav2 params | yes |
| Max angular speed | `0.8` rad/s in Nav2 params | yes |
