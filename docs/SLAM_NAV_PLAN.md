# SLAM 및 길찾기 진행 계획

## 1단계: 토픽과 TF 확인

가장 먼저 할 일은 알고리즘을 켜는 것이 아니라 센서 입력이 제대로 들어오는지 확인하는 것입니다.

1. base driver, LiDAR driver, IMU driver, static sensor TF를 실행합니다.
2. `/scan`, `/wheel/odom`, `/imu`, `/cmd_vel`을 확인합니다.
3. TF를 확인합니다.

```bash
ros2 run tf2_tools view_frames
```

최소한 아래 구조가 나와야 합니다.

```text
odom -> base_link -> laser_frame
                  -> camera_frame
```

SLAM을 켜면 여기에 `map -> odom`이 추가됩니다.

## 2단계: 실시간 지도 작성

아래 명령으로 EKF, SLAM Toolbox, Nav2를 함께 실행합니다.

```bash
ros2 launch snu_robot_bringup bringup.launch.py enable_slam:=true enable_nav2:=true
```

지도 작성 중에는 다음을 지키는 것이 좋습니다.

- 로봇을 천천히 움직입니다.
- 교차로나 코너에서는 제자리 회전을 하며 scan matching에 충분한 정보를 줍니다.
- 빠른 회전은 LiDAR scan을 흐리게 만들 수 있으므로 피합니다.
- 이미 지나간 구역을 다시 방문해서 loop closure 기회를 줍니다.

맵 저장:

```bash
ros2 run nav2_map_server map_saver_cli -f maps/challenge_map
```

## 3단계: 저장된 맵으로 localization + navigation

맵을 저장한 뒤에는 매번 새로 SLAM을 할 필요가 없습니다. 저장된 맵을 기준으로
localization을 수행하고 Nav2로 이동합니다.

```bash
ros2 launch snu_robot_bringup localization.launch.py map:=maps/challenge_map.yaml
ros2 launch snu_robot_bringup navigation.launch.py
```

튜닝 순서:

1. LiDAR와 카메라 static TF 위치
2. EKF odometry 안정성
3. SLAM Toolbox scan matching 파라미터
4. Nav2 local costmap의 obstacle range와 inflation radius
5. controller의 속도와 가속도 제한

## 4단계: 목표 물체 접근

YOLO와 적외선 거리 센서가 `/perception/targets`를 발행합니다.

target navigation 노드는 다음 순서로 동작합니다.

1. `pick_allowed=true`인 target만 봅니다.
2. `target_confirmed=true`인 target만 봅니다.
3. `distance_m`이 있는 target만 봅니다.
4. `bearing_deg + distance_m`을 `base_link` 기준 pose로 변환합니다.
5. `/target_pose_base`로 발행합니다.

상위 mission logic은 이 pose를 이용해 다음처럼 확장하면 됩니다.

1. Nav2로 목표 근처까지 이동합니다.
2. 가까워지면 bearing 기반 정렬 제어로 전환합니다.
3. IR 거리가 집기/조작 가능 거리까지 줄어들면 정지합니다.

## 제어 역할 분리

| 거리 상황 | 제어 방식 | 이유 |
| --- | --- | --- |
| 멀리 있거나 지도 기반 이동이 필요할 때 | Nav2 global planner | 장애물과 맵을 고려할 수 있음 |
| 목표 근처 | Nav2 local controller 또는 짧은 visual servoing | 회피와 접근을 함께 처리 |
| 마지막 정렬 | bearing PID + IR stop distance | 목표 물체 기준 정렬이 더 정확함 |

## 현재 코드의 시작점

SLAM/Nav 쪽 시작점:

```bash
ros2 launch snu_robot_bringup bringup.launch.py
```

목표 pose 변환 쪽 시작점:

```bash
ros2 launch snu_target_navigation target_navigation.launch.py
```

아직 이 브랜치에는 실제 하드웨어 driver가 없습니다. 즉 `/scan`, `/wheel/odom`,
`/imu`, `/cmd_vel`은 로봇 base bringup 쪽에서 제공되어야 합니다.
