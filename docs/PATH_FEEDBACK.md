# 경로 평가와 피드백

`path_feedback_monitor`는 Nav2가 만든 실제 경로를 계속 평가해서 로봇이 목표에 빠르고 안전하게 도달할 수 있는지 알려주는 노드입니다.

## 입력 토픽

| 토픽 | 타입 | 의미 |
| --- | --- | --- |
| `/plan` | `nav_msgs/Path` | Nav2 planner가 만든 현재 전역 경로 |
| `/semantic_obstacles` | `sensor_msgs/PointCloud2` | 카메라/IR로 인식해 map 좌표에 저장한 장애물 |
| `/mission/nav_goal` | `geometry_msgs/PoseStamped` | mission manager가 보낸 현재 목적지 |

## 출력 토픽

| 토픽 | 타입 | 의미 |
| --- | --- | --- |
| `/navigation/path_feedback` | `std_msgs/String` | 경로 상태, 예상 도착시간, 장애물 여유거리, 우회 정도 |

예시:

```text
status=OK eta=12.84s path_length=2.18m straight=1.92m detour=1.14 rotation=1.35rad min_clearance=0.58m goal_error=0.04m poses=64 obstacles=20
```

## 상태값

| 상태 | 의미 |
| --- | --- |
| `WAITING` | 아직 경로가 없거나 경로 pose가 부족함 |
| `STALE_PATH` | 최근 경로가 오래되어 현재 상황 판단에 쓰기 어려움 |
| `OK` | 장애물 여유거리와 우회 정도가 허용 범위 안에 있음 |
| `SLOW` | 도착은 가능하지만 최단시간 관점에서 우회가 큼 |
| `CAUTION` | 경로가 semantic obstacle에 가까워 감속이 필요함 |
| `GOAL_MISMATCH` | 경로의 끝점이 mission goal과 충분히 맞지 않음 |
| `BLOCKED` | 경로가 semantic obstacle 영역과 너무 가까워 사실상 막힌 경로로 판단 |

## 최단시간 평가 방식

단순 최단거리만 보면 회전이 많거나 장애물에 너무 가까운 경로를 좋은 경로로 착각할 수 있습니다. 그래서 현재 평가는 아래 값을 합쳐 예상 도착시간 `eta`를 계산합니다.

```text
예상시간 = 경로길이 / 기준 선속도
        + 누적 회전량 / 기준 회전속도
        + 장애물 근접 감속 페널티
```

기본값은 현재 Nav2 controller 설정에 맞춰 `desired_linear_speed_mps=0.20`, `max_angular_speed_radps=0.80`입니다. 실제 로봇에서 더 빠르게 달릴 수 있으면 이 값을 올려야 `eta`가 현실에 가까워집니다.

## 튜닝해야 하는 파라미터

`ros2_ws/src/snu_target_navigation/config/target_navigation.yaml`의 `path_feedback_monitor` 항목에서 조정합니다.

| 파라미터 | 기본값 | 의미 |
| --- | --- | --- |
| `blocked_clearance_m` | `0.22` | 이보다 가까우면 `BLOCKED` |
| `caution_clearance_m` | `0.45` | 이보다 가까우면 `CAUTION` 및 감속 페널티 |
| `detour_ratio_warn` | `1.60` | 직선거리 대비 경로가 길면 `SLOW` |
| `goal_tolerance_m` | `0.25` | 경로 끝점과 mission goal 허용 오차 |
| `desired_linear_speed_mps` | `0.20` | 예상 시간 계산용 기준 선속도 |
| `max_angular_speed_radps` | `0.80` | 예상 시간 계산용 기준 회전속도 |
| `obstacle_slowdown_weight` | `0.80` | 장애물 근접 시 예상 시간 페널티 강도 |

## 실험 중 확인 명령

```bash
ros2 topic echo /navigation/path_feedback
ros2 topic echo /plan
ros2 topic echo /semantic_obstacles
ros2 topic echo /mission/nav_goal
```

랜덤 장애물/타겟 실험에서는 `eta`가 작고, `min_clearance`가 충분하며, `detour`가 낮은 경로가 좋은 경로입니다. 목표는 `OK` 상태 중에서 `eta`가 가장 낮은 경로를 선택하도록 planner와 costmap 파라미터를 조정하는 것입니다.
