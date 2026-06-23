# SLAM 및 길찾기 진행 계획

## 1단계: 토픽과 TF 확인

가장 먼저 할 일은 알고리즘을 켜는 것이 아니라 센서 입력이 제대로 들어오는지 확인하는 것입니다.

1. base driver, LiDAR driver, IMU driver, static sensor TF를 실행합니다.
2. `/scan`, `/joint_states`, `/wheel/odom`, `/imu`, `/cmd_vel`을 확인합니다.
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

## 2단계: 모터 명령과 실제 움직임 캘리브레이션

4개 바퀴가 독립 모터이므로 `/cmd_vel`이 실제로 어떤 바퀴 명령이 되고, 그 결과 로봇의
orientation과 위치가 어떻게 바뀌는지 확인해야 합니다.

```text
/cmd_vel
  -> cmd_vel_to_four_wheel
  -> /wheel_commands
  -> motor driver
  -> /joint_states
  -> four_wheel_odometry
  -> /wheel/odom
```

처음에는 아래 순서로 맞춥니다.

1. 낮은 속도로 직진 명령을 주고 실제 이동 거리와 `/wheel/odom` 이동 거리를 비교합니다.
2. 낮은 속도로 제자리 회전 명령을 주고 IMU yaw 변화와 `/wheel/odom` yaw 변화를 비교합니다.
3. 한쪽으로 휘면 좌우 motor scale 또는 wheel sign을 보정합니다.
4. 직진과 회전이 맞은 뒤 EKF에 `/wheel/odom`과 `/imu`를 넣습니다.

## 3단계: 실시간 지도 작성

아래 명령으로 EKF, SLAM Toolbox, Nav2를 함께 실행합니다.

```bash
ros2 launch snu_robot_bringup bringup.launch.py \
  enable_wheel_command_mapper:=true \
  enable_base_odometry:=true \
  enable_slam:=true \
  enable_nav2:=true
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

## 4단계: 저장된 맵으로 localization + navigation

맵을 저장한 뒤에는 매번 새로 SLAM을 할 필요가 없습니다. 저장된 맵을 기준으로
localization을 수행하고 Nav2로 이동합니다.

```bash
ros2 launch snu_robot_bringup localization.launch.py map:=maps/challenge_map.yaml
ros2 launch snu_robot_bringup navigation.launch.py
```

튜닝 순서:

1. LiDAR와 카메라 static TF 위치
2. 휠 명령과 실제 움직임의 scale/sign
3. EKF odometry 안정성
4. SLAM Toolbox scan matching 파라미터
5. Nav2 local costmap의 semantic obstacle 반영
6. controller의 속도와 가속도 제한

## 5단계: 목표 물체 접근과 object 장애물 생성

YOLO와 적외선 거리 센서가 `/perception/objects`를 발행합니다. 여기에는 필요한 object와
필요하지 않은 object가 모두 포함됩니다.

semantic object projector는 다음 순서로 동작합니다.

1. `navigation_role=TARGET`이고 `pick_allowed=true`인 object를 접근 목표 후보로 봅니다.
2. `target_confirmed=true`이고 `distance_m`이 있는 target을 고릅니다.
3. target의 `bearing_deg + distance_m`을 `base_link` 기준 pose로 변환합니다.
4. `/target_pose_base`로 발행합니다.
5. `navigation_role=OBSTACLE`인 object는 `bearing_deg + distance_m`을 point cloud로 변환합니다.
6. `/semantic_obstacles`로 발행해서 Nav2 costmap에 넣습니다.

다음 단계에서는 이 object들을 `map` 좌표로 변환해 semantic object registry에 저장하는 것이 좋습니다.
그렇게 하면 카메라 시야에서 잠깐 사라진 obstacle도 바로 잊지 않고 회피할 수 있습니다.

## 6단계: target 수거

target 근처까지 Nav2로 이동한 뒤에는 짧은 거리 직접 제어로 전환합니다.

1. target bearing을 0도에 가깝게 맞춥니다.
2. 집게를 엽니다.
3. IR distance가 수거 거리까지 줄어들도록 저속 전진합니다.
4. target이 집게 안쪽에 들어왔다고 판단하면 집게를 닫습니다.
5. `/gripper/state.has_object`를 확인합니다.

집게 센서가 아직 없다면, 임시로 카메라에서 target bbox가 집게 안쪽 영역에 들어왔는지로 판단할 수 있습니다.

## 7단계: 고정 drop zone으로 이동 후 배치

target을 수거하면 map 기준 고정 목적지로 이동합니다.

```text
drop_pose:
  frame_id: map
  x: <측정 필요>
  y: <측정 필요>
  yaw: <측정 필요>
```

drop zone에 도착하면:

1. 집게를 엽니다.
2. target을 내려놓습니다.
3. 짧게 후진합니다.
4. semantic object registry에서 해당 target을 삭제합니다.

## 제어 역할 분리

| 상황 | 제어 방식 | 이유 |
| --- | --- | --- |
| 맵 작성 | 저속 수동 또는 보수적 autonomous | SLAM 안정성 확보 |
| 먼 거리 target 접근 | Nav2 global planner | 맵과 semantic obstacle을 고려 |
| target 근처 | bearing + IR 기반 visual servoing | target 기준 정렬이 더 정확함 |
| 집게 수거 | 저속 직접 제어 | 매우 짧은 거리에서 정확도 필요 |
| drop zone 이동 | Nav2 goal | map 기준 고정 목적지 |

## 현재 코드의 시작점

SLAM/Nav 쪽 시작점:

```bash
ros2 launch snu_robot_bringup bringup.launch.py
```

목표 pose와 semantic obstacle 변환:

```bash
ros2 launch snu_target_navigation target_navigation.launch.py
```

4륜 명령 변환과 odometry:

```bash
ros2 launch snu_base_control cmd_vel_to_four_wheel.launch.py
ros2 launch snu_base_control four_wheel_odometry.launch.py
```

아직 이 브랜치에는 실제 하드웨어 driver가 없습니다. 즉 `/scan`, `/joint_states`,
`/imu`, `/cmd_vel`, `/gripper/state`는 로봇 하드웨어 bringup 쪽에서 제공되어야 합니다.
