# Jetson Orin Nano 직접 GPIO 모터/엔코더 테스트

이 문서는 모터드라이버와 엔코더가 Jetson Orin Nano 40핀 헤더에 직접 연결된 경우의 절차입니다.

현재 사용 물품 문서에는 `ESP32 DevKitC`가 포함되어 있고, 제공된 핀 번호도 ESP32 GPIO 번호 형태입니다. 그 경우에는 이 문서보다 `ESP32_SERIAL_TEST.md`의 `Jetson -> USB Serial -> ESP32 -> 모터/엔코더` 방식을 먼저 사용해야 합니다.

## 현재 연결 정보

### 엔코더

| 바퀴 | A | B |
| --- | --- | --- |
| BR, 뒤 오른쪽 | 26 | 27 |
| FR, 앞 오른쪽 | 16 | 17 |
| BL, 뒤 왼쪽 | 32 | 33 |
| FL, 앞 왼쪽 | 18 | 19 |

### 모터드라이버 입력

| 바퀴 | A | B |
| --- | --- | --- |
| BR, 뒤 오른쪽 | 14 | 13 |
| FR, 앞 오른쪽 | 4 | 5 |
| BL, 뒤 왼쪽 | 2 | 15 |
| FL, 앞 왼쪽 | 23 | 25 |

### IMU

| 신호 | 번호 |
| --- | --- |
| SCL | 22 |
| SDA | 21 |

## 매우 중요한 확인

위 번호가 Jetson 40핀 헤더의 물리 핀 번호라면 그대로 실행하면 안 됩니다. 물리 핀 기준으로 2번/4번은 전원 핀이고, 14번/25번 등은 GND라 모터 제어 출력으로 사용할 수 없습니다.

현재 설정은 이 번호들을 Jetson.GPIO의 `BCM` 번호로 해석하도록 되어 있습니다.

```yaml
pin_numbering: BCM
dry_run: true
```

실제 모터를 돌리기 전에 아래 둘을 확인해야 합니다.

- 핀 번호가 `BCM/GPIO 번호`인지, `BOARD 물리 핀 번호`인지
- 모터드라이버가 `A/B 두 입력 핀에 PWM을 넣는 H-bridge 방식`인지

## 추가로 필요한 값

| 항목 | 필요한 이유 |
| --- | --- |
| 모터드라이버 모델명 | EN/PWM/STBY 핀이 따로 필요한 드라이버인지 확인 |
| 엔코더 counts per revolution | `/joint_states` 위치/속도 값을 실제 rad/s로 환산 |
| 모터 전원 전압과 별도 배터리 여부 | Jetson GPIO와 모터 전원 분리 확인 |
| IMU 모델명과 I2C 주소 | `/imu` driver 작성에 필요 |
| 핀 번호 체계 | `BCM`, `BOARD`, `TEGRA_SOC` 중 무엇인지 확정 |

## 코드 구성

| 노드 | 역할 |
| --- | --- |
| `gpio_four_wheel_driver` | `/wheel_commands`를 받아 4개 모터 A/B 핀에 PWM 출력 |
| `gpio_encoder_joint_state` | 엔코더 A/B를 읽어 `/joint_states` 발행 |
| `wheel_jog_test` | 바퀴 하나씩 낮은 출력으로 짧게 돌리는 테스트 명령 발행 |

설정 파일:

```text
ros2_ws/src/snu_hardware_drivers/config/jetson_gpio.yaml
```

## Jetson에서 빌드

```bash
cd ~/SNU_Robot_AI_Challenge/ros2_ws
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
source install/setup.bash
```

Jetson.GPIO가 없다면 Jetson에서 설치합니다.

```bash
python3 -m pip install Jetson.GPIO
```

## 1단계: dry-run 테스트

아직 모터 핀을 실제로 구동하지 않고 ROS 토픽 흐름만 확인합니다.

```bash
ros2 launch snu_hardware_drivers jetson_gpio_hardware.launch.py \
  dry_run:=true \
  enable_encoder:=true \
  enable_jog_test:=true
```

정상이라면 `dry_run wheel output` 로그가 나오고 실제 바퀴는 움직이지 않습니다.

## 2단계: 실제 모터 jog 테스트

로봇을 반드시 바닥에서 띄운 상태로 테스트합니다. 처음에는 바퀴가 바닥에 닿지 않아야 합니다.

터미널 1:

```bash
ros2 launch snu_hardware_drivers jetson_gpio_hardware.launch.py \
  dry_run:=false \
  enable_encoder:=true \
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

기본 순서는 `FL -> FR -> BL -> BR`입니다. 각 바퀴가 기대한 바퀴인지, 회전 방향이 맞는지 확인합니다.

## 3단계: 엔코더 확인

모터 jog 중 다른 터미널에서 확인합니다.

```bash
ros2 topic echo /joint_states
```

바퀴가 앞으로 돌 때 해당 joint의 position이 증가해야 합니다. 반대로 감소하면 `jetson_gpio.yaml`에서 해당 바퀴의 encoder sign을 `-1.0`으로 바꿉니다.

현재 `encoder_counts_per_revolution`은 임시값 `1.0`입니다. 실제 엔코더 사양과 기어비를 반영하지 않으면 odometry 속도/거리 값은 맞지 않습니다.

## 4단계: 방향 보정

바퀴가 기대한 방향과 반대로 돌면 `gpio_four_wheel_driver` 설정에서 해당 바퀴 sign을 바꿉니다.

```yaml
front_left_sign: -1.0
```

엔코더 방향이 반대면 `gpio_encoder_joint_state` 설정에서 해당 바퀴 sign을 바꿉니다.

```yaml
front_left_sign: -1.0
```

모터 sign과 엔코더 sign은 별개입니다. 모터는 앞으로 가는 명령의 실제 회전 방향을 맞추고, 엔코더는 앞으로 돌 때 position이 증가하도록 맞춥니다.

## 다음 단계

1. 핀 번호 체계를 확정합니다.
2. 모터드라이버 모델명을 확인합니다.
3. 바퀴별 jog 테스트로 motor sign을 보정합니다.
4. 엔코더 counts per revolution을 입력합니다.
5. `/cmd_vel -> /wheel_commands -> GPIO motor -> encoder -> /joint_states -> /wheel/odom` 루프를 확인합니다.
6. IMU 모델명과 I2C 주소를 기준으로 `/imu` driver를 붙입니다.
