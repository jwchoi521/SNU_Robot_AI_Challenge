# `/cmd_vel` 속도 제어 테스트

현재 실측 기구 파라미터:

```text
wheel_radius_m = 0.035   # 바퀴 지름 약 70 mm
track_width_m  = 0.112   # 좌우 바퀴 중심 간 거리 112 mm
wheelbase_m    = 0.0986  # 앞뒤 바퀴축 간 거리 98.6 mm
```

일반 skid-steer 4륜 기준 변환식:

```text
left_wheel_mps  = linear.x - angular.z * track_width_m / 2
right_wheel_mps = linear.x + angular.z * track_width_m / 2

left_wheel_rad_s  = left_wheel_mps / wheel_radius_m
right_wheel_rad_s = right_wheel_mps / wheel_radius_m
```

예시:

```text
linear.x = 0.10 m/s, angular.z = 0.0 rad/s
wheel speed = 0.10 / 0.035 = 2.86 rad/s
```

## 아직 필요한 보정값

`encoder_counts_per_revolution`은 반드시 실측해야 한다. 이 값이 틀리면 `/joint_states`,
`/wheel/odom`, ESP32 velocity PID의 실제 속도 기준이 모두 틀어진다.

측정 방법:

1. 로봇을 들어 올린다.
2. ESP32 bridge를 켠다.
3. `/joint_states` 또는 ESP32 `E ...` count를 본다.
4. 바퀴 하나를 손으로 정확히 1바퀴 돌린다.
5. 증가한 count를 기록한다.
6. 네 바퀴가 비슷한지 확인하고 평균값을 `encoder_counts_per_revolution`에 넣는다.

## Jetson 테스트 순서

새 터미널마다:

```bash
cd ~/SNU_Robot_AI_Challenge/ros2_ws
source /opt/ros/humble/setup.bash
source install/setup.bash
```

ESP32 bridge:

```bash
ros2 launch snu_hardware_drivers esp32_serial_hardware.launch.py \
  dry_run:=false \
  serial_port:=/dev/ttyUSB0 \
  baud_rate:=115200 \
  esp32_command_mode:=velocity \
  max_power:=0.60 \
  max_wheel_velocity_rad_s:=20.0 \
  encoder_counts_per_revolution:=1.0 \
  enable_jog_test:=false
```

`encoder_counts_per_revolution`은 측정 전까지 임시값이다. 측정 후에는 `1.0` 대신 실제 값을 넣는다.

다른 터미널에서 `/cmd_vel` 변환 노드:

```bash
cd ~/SNU_Robot_AI_Challenge/ros2_ws
source /opt/ros/humble/setup.bash
source install/setup.bash

ros2 launch snu_base_control cmd_vel_to_four_wheel.launch.py
```

필요하면 odometry 노드도 같이 실행:

```bash
ros2 launch snu_base_control four_wheel_odometry.launch.py
```

아주 약한 직진 테스트:

```bash
timeout 2s ros2 topic pub -r 20 /cmd_vel geometry_msgs/msg/Twist \
"{linear: {x: 0.05, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}"
```

조금 더 강한 직진 테스트:

```bash
timeout 2s ros2 topic pub -r 20 /cmd_vel geometry_msgs/msg/Twist \
"{linear: {x: 0.10, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}"
```

제자리 회전 테스트:

```bash
timeout 2s ros2 topic pub -r 20 /cmd_vel geometry_msgs/msg/Twist \
"{linear: {x: 0.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.3}}"
```

## 판단 기준

- 직진 명령에서 왼쪽/오른쪽이 서로 반대로 움직이면 motor sign 문제다.
- 바퀴는 도는데 `/joint_states` 속도가 거의 안 나오면 encoder sign/pin/count 문제다.
- `/cmd_vel` 직진에서 실제 거리가 명령 거리보다 계속 작거나 크면 `wheel_radius_m` 또는
  `encoder_counts_per_revolution`을 보정한다.
- 제자리 회전에서 실제 yaw가 명령보다 작거나 크면 `track_width_m`을 보정한다.
- 네 바퀴 속도가 서로 다르면 ESP32 velocity gain 또는 바퀴별 scale 보정이 필요하다.
