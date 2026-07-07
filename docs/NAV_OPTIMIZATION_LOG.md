# 경로 알고리즘 최적화 로그

이 문서는 SLAM/Nav2/semantic obstacle 기반 주행 알고리즘을 수정할 때마다 변경 이유와 평가 기준을 남기기 위한 기록입니다. 목표는 단순 최단거리가 아니라 `최단시간으로 안전하게 도착`하는 것입니다.

## 공통 평가 기준

좋은 변경은 아래 조건을 동시에 만족해야 합니다.

| 지표 | 목표 |
| --- | --- |
| `status` | `OK` 유지. 좁은 환경에서는 `SLOW`까지 허용 |
| `score` / `best_eta` | 이전 설정보다 감소 |
| `min_clearance` | `caution_clearance_m` 이상 유지 |
| `detour` | 가능하면 `detour_ratio_warn` 미만 유지 |
| `goal_error` | `goal_tolerance_m` 이하 유지 |

`CAUTION`, `BLOCKED`, `GOAL_MISMATCH` 경로는 빨라도 최단시간 후보로 인정하지 않습니다.

## 2026-06-24 / 1차 최적화

### 변경 내용

- Nav2 global planner의 `use_astar`를 `false`에서 `true`로 변경
- `planner_server.expected_planner_frequency`를 `5.0Hz`에서 `10.0Hz`로 변경
- Nav2 goal tolerance를 `0.30m`에서 `0.20m`로 줄여 mission goal과 경로 끝점 차이를 줄임
- Regulated Pure Pursuit의 `desired_linear_vel`을 `0.20m/s`에서 `0.23m/s`로 변경
- local/global costmap의 semantic obstacle inflation radius를 `0.35m`에서 `0.45m`로 변경
- inflation radius 증가에 따른 과도한 우회를 줄이기 위해 `cost_scaling_factor`를 `3.0`에서 `4.0`으로 변경
- `path_feedback_monitor`에 `score`, `best_eta`, `eta_delta`, `trend`를 추가

### 의도

기존 설정에서는 planner가 semantic obstacle 근처를 지나가는 경로를 만들 수 있고, 이후 controller 또는 feedback 단계에서 감속/주의가 걸릴 가능성이 있었습니다. 이번 변경은 경로 생성 단계에서부터 장애물 근접 경로를 줄여 실제 도착시간을 줄이는 쪽에 맞춥니다.

A*는 Dijkstra/NavFn보다 목표 방향 heuristic을 사용하므로 동일 costmap에서 더 빠르게 목표 지향 경로를 찾는 것을 기대합니다. 실제 주행 시간 최적화는 `eta`, `score`, `best_eta`로 판단합니다.

### 다음 실험에서 볼 것

```bash
ros2 topic echo /navigation/path_feedback
```

- `trend=best`가 새로 뜨는지 확인
- `score`와 `best_eta`가 이전 설정보다 낮아지는지 확인
- `min_clearance`가 `0.45m` 이상인지 확인
- `detour`가 커져서 `SLOW`가 자주 뜨면 inflation 또는 cost scaling 재조정
- `CAUTION`이 자주 뜨면 obstacle radius, inflation radius, semantic registry TTL 확인

### 아직 미정

- 실제 로봇의 안정적인 최고 선속도
- 실제 로봇의 안정적인 최고 회전속도
- target을 담은 상태에서의 감속 비율
- 바닥 마찰과 미끄러짐에 따른 회전 시간 보정
- obstacle class별 radius와 위험도 가중치
