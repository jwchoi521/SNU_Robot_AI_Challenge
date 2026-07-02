# ㄷ자 로봇 SLAM/주행 좌표 추정 + 앞문 제어 가이드

이 폴더는 기존 그리퍼 전략이 아니라 **ㄷ자 몸체로 물체를 가두어 운반하는 전략**을 기준으로 작성했습니다.

핵심 흐름은 아래 순서입니다.

1. ArUco 마커를 바닥에 출력/부착하고, 마커의 중심 좌표를 LiDAR 좌표계로 측정합니다.
2. 카메라 이미지의 ArUco 위치와 LiDAR 기준 마커 좌표로 `image pixel -> x_lidar_m, y_lidar_m` homography를 계산합니다.
3. YOLO bbox의 `bbox_bottom_center`를 homography에 넣어 물체의 `x_lidar_m, y_lidar_m`를 1차 추정합니다.
4. 실험 데이터로 residual model을 학습해 `x_lidar, y_lidar` 오차를 보정합니다.
5. Jetson은 보정된 물체 좌표로 접근/정렬을 판단하고, ESP32는 모터/IMU/IR 센서/앞문 서보를 제어합니다.

## 파일 역할

| 파일 | 실행 위치 | 역할 |
| --- | --- | --- |
| `object_lidar_localizer.py` | Jetson, PC | ArUco 생성, homography 계산, bbox 좌표 추정, YOLO JSONL 후처리 |
| `train_residual_model.py` | Colab 권장, PC 가능 | residual learning 모델 학습 |
| `colab/train_residual_colab.py` | Colab | 기본 경로로 residual 학습을 바로 실행하는 진입점 |
| `config/recommended_marker_layout.csv` | Jetson, PC | 권장 ArUco 마커 배치표 |
| `data/residual_samples_template.csv` | PC, Colab | residual 학습 데이터 CSV 템플릿 |
| `esp32_u_shape_robot/esp32_u_shape_robot.ino` | ESP32 | 모터, BNO085 IMU, MG996R 앞문, IR 브레이크 빔 제어 |
| `requirements.txt` | Jetson, Colab | Python 의존성 |

## 좌표계

이 코드의 LiDAR 좌표계는 다음처럼 고정합니다.

| 값 | 의미 |
| --- | --- |
| `x_lidar_m` | LiDAR 중심에서 로봇 정면 방향, meter |
| `y_lidar_m` | LiDAR 중심에서 로봇 왼쪽 방향, meter |
| `bbox_bottom_center` | bbox의 아래쪽 중앙 픽셀. 물체가 바닥에 닿는 점으로 근사합니다. |

카메라와 LiDAR가 로봇에 단단히 고정되어 있어야 합니다. 카메라 각도, 높이, LiDAR 위치가 바뀌면 homography와 residual model을 다시 만들어야 합니다.

## 1. Jetson/PC 설치

Jetson에서는 먼저 기존 환경을 쓰되, ArUco가 되는 OpenCV인지 확인합니다.

```bash
cd ~/AI_robot_challenge
python3 -m pip install -r u_shape_robot_slam/requirements.txt
python3 - <<'PY'
import cv2
print("opencv", cv2.__version__, "aruco", hasattr(cv2, "aruco"))
PY
```

`aruco False`가 나오면 `opencv-contrib-python`이 필요합니다. Jetson OpenCV 충돌이 생기면 기존 `python3-opencv`와 pip OpenCV가 섞였는지 확인하세요.

## 2. ArUco 마커 생성 및 부착

외부 이미지를 다운로드하지 않고, OpenCV로 직접 생성합니다. 이렇게 하면 marker ID, dictionary, 실제 출력 크기를 코드와 CSV에서 항상 일치시킬 수 있습니다.

```bash
python3 u_shape_robot_slam/object_lidar_localizer.py generate-markers \
  --output-dir u_shape_robot_slam/generated_markers \
  --dictionary DICT_4X4_50 \
  --ids 10,11,12,13,14,15 \
  --marker-size-mm 80
```

출력물:

| 출력 | 설명 |
| --- | --- |
| `generated_markers/aruco_DICT_4X4_50_010_80mm.png` 등 | 출력해서 사용할 마커 이미지 |
| `generated_markers/recommended_marker_layout.csv` | 권장 배치표 |
| `generated_markers/print_manifest.json` | 생성 설정 기록 |

### 권장 부착 위치

마커는 **바닥에 평평하게** 붙입니다. 중심점 기준 좌표를 LiDAR 원점에서 줄자로 재세요.

| marker_id | x_lidar_m | y_lidar_m | 위치 설명 |
| ---: | ---: | ---: | --- |
| 10 | 0.40 | -0.45 | 로봇 정면 40 cm, 오른쪽 45 cm |
| 11 | 0.40 | 0.45 | 로봇 정면 40 cm, 왼쪽 45 cm |
| 12 | 0.80 | -0.55 | 로봇 정면 80 cm, 오른쪽 55 cm |
| 13 | 0.80 | 0.55 | 로봇 정면 80 cm, 왼쪽 55 cm |
| 14 | 1.20 | -0.65 | 로봇 정면 120 cm, 오른쪽 65 cm |
| 15 | 1.20 | 0.65 | 로봇 정면 120 cm, 왼쪽 65 cm |

최소 4개 이상, 한 직선 위가 아닌 마커가 보여야 합니다. 카메라 화각이 좁으면 `config/recommended_marker_layout.csv`의 좌표를 실제 보이는 위치로 수정하고, 수정한 좌표를 그대로 calibration에 사용하세요.

## 3. Homography 계산

1. 로봇을 calibration 위치에 세우고, 위 마커들이 보이게 카메라 이미지를 한 장 저장합니다.
2. `config/recommended_marker_layout.csv`가 실제 측정 좌표와 일치하는지 수정합니다.
3. 아래 명령을 실행합니다.

```bash
python3 u_shape_robot_slam/object_lidar_localizer.py calibrate-homography \
  --image u_shape_robot_slam/data/aruco_calibration.jpg \
  --layout u_shape_robot_slam/config/recommended_marker_layout.csv \
  --output u_shape_robot_slam/calibration/homography_lidar.json \
  --dictionary DICT_4X4_50 \
  --point-mode center \
  --preview u_shape_robot_slam/calibration/homography_preview.jpg
```

입력:

| 입력 | 설명 |
| --- | --- |
| `--image` | ArUco 마커가 보이는 카메라 이미지 |
| `--layout` | `marker_id,x_lidar_m,y_lidar_m`가 들어 있는 CSV |
| `--point-mode center` | 마커 중심점으로 homography 계산. 실험 초반 추천 |

출력:

| 출력 | 설명 |
| --- | --- |
| `homography_lidar.json` | Jetson 실시간 추론에 사용할 calibration 파일 |
| `homography_preview.jpg` | 검출된 마커와 reprojection error 확인 이미지 |
| `reprojection_rmse_m` | 마커 재투영 오차. 처음 목표는 0.02~0.04 m 이하 |

오차가 크면 마커 중심 좌표 측정, 마커가 말려 있는지, 카메라 흔들림, 해상도 변경 여부를 먼저 확인하세요.

## 4. bbox CSV에 LiDAR 좌표 붙이기

YOLO bbox CSV가 아래 열을 가지면 바로 처리됩니다.

| 열 | 설명 |
| --- | --- |
| `image_width`, `image_height` | bbox가 나온 이미지 크기 |
| `x_center`, `y_center`, `width`, `height` | YOLO 형식이면 0~1 정규화 값, pixel 값도 자동 판별 |

실행:

```bash
python3 u_shape_robot_slam/object_lidar_localizer.py estimate-csv \
  --input u_shape_robot_slam/data/detections.csv \
  --calibration u_shape_robot_slam/calibration/homography_lidar.json \
  --output u_shape_robot_slam/data/detections_with_lidar.csv
```

residual model까지 적용:

```bash
python3 u_shape_robot_slam/object_lidar_localizer.py estimate-csv \
  --input u_shape_robot_slam/data/detections.csv \
  --calibration u_shape_robot_slam/calibration/homography_lidar.json \
  --residual-model u_shape_robot_slam/models/residual_lidar_corrector.joblib \
  --output u_shape_robot_slam/data/detections_with_lidar_corrected.csv
```

추가되는 출력 열:

| 열 | 설명 |
| --- | --- |
| `bbox_bottom_center_x_px`, `bbox_bottom_center_y_px` | homography에 넣은 픽셀 좌표 |
| `x_lidar_homography_m`, `y_lidar_homography_m` | homography만 사용한 좌표 |
| `x_lidar_residual_dx_m`, `y_lidar_residual_dy_m` | residual model이 예측한 보정량 |
| `x_lidar_m`, `y_lidar_m` | 최종 보정 좌표 |
| `position_source` | `homography` 또는 `homography_residual` |

## 5. residual learning 데이터 수집

템플릿:

```text
u_shape_robot_slam/data/residual_samples_template.csv
```

실제 학습 파일은 아래 이름으로 복사해서 채우세요.

```text
u_shape_robot_slam/data/residual_samples.csv
```

필수 열:

| 열 | 의미 |
| --- | --- |
| `frame_id` | 이미지/프레임 식별자 |
| `object_id` | 같은 프레임 내 물체 식별자 |
| `class_name` | `cube_any`, `octahedron` 등 |
| `image_width`, `image_height` | bbox 이미지 크기 |
| `x_center`, `y_center`, `width`, `height` | bbox 전체 파라미터. YOLO 정규화 권장 |
| `x_lidar_gt_m`, `y_lidar_gt_m` | 줄자, LiDAR, 바닥 기준 측정으로 얻은 실제 좌표 |
| `notes` | 조명, 물체 종류, 특이사항 |

권장 수집량:

| 조건 | 권장 |
| --- | --- |
| 최소 테스트 | 30개 이상 |
| 실제 residual 학습 | 100~200개 이상 |
| 좌표 범위 | x=0.25~1.80 m, y=-0.70~0.70 m |
| 샘플 분포 | 중앙/좌/우, 가까움/중간/먼 거리, 여러 조명, 여러 물체 |

중요한 점은 `x_lidar_gt_m, y_lidar_gt_m`가 **bbox bottom-center가 나타내는 실제 바닥 접점**의 좌표여야 한다는 것입니다.

## 6. Colab에서 residual model 학습

Colab에 프로젝트 폴더를 Drive로 올린 뒤 아래 셀을 순서대로 실행합니다.

```python
from google.colab import drive
drive.mount('/content/drive')
```

```python
%cd /content/drive/MyDrive/AI_robot_challenge
!pip install -q -r u_shape_robot_slam/requirements.txt
```

```python
!python u_shape_robot_slam/train_residual_model.py \
  --data u_shape_robot_slam/data/residual_samples.csv \
  --calibration u_shape_robot_slam/calibration/homography_lidar.json \
  --output-model u_shape_robot_slam/models/residual_lidar_corrector.joblib \
  --metrics-json u_shape_robot_slam/models/residual_metrics.json \
  --predictions-csv u_shape_robot_slam/models/residual_predictions.csv \
  --model random_forest \
  --n-estimators 500 \
  --min-samples-leaf 2
```

학습 후 확인할 파일:

| 파일 | 설명 |
| --- | --- |
| `models/residual_lidar_corrector.joblib` | Jetson으로 옮길 residual model |
| `models/residual_metrics.json` | homography 대비 보정 성능 |
| `models/residual_predictions.csv` | 각 샘플별 보정 전/후 오차 |

`test.corrected_rmse_cm`가 `test.homography_rmse_cm`보다 작아야 합니다. test 오차가 더 커지면 데이터 수가 부족하거나, GT 좌표 측정이 흔들렸거나, calibration과 실제 카메라 위치가 달라졌을 가능성이 큽니다.

## 7. Jetson 실시간 YOLO와 연결

기존 YOLO 스크립트가 JSONL을 출력하므로, 파이프로 좌표를 붙일 수 있습니다.

```bash
python3 SNU_Robot_AI_Challenge-codex-yolo/src/jetson_realtime_yolo.py \
  --model SNU_Robot_AI_Challenge-codex-yolo/runs/detect/robot_yolo/weights/best.pt \
  --camera csi \
  --raw-detections \
  --capture-width 1280 \
  --capture-height 720 \
| python3 u_shape_robot_slam/object_lidar_localizer.py live-yolo-jsonl \
  --calibration u_shape_robot_slam/calibration/homography_lidar.json \
  --residual-model u_shape_robot_slam/models/residual_lidar_corrector.joblib \
  --image-width 1280 \
  --image-height 720
```

각 detection/target에 아래 필드가 붙습니다.

```json
"lidar_position_m": {
  "x": 0.8421,
  "y": -0.1152,
  "source": "homography_residual",
  "x_homography": 0.8610,
  "y_homography": -0.0924,
  "dx_residual": -0.0189,
  "dy_residual": -0.0228
}
```

주행 알고리즘에서는 보통 `x`가 전방 거리, `y`가 좌우 정렬 오차입니다.

예시 제어 판단:

| 조건 | 동작 |
| --- | --- |
| `abs(y) > 0.08` | y가 0에 가까워지도록 회전 또는 좌우 보정 |
| `x > 0.35` | 천천히 전진 |
| `0.18 <= x <= 0.35` and `abs(y) <= 0.08` | `GATE OPEN` 후 낮은 PWM으로 물체를 ㄷ자 몸체 안으로 유도 |
| ESP32 `EVENT CARGO_ENTRY` 수신 | 정지, 앞문 자동 닫힘 확인 |
| `cargoCount >= targetCapacity` | 보관함으로 이동 |

## 8. ESP32 업로드 및 핀

업로드할 파일:

```text
u_shape_robot_slam/esp32_u_shape_robot/esp32_u_shape_robot.ino
```

Arduino IDE 라이브러리:

| 라이브러리 | 용도 |
| --- | --- |
| `Adafruit BNO08x` | BNO085 IMU |
| `Adafruit BusIO` | BNO085 의존성 |

핀 연결:

| 장치 | ESP32 GPIO |
| --- | --- |
| FL motor A/B | 23 / 25 |
| FR motor A/B | 4 / 5 |
| BL motor A/B | 2 / 15 |
| BR motor A/B | 14 / 13 |
| BNO085 SDA/SCL | 21 / 22 |
| MG996R 왼쪽 앞문 servo signal | 33 |
| MG996R 오른쪽 앞문 servo signal | 12 |
| DFRobot IR break beam OUT | 35 |

MG996R은 전류를 많이 먹습니다. 서보 전원은 ESP32 3.3V에서 직접 빼지 말고, 별도 5~6V 전원을 쓰되 GND는 ESP32와 공통으로 묶으세요.

### ESP32 주요 명령

| 명령 | 의미 |
| --- | --- |
| `GATE OPEN` | 앞문 열기 |
| `GATE CLOSE` | 앞문 닫기 |
| `CARGO?` | 적재 개수, 목표 개수, IR 상태, 문 상태 출력 |
| `CARGO RESET` | 적재 개수 0으로 초기화 |
| `BATCH 0` | 첫 운반: 목표 3개, count reset |
| `BATCH 1` | 두 번째 운반: 목표 2개, count reset |
| `BATCH 2` | 세 번째 운반: 목표 2개, count reset |
| `CAPACITY 1..3` | 임시 목표 개수 변경 |
| `AUTO_GATE ON/OFF` | IR 감지 후 자동 닫힘 켜기/끄기 |
| `UNLOAD` | 보관함에서 문 열고 count reset |

IR 빔이 끊기면 ESP32가 다음 이벤트를 보냅니다.

```text
EVENT CARGO_ENTRY count=1 target=3
OK GATE CLOSE
```

IR 센서는 **입구 바로 뒤쪽**에 설치하는 것을 권장합니다. 수납 공간 한가운데에 설치해서 물체가 빔을 계속 가리면 두 번째, 세 번째 물체 카운트가 어려워집니다.

## 9. 3-2-2 운반 전략

현재 전략은 보관함까지 `3개 -> 2개 -> 2개`로 운반하는 것입니다.

권장 상태 흐름:

1. 경기 시작 또는 첫 수집 전에 Jetson이 ESP32에 `BATCH 0` 전송.
2. 목표 물체 앞에서 정렬되면 `GATE OPEN`.
3. 낮은 PWM으로 접근해 물체가 ㄷ자 몸체 안으로 들어오게 함.
4. IR이 `EVENT CARGO_ENTRY`를 보내면 Jetson은 정지하고 `CARGO?`로 상태 확인.
5. count가 target보다 작으면 다음 물체로 이동해서 다시 `GATE OPEN`.
6. count가 target에 도달하면 보관함으로 이동.
7. 보관함 앞에서 `UNLOAD`, 필요한 배출 동작 수행, 다음 운반은 `BATCH 1`, 그다음은 `BATCH 2`.

이 전략에서는 그리퍼 관련 판단, pick pose, grasp close/open 동작을 사용하지 않습니다.

## 10. 조절해야 할 파라미터

| 위치 | 파라미터 | 기본값 | 조절 기준 |
| --- | --- | ---: | --- |
| `config/recommended_marker_layout.csv` | `x_lidar_m`, `y_lidar_m` | 표 참고 | 실제 줄자 측정값으로 반드시 수정 |
| homography CLI | `--ransac-threshold-m` | 0.035 | 마커 측정 오차가 크면 약간 증가 |
| marker generation | `--marker-size-mm` | 80 | 멀리서 검출이 불안정하면 100~120 mm |
| residual training | `--min-samples-leaf` | 2 | 데이터가 적고 overfit이면 3~5 |
| residual training | `--n-estimators` | 500 | Colab 시간 여유가 있으면 800~1000 |
| ESP32 sketch | `LEFT_GATE_*_DEG`, `RIGHT_GATE_*_DEG` | 코드 상수 | 실제 앞문이 열리고 닫히는 각도로 튜닝 |
| ESP32 sketch | `ENTRY_CLOSE_DELAY_MS` | 250 ms | 문이 너무 빨리 닫히면 증가 |
| ESP32 sketch | `IR_ACTIVE_LOW` | true | 센서 출력 논리가 반대면 false |

## 11. Jetson과 ESP32에 옮길 것

Jetson Orin Nano:

```text
u_shape_robot_slam/object_lidar_localizer.py
u_shape_robot_slam/requirements.txt
u_shape_robot_slam/calibration/homography_lidar.json
u_shape_robot_slam/models/residual_lidar_corrector.joblib
SNU_Robot_AI_Challenge-codex-yolo/src/jetson_realtime_yolo.py
YOLO best.pt 또는 TensorRT engine
```

ESP32:

```text
u_shape_robot_slam/esp32_u_shape_robot/esp32_u_shape_robot.ino
```

Colab:

```text
u_shape_robot_slam/train_residual_model.py
u_shape_robot_slam/object_lidar_localizer.py
u_shape_robot_slam/data/residual_samples.csv
u_shape_robot_slam/calibration/homography_lidar.json
```

## 12. 실험 체크리스트

| 단계 | 성공 기준 |
| --- | --- |
| ArUco 생성 | 10~15번 마커 PNG가 생성됨 |
| ArUco 부착 | 카메라 이미지에서 최소 4개 이상 검출됨 |
| Homography | `reprojection_rmse_m`가 0.02~0.04 m 근처 |
| bbox 추정 | 중앙 물체의 `y_lidar_m`가 0 근처 |
| residual 학습 | test corrected RMSE가 homography RMSE보다 작음 |
| ESP32 앞문 | `GATE OPEN/CLOSE`가 양쪽 문을 반대 방향으로 정상 구동 |
| IR 카운트 | 물체 1개 진입마다 `EVENT CARGO_ENTRY`가 1회만 발생 |
| 3-2-2 전략 | `BATCH 0/1/2`에서 목표 count가 3/2/2로 바뀜 |

