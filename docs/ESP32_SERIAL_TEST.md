# Jetson-ESP32 모터/엔코더 테스트

현재 사용 물품 기준으로 권장하는 1차 테스트 구조입니다.

```text
Jetson Orin Nano / ROS2
  -> USB Serial
  -> ESP32 DevKitC
  -> Cytron MDD3A motor drivers
  -> 4 DC encoder motors
```

Jetson은 SLAM, Nav2, mission logic을 실행하고, ESP32는 실시간성이 필요한 모터 PWM 출력과 엔코더 카운트를 담당합니다.

## 사용 물품에서 확인된 것

| 항목 | 모델 |
| --- | --- |
| 모터 | L-type 520 Encoder DC Reduction Motor |
| 모터드라이버 | Cytron 3Amp 4V-16V DC Motor Driver, 2 Channels, MDD3A |
| 마이크로컨트롤러 | ESP32 DevKitC WROOM-32D V4 |
| IMU | Adafruit BNO085/BNO080 9-DOF Orientation IMU |
| 배터리 | 12V |

## 현재 핀 매핑

### 모터드라이버 입력

| 바퀴 | ESP32 A | ESP32 B |
| --- | --- | --- |
| BR, 뒤 오른쪽 | 14 | 13 |
| FR, 앞 오른쪽 | 4 | 5 |
| BL, 뒤 왼쪽 | 2 | 15 |
| FL, 앞 왼쪽 | 23 | 25 |

### 엔코더

| 바퀴 | ESP32 A | ESP32 B |
| --- | --- | --- |
| BR, 뒤 오른쪽 | 26 | 27 |
| FR, 앞 오른쪽 | 16 | 17 |
| BL, 뒤 왼쪽 | 32 | 33 |
| FL, 앞 왼쪽 | 18 | 19 |

### IMU

| 신호 | ESP32 |
| --- | --- |
| SCL | 22 |
| SDA | 21 |

## 추가 확인 필요

| 항목 | 이유 |
| --- | --- |
| MDD3A 입력 모드 | 현재 펌웨어는 A/B 두 핀 중 한쪽에 PWM을 넣는 방식입니다. 드라이버가 PWM/DIR 방식이면 펌웨어를 바꿔야 합니다. |
| 엔코더 CPR과 기어비 | `/joint_states`를 실제 rad/s로 변환하려면 필요합니다. |
| ESP32와 Jetson 사이 serial 포트 | Jetson에서 `/dev/ttyUSB0`인지 `/dev/ttyACM0`인지 확인해야 합니다. |
| 모터 전원 GND와 ESP32/Jetson GND 공통 여부 | 제어 신호 기준 전압을 맞추기 위해 필요합니다. |
| BNO085 I2C 주소 | `/imu` driver 연결에 필요합니다. 보통 `0x4A` 또는 `0x4B`입니다. |

## ESP32 펌웨어 업로드

펌웨어 위치:

```text
firmware/esp32_motor_bridge/esp32_motor_bridge.ino
```

Arduino IDE 또는 arduino-cli로 ESP32에 업로드합니다. 업로드 후 Serial Monitor에서 아래 로그가 나오면 시작은 정상입니다.

```text
READY esp32_motor_bridge
E 0 0 0 0
```

ESP32 serial protocol:

```text
Jetson -> ESP32: M <front_left> <front_right> <rear_left> <rear_right>
ESP32 -> Jetson: E <front_left_count> <front_right_count> <rear_left_count> <rear_right_count>
```

## Jetson에서 빌드

```bash
cd ~/SNU_Robot_AI_Challenge/ros2_ws
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
source install/setup.bash
```

pyserial이 없다면 설치합니다.

```bash
sudo apt install python3-serial
```

## Serial 포트 확인

ESP32를 Jetson에 USB로 연결한 뒤 확인합니다.

```bash
ls /dev/ttyUSB* /dev/ttyACM*
```

권한 문제가 있으면 Jetson 사용자를 `dialout` 그룹에 넣고 재로그인합니다.

```bash
sudo usermod -aG dialout $USER
```

## 1단계: ROS dry-run

serial 포트를 열지 않고 ROS 토픽 흐름만 확인합니다.

```bash
ros2 launch snu_hardware_drivers esp32_serial_hardware.launch.py \
  dry_run:=true \
  enable_jog_test:=true
```

로그에 `dry_run serial write: M ...`가 나오면 `/wheel_commands` 흐름은 정상입니다.

## 2단계: ESP32 연결 확인

아직 jog test는 켜지 않고 bridge만 실제 serial로 엽니다.

```bash
ros2 launch snu_hardware_drivers esp32_serial_hardware.launch.py \
  dry_run:=false \
  serial_port:=/dev/ttyUSB0 \
  enable_jog_test:=false
```

다른 터미널:

```bash
ros2 topic echo /joint_states
```

손으로 바퀴를 살짝 돌렸을 때 해당 joint 값이 변하면 엔코더 serial 수신은 정상입니다.

## 3단계: 바퀴 jog 테스트

로봇을 반드시 바닥에서 띄운 상태로 실행합니다.

터미널 1:

```bash
ros2 launch snu_hardware_drivers esp32_serial_hardware.launch.py \
  dry_run:=false \
  serial_port:=/dev/ttyUSB0 \
  enable_jog_test:=false
```

터미널 2:

```bash
ros2 run snu_hardware_drivers wheel_jog_test --ros-args \
  -p power:=0.08 \
  -p run_sec:=0.30 \
  -p pause_sec:=1.00 \
  -p include_reverse:=false
```

기본 테스트 순서:

```text
FL -> FR -> BL -> BR
```

각 단계에서 확인할 것:

- 실제로 도는 바퀴가 명령한 바퀴와 같은지
- 앞으로 명령했을 때 기대한 방향으로 도는지
- `/joint_states`에서 해당 joint position이 증가하는지
- 모터가 멈춰야 할 때 바로 멈추는지

## 방향 보정

모터가 반대로 돌면 `esp32_serial.yaml`에서 motor sign을 바꿉니다.

```yaml
front_left_motor_sign: -1.0
```

엔코더 position이 반대로 움직이면 encoder sign을 바꿉니다.

```yaml
front_left_encoder_sign: -1.0
```

## 다음 단계

1. 바퀴별 motor sign 확인
2. 바퀴별 encoder sign 확인
3. 엔코더 CPR 입력
4. `/cmd_vel -> /wheel_commands -> ESP32 -> /joint_states -> /wheel/odom` 확인
5. BNO085 IMU driver 추가
6. low-speed 직진/제자리 회전 calibration
