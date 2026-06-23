# SNU Robot AI Challenge - SLAM Skeleton

This branch contains the first ROS 2 skeleton for mapping, navigation, and
target approach. The object detector lives on the YOLO branch; this branch
defines the SLAM/Nav2 side and the ROS message contract that will connect the
perception output to navigation.

## Current Sensor Assumptions

| Sensor / signal | ROS interface | Purpose |
| --- | --- | --- |
| 2D LiDAR | `/scan` (`sensor_msgs/LaserScan`) | SLAM, local obstacle updates |
| Wheel odometry | `/wheel/odom` (`nav_msgs/Odometry`) | Continuous local motion estimate |
| IMU | `/imu` (`sensor_msgs/Imu`) | Optional yaw-rate/orientation stabilization |
| Camera detector | `/perception/targets` (`snu_robot_interfaces/DetectedTargetArray`) | Object class and bearing |
| Infrared distance | folded into `distance_m` in detected target messages | Target distance, not mapping |
| Velocity command | `/cmd_vel` (`geometry_msgs/Twist`) | Robot control output |

## Packages

```text
ros2_ws/src/
  snu_robot_bringup/       SLAM, EKF, Nav2, sensor TF launch files and params
  snu_robot_interfaces/    Messages shared by perception and navigation
  snu_target_navigation/   Target pose projection and approach planning hooks
docs/
  SENSOR_CONTRACT.md       Required topics, frames, and message semantics
  SLAM_NAV_PLAN.md         Mapping, localization, and target approach plan
```

## Build

```bash
cd ros2_ws
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
source install/setup.bash
```

Required external ROS 2 packages:

- `slam_toolbox`
- `nav2_bringup`
- `robot_localization`
- `tf2_ros`
- `rviz2`

## Bringup

Mapping with live SLAM and Nav2:

```bash
ros2 launch snu_robot_bringup bringup.launch.py
```

Useful launch arguments:

```bash
ros2 launch snu_robot_bringup bringup.launch.py \
  scan_topic:=/scan \
  use_sim_time:=false \
  enable_ekf:=true \
  enable_slam:=true \
  enable_nav2:=true
```

Run only SLAM:

```bash
ros2 launch snu_robot_bringup slam.launch.py
```

Run Nav2 localization on a saved map:

```bash
ros2 launch snu_robot_bringup localization.launch.py map:=/path/to/map.yaml
```

Project camera/IR target detections into a base-frame target pose:

```bash
ros2 launch snu_target_navigation target_navigation.launch.py
```

## First Hardware Checklist

Before tuning SLAM, confirm these on the robot:

```bash
ros2 topic list -t
ros2 topic hz /scan
ros2 topic hz /wheel/odom
ros2 topic hz /imu
ros2 run tf2_tools view_frames
```

The expected TF tree is:

```text
map -> odom -> base_link -> laser_frame
                         -> camera_frame
```

`map -> odom` is produced by SLAM/localization. `odom -> base_link` is produced
by `robot_localization` or the robot base. Sensor transforms are static.
