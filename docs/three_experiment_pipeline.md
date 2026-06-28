# Three Quick Experiments

This file describes three small experiments for checking the shape detector and
two fruit-classifier training strategies.

## Inputs

Expected local or Colab paths:

```text
models/shape_yolo_best.pt
dataset/data_shapes.yaml
dataset/images/
dataset/labels/
dataset/fruits360/
```

`dataset/fruits360` should be created from the Kaggle Fruits 360 source:

```powershell
python scripts/prepare_fruits360.py `
  --source-root /content/drive/MyDrive/robot_object_detector/fruits-360 `
  --output-root dataset/fruits360 `
  --clear
```

## Experiment 1: Shape YOLO On Fruit-Cube Images

Goal: check whether the trained shape detector still detects a cube as class
`0 = cube_any` after a fruit image is attached.

If you have real fruit-cube photos, put them here:

```text
dataset/fruit_cube_real/
  apple/
  orange/
  banana/
  pineapple/
  none/
```

Then run:

```powershell
python scripts/evaluate_shape_detector.py `
  --model models/shape_yolo_best.pt `
  --source dataset/fruit_cube_real `
  --expected-class-id 0 `
  --output runs/eval/exp1_shape_on_real.csv
```

If you do not have real photos yet, first create synthetic fruit-cube crops with
Experiment 3's synthesis step, then run:

```powershell
python scripts/evaluate_shape_detector.py `
  --model models/shape_yolo_best.pt `
  --source dataset/cube_fruits_synthetic/test `
  --expected-class-id 0 `
  --output runs/eval/exp1_shape_on_synthetic.csv
```

Read the printed `images_with_cube_any` rate. A high rate means YOLO still sees
fruit-attached cubes as cubes.

## Experiment 2: Fruits 360 Classifier On Cube Bboxes

Goal: train a classifier only on original Fruits 360 fruit images, then test
whether it can classify fruit from cube crops.

Train the raw Fruits 360 classifier:

```powershell
python src/train_fruit_classifier.py `
  --data-root dataset/fruits360 `
  --epochs 30 `
  --imgsz 100 `
  --batch 64 `
  --device cuda `
  --output runs/classify/fruits360_raw
```

Evaluate it on real full images by letting YOLO provide the cube bbox:

```powershell
python scripts/evaluate_cube_fruit_classifier.py `
  --model runs/classify/fruits360_raw/best.pt `
  --detector-model models/shape_yolo_best.pt `
  --source dataset/fruit_cube_real `
  --labels-from-parent `
  --output runs/eval/exp2_raw_fruits_on_real.csv
```

Or evaluate it on synthetic cube-crop images:

```powershell
python scripts/evaluate_cube_fruit_classifier.py `
  --model runs/classify/fruits360_raw/best.pt `
  --source dataset/cube_fruits_synthetic/test `
  --labels-from-parent `
  --output runs/eval/exp2_raw_fruits_on_synthetic.csv
```

If `accuracy` is poor here, it means original fruit-only photos do not transfer
well to cube bbox crops.

## Experiment 3: Synthetic Cube-Fruit Classifier

Goal: create synthetic cube crops by estimating a cube face and perspective
warping fruit images onto that face, then train/evaluate the classifier.

The automatic face estimate is only a fallback. For better data quality, first
manually annotate visible cube faces:

```powershell
python scripts/annotate_cube_faces.py `
  --data dataset/data_shapes.yaml `
  --output dataset/cube_face_annotations.json `
  --splits train val test `
  --display-scale 3
```

In the annotation window, click four corners for each visible face in a cube
crop. Every four clicks adds one face. Press `n` to save and move to the next
cube. A cube can have multiple visible faces.

When a cube has multiple annotated faces, synthesis picks a non-empty subset of
those faces for each output image. If more than one face is selected, every
selected face receives the same fruit class, but each face may use a different
source image from that class. Use `--sticker-face-mode all` to force every
annotated face to receive a sticker, or `--sticker-face-mode one` to force
exactly one face. `--max-sticker-faces` caps the number of selected faces; its
default is `2`.

To verify the saved face quads before generating training data:

```powershell
python scripts/synthesize_cube_fruit_dataset.py `
  --data dataset/data_shapes.yaml `
  --fruit-root dataset/fruits360 `
  --output-root dataset/cube_fruits_debug `
  --face-annotations dataset/cube_face_annotations.json `
  --per-cube-per-fruit 0 `
  --none-per-cube 0 `
  --debug-face-overlays `
  --debug-max-per-split 20 `
  --clear
```

Check:

```text
dataset/cube_fruits_debug/debug_faces/
```

Create the synthetic dataset:

```powershell
python scripts/synthesize_cube_fruit_dataset.py `
  --data dataset/data_shapes.yaml `
  --fruit-root dataset/fruits360 `
  --output-root dataset/cube_fruits_synthetic `
  --face-annotations dataset/cube_face_annotations.json `
  --output-split-mode random `
  --train-ratio 0.7 `
  --val-ratio 0.15 `
  --test-ratio 0.15 `
  --max-sticker-faces 2 `
  --per-cube-per-fruit 2 `
  --none-per-cube 2 `
  --clear
```

`--output-split-mode random` reshuffles all annotated cube crops into the
requested classifier split ratio. Without it, the synthetic dataset keeps the
original YOLO `train/val/test` split, which can make validation and test too
small.

The output is:

```text
dataset/cube_fruits_synthetic/
  train/apple/
  train/orange/
  train/banana/
  train/pineapple/
  train/none/
  val/...
  test/...
  metadata.csv
```

Train the synthetic cube-fruit classifier:

```powershell
python src/train_fruit_classifier.py `
  --data-root dataset/cube_fruits_synthetic `
  --epochs 30 `
  --imgsz 100 `
  --batch 64 `
  --device cuda `
  --output runs/classify/cube_fruits_synthetic
```

Evaluate on the synthetic test split:

```powershell
python scripts/evaluate_cube_fruit_classifier.py `
  --model runs/classify/cube_fruits_synthetic/best.pt `
  --source dataset/cube_fruits_synthetic/test `
  --labels-from-parent `
  --output runs/eval/exp3_synthetic_on_synthetic.csv
```

Evaluate on real full images, if available:

```powershell
python scripts/evaluate_cube_fruit_classifier.py `
  --model runs/classify/cube_fruits_synthetic/best.pt `
  --detector-model models/shape_yolo_best.pt `
  --source dataset/fruit_cube_real `
  --labels-from-parent `
  --output runs/eval/exp3_synthetic_on_real.csv
```

## What To Compare

For Experiment 1:

```text
images_with_cube_any rate
detections_by_class
```

For Experiments 2 and 3:

```text
accuracy
prediction_counts
runs/eval/*.csv
```

The most important comparison is:

```text
exp2_raw_fruits_on_real.csv
vs
exp3_synthetic_on_real.csv
```

If real fruit-cube photos are not available yet, use the synthetic test split
first, then repeat with real photos later.
