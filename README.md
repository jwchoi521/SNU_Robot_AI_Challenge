# Robot Object Detector

YOLO 기반 로봇 AI 챌린지 객체 인식 프로젝트입니다. 카메라 추론은 객체 종류와 `bearing_deg`를 계산하고, 목표 물체까지의 거리는 적외선 센서를 통해 받을 수 있도록 `InfraredDistanceProvider` 인터페이스를 열어두었습니다. LiDAR는 추론 거리 측정이 아니라 지도 제작 용도로만 사용합니다.

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

## Distance Sensor

추론 결과의 `distance_m`은 LiDAR가 아니라 적외선 센서 provider에서 채웁니다. 기본 추론 스크립트는 센서가 연결되지 않은 상태를 가정하므로 `distance_m=None`을 출력하며, 추후 하드웨어 연동 시 `src/postprocess.py`의 `InfraredDistanceProvider`를 구현해 연결하면 됩니다.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt -r requirements-dev.txt
```

환경 확인:

```powershell
python scripts/check_env.py
python scripts/check_env.py --check-camera --camera-index 0
```

## Dataset

기본 데이터셋 설정은 `dataset/data.yaml`입니다.

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

데이터셋 확인:

```powershell
python scripts/check_dataset.py --data dataset/data.yaml
```

## Train

```powershell
python src/train.py --model yolov8n.pt --data dataset/data.yaml --epochs 100 --imgsz 640
```

## Validate

```powershell
python src/validate.py --model runs/detect/robot_yolo/weights/best.pt --data dataset/data.yaml
```

## Export TensorRT Engine

```powershell
python src/export_engine.py --model runs/detect/robot_yolo/weights/best.pt --imgsz 640 --half
```

## Camera Inference

```powershell
python src/infer_camera.py --model runs/detect/robot_yolo/weights/best.pt --camera-index 0 --display
```

JSONL 로그 저장:

```powershell
python src/infer_camera.py --model best.pt --save-jsonl outputs/infer.jsonl
```

## Quality Checks

```powershell
ruff check .
pytest
```
