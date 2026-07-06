# BBox Pose Mapping

카메라 YOLO bounding box를 LiDAR 기준 2D 좌표로 변환하기 위한 보정 도구입니다.

현재 모델 구조는 2단계입니다.

```text
bbox 아래쪽 기준점
-> homography로 1차 LiDAR 기준 x,y 추정
-> bbox 전체 특징으로 RandomForest residual 보정
-> 최종 x,y 출력
```

코드 컬럼명은 `x_robot`, `y_robot`이지만 이 프로젝트에서는 LiDAR 기준 좌표로 사용합니다.

## 입력 데이터

### ground-data

물체 없이 바닥 기준점/마커를 찍어서 만든 데이터입니다.

```csv
anchor_x,anchor_y,x_robot,y_robot
320,345,1.20,0.00
280,342,1.15,-0.20
360,338,1.18,0.20
```

- `anchor_x`, `anchor_y`: 이미지에서 바닥 기준점의 픽셀 좌표
- `x_robot`, `y_robot`: 그 기준점의 LiDAR 기준 실제 좌표

최소 4개가 필요하고, 한 직선 위에만 있으면 안 됩니다. 추천 수량은 30~80개입니다.

### object-data

실제 물체 detection bbox와 LiDAR 기준 실제 위치를 기록한 데이터입니다.

```csv
bbox_cx,bbox_cy,bbox_w,bbox_h,object_type,x_robot,y_robot
322,241,100,135,bottle,1.22,0.02
280,245,95,130,bottle,1.30,-0.25
360,240,98,132,box,1.28,0.24
```

`x1,y1,x2,y2` 형태 bbox도 입력할 수 있습니다.

## 설치

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r tools/bbox_pose_mapping/requirements.txt
```

Windows PowerShell에서는:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r tools\bbox_pose_mapping\requirements.txt
```

## 학습

```bash
python tools/bbox_pose_mapping/bbox_pose_ml.py train \
  --ground-data ground.csv \
  --object-data objects.csv \
  --model bbox_pose_model.joblib \
  --anchor-alpha 0.5
```

`anchor-alpha`는 bbox 기준점 위치입니다.

```text
anchor_x = bbox_cx
anchor_y = bbox_cy + anchor_alpha * bbox_h
```

기본값 `0.5`는 bbox 아래쪽 중앙점입니다. 실제 물체 접지점이 bbox 아래쪽보다 조금 위로 잡히면 `0.35~0.45`도 테스트합니다.

## 예측

```bash
python tools/bbox_pose_mapping/bbox_pose_ml.py predict \
  --model bbox_pose_model.joblib \
  --bbox-cx 322 \
  --bbox-cy 241 \
  --bbox-w 100 \
  --bbox-h 135 \
  --object-type bottle
```

출력 예:

```json
{
  "x_robot": 1.23,
  "y_robot": 0.02,
  "distance": 1.23,
  "angle": 0.9,
  "base_x": 1.21,
  "base_y": 0.01,
  "x_residual": 0.02,
  "y_residual": 0.01
}
```

## ROS 연동 방향

나중에 YOLO bridge에서 bbox를 받으면 이 모델의 예측 결과를 `/perception/objects` 또는 target pose projector 입력으로 넘기면 됩니다.

추천 흐름:

```text
camera image
-> YOLO bbox
-> bbox_pose_model predict
-> LiDAR/base frame object x,y
-> semantic object registry
-> target approach planner
```

실시간 ROS 노드로 붙일 때는 `joblib.load()`를 노드 시작 시 한 번만 호출하고, bbox callback마다 `predict` 함수의 내부 로직을 호출하도록 분리하면 됩니다.
