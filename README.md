# SNU Robot AI Challenge

4m × 4m 아레나에서 자율 주행하는 4륜 로봇의 ROS 2 스택입니다. 카메라로 과일 큐브를 찾아
인식하고, LiDAR로 자기 위치를 추정하고, Nav2로 접근해서 앞쪽 집게에 담은 뒤 지정된 보관
구역에 내려놓습니다.

주 연산 장치는 **Jetson Orin Nano**이고, 모터/엔코더/IMU는 시리얼로 연결된 **ESP32**가
담당합니다.

## 전체 파이프라인

```text
USB 카메라 ──> opencv_camera_node          (C++)
                    │ /camera/image_raw
                    ├──> shape_yolo_node            (TensorRT) ─ /shape_yolo/detections
                    └──> cube_fruit_classifier_node (TensorRT) ─ /cube_fruit/classifications
                                   │
                                   ▼
                         yolo_detection_adapter_node
                                   │ /perception/objects
                                   ▼
RPLIDAR C1 ──┐         object_localizer_node
             │           homography → RandomForest residual 보정
/scan, /odom │           → LiDAR 기준 object x/y
             ▼                     │
    four_wall_localizer_node       │ tf2 lookup (이미지 timestamp 기준)
      4개 벽에 ray-cast            ▼
      → map 기준 robot pose  ─> object x/y (map frame)
                                   │
                    ┌──────────────┴──────────────┐
                    ▼                             ▼
      semantic_obstacle_cloud_node      bbox_goal_navigator_node
        /semantic_obstacles               탐색 → 접근 → 수거 → 보관 미션
        → Nav2 obstacle_layer             (mission brain)
                    │                             │ NavigateToPose
                    └──────────────┬──────────────┘
                                   ▼
                     Nav2 Smac Hybrid-A* (REEDS_SHEPP)
                                   │ /cmd_vel
                                   ▼
                        cmd_vel_to_four_wheel
                                   │ /wheel_commands (FourWheelCommand)
                                   ▼
                          esp32_serial_bridge ──> ESP32 펌웨어 ──> 모터 4개
```

핵심 설계는 사각형 아레나의 벽 4개를 이미 안다고 가정하는 데 있습니다.
`four_wall_localizer_node`가 LiDAR 스캔을 알려진 벽에 ray-cast해서 로봇 pose를 구하고,
정사각형 대칭 때문에 생기는 4개 후보는 직전 카메라 detection과 원본 이미지 timestamp로
해소합니다.

## 저장소 구조

| 경로 | 내용 |
| --- | --- |
| `ros2_ws/` | **현재 사용 중인 colcon 워크스페이스.** ROS 2 패키지 11개 |
| `robot_nav_ros2_ws/` | 초기 스캐폴드 스냅샷. `ros2_ws/`의 부분집합이며 갱신되지 않음 |
| `docs/` | 설계 계약, 브링업 절차, 테스트 체크리스트 16종 |
| `firmware/` | ESP32 Arduino 스케치 2종 (모터/엔코더 브리지, U자형 로봇) |
| `tools/` | bbox↔pose 보정 학습 도구, RViz mock publisher, 순차 주행 테스트 |
| `TODO.md` | 실측이 필요한 하드웨어 파라미터 체크리스트 |

`src/`, `scripts/`, `dataset/`, `models/`, `runs/`는 git이 추적하지 않는 로컬 디렉터리입니다.
YOLO/분류기 **학습** 코드는 이 브랜치가 아니라 `codex/yolo` 브랜치에 있습니다
(자세한 내용은 [브랜치 구성](#브랜치-구성) 참고).

## ROS 2 패키지

| 패키지 | 언어 | 역할 |
| --- | --- | --- |
| `robot_nav_stack` | Python | 위치추정·object localization·미션 주행 노드 14종 |
| `robot_nav_stack_cpp` | C++ | `four_wall_localizer` / `object_localizer`의 고부하 C++ 포팅본 |
| `robot_object_detector_ros` | C++ | TensorRT 카메라·YOLO·과일 분류 노드 |
| `snu_robot_interfaces` | msg | `PerceivedObject`, `FourWheelCommand`, `GripperCommand` 등 공용 인터페이스 |
| `snu_robot_bringup` | launch | 통합 launch, Nav2/EKF/SLAM 설정, 아레나 맵 |
| `snu_base_control` | Python | `cmd_vel` → 4륜 변환, 휠 오도메트리, 시작 시 측면 이탈 |
| `snu_hardware_drivers` | Python | ESP32 시리얼 브리지, Jetson GPIO 드라이버, 휠 조그 테스트 |
| `snu_target_navigation` | Python | semantic object 투영/등록, target pose 투영, 경로 피드백 감시 |
| `snu_mission_manager` | Python | pick & place 미션 상태기계 |
| `snu_yaw_calibration` | Python | yaw 응답 모델 수집·학습·보정 |
| `sllidar_ros2` | C++ | SLAMTEC RPLIDAR 드라이버 (upstream) |

### 주요 노드

`bbox_goal_navigator_node` (2,650줄)가 실질적인 미션 브레인입니다. target 탐색 스핀/순찰,
가까운 target으로의 전환, 수거 확인, 보관 구역 진입 계획(`storage_dropoff.py`), 후진/전진
복귀까지 처리합니다.

로직 중 순수 함수 부분은 노드에서 분리되어 단위 테스트가 붙어 있습니다 —
`target_lock.py`, `track_evidence.py`, `time_alignment.py`, `exact_frame_sync.py`,
`object_role.py`, `semantic_obstacle_state.py`, `storage_dropoff.py`.

## 인식 모델

2단계 구조입니다.

1. **shape detector** — YOLO11n, from scratch 학습. 클래스 4종:
   `cube_any`, `octahedron`, `dodecahedron`, `icosahedron`
2. **fruit classifier** — `class_id == 0`(큐브)인 bbox만 크롭해서 분류:
   `apple`, `orange`, `banana`, `pineapple`, `none`

두 모델 모두 Jetson에서 TensorRT `.engine`으로 변환해 실행합니다. 설정은
`ros2_ws/src/robot_object_detector_ros/config/jetson_shape_fruit.yaml`에 있습니다.

거리는 LiDAR가 아니라 bbox 기반 회귀 모델로 추정합니다
(`models/bbox_pose_anchor033.joblib`, C++용 `.cppbin`). 학습 절차는
[`tools/bbox_pose_mapping/README.md`](tools/bbox_pose_mapping/README.md)에 있습니다.

## 실행

### 빌드

대상 환경은 **ROS 2 Humble / Python 3.10**입니다. `requirements-jetson.txt`의 패키지 핀도
이 조합에 맞춰져 있습니다.

```bash
source /opt/ros/humble/setup.bash
cd ros2_ws
python3 -m pip install -r requirements-jetson.txt
rosdep install --from-paths src -y --ignore-src
colcon build --symlink-install
source install/setup.bash
```

### 전체 스택 기동

```bash
ros2 launch snu_robot_bringup full_robot_stack.launch.py \
  shape_engine:=models/shape_yolo_best_640.engine \
  classifier_engine:=models/classifier_real_sz256_640.engine \
  camera_index:=0 \
  lidar_serial_port:=/dev/ttyUSB0 \
  arena_origin:=center \
  arena_width_m:=4.0 \
  arena_height_m:=4.0
```

`full_robot_stack.launch.py`가 카메라·LiDAR·TF·오도메트리·EKF·SLAM·Nav2·미션 노드를 한 번씩
include합니다. **`jetson_shape_fruit.launch.py`나 `sllidar_c1_launch.py`를 따로 띄우지 마세요.**
카메라/LiDAR 파이프라인이 중복 기동됩니다.

기동 대상은 `enable_*` 인자로 개별 제어합니다 — `enable_camera`, `enable_lidar_driver`,
`enable_slam`, `enable_nav2`, `enable_ekf`, `enable_bbox_goal_navigation`,
`enable_semantic_obstacle_cloud`, `enable_startup_escape` 등.

> `enable_bbox_goal_navigation`은 인식과 위치추정을 검증하는 동안 `false`로 두세요.
> `true`이면 새 `/object_pose_map` target이 들어올 때마다 `NavigateToPose` goal을 보냅니다.
> 안전 브링업 순서는 [`docs/BBOX_GOAL_NAVIGATION_TEST.md`](docs/BBOX_GOAL_NAVIGATION_TEST.md) 참고.

### 테스트

```bash
cd ros2_ws && colcon test --event-handlers console_direct+ && colcon test-result --verbose
```

Windows의 한글 경로에서 WSL `/mnt/c/...`를 그대로 쓰면 `rosidl` 메시지 생성이 깨집니다.
반드시 WSL 내부 ASCII 경로에 복사해서 빌드/테스트하세요. 자세한 절차는
[`docs/BUILD_AND_TEST.md`](docs/BUILD_AND_TEST.md)에 있습니다.

## 하드웨어

| 장치 | 연결 | 비고 |
| --- | --- | --- |
| Jetson Orin Nano | — | JetPack의 CUDA/TensorRT 사용 |
| RPLIDAR C1 | `/dev/ttyUSB0`, 460800 baud | `dialout` 그룹 권한 필요 |
| USB 카메라 | `camera_index:=0` | 1280×720 기본 |
| ESP32 | 시리얼 | 모터 4개 + 엔코더 + IMU + 집게 |

ESP32 시리얼 프로토콜은 `firmware/esp32_motor_bridge/esp32_motor_bridge.ino` 상단 주석에
정의되어 있습니다 (`M` = normalized power, `V` = 엔코더 피드백 속도 제어, `E` = 엔코더 카운트).

아레나 맵은 `snu_robot_bringup/maps/arena_4x4_center.yaml` — 4m × 4m, 해상도 0.01m,
원점 `[-2.01, -2.01, 0]` (중앙 기준).

## 인터페이스 계약

토픽·TF 프레임·메시지 의미는 [`docs/SENSOR_CONTRACT.md`](docs/SENSOR_CONTRACT.md)에
정리되어 있습니다. 모듈을 따로 작업해도 이름이 흔들리지 않게 하는 것이 목적입니다.

주의할 부호 규약 두 가지:

- `bearing_deg`는 YOLO 기준으로 **0이 이미지 중앙, 양수가 이미지 오른쪽**입니다.
  ROS `base_link`는 y 양수가 왼쪽이므로 `snu_target_navigation`이
  `bearing_positive_is_left` 파라미터로 변환합니다 (기본값 `false`).
- `distance_m`은 bbox 모델 또는 별도 distance provider에서 옵니다. **LiDAR는 object 장애물
  회피에 사용하지 않습니다.**

기대 TF 구조:

```text
map -> odom -> base_link -> laser_frame
                         -> camera_frame
```

## 문서

| 문서 | 내용 |
| --- | --- |
| [`SENSOR_CONTRACT.md`](docs/SENSOR_CONTRACT.md) | 토픽/TF/메시지 계약 |
| [`ROBOT_NAV_STACK.md`](docs/ROBOT_NAV_STACK.md) | 워크스페이스 셋업과 launch 사용법 |
| [`SLAM_NAV_PLAN.md`](docs/SLAM_NAV_PLAN.md) | SLAM·Nav2 구성 계획 |
| [`PICK_AND_PLACE_MISSION.md`](docs/PICK_AND_PLACE_MISSION.md) | 수거·배치 미션 상태기계 |
| [`FOUR_WHEEL_BASE.md`](docs/FOUR_WHEEL_BASE.md) | 4륜 기구학과 오도메트리 |
| [`jetson_ros2_tensorrt.md`](docs/jetson_ros2_tensorrt.md) | Jetson TensorRT 노드 빌드/실행 |
| [`shape_fruit_pipeline.md`](docs/shape_fruit_pipeline.md) | 검출기·분류기 학습 파이프라인 |
| [`BUILD_AND_TEST.md`](docs/BUILD_AND_TEST.md) | 빌드/테스트 절차와 한글 경로 이슈 |
| [`BBOX_GOAL_NAVIGATION_TEST.md`](docs/BBOX_GOAL_NAVIGATION_TEST.md) | bbox goal 주행 안전 브링업 |
| [`NAV2_OBJECT_ROUTE_TEST.md`](docs/NAV2_OBJECT_ROUTE_TEST.md) | Nav2 object 경로 테스트 |
| [`NAV_OPTIMIZATION_LOG.md`](docs/NAV_OPTIMIZATION_LOG.md) | 주행 파라미터 튜닝 기록 |
| [`PATH_FEEDBACK.md`](docs/PATH_FEEDBACK.md) | 경로 피드백 모니터 |
| [`CMD_VEL_SPEED_TEST.md`](docs/CMD_VEL_SPEED_TEST.md) | 속도 명령 검증 |
| [`ESP32_SERIAL_TEST.md`](docs/ESP32_SERIAL_TEST.md) · [`ESP32_UPLOAD_TROUBLESHOOTING.md`](docs/ESP32_UPLOAD_TROUBLESHOOTING.md) | ESP32 통신/업로드 |
| [`JETSON_GPIO_TEST.md`](docs/JETSON_GPIO_TEST.md) | Jetson GPIO 검증 |

## 브랜치 구성

이 저장소에는 **공통 조상이 없는 두 개의 히스토리**가 들어 있습니다. 브랜치를 옮길 때
주의하세요.

| 계보 | 브랜치 | 내용 |
| --- | --- | --- |
| ROS 2 스택 | `main`, `codex/jetson-robot-nav-stack`, `slam`, `slam2`, `ESP32_PID`, `motor-test-code` | 이 README가 설명하는 코드 |
| 비전 학습 | `codex/yolo`, `Ros2-TensorRT` | YOLO/분류기 학습 코드 (`src/`, `scripts/`, `tests/`) |

두 계보 사이에는 `git merge`나 `git pull`이 성립하지 않습니다
(`refusing to merge unrelated histories`). 학습 코드가 필요하면 브랜치를 체크아웃해서
쓰세요.

## 현재 상태

동작하는 뼈대이며, 실측 파라미터가 아직 비어 있습니다. `base_link → laser_frame` /
`camera_frame` 외부 파라미터, 휠 joint 이름과 부호, 최대 휠 각속도, 카메라 FOV, IR 유효
거리 등은 실제 로봇에서 측정해 채워야 합니다. 전체 목록은 [`TODO.md`](TODO.md)에 있습니다.
