# 4륜 독립 구동 odometry와 제어 모델

로봇은 4개의 바퀴가 각각 독립 모터로 제어되는 구조입니다. 따라서 base driver는
각 바퀴의 encoder 위치 또는 속도를 알아야 하고, 이 값으로 로봇의 선속도와 각속도를
계산해야 합니다.

## 입력과 출력

입력:

```text
/joint_states
  front_left_wheel_joint
  front_right_wheel_joint
  rear_left_wheel_joint
  rear_right_wheel_joint
```

출력:

```text
/wheel/odom
```

`/wheel/odom`은 이후 `robot_localization`으로 들어가고, IMU와 함께
`/odometry/filtered`로 보정됩니다.

## 일반 4륜 skid-steer 모델

바퀴가 일반 바퀴이고 좌우 속도 차이로 회전하는 구조라면 기본 모델은 skid-steer입니다.

```text
v_left  = r * (w_front_left + w_rear_left) / 2
v_right = r * (w_front_right + w_rear_right) / 2

v_x     = (v_left + v_right) / 2
omega_z = (v_right - v_left) / track_width
```

| 기호 | 의미 |
| --- | --- |
| `r` | 바퀴 반지름 |
| `w_*` | 각 바퀴의 각속도 |
| `track_width` | 좌우 바퀴 중심 간 거리 |
| `v_x` | 로봇 전진 속도 |
| `omega_z` | 로봇 yaw 회전 속도 |

위 값을 시간 `dt`만큼 적분하면 위치가 바뀝니다.

```text
theta += omega_z * dt
x     += v_x * cos(theta) * dt
y     += v_x * sin(theta) * dt
```

실제 코드에서는 회전 중 오차를 줄이기 위해 중간 yaw를 사용해 적분합니다.

## mecanum 모델

만약 mecanum wheel이라면 좌우 이동 `v_y`도 계산할 수 있습니다. 이 경우
`drive_model:=mecanum`으로 바꿉니다.

```text
v_x     = r / 4 * (w_fl + w_fr + w_rl + w_rr)
v_y     = r / 4 * (-w_fl + w_fr + w_rl - w_rr)
omega_z = r / (4 * (lx + ly)) * (-w_fl + w_fr - w_rl + w_rr)
```

mecanum은 바퀴 장착 방향과 encoder 부호에 민감하므로 실제 로봇에서 반드시 부호를
검증해야 합니다.

## 현재 코드 위치

```bash
ros2 launch snu_base_control four_wheel_odometry.launch.py
```

설정 파일:

```text
ros2_ws/src/snu_base_control/config/four_wheel_odometry.yaml
```

기본값은 `drive_model: skid_steer`입니다.

## 제어 관점

상위 제어기는 보통 `/cmd_vel`로 다음 값을 냅니다.

```text
linear.x
linear.y
angular.z
```

일반 skid-steer라면 `linear.y`는 사용할 수 없고, base driver는 `linear.x`와
`angular.z`를 4개 바퀴 속도로 변환합니다.

```text
v_left  = linear.x - angular.z * track_width / 2
v_right = linear.x + angular.z * track_width / 2

w_front_left  = v_left / r
w_rear_left   = v_left / r
w_front_right = v_right / r
w_rear_right  = v_right / r
```

이 변환은 실제 모터 드라이버 쪽에서 수행해야 합니다. `snu_base_control`은 현재
encoder 값을 바탕으로 `/wheel/odom`을 계산하는 역할부터 맡습니다.
