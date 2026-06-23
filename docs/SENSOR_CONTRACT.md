# 센서 및 하드웨어 인터페이스 계약

이 문서는 하드웨어 bringup, SLAM/Nav2, perception, base control, gripper 사이의 약속을
정리합니다. 각 모듈을 따로 작업하더라도 토픽과 TF 이름이 흔들리지 않도록 하는 것이 목적입니다.

## 필수 토픽

| 토픽 | 타입 | 발행자 | 구독자 | 설명 |
| --- | --- | --- | --- | --- |
| `/scan` | `sensor_msgs/LaserScan` | LiDAR driver | `slam_toolbox` | SLAM/localization 보정에 사용 |
| `/joint_states` | `sensor_msgs/JointState` | 모터/base driver | `snu_base_control` | 4개 휠의 위치/속도 |
| `/wheel/odom` | `nav_msgs/Odometry` | `snu_base_control` 또는 base driver | `robot_localization` | 원본 휠 오도메트리 |
| `/imu` | `sensor_msgs/Imu` | IMU driver | `robot_localization` | 선택이지만 권장 |
| `/odometry/filtered` | `nav_msgs/Odometry` | `robot_localization` | Nav2 | EKF로 보정된 odom |
| `/map` | `nav_msgs/OccupancyGrid` | SLAM 또는 map server | Nav2 global costmap | 전역 지도 |
| `/cmd_vel` | `geometry_msgs/Twist` | Nav2 controller | base driver 또는 `cmd_vel_to_four_wheel` | 로봇 몸체 기준 속도 명령 |
| `/wheel_commands` | `snu_robot_interfaces/FourWheelCommand` | `cmd_vel_to_four_wheel` | 모터/base driver | 4개 바퀴별 속도 또는 normalized power |
| `/perception/objects` | `snu_robot_interfaces/PerceivedObjectArray` | YOLO + IR bridge | target navigation | 모든 object의 역할, 방향, 거리 |
| `/target_pose_base` | `geometry_msgs/PoseStamped` | target navigation | mission logic | `base_link` 기준 목표 위치 |
| `/semantic_obstacles` | `sensor_msgs/PointCloud2` | target navigation | Nav2 costmap | target이 아닌 object 장애물 |
| `/gripper/command` | `snu_robot_interfaces/GripperCommand` | mission logic | gripper driver | 집게 열기/닫기 |
| `/gripper/state` | `snu_robot_interfaces/GripperState` | gripper driver | mission logic | 집게 상태와 물체 수납 여부 |

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

## perception 메시지 의미

`PerceivedObject.bearing_deg`는 현재 YOLO 코드의 기준을 따릅니다.

- `0`은 이미지 중앙입니다.
- 양수는 이미지 오른쪽입니다.

ROS의 `base_link`에서는 보통 y 양수가 왼쪽이므로, `snu_target_navigation`은
`bearing_positive_is_left` 파라미터로 이 부호를 변환합니다. 기본값은 `false`입니다.

`distance_m`은 적외선 센서 또는 별도 target-distance provider에서 들어와야 합니다.
LiDAR는 object 장애물 회피용으로 사용하지 않습니다.

`navigation_role`은 다음 의미입니다.

| 값 | 의미 |
| --- | --- |
| `ROLE_TARGET` | 이번 mission에서 접근해야 하는 object |
| `ROLE_OBSTACLE` | 접근하면 안 되며 회피해야 하는 object |
| `ROLE_IGNORE` | 길찾기에 반영하지 않을 object |
| `ROLE_UNKNOWN` | 아직 분류되지 않은 object |

## 모터 명령 의미

`/cmd_vel`은 로봇 몸체 기준 속도 명령입니다.

```text
linear.x   전후 이동
linear.y   좌우 이동, mecanum일 때만 사용
angular.z  yaw 회전
```

`cmd_vel_to_four_wheel` 노드는 이 값을 `/wheel_commands`로 변환합니다. `command_mode`가
`VELOCITY_RAD_S`이면 각 바퀴 목표 각속도이고, `NORMALIZED_POWER`이면 -1..1 범위의
open-loop 출력입니다.

실제 orientation 변화는 `/wheel_commands` 자체가 아니라 encoder와 IMU로 검증합니다.
즉 “명령한 값”과 “실제로 회전한 값”을 비교해서 `wheel_radius_m`, `track_width_m`,
wheel sign, motor scale을 보정해야 합니다.

## 집게 인터페이스 의미

집게는 로봇 앞쪽의 바스켓형 수납 장치로 가정합니다.

1. target 앞에서 `/gripper/command=OPEN`을 보냅니다.
2. bearing과 IR 거리로 짧게 정렬/전진합니다.
3. target이 집게 안쪽에 들어오면 `/gripper/command=CLOSE`를 보냅니다.
4. `/gripper/state.has_object=true`이면 수거 완료로 봅니다.
5. map 기준 drop pose로 이동한 뒤 다시 `OPEN`합니다.

## 하드웨어에서 실제 측정해야 할 값

| 항목 | 현재 기본값 | 실제 측정 필요 |
| --- | --- | --- |
| `base_link -> laser_frame` | x `0.15`, y `0.0`, z `0.12` | 필요 |
| `base_link -> camera_frame` | x `0.12`, y `0.0`, z `0.18` | 필요 |
| 로봇 반경 | Nav2 params 기준 `0.18` m | 필요 |
| 최대 선속도 | Nav2 params 기준 `0.25` m/s | 필요 |
| 최대 각속도 | Nav2 params 기준 `0.8` rad/s | 필요 |
| 바퀴 반지름 | base control 기준 `0.05` m | 필요 |
| 좌우 바퀴 간 거리 | base control 기준 `0.30` m | 필요 |
| 앞뒤 바퀴 간 거리 | base control 기준 `0.30` m | 필요 |
| 각 모터 출력 scale | 기본값 `1.0` | 필요 |
| 집게 open/close 시간 | 미정 | 필요 |
| drop zone pose | 미정 | 필요 |
