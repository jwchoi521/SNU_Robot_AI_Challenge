# Robot Object Detector

YOLO 기반 로봇 AI 챌린지 객체 인식 프로젝트입니다. 카메라 추론은 객체 종류와 `bearing_deg`를 계산하고, LiDAR 거리는 추후 같은 bearing 기준으로 매칭할 수 있도록 `BearingDistanceProvider` 인터페이스를 열어두었습니다.

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
