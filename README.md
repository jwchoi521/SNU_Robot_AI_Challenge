# SNU Robot AI Challenge - SLAM 브랜치

이 브랜치는 로봇의 SLAM, 지도 기반 길찾기, 목표 물체 접근을 위한 ROS 2 기본 뼈대입니다.
YOLO 객체 인식 코드는 별도 브랜치에서 진행 중이고, 이 브랜치는 그 인식 결과를 받아
로봇이 어디로 움직일지 결정하는 쪽을 담당합니다.

## 전체 흐름

```text
하드웨어 센서
  ├─ LiDAR /scan
  ├─ 4개 휠 엔코더 /joint_states
  ├─ IMU /imu
  └─ camera + IR distance

        ↓

4륜 odometry
  └─ snu_base_control
      └─ /wheel/odom

        ↓

상태 추정
  └─ robot_localization EKF
      └─ /odometry/filtered, odom -> base_link

        ↓

지도 작성
  └─ slam_toolbox
      └─ /map, map -> odom

        ↓

길찾기와 회피
  └─ Nav2
      ├─ global costmap
      ├─ local costmap
      ├─ semantic obstacles from camera + IR
      ├─ planner
      ├─ controller
      └─ /cmd_vel

        ↓

목표 물체 접근
  └─ YOLO objects + IR distance_m
      ├─ target object -> /target_pose_base
      └─ non-target object -> /semantic_obstacles
```

## 현재 센서 역할

| 센서 / 신호 | ROS 인터페이스 | 역할 |
| --- | --- | --- |
| 2D LiDAR | `/scan` (`sensor_msgs/LaserScan`) | SLAM/localization 보정 |
| 4개 휠 엔코더 | `/joint_states` (`sensor_msgs/JointState`) | 각 바퀴 회전량/속도 |
| 휠 오도메트리 | `/wheel/odom` (`nav_msgs/Odometry`) | 4개 휠 모델로 계산한 이동 추정 |
| IMU | `/imu` (`sensor_msgs/Imu`) | 회전 안정화, yaw-rate 보정 |
| 카메라 객체 인식 | `/perception/objects` (`snu_robot_interfaces/PerceivedObjectArray`) | 모든 object의 종류와 방향 |
| 적외선 거리 센서 | `distance_m` | object까지의 거리 |
| semantic 장애물 | `/semantic_obstacles` (`sensor_msgs/PointCloud2`) | target이 아닌 object를 Nav2 장애물로 전달 |
| 속도 명령 | `/cmd_vel` (`geometry_msgs/Twist`) | 모터 제어 입력 |

이 프로젝트에서는 LiDAR를 object 장애물 감지용으로 보지 않습니다. LiDAR는 위치 추정과
지도 작성 보정에 쓰고, 실제 피해야 하는 object는 카메라와 적외선 거리 센서를 기반으로
좌표를 추정합니다. 필요한 object는 target, 나머지 object는 semantic obstacle로 처리합니다.

## 패키지 구성

```text
ros2_ws/src/
  snu_base_control/        4륜 독립 구동 odometry 계산
  snu_robot_bringup/       SLAM, EKF, Nav2, sensor TF launch와 설정
  snu_robot_interfaces/    perception과 navigation 사이에서 공유하는 메시지
  snu_target_navigation/   object를 target pose와 semantic obstacle로 변환하는 노드
docs/
  SENSOR_CONTRACT.md       필요한 토픽, TF, 메시지 의미
  SLAM_NAV_PLAN.md         매핑, 로컬라이제이션, 길찾기 진행 계획
  FOUR_WHEEL_BASE.md       4륜 독립 구동 odometry와 제어 모델
```

## 빌드

```bash
cd ros2_ws
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
source install/setup.bash
```

필요한 ROS 2 패키지:

- `slam_toolbox`
- `nav2_bringup`
- `robot_localization`
- `tf2_ros`
- `rviz2`

## 실행 순서

### 1. 센서와 TF 확인

로봇에서 먼저 센서 토픽이 살아있는지 확인합니다.

```bash
ros2 topic list -t
ros2 topic hz /scan
ros2 topic hz /joint_states
ros2 topic hz /wheel/odom
ros2 topic hz /imu
ros2 run tf2_tools view_frames
```

기대하는 TF 구조:

```text
map -> odom -> base_link -> laser_frame
                         -> camera_frame
```

처음에는 `map -> odom`이 없어도 괜찮습니다. 이 transform은 SLAM 또는 localization이
실행된 뒤 생성됩니다.

### 2. SLAM + Nav2 실행

지도 작성과 길찾기를 같이 켭니다.

```bash
ros2 launch snu_robot_bringup bringup.launch.py
```

주요 launch argument:

```bash
ros2 launch snu_robot_bringup bringup.launch.py \
  scan_topic:=/scan \
  use_sim_time:=false \
  enable_base_odometry:=true \
  enable_ekf:=true \
  enable_slam:=true \
  enable_nav2:=true
```

### 3. 지도 저장

로봇을 천천히 움직이며 맵을 만든 뒤 저장합니다.

```bash
ros2 run nav2_map_server map_saver_cli -f maps/challenge_map
```

### 4. 저장된 맵으로 길찾기

맵을 저장한 뒤에는 SLAM 대신 localization 모드로 운용합니다.

```bash
ros2 launch snu_robot_bringup localization.launch.py map:=maps/challenge_map.yaml
ros2 launch snu_robot_bringup navigation.launch.py
```

### 5. 목표 물체 접근과 object 장애물 회피

YOLO/IR 쪽에서 `/perception/objects`를 발행하면, target navigation 노드가
object 역할에 따라 출력을 나눕니다.

```bash
ros2 launch snu_target_navigation target_navigation.launch.py
```

출력:

```text
/target_pose_base    geometry_msgs/PoseStamped
/semantic_obstacles  sensor_msgs/PointCloud2
```

`navigation_role=TARGET`인 object는 접근 목표가 되고, `navigation_role=OBSTACLE`인
object는 Nav2 costmap에 들어가는 장애물이 됩니다.

## 현재 브랜치의 목표

지금 단계는 완성된 자율주행 코드가 아니라, 팀이 각 모듈을 붙일 수 있는 기본 골격입니다.

1. 센서 토픽과 TF 이름을 고정합니다.
2. 4개 휠 encoder로 `/wheel/odom`을 만듭니다.
3. EKF로 휠 odom과 IMU를 안정화합니다.
4. LiDAR와 odom으로 SLAM/localization을 수행합니다.
5. Nav2가 `/map`, `/semantic_obstacles`, `/odometry/filtered`를 사용해 이동합니다.
6. YOLO와 IR 결과를 `/perception/objects`로 받아 target과 obstacle로 분리합니다.

하드웨어에서 먼저 튜닝해야 하는 값은 LiDAR/카메라 위치, 로봇 반경, 최대 속도,
오도메트리 토픽 이름, 바퀴 반지름, 좌우 바퀴 간 거리, 앞뒤 바퀴 간 거리입니다.
