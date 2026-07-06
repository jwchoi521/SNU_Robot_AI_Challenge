# TODO

이 문서는 `slam` 브랜치의 남은 작업을 한곳에 모은 체크리스트입니다. 현재 코드는 SLAM,
semantic object navigation, 4륜 base control, pick-and-place mission의 뼈대입니다.
아래 항목을 실제 로봇에서 측정하고 채우면서 완성해야 합니다.

## 1. 하드웨어 파라미터 입력

### 로봇 좌표계 / TF

- [ ] `base_link -> laser_frame` 실제 위치 측정
  - [ ] `laser_x`
  - [ ] `laser_y`
  - [ ] `laser_z`
  - [ ] `laser_roll`
  - [ ] `laser_pitch`
  - [ ] `laser_yaw`
- [ ] `base_link -> camera_frame` 실제 위치 측정
  - [ ] `camera_x`
  - [ ] `camera_y`
  - [ ] `camera_z`
  - [ ] `camera_roll`
  - [ ] `camera_pitch`
  - [ ] `camera_yaw`
- [ ] 로봇 footprint 또는 `robot_radius` 측정
- [ ] 집게가 닫힌 상태와 열린 상태에서 footprint가 달라지는지 확인

### 4륜 구동

- [x] 바퀴 반지름 `wheel_radius_m` 입력: `0.035` m
- [x] 좌우 바퀴 중심 간 거리 `track_width_m` 입력: `0.112` m
- [x] 앞뒤 바퀴 중심 간 거리 `wheelbase_m` 입력: `0.0986` m
- [ ] 각 바퀴 joint 이름 확정
  - [ ] `front_left_wheel_joint`
  - [ ] `front_right_wheel_joint`
  - [ ] `rear_left_wheel_joint`
  - [ ] `rear_right_wheel_joint`
- [ ] 각 바퀴 회전 방향 sign 확인
  - [ ] `front_left_sign`
  - [ ] `front_right_sign`
  - [ ] `rear_left_sign`
  - [ ] `rear_right_sign`
- [ ] 모터 드라이버 입력 방식 확정
  - [ ] velocity rad/s 제어
  - [ ] normalized power / PWM 제어
- [ ] 최대 바퀴 각속도 `max_wheel_velocity_rad_s` 측정
- [ ] skid-steer인지 mecanum인지 최종 확정

### 카메라 / IR

- [ ] 카메라 horizontal FOV 실제값 확인
- [ ] `bearing_deg` 부호 확인
  - 현재 가정: YOLO 양수는 이미지 오른쪽
  - ROS `base_link`는 y 양수가 왼쪽
- [ ] IR distance와 카메라 bearing이 같은 object를 보고 있는지 확인
- [ ] IR 유효 거리 범위 측정
  - [ ] `min_distance_m`
  - [ ] `max_distance_m`
- [ ] object별 obstacle radius 기본값 측정
- [ ] YOLO class 중 mission target과 obstacle 분류 규칙 확정

### 집게 / 바스켓

- [ ] `/gripper/command` 실제 driver 구현
- [ ] `/gripper/state` 실제 feedback 구현
- [ ] 집게 open 완료 시간 측정
- [ ] 집게 close 완료 시간 측정
- [ ] target이 들어왔는지 확인할 센서 유무 확정
  - [ ] gripper sensor
  - [ ] camera bbox 위치 기반 임시 판정
  - [ ] IR distance 변화 기반 임시 판정
- [ ] target을 담기 위한 최종 접근 거리 측정
- [ ] 집게가 target을 밀어내지 않는 접근 속도 측정

### Drop Zone

- [ ] 저장된 LiDAR map에서 drop zone 위치 측정
  - [ ] `drop_x`
  - [ ] `drop_y`
  - [ ] `drop_yaw`
- [ ] drop zone 접근 방향 확정
- [ ] target 내려놓은 뒤 후진 거리 확정

## 2. 캘리브레이션 절차

### 모터 출력과 orientation 매칭

- [ ] `/cmd_vel` 직진 명령 테스트
  - [ ] 실제 이동 거리 측정
  - [ ] `/wheel/odom` 이동 거리와 비교
  - [ ] `wheel_radius_m` 보정
- [ ] `/cmd_vel` 제자리 회전 명령 테스트
  - [ ] IMU yaw 변화 측정
  - [ ] `/wheel/odom` yaw 변화와 비교
  - [ ] `track_width_m` 보정
- [ ] 좌우 motor scale 보정
  - [ ] 직진 시 한쪽으로 휘는지 확인
  - [ ] 각 바퀴 sign과 scale 보정
- [ ] 사각형 주행 테스트
  - [ ] 시작점으로 돌아오는지 확인
  - [ ] odom drift 기록

### EKF / Localization

- [ ] `/wheel/odom` 단독 품질 확인
- [ ] `/imu` yaw-rate 노이즈 확인
- [ ] `robot_localization` covariance 튜닝
- [ ] `/odometry/filtered`가 끊기지 않는지 확인
- [ ] `odom -> base_link` TF 주기 확인

### LiDAR SLAM

- [ ] `/scan` frame이 `laser_frame`과 일치하는지 확인
- [ ] `slam_toolbox`로 저속 mapping 테스트
- [ ] loop closure가 되는지 확인
- [ ] map 저장 후 localization 모드 테스트
- [ ] map 위에서 로봇 pose가 실제 위치와 맞는지 확인

### Semantic Object 위치

- [ ] `/perception/objects` 발행 확인
- [ ] `/target_pose_base`가 로봇 기준으로 맞는지 RViz에서 확인
- [ ] `/target_pose_map`이 map 기준으로 맞는지 확인
- [ ] `/semantic_obstacles_live`와 `/semantic_obstacles` 비교
- [ ] object가 시야에서 사라진 뒤 TTL 동안 유지되는지 확인
- [ ] 실제로 없는 object가 오래 남지 않도록 TTL 조정

### 집기 / 배치

- [ ] target 앞 final alignment 테스트
- [ ] gripper open/close command 테스트
- [ ] target capture 성공률 기록
- [ ] drop zone 이동 테스트
- [ ] target release 후 registry 삭제 정책 구현 및 확인

## 3. 소프트웨어 구현 TODO

### Perception Bridge

- [ ] YOLO 브랜치의 추론 결과를 ROS 2 `/perception/objects`로 발행하는 bridge 작성
- [ ] IR distance provider를 실제 하드웨어와 연결
- [ ] 현재 mission target class를 받아 `ROLE_TARGET` / `ROLE_OBSTACLE` 분류
- [ ] 같은 object에 대한 YOLO bbox와 IR distance matching 개선

### Semantic Object Registry

- [x] base 관측을 map 좌표로 저장하는 `semantic_object_registry` 골격 추가
- [ ] registry entry 삭제 service 추가
  - target을 집은 뒤 registry에서 삭제 필요
- [ ] object별 radius 설정
- [ ] object confidence decay 개선
- [ ] 같은 object 중복 등록 방지 강화
- [ ] RViz marker 발행 추가
- [ ] registry 내용을 debug topic 또는 JSON log로 출력

### Nav2 연동

- [ ] `/mission/nav_goal`을 Nav2 NavigateToPose action으로 보내는 bridge 작성
- [ ] `target_pose_map` 기준 approach pose 생성
  - target 바로 위가 아니라 target 앞쪽 정렬 pose로 이동해야 함
- [ ] target 근처 final alignment controller 작성
- [ ] `/semantic_obstacles`가 global/local costmap에 제대로 들어가는지 검증
- [ ] recovery behavior 설정

### Base Control

- [x] `/cmd_vel -> /wheel_commands` 변환 노드 추가
- [x] `/joint_states -> /wheel/odom` 변환 노드 추가
- [ ] 실제 motor driver 작성 또는 기존 driver와 topic 연결
- [ ] normalized power 모드에서 deadband 보정
- [ ] 각 바퀴별 scale parameter 추가
- [ ] motor saturation과 acceleration limit 추가

### Gripper

- [x] `GripperCommand`, `GripperState` 메시지 추가
- [ ] 실제 gripper driver 작성
- [ ] open/close 완료 판정
- [ ] `has_object` 판정 센서 연결
- [ ] 집게 상태에 따라 로봇 footprint 또는 안전 거리 조정

### Mission Manager

- [x] pick-and-place 상태기계 골격 추가
- [ ] Nav2 action client 직접 연동
- [ ] final alignment 상태 구현
- [ ] capture 실패 시 재시도 로직
- [ ] drop 실패 시 재시도 로직
- [ ] target 수거 후 semantic registry 삭제 연동
- [ ] 여러 target 순서 결정 로직

## 4. 테스트 / 검증 TODO

- [ ] Jetson 또는 ROS 2 환경에서 `colcon build --symlink-install`
- [ ] `ros2 launch snu_robot_bringup bringup.launch.py` 실행 확인
- [ ] `ros2 launch snu_target_navigation target_navigation.launch.py` 실행 확인
- [ ] `ros2 launch snu_base_control cmd_vel_to_four_wheel.launch.py` 실행 확인
- [ ] `ros2 launch snu_base_control four_wheel_odometry.launch.py` 실행 확인
- [ ] `ros2 launch snu_mission_manager pick_place_mission.launch.py` 실행 확인
- [ ] rosbag 기록
  - [ ] `/cmd_vel`
  - [ ] `/wheel_commands`
  - [ ] `/joint_states`
  - [ ] `/wheel/odom`
  - [ ] `/imu`
  - [ ] `/odometry/filtered`
  - [ ] `/scan`
  - [ ] `/perception/objects`
  - [ ] `/semantic_obstacles`
  - [ ] `/target_pose_map`
  - [ ] `/gripper/state`
- [ ] RViz에서 map, TF, scan, semantic obstacles, target pose 확인
- [ ] 장애물 회피 시나리오 테스트
- [ ] target 수거 후 drop zone 배치 end-to-end 테스트

## 5. 현재 미정인 값

아래 값들은 코드에 기본값이 들어 있지만 실제 로봇에서는 반드시 수정해야 합니다.

| 항목 | 현재 기본값 | 위치 |
| --- | --- | --- |
| LiDAR 위치 | x `0.15`, z `0.12` | `sensor_tf.launch.py` |
| 카메라 위치 | x `0.12`, z `0.18` | `sensor_tf.launch.py` |
| 바퀴 반지름 | `0.035` m | `four_wheel_odometry.yaml`, `cmd_vel_to_four_wheel.yaml` |
| 좌우 바퀴 거리 | `0.112` m | base control configs |
| 앞뒤 바퀴 거리 | `0.0986` m | base control configs |
| 로봇 반경 | `0.18` m | `nav2_params.yaml` |
| obstacle TTL | `30.0` sec | `target_navigation.yaml` |
| target TTL | `60.0` sec | `target_navigation.yaml` |
| drop pose | `0, 0, 0`, disabled | `pick_place_mission.yaml` |
| 집게 effort | `0.5` | `pick_place_mission_manager.py` |

## 6. 권장 다음 작업 순서

1. ROS 2 환경에서 빌드 오류를 먼저 잡습니다.
2. 4개 휠 encoder와 motor driver topic을 확정합니다.
3. `/cmd_vel -> /wheel_commands -> /joint_states -> /wheel/odom` 루프를 실제 로봇에서 맞춥니다.
4. IMU와 EKF를 붙여 `/odometry/filtered`를 안정화합니다.
5. LiDAR SLAM으로 map을 만들고 drop zone pose를 찍습니다.
6. YOLO/IR bridge로 `/perception/objects`를 발행합니다.
7. semantic registry가 map 좌표에 object를 잘 저장하는지 RViz에서 확인합니다.
8. Nav2 action bridge와 final alignment controller를 구현합니다.
9. gripper driver를 붙이고 pick-and-place를 end-to-end로 테스트합니다.
