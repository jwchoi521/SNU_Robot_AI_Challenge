# SLAM and Navigation Plan

## Phase 1 - Topic and TF Verification

1. Start the base driver, LiDAR driver, IMU driver, and static sensor TF.
2. Verify `/scan`, `/wheel/odom`, `/imu`, and `/cmd_vel`.
3. Verify TF:

```bash
ros2 run tf2_tools view_frames
```

The minimum valid tree is:

```text
odom -> base_link -> laser_frame
                  -> camera_frame
```

## Phase 2 - Live Mapping

Run:

```bash
ros2 launch snu_robot_bringup bringup.launch.py enable_slam:=true enable_nav2:=true
```

During mapping:

- Drive slowly.
- Rotate in place at corridor junctions.
- Avoid fast turns that smear LiDAR scans.
- Revisit known areas to give SLAM loop-closure opportunities.

Save a map:

```bash
ros2 run nav2_map_server map_saver_cli -f maps/challenge_map
```

## Phase 3 - Localization and Navigation

After saving a map, run localization mode:

```bash
ros2 launch snu_robot_bringup localization.launch.py map:=maps/challenge_map.yaml
ros2 launch snu_robot_bringup navigation.launch.py
```

Tune in this order:

1. Static TF offsets.
2. EKF odometry stability.
3. SLAM Toolbox scan matching parameters.
4. Nav2 local costmap obstacle range and inflation radius.
5. Controller speed and acceleration limits.

## Phase 4 - Target Approach

The detector publishes `/perception/targets`.

The target navigation node:

1. Selects confirmed, pickable targets with a valid infrared distance.
2. Converts `bearing_deg + distance_m` into a `base_link` pose.
3. Publishes `/target_pose_base`.

Higher-level mission logic should:

1. Use Nav2 to approach a waypoint near the target.
2. Switch to short-range visual servoing for final alignment.
3. Stop when IR distance reaches the manipulation/grasp threshold.

## Recommended Control Split

| Range | Control method | Reason |
| --- | --- | --- |
| Far / unknown map | Nav2 global planner | Avoids known obstacles |
| Near target | Nav2 local controller or short visual servo | Keeps obstacle avoidance active |
| Final alignment | Bearing PID + IR stop distance | More accurate than map-based pose |
