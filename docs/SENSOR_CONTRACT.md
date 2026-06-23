# 센서 인터페이스 계약

이 문서는 하드웨어 bringup, SLAM/Nav2, perception 사이의 약속을 정리합니다.
각 팀원이 다른 모듈을 작업하더라도 토픽과 TF 이름이 흔들리지 않도록 하는 것이 목적입니다.

## 필수 토픽

| 토픽 | 타입 | 발행자 | 구독자 | 설명 |
| --- | --- | --- | --- | --- |
| `/scan` | `sensor_msgs/LaserScan` | LiDAR driver | `slam_toolbox`, Nav2 costmap | 지도 작성과 장애물 회피에 사용 |
| `/wheel/odom` | `nav_msgs/Odometry` | 모터/base driver | `robot_localization` | 원본 휠 오도메트리 |
| `/imu` | `sensor_msgs/Imu` | IMU driver | `robot_localization` | 선택이지만 권장 |
| `/odometry/filtered` | `nav_msgs/Odometry` | `robot_localization` | Nav2 | EKF로 보정된 odom |
| `/map` | `nav_msgs/OccupancyGrid` | SLAM 또는 map server | Nav2 global costmap | 전역 지도 |
| `/cmd_vel` | `geometry_msgs/Twist` | Nav2 controller | 모터/base driver | 로봇 속도 명령 |
| `/perception/targets` | `snu_robot_interfaces/DetectedTargetArray` | YOLO + IR bridge | target navigation | 물체 방향과 거리 |
| `/target_pose_base` | `geometry_msgs/PoseStamped` | target navigation | mission logic | `base_link` 기준 목표 위치 |

## 필수 TF 프레임

| 프레임 | 담당 | 의미 |
| --- | --- | --- |
| `map` | SLAM/localization | 전역 지도 좌표계 |
| `odom` | odometry/EKF | 부드럽게 이어지는 지역 좌표계 |
| `base_link` | robot base | 로봇 중심 좌표계. x는 전방, y는 좌측 |
| `laser_frame` | static TF | LiDAR 좌표계 |
| `camera_frame` | static TF | 카메라 좌표계 |

기대하는 TF 구조:

```text
map -> odom -> base_link -> laser_frame
                         -> camera_frame
```

`map -> odom`은 SLAM 또는 localization이 만듭니다. `odom -> base_link`는
`robot_localization` 또는 base driver가 만듭니다. 센서 위치는 static TF로 둡니다.

## perception 메시지 의미

`DetectedTarget.bearing_deg`는 현재 YOLO 코드의 기준을 따릅니다.

- `0`은 이미지 중앙입니다.
- 양수는 이미지 오른쪽입니다.

ROS의 `base_link`에서는 보통 y 양수가 왼쪽이므로, `snu_target_navigation`은
`bearing_positive_is_left` 파라미터로 이 부호를 변환합니다. 기본값은 `false`입니다.

`distance_m`은 적외선 센서 또는 별도 target-distance provider에서 들어와야 합니다.
LiDAR는 SLAM과 장애물 회피용으로만 사용합니다.

## 하드웨어에서 실제 측정해야 할 값

| 항목 | 현재 기본값 | 실제 측정 필요 |
| --- | --- | --- |
| `base_link -> laser_frame` | x `0.15`, y `0.0`, z `0.12` | 필요 |
| `base_link -> camera_frame` | x `0.12`, y `0.0`, z `0.18` | 필요 |
| 로봇 반경 | Nav2 params 기준 `0.18` m | 필요 |
| 최대 선속도 | Nav2 params 기준 `0.25` m/s | 필요 |
| 최대 각속도 | Nav2 params 기준 `0.8` rad/s | 필요 |
