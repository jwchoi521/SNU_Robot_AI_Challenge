# yaw calibration 사용법

이 폴더는 로봇의 `angular.z` 명령과 실제 IMU yaw rate 사이의 비선형 관계를 데이터로 모으고, 학습한 모델로 주행 중 `angular.z`를 보정하기 위한 코드입니다.

핵심 아이디어는 다음과 같습니다.

```text
Nav2 또는 테스트 노드가 원하는 각속도 target_wz를 냄
-> 여러 yaw_cmd 후보 중 실제 IMU yaw rate가 target_wz에 가장 가까울 값을 모델이 고름
-> 보정된 yaw_cmd를 기존 cmd_vel_to_four_wheel로 보냄
-> ESP32는 기존 SET1 encoder velocity + IMU feedback으로 남은 오차를 잡음
```

## 들어있는 파일

```text
collector_node.py
  여러 linear.x, yaw_cmd 조합을 자동으로 실행하고 /imu, /joint_states, /wheel_commands, ESP32 SET1_DBG PWM 로그를 CSV로 저장합니다.

train_yaw_response_model.py
  CSV를 읽어서 yaw_cmd -> 실제 imu_wz 응답 모델 JSON을 만듭니다.

yaw_response_model.py
  모델 로드, actual_wz 예측, target_wz에 맞는 yaw_cmd 선택 로직입니다.

yaw_cmd_compensator_node.py
  주행 중 /cmd_vel을 받아 보정된 /cmd_vel_calibrated를 publish합니다.
```

## 0. 빌드

젯슨에서 pull한 뒤 빌드합니다.

```bash
cd ~/SNU_Robot_AI_Challenge/ros2_ws
colcon build --symlink-install
source install/setup.bash
```

## 1. 데이터 수집 준비

캘리브레이션할 때는 Nav2나 목표 추종 노드가 동시에 `/cmd_vel`을 publish하면 안 됩니다.

터미널 1에서 ESP32 bridge를 켭니다.

```bash
cd ~/SNU_Robot_AI_Challenge/ros2_ws && source install/setup.bash && ros2 launch snu_hardware_drivers esp32_serial_hardware.launch.py dry_run:=false serial_port:=/dev/ttyUSB1 esp32_protocol:=u_shape esp32_command_mode:=encoder_velocity max_wheel_velocity_rad_s:=50.0 publish_imu:=true
```

터미널 2에서 `/cmd_vel -> /wheel_commands` 변환기를 켭니다.

```bash
cd ~/SNU_Robot_AI_Challenge/ros2_ws && source install/setup.bash && ros2 launch snu_base_control cmd_vel_to_four_wheel.launch.py
```

데이터가 들어오는지 확인합니다.

```bash
ros2 topic hz /imu
ros2 topic hz /joint_states
ros2 topic echo /wheel_commands --once
ros2 topic echo /rosout | grep SET1_DBG
```

## 2. 데이터 수집 실행

로봇 주변에 충분한 빈 공간을 확보한 뒤 실행합니다. 기본값은 `enable_motion:=false`라서 실제 움직이지 않습니다. 실제 수집할 때만 `true`로 바꿉니다.

처음에는 좁은 범위로 테스트하는 것을 추천합니다.

```bash
cd ~/SNU_Robot_AI_Challenge/ros2_ws && source install/setup.bash && ros2 run snu_yaw_calibration yaw_calibration_collector --ros-args -p enable_motion:=true -p output_csv:=/home/cho/yaw_calibration/yaw_run1.csv -p linear_x_values:="[0.0, 0.04, 0.08, 0.12]" -p yaw_cmd_values:="[-2.0, -1.5, -1.0, -0.6, -0.3, 0.3, 0.6, 1.0, 1.5, 2.0]" -p repeat_count:=1
```

만약 `yaw_cmd=2.0`에서도 실제 `imu_wz`가 너무 작으면 더 넓은 범위로 다시 수집합니다.

```bash
cd ~/SNU_Robot_AI_Challenge/ros2_ws && source install/setup.bash && ros2 run snu_yaw_calibration yaw_calibration_collector --ros-args -p enable_motion:=true -p output_csv:=/home/cho/yaw_calibration/yaw_run_wide.csv -p linear_x_values:="[0.0, 0.04, 0.08, 0.12, 0.15]" -p yaw_cmd_values:="[-4.0, -3.5, -3.0, -2.5, -2.0, -1.5, -1.0, -0.6, -0.3, 0.3, 0.6, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]" -p repeat_count:=1
```

수집 CSV에는 이런 값이 저장됩니다.

```text
linear_x
yaw_cmd
imu_wz
wheel_cmd_fl/fr/rl/rr
joint_fl/fr/rl/rr_rad_s
pwm_fl/fr/bl/br
pwm_saturated
esp32_target_wz / esp32_imu_wz / esp32_yaw_corr
valid_sample
```

PWM이 임계값에 가까워지면 collector가 이런 경고를 냅니다.

```text
PWM saturation near limit: FL=+250 FR=+255 BL=+247 BR=+255; target_wz=+2.000 imu_wz=+0.350
```

기본 포화 기준은 `pwm_saturation_threshold:=245.0`입니다. 필요하면 실행할 때 바꿀 수 있습니다.

각 trial에서 처음 `settle_sec` 구간은 버리고, 안정된 `sample` 구간만 학습에 씁니다.

## 3. 모델 학습

CSV 하나만 쓸 수도 있고 여러 개를 같이 넣을 수도 있습니다.

```bash
cd ~/SNU_Robot_AI_Challenge/ros2_ws && source install/setup.bash && ros2 run snu_yaw_calibration train_yaw_response_model /home/cho/yaw_calibration/yaw_run1.csv -o /home/cho/yaw_calibration/yaw_response_model.json --max-abs-yaw-cmd-rad-s 4.0
```

여러 CSV를 합칠 때는 이렇게 합니다.

```bash
cd ~/SNU_Robot_AI_Challenge/ros2_ws && source install/setup.bash && ros2 run snu_yaw_calibration train_yaw_response_model /home/cho/yaw_calibration/yaw_run1.csv /home/cho/yaw_calibration/yaw_run_wide.csv -o /home/cho/yaw_calibration/yaw_response_model.json --max-abs-yaw-cmd-rad-s 4.0
```

학습 결과는 JSON 파일입니다.

```text
/home/cho/yaw_calibration/yaw_response_model.json
```

## 4. 학습 모델 적용

적용할 때는 기본 wheel mapper가 raw `/cmd_vel`을 바로 먹지 않게 해야 합니다.

full stack 실행 시에는 `enable_wheel_command_mapper:=false`로 둡니다. ESP32 bridge는 켜도 됩니다.

그 다음 터미널 하나에서 보정 노드를 켭니다.

```bash
cd ~/SNU_Robot_AI_Challenge/ros2_ws && source install/setup.bash && ros2 run snu_yaw_calibration yaw_cmd_compensator --ros-args -p model_path:=/home/cho/yaw_calibration/yaw_response_model.json -p input_cmd_vel_topic:=/cmd_vel -p output_cmd_vel_topic:=/cmd_vel_calibrated -p max_abs_yaw_cmd_rad_s:=4.0
```

다른 터미널에서 wheel mapper를 보정된 토픽에 연결합니다.

```bash
cd ~/SNU_Robot_AI_Challenge/ros2_ws && source install/setup.bash && ros2 run snu_base_control cmd_vel_to_four_wheel --ros-args -p cmd_vel_topic:=/cmd_vel_calibrated -p wheel_command_topic:=/wheel_commands -p drive_model:=skid_steer -p command_mode:=velocity -p wheel_radius_m:=0.033 -p track_width_m:=0.30 -p wheelbase_m:=0.235 -p max_wheel_velocity_rad_s:=50.0
```

그러면 흐름이 이렇게 됩니다.

```text
Nav2 / direct controller
  -> /cmd_vel
  -> yaw_cmd_compensator
  -> /cmd_vel_calibrated
  -> cmd_vel_to_four_wheel
  -> /wheel_commands
  -> esp32_serial_bridge
  -> ESP32 SET1
```

## 5. 적용 상태 확인

보정 노드는 이런 로그를 냅니다.

```text
yaw_comp ok: v=+0.120 target_wz=+0.500 yaw_cmd=+2.350 predicted_wz=+0.480
```

확인할 토픽은 다음입니다.

```bash
ros2 topic echo /cmd_vel --once
ros2 topic echo /cmd_vel_calibrated --once
ros2 topic echo /wheel_commands --once
ros2 topic echo /imu --once
```

`/cmd_vel`의 `angular.z`보다 `/cmd_vel_calibrated`의 `angular.z`가 더 커질 수 있습니다. 이것이 의도된 동작입니다.

## 주의

`yaw_cmd`를 크게 줬는데도 `imu_wz`가 더 이상 커지지 않으면 제어 코드 문제가 아니라 물리적 포화일 수 있습니다. 이 경우에는 해당 `linear.x`에서 목표 각속도를 만들 수 없으므로 Nav2/controller 쪽에서 선속도를 줄여야 합니다.

또한 이 모델은 단순 비례 gain이 아닙니다. `linear_x, yaw_cmd -> 실제 imu_wz`의 비선형 응답을 저장하고, 주행 중 목표 `target_wz`에 가장 가까운 `yaw_cmd`를 후보 탐색으로 고릅니다.
