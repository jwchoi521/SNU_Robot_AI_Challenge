from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

IMAGE_SUFFIXES = {".bmp", ".jpg", ".jpeg", ".png", ".webp"}
NO_FRUIT_CLASS = "none"


def collect_images(source: Path) -> list[Path]:
    if source.is_file() and source.suffix.lower() in IMAGE_SUFFIXES:
        return [source]
    if source.is_file():
        return [
            Path(line.strip())
            for line in source.read_text().splitlines()
            if line.strip()
        ]
    if source.is_dir():
        return sorted(
            path
            for path in source.rglob("*")
            if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
        )
    raise FileNotFoundError(f"source not found: {source}")


def truth_from_parent(image_path: Path, class_names: Sequence[str]) -> str | None:
    parent = image_path.parent.name.lower()
    lookup = {class_name.lower(): class_name for class_name in class_names}
    return lookup.get(parent)


def _best_class(probabilities: dict[str, float]) -> tuple[str, float]:
    if not probabilities:
        return "", 0.0
    class_name, probability = max(probabilities.items(), key=lambda item: item[1])
    return class_name, probability


def _detect_cube_boxes(
    detector: Any,
    image_path: Path,
    cube_class_id: int,
    imgsz: int,
    conf: float,
    iou: float,
    device: str | None,
) -> list[tuple[float, float, float, float]]:
    result = detector.predict(
        str(image_path),
        imgsz=imgsz,
        conf=conf,
        iou=iou,
        device=device,
        verbose=False,
    )[0]
    boxes = getattr(result, "boxes", None)
    if boxes is None or len(boxes) == 0:
        return []

    xyxy = boxes.xyxy.cpu().numpy()
    cls = boxes.cls.cpu().numpy()
    confs = boxes.conf.cpu().numpy()
    cube_boxes = [
        (tuple(float(value) for value in box), float(confidence))
        for box, class_id, confidence in zip(xyxy, cls, confs)
        if int(class_id) == cube_class_id
    ]
    cube_boxes.sort(key=lambda item: item[1], reverse=True)
    return [box for box, _confidence in cube_boxes]


def _bbox_text(bbox: Sequence[float] | None) -> str:
    if bbox is None:
        return ""
    return " ".join(f"{value:.2f}" for value in bbox)


def evaluate_cube_fruit_classifier(args: argparse.Namespace) -> int:
    from ultralytics import YOLO

    from src.fruit_classifier import (
        crop_rgb,
        load_fruit_classifier,
        predict_fruit,
        read_image_rgb,
    )

    image_paths = collect_images(args.source)
    if not image_paths:
        raise ValueError(f"no images found in {args.source}")

    model, classes, image_size, checkpoint_threshold = load_fruit_classifier(
        args.model,
        device=args.device,
    )
    threshold = args.threshold if args.threshold is not None else checkpoint_threshold
    detector = YOLO(args.detector_model) if args.detector_model else None
    class_names_for_truth = tuple(classes) + (NO_FRUIT_CLASS,)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    prediction_counts: Counter[str] = Counter()
    truth_counts: Counter[str] = Counter()
    correct = 0
    labeled = 0
    rows = 0
    images_without_cube = 0

    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "image",
                "crop_index",
                "bbox_xyxy",
                "truth",
                "prediction",
                "best_class",
                "best_probability",
                "confidence",
                "correct",
                "probabilities_json",
                "error",
            ],
        )
        writer.writeheader()

        for image_path in image_paths:
            truth = (
                truth_from_parent(image_path, class_names_for_truth)
                if args.labels_from_parent
                else None
            )
            if truth is not None:
                truth_counts[truth] += 1

            image_rgb = read_image_rgb(image_path)
            if detector is not None:
                crop_boxes = _detect_cube_boxes(
                    detector=detector,
                    image_path=image_path,
                    cube_class_id=args.cube_class_id,
                    imgsz=args.imgsz,
                    conf=args.detector_conf,
                    iou=args.detector_iou,
                    device=args.device,
                )
                if args.max_crops:
                    crop_boxes = crop_boxes[: args.max_crops]
            elif args.bbox is not None:
                crop_boxes = [tuple(args.bbox)]
            else:
                height, width = image_rgb.shape[:2]
                crop_boxes = [(0.0, 0.0, float(width), float(height))]

            if not crop_boxes:
                images_without_cube += 1
                writer.writerow(
                    {
                        "image": str(image_path),
                        "crop_index": "",
                        "bbox_xyxy": "",
                        "truth": truth or "",
                        "prediction": "",
                        "best_class": "",
                        "best_probability": "",
                        "confidence": "",
                        "correct": "",
                        "probabilities_json": "{}",
                        "error": "no_cube_detection",
                    }
                )
                continue

            for crop_index, bbox in enumerate(crop_boxes):
                crop = crop_rgb(image_rgb, bbox)
                prediction = predict_fruit(
                    model=model,
                    image_rgb=crop,
                    classes=classes,
                    image_size=image_size,
                    threshold=threshold,
                    device=args.device,
                )
                best_class, best_probability = _best_class(prediction.probabilities)
                predicted_label = prediction.fruit_kind or NO_FRUIT_CLASS
                prediction_counts[predicted_label] += 1
                is_correct = truth is not None and predicted_label == truth
                if truth is not None:
                    labeled += 1
                    correct += int(is_correct)
                rows += 1
                writer.writerow(
                    {
                        "image": str(image_path),
                        "crop_index": crop_index,
                        "bbox_xyxy": _bbox_text(bbox),
                        "truth": truth or "",
                        "prediction": predicted_label,
                        "best_class": best_class,
                        "best_probability": round(best_probability, 6),
                        "confidence": round(prediction.confidence, 6),
                        "correct": is_correct if truth is not None else "",
                        "probabilities_json": json.dumps(prediction.probabilities),
                        "error": "",
                    }
                )

    print(f"images={len(image_paths)}")
    print(f"crops_classified={rows}")
    print(f"images_without_cube_detection={images_without_cube}")
    if labeled:
        print(f"accuracy={correct / labeled:.4f} correct={correct}/{labeled}")
    print("prediction_counts:")
    for class_name, count in sorted(prediction_counts.items()):
        print(f"  {class_name}: {count}")
    if truth_counts:
        print("truth_counts:")
        for class_name, count in sorted(truth_counts.items()):
            print(f"  {class_name}: {count}")
    print(f"csv={args.output}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Evaluate a fruit classifier on cube crops or detected cubes.",
    )
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("runs/eval/cube_fruit_classifier.csv"),
    )
    parser.add_argument("--detector-model", type=Path, default=None)
    parser.add_argument("--cube-class-id", type=int, default=0)
    parser.add_argument("--bbox", type=float, nargs=4, default=None)
    parser.add_argument("--labels-from-parent", action="store_true")
    parser.add_argument("--threshold", type=float, default=None)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--detector-conf", type=float, default=0.25)
    parser.add_argument("--detector-iou", type=float, default=0.7)
    parser.add_argument("--max-crops", type=int, default=1)
    parser.add_argument("--device", default=None)
    return parser


def main() -> int:
    return evaluate_cube_fruit_classifier(build_parser().parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
