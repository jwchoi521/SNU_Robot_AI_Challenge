# Target 수거 및 고정 목적지 배치 흐름

이 문서는 target object에 접근한 뒤, 로봇 앞쪽 집게/바스켓에 target을 담고,
맵 상의 고정 목적지로 이동해 내려놓는 mission 흐름을 정리합니다.

## 전제

- target과 obstacle 위치는 YOLO + IR distance로 추정합니다.
- 추정된 object 위치는 TF를 통해 `map` 좌표로 변환할 수 있습니다.
- 로봇의 현재 위치는 SLAM/localization, 휠 odom, IMU를 통해 `map -> base_link`로 얻습니다.
- 집게는 로봇 앞쪽에 있고, 열어서 target을 안쪽에 넣은 뒤 닫는 방식입니다.

## 필요한 인터페이스

| 토픽 | 타입 | 설명 |
| --- | --- | --- |
| `/perception/objects` | `PerceivedObjectArray` | target/obstacle 후보 |
| `/target_pose_base` | `PoseStamped` | 로봇 기준 target 위치 |
| `/target_pose_map` | `PoseStamped` | 맵 기준 target 위치 |
| `/semantic_obstacles` | `PointCloud2` | 회피해야 하는 object |
| `/cmd_vel` | `Twist` | 로봇 속도 명령 |
| `/mission/nav_goal` | `PoseStamped` | mission manager가 요청한 이동 목표 |
| `/mission/event` | `String` | mission 상태 전환 이벤트 |
| `/gripper/command` | `GripperCommand` | 집게 열기/닫기 |
| `/gripper/state` | `GripperState` | 수거 여부 확인 |

## Mission 상태기계

```text
IDLE
  -> SEARCH_TARGET
  -> NAV_TO_TARGET
  -> FINAL_ALIGN
  -> OPEN_GRIPPER
  -> CAPTURE_TARGET
  -> CLOSE_GRIPPER
  -> VERIFY_CAPTURE
  -> NAV_TO_DROP_ZONE
  -> OPEN_GRIPPER_AT_DROP
  -> BACK_OFF
  -> DONE
```

## 단계별 동작

1. `SEARCH_TARGET`

YOLO가 현재 mission에서 필요한 object를 찾습니다. 필요한 object는
`navigation_role=TARGET`, 나머지 object는 `navigation_role=OBSTACLE`로 처리합니다.

2. `NAV_TO_TARGET`

target의 map 좌표 또는 `/target_pose_base`를 기반으로 target 근처까지 Nav2로 이동합니다.
이때 `/semantic_obstacles`는 Nav2 costmap에 들어가므로, target이 아닌 object를 피합니다.

3. `FINAL_ALIGN`

target이 가까워지면 map goal만 믿지 말고, 카메라 bearing과 IR distance로 천천히 정렬합니다.

4. `OPEN_GRIPPER`

집게를 엽니다.

```text
/gripper/command = OPEN
```

5. `CAPTURE_TARGET`

짧은 거리만 저속 전진합니다. 이 단계에서는 Nav2 global path보다 직접 제어가 더 적합합니다.

```text
linear.x = 낮은 속도
angular.z = bearing_deg 기반 작은 보정
```

6. `CLOSE_GRIPPER`

target이 집게 안쪽에 들어왔다고 판단하면 집게를 닫습니다.

```text
/gripper/command = CLOSE
```

7. `VERIFY_CAPTURE`

`/gripper/state.has_object`가 true인지 확인합니다. 센서가 없다면 카메라에서 target이
집게 안쪽 영역에 유지되는지로 임시 판단할 수 있습니다.

8. `NAV_TO_DROP_ZONE`

맵 기준 고정 목적지로 이동합니다.

```text
drop_pose:
  frame_id: map
  x: <측정 필요>
  y: <측정 필요>
  yaw: <측정 필요>
```

9. `OPEN_GRIPPER_AT_DROP`

목적지에 도착하면 집게를 열고 target을 내려놓습니다.

10. `BACK_OFF`

target을 다시 밀거나 건드리지 않도록 짧게 후진합니다.

11. `DONE`

해당 target을 semantic object registry에서 삭제하고 다음 mission으로 넘어갑니다.

## 현재 코드 상태

현재 `snu_mission_manager`는 완성된 Nav2 action client가 아니라 상태기계 골격입니다.

```bash
ros2 launch snu_mission_manager pick_place_mission.launch.py
```

기본 동작:

- `/target_pose_map`을 받으면 `/mission/nav_goal`로 target goal을 발행합니다.
- `/mission/event`에 `target_reached`가 들어오면 집게를 엽니다.
- `/mission/event`에 `target_inside`가 들어오면 집게를 닫습니다.
- `/gripper/state.has_object=true`가 들어오면 drop pose로 `/mission/nav_goal`을 발행합니다.
- `/mission/event`에 `drop_reached`가 들어오면 집게를 엽니다.

Nav2 action client 연결, final alignment 제어, registry에서 수거한 target 삭제는 다음 단계 TODO입니다.

## 중요한 설계 포인트

- target을 집은 뒤에는 그 target을 obstacle로 남겨두면 안 됩니다.
- target을 놓은 위치는 필요하면 semantic map에 "delivered target"으로 기록할 수 있습니다.
- 집게가 닫힌 상태에서는 로봇 footprint를 약간 크게 잡는 것이 안전합니다.
- drop zone은 LiDAR 맵 위에서 사람이 미리 찍은 `map` 좌표로 두는 것이 가장 단순합니다.
