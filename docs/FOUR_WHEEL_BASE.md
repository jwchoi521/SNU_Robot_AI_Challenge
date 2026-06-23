# 4륜 독립 구동 odometry와 제어 모델

로봇은 4개의 바퀴가 각각 독립 모터로 제어되는 구조입니다. 따라서 base driver는 각 바퀴의
encoder 위치 또는 속도를 알아야 하고, 이 값으로 로봇의 선속도와 각속도를 계산해야 합니다.

## 입력과 출력

입력:

```text
/cmd_vel
/joint_states
  front_left_wheel_joint
  front_right_wheel_joint
  rear_left_wheel_joint
  rear_right_wheel_joint
```

출력:

```text
/wheel_commands
/wheel/odom
```

`/wheel_commands`는 모터 드라이버가 받을 바퀴별 명령이고, `/wheel/odom`은 이후
`robot_localization`으로 들어가 IMU와 함께 `/odometry/filtered`로 보정됩니다.

## 일반 4륜 skid-steer 모델

바퀴가 일반 바퀴이고 좌우 속도 차이로 회전하는 구조라면 기본 모델은 skid-steer입니다.

```text
v_left  = r * (w_front_left + w_rear_left) / 2
v_right = r * (w_front_right + w_rear_right) / 2

v_x     = (v_left + v_right) / 2
omega_z = (v_right - v_left) / track_width
```

## `/cmd_vel`에서 바퀴 명령으로 변환

상위 제어기는 보통 `/cmd_vel`로 다음 값을 냅니다.

```text
linear.x
linear.y
angular.z
```

일반 skid-steer라면 `linear.y`는 사용할 수 없고, `linear.x`와 `angular.z`를 4개 바퀴
속도로 변환합니다.

```text
v_left  = linear.x - angular.z * track_width / 2
v_right = linear.x + angular.z * track_width / 2

w_front_left  = v_left / r
w_rear_left   = v_left / r
w_front_right = v_right / r
w_rear_right  = v_right / r
```

현재 코드 위치:

```bash
ros2 launch snu_base_control cmd_vel_to_four_wheel.launch.py
ros2 launch snu_base_control four_wheel_odometry.launch.py
```

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

## 모터 출력과 실제 orientation 매칭

현재 계획에는 두 방향의 매칭이 들어갑니다.

1. 명령 변환

```text
/cmd_vel
  -> cmd_vel_to_four_wheel
  -> /wheel_commands
  -> motor driver
```

2. 실제 움직임 검증

```text
encoder /joint_states + IMU
  -> /wheel/odom
  -> /odometry/filtered
  -> 실제 x, y, yaw 변화
```

즉 “모터에 어떤 출력을 줬을 때 orientation이 얼마나 바뀌는가”는 아래 실험으로 맞춥니다.

| 실험 | 명령 | 확인할 값 | 보정 파라미터 |
| --- | --- | --- | --- |
| 직진 | `linear.x > 0`, `angular.z = 0` | 실제 이동 거리 | `wheel_radius_m`, 좌우 scale |
| 제자리 회전 | `linear.x = 0`, `angular.z != 0` | 실제 yaw 변화 | `track_width_m`, wheel sign |
| 좌우 대칭 | 같은 크기의 좌/우 명령 | 한쪽으로 휘는지 | 각 바퀴 motor scale |
| 반복 주행 | 사각형 또는 왕복 | 시작점으로 돌아오는지 | odom covariance, EKF 설정 |

실제 로봇에서 반드시 기록해야 하는 값:

```text
명령한 /cmd_vel
생성된 /wheel_commands
encoder 기반 /wheel/odom
IMU yaw-rate
최종 /odometry/filtered
```

이 로그를 비교해서 명령 모델과 실제 로봇 움직임을 맞춥니다. 처음부터 완벽하게 맞추려고
하기보다, 직진과 제자리 회전을 먼저 맞춘 뒤 target 접근 속도를 낮게 잡는 것이 좋습니다.
