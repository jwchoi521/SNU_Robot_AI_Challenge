# Robot Object Detector

YOLO 기반 로봇 AI 챌린지 객체 인식 프로젝트입니다. 전체 흐름은 카메라 이미지 수집, 외부 라벨링 도구를 이용한 YOLO 라벨 생성, train/val/test 분할, 학습, 검증, 추론 순서입니다.

카메라 추론은 객체 종류와 `bearing_deg`를 계산합니다. 목표 물체까지의 거리는 LiDAR가 아니라 적외선 센서를 통해 받을 수 있도록 `InfraredDistanceProvider` 인터페이스를 열어두었습니다. LiDAR는 추론 거리 측정이 아니라 지도 제작 용도로만 사용합니다.

## Classes

Detection 클래스는 아래 8개로 고정합니다.

| id | name |
| --- | --- |
| 0 | cube_any |
| 1 | octahedron |
| 2 | dodecahedron |
| 3 | icosahedron |
| 4 | apple_sticker |
| 5 | orange_sticker |
| 6 | banana_sticker |
| 7 | pineapple_sticker |

`cube_any`만 보이면 `unknown_cube`로 처리하며 `pick_allowed=False`입니다. 과일 객체는 `cube_any`와 fruit sticker가 같은 물체로 연결되어 있을 때만 `set2_fruit`로 처리합니다. `target_confirmed`는 여러 프레임에서 반복 확인된 뒤에만 `True`가 됩니다.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt -r requirements-dev.txt
```

환경과 카메라 확인:

```powershell
python scripts/check_env.py
python scripts/check_env.py --check-camera --camera-index 0
```

Jetson Orin Nano에서 GPU와 카메라까지 확인할 때는 프로젝트 폴더에서 아래처럼 실행합니다.

```bash
source .venv/bin/activate
python scripts/check_env.py --require-cuda --check-camera --camera-index 0
```

현재 검증된 Jetson 핵심 패키지 조합은 아래와 같습니다.

| package | version |
| --- | --- |
| torch | 2.8.0, CUDA 12.6 |
| torchvision | 0.23.0 |
| numpy | 1.26.4 |
| matplotlib | 3.10.9 |
| opencv | 4.10.0.84 |
| ultralytics | 8.4.75 |
| tqdm | 4.68.3 |

## Pipeline

1. 카메라 원본 이미지 수집

```powershell
python scripts/collect_camera.py --camera-index 0 --display --max-images 200
```

기본 저장 위치는 `dataset/raw/<session>/`입니다. `--interval-sec`로 자동 저장 간격을 조정할 수 있고, `--display` 모드에서는 `space` 또는 `s`로 추가 저장, `q`로 종료할 수 있습니다.

2. 라벨링

`dataset/raw/<session>/`의 이미지를 CVAT, Label Studio, labelImg 같은 도구로 라벨링한 뒤 YOLO 형식으로 export합니다. 권장 작업 폴더는 아래와 같습니다.

```text
dataset/labeled/
  images/
    sample_000001.jpg
  labels/
    sample_000001.txt
```

YOLO label 파일은 `class_id x_center y_center width height` 형식이고 좌표는 0..1 정규화 값이어야 합니다.

3. train/val/test 분할

```powershell
python scripts/split_dataset.py --source-images dataset/labeled/images --clear
```

이 명령은 기본적으로 `dataset/labeled/labels`를 라벨 폴더로 사용하고, 결과를 아래 구조로 복사합니다.

```text
dataset/
  data.yaml
  images/
    train/
    val/
    test/
  labels/
    train/
    val/
    test/
```

4. 데이터셋 검증

```powershell
python scripts/check_dataset.py --data dataset/data.yaml --require-non-empty --strict
```

5. 학습

```powershell
python src/train.py --model yolov8n.pt --data dataset/data.yaml --epochs 100 --imgsz 640
```

6. 검증

```powershell
python src/validate.py --model runs/detect/robot_yolo/weights/best.pt --data dataset/data.yaml
```

7. 추론

```powershell
python src/infer_camera.py --model runs/detect/robot_yolo/weights/best.pt --camera-index 0 --display
```

JSONL 로그 저장:

```powershell
python src/infer_camera.py --model runs/detect/robot_yolo/weights/best.pt --save-jsonl outputs/infer.jsonl
```

## Export TensorRT Engine

```powershell
python src/export_engine.py --model runs/detect/robot_yolo/weights/best.pt --imgsz 640 --half
```

## Distance Sensor

추론 결과의 `distance_m`은 LiDAR가 아니라 적외선 센서 provider에서 채웁니다. 기본 추론 스크립트는 센서가 연결되지 않은 상태를 가정하므로 `distance_m=None`을 출력하며, 추후 하드웨어 연동 시 `src/postprocess.py`의 `InfraredDistanceProvider`를 구현해 연결하면 됩니다.

## Quality Checks

```powershell
ruff check .
pytest
```
