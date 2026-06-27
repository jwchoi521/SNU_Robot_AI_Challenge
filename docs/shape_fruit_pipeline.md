# Shape Detector + Fruit Classifier Pipeline

This pipeline trains two separate models:

1. A YOLO11n shape detector trained from scratch with class ids `0..3`.
2. A 4-class fruit classifier for cube crops: `apple`, `orange`, `banana`,
   `pineapple`. At inference time, if the highest softmax probability is below
   the threshold, the cube is treated as having no fruit.

## Shape Detector

Use the shape-only data config:

```powershell
python scripts/check_dataset.py --data dataset/data_shapes.yaml --profile shape4 --require-non-empty --strict
python src/train.py --from-scratch --model yolo11n.pt --data dataset/data_shapes.yaml --epochs 100 --imgsz 640 --name shape_yolo
python src/validate.py --model runs/detect/shape_yolo/weights/best.pt --data dataset/data_shapes.yaml --split val
```

`--from-scratch` converts `yolo11n.pt` to the matching architecture config
`yolo11n.yaml`, so the detector does not start from pretrained weights.

## Fruits 360 Classifier Dataset

Prepare a filtered Fruits 360 dataset:

```powershell
python scripts/prepare_fruits360.py --source-root C:\path\to\fruits-360 --output-root dataset/fruits360 --clear
```

The script reads the usual Fruits 360 `Training` and `Test` folders, keeps only
class folders whose names match apple, orange, banana, or pineapple, and writes:

```text
dataset/fruits360/
  train/apple/
  train/orange/
  train/banana/
  train/pineapple/
  val/...
  test/...
```

## Fruit Classifier Training

Train the classifier:

```powershell
python src/train_fruit_classifier.py --data-root dataset/fruits360 --epochs 30 --imgsz 100 --output runs/classify/fruits360
```

The final layer outputs four logits in this order:

```text
0 apple
1 orange
2 banana
3 pineapple
```

The best checkpoint is saved to:

```text
runs/classify/fruits360/best.pt
```

## Cube Crop Inference

Run the classifier on a full image or on a cube bbox crop:

```powershell
python src/infer_fruit_classifier.py --model runs/classify/fruits360/best.pt --image sample.jpg --bbox 120 80 260 220 --threshold 0.7
```

Output is JSON. `fruit_kind` is `null` when no fruit probability reaches the
threshold.
