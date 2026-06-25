# ESP32 + Jetson Orin Nano 모터 직진 테스트

이 테스트는 Jetson Orin Nano에서 USB 시리얼로 ESP32에 명령을 보내고, ESP32가 4개 바퀴 모터를 동시에 돌려 직진을 확인하는 구조입니다.

## 파일 위치

- ESP32 업로드 코드: `esp32_motor_test/esp32_motor_test.ino`
- Jetson 실행 코드: `jetson_motor_test/motor_straight_test.py`

## 현재 핀 설정

`pin번호 연결.txt` 기준으로 아래 모터 드라이버 핀을 사용합니다.

| 바퀴 | ESP32 핀 A | ESP32 핀 B |
| --- | ---: | ---: |
| FL 앞 왼쪽 | 23 | 25 |
| FR 앞 오른쪽 | 4 | 5 |
| BL 뒤 왼쪽 | 2 | 15 |
| BR 뒤 오른쪽 | 14 | 13 |

각 모터는 A/B 중 한쪽에 PWM을 넣어 정방향/역방향을 만듭니다.

## 조절하면서 찾을 값

1. `--base`: 전체 기본 속도입니다. 0~255 범위이고 처음에는 `90~130` 정도로 낮게 시작하세요.
2. `--fl --fr --bl --br`: 각 바퀴별 속도 배율입니다. 예를 들어 오른쪽으로 휘면 왼쪽 바퀴가 빠르거나 오른쪽 바퀴가 느린 것이므로 `--fl`, `--bl`을 낮추거나 `--fr`, `--br`을 올립니다.
3. ESP32 코드의 `direction`: 바퀴가 반대로 돌면 해당 모터의 `direction` 값을 `1`에서 `-1`로 바꿔 다시 업로드합니다.
4. ESP32 코드의 `MIN_MOVING_PWM`: 낮은 PWM에서 모터가 안 움직이면 30, 40, 50처럼 올려봅니다.
5. ESP32 코드의 `RAMP_STEP`, `RAMP_DELAY_MS`: 출발이 너무 급하면 `RAMP_STEP`을 줄이거나 `RAMP_DELAY_MS`를 키웁니다.

## ESP32 업로드 순서

### Arduino IDE를 쓰는 경우

1. Arduino IDE에서 `esp32_motor_test/esp32_motor_test.ino`를 엽니다.
2. 보드 매니저에서 ESP32 보드 패키지를 설치합니다.
3. 보드는 사용하는 ESP32 보드에 맞게 선택합니다. 보통 `ESP32 Dev Module`이면 됩니다.
4. ESP32를 USB로 PC에 연결합니다.
5. 업로드합니다.
6. 업로드가 끝나면 ESP32를 Jetson Orin Nano에 USB로 연결합니다.

### arduino-cli를 쓰는 경우

```bash
arduino-cli core update-index
arduino-cli core install esp32:esp32
arduino-cli board list
arduino-cli compile --fqbn esp32:esp32:esp32 esp32_motor_test
arduino-cli upload -p /dev/ttyUSB0 --fqbn esp32:esp32:esp32 esp32_motor_test
```

포트가 `/dev/ttyACM0`로 잡히면 upload 명령의 `/dev/ttyUSB0`만 바꾸면 됩니다.

## Jetson Orin Nano 실행 순서

Jetson에서 이 프로젝트 폴더로 이동합니다.

```bash
cd ~/AI_robot_challenge
python3 -m pip install pyserial
ls /dev/ttyUSB* /dev/ttyACM*
```

ESP32가 `/dev/ttyUSB0`로 잡힌 경우:

```bash
python3 jetson_motor_test/motor_straight_test.py --port /dev/ttyUSB0 --base 100 --time 2
```

ESP32가 `/dev/ttyACM0`로 잡힌 경우:

```bash
python3 jetson_motor_test/motor_straight_test.py --port /dev/ttyACM0 --base 100 --time 2
```

실험하면서 값을 바꾸려면 인터랙티브 모드를 쓰세요.

```bash
python3 jetson_motor_test/motor_straight_test.py --port /dev/ttyUSB0 --base 110 --time 1.5 --interactive
```

프롬프트에서 그냥 Enter를 누르면 현재 값으로 한 번 직진 테스트를 합니다.

예시:

```text
fl 0.98
fr 1.03
bl 0.99
br 1.02
base 120
time 2
```

## 튜닝 방법

1. 로봇 바퀴가 바닥에 닿지 않게 들어 올린 상태에서 `--base 80 --time 1`로 먼저 테스트합니다.
2. 네 바퀴가 모두 같은 "앞 방향"으로 도는지 봅니다.
3. 반대로 도는 바퀴가 있으면 ESP32 코드의 해당 모터 `direction`을 `-1`로 바꿔 업로드합니다.
4. 바닥에 내려놓고 짧게 `--base 100 --time 1`을 실행합니다.
5. 오른쪽으로 휘면 왼쪽 배율(`fl`, `bl`)을 0.02씩 낮추거나 오른쪽 배율(`fr`, `br`)을 0.02씩 올립니다.
6. 왼쪽으로 휘면 오른쪽 배율(`fr`, `br`)을 낮추거나 왼쪽 배율(`fl`, `bl`)을 올립니다.
7. 어느 한쪽 앞/뒤 바퀴만 유독 빠르거나 느리면 그 바퀴 배율만 0.01~0.03씩 조절합니다.

추천 시작값:

```bash
python3 jetson_motor_test/motor_straight_test.py --port /dev/ttyUSB0 --base 110 --fl 1.00 --fr 1.00 --bl 1.00 --br 1.00 --time 1.5
```

## 주의

- 처음 테스트는 반드시 바퀴를 띄우고 낮은 PWM으로 하세요.
- 모터 전원과 ESP32 GND는 반드시 공통 GND로 연결되어 있어야 합니다.
- USB 권한 오류가 나면 Jetson에서 `sudo usermod -a -G dialout $USER` 실행 후 로그아웃/로그인하거나, 임시로 `sudo`를 붙여 실행하세요.
