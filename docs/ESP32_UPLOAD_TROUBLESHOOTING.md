# ESP32 업로드 문제 해결

## `ledcSetup` 또는 `ledcAttachPin` 컴파일 에러

에러 예시:

```text
error: 'ledcSetup' was not declared in this scope
error: 'ledcAttachPin' was not declared in this scope
```

원인:

- Arduino IDE의 `esp32 by Espressif Systems` 보드 패키지가 3.x 버전이면 예전 LEDC API가 제거되어 발생합니다.
- ESP32 Arduino core 3.x에서는 `ledcSetup`과 `ledcAttachPin` 대신 `ledcAttach(pin, freq, resolution)`와 `ledcWrite(pin, duty)`를 사용해야 합니다.

해결:

- `firmware/esp32_motor_bridge/esp32_motor_bridge.ino` 최신 버전을 다시 받아 업로드합니다.
- GitHub `slam` 브랜치 기준 최신 펌웨어는 Arduino ESP32 core 3.x API에 맞춰져 있습니다.

## Serial Monitor에 깨진 문자가 반복되는 경우

정상 출력:

```text
READY esp32_motor_bridge
E 0 0 0 0
E 0 0 0 0
```

깨진 문자가 반복되면 아래를 확인합니다.

- Serial Monitor baud rate가 `115200`인지 확인
- `/dev/ttyUSB0`가 ESP32 포트인지 확인
- ESP32에 `esp32_motor_bridge.ino`가 업로드됐는지 확인
- 모터드라이버 연결이 ESP32 부팅 핀을 방해하지 않는지 확인

특히 `GPIO2`, `GPIO4`, `GPIO5`, `GPIO15`는 ESP32 부팅 상태에 영향을 줄 수 있으므로, 업로드/부팅이 불안정하면 모터드라이버 입력선을 잠깐 분리하고 USB만 연결해 확인합니다.
