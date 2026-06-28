from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any


IMAGE_SUFFIXES = {".bmp", ".jpg", ".jpeg", ".png", ".webp"}


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


def _box_rows(result: Any, names: dict[int, str]) -> list[dict[str, object]]:
    boxes = getattr(result, "boxes", None)
    if boxes is None or len(boxes) == 0:
        return []

    xyxy = boxes.xyxy.cpu().numpy()
    cls = boxes.cls.cpu().numpy()
    conf = boxes.conf.cpu().numpy()
    rows: list[dict[str, object]] = []
    for box, class_id, confidence in zip(xyxy, cls, conf):
        class_id_int = int(class_id)
        rows.append(
            {
                "class_id": class_id_int,
                "class_name": names.get(class_id_int, str(class_id_int)),
                "confidence": float(confidence),
                "bbox_xyxy": [round(float(value), 2) for value in box],
            }
        )
    return rows


def evaluate_shape_detector(args: argparse.Namespace) -> int:
    from ultralytics import YOLO

    image_paths = collect_images(args.source)
    if not image_paths:
        raise ValueError(f"no images found in {args.source}")

    model = YOLO(args.model)
    names = {int(key): str(value) for key, value in model.names.items()}
    args.output.parent.mkdir(parents=True, exist_ok=True)

    class_counts: Counter[int] = Counter()
    images_with_expected = 0
    images_without_detection = 0

    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "image",
                "detections",
                "has_expected_class",
                "best_class_id",
                "best_class_name",
                "best_confidence",
                "best_expected_confidence",
                "all_detections_json",
            ],
        )
        writer.writeheader()

        for image_path in image_paths:
            result = model.predict(
                str(image_path),
                imgsz=args.imgsz,
                conf=args.conf,
                iou=args.iou,
                device=args.device,
                verbose=False,
            )[0]
            detections = _box_rows(result, names)
            detections.sort(key=lambda item: float(item["confidence"]), reverse=True)
            for detection in detections:
                class_counts[int(detection["class_id"])] += 1

            expected = [
                detection
                for detection in detections
                if int(detection["class_id"]) == args.expected_class_id
            ]
            if expected:
                images_with_expected += 1
            if not detections:
                images_without_detection += 1

            best = detections[0] if detections else {}
            writer.writerow(
                {
                    "image": str(image_path),
                    "detections": len(detections),
                    "has_expected_class": bool(expected),
                    "best_class_id": best.get("class_id", ""),
                    "best_class_name": best.get("class_name", ""),
                    "best_confidence": best.get("confidence", ""),
                    "best_expected_confidence": (
                        expected[0]["confidence"] if expected else ""
                    ),
                    "all_detections_json": json.dumps(detections),
                }
            )

    total = len(image_paths)
    expected_name = names.get(args.expected_class_id, str(args.expected_class_id))
    print(f"images={total}")
    print(
        f"images_with_{expected_name}={images_with_expected} "
        f"rate={images_with_expected / total:.4f}"
    )
    print(f"images_without_detection={images_without_detection}")
    print("detections_by_class:")
    for class_id, count in sorted(class_counts.items()):
        print(f"  {class_id} {names.get(class_id, class_id)}: {count}")
    print(f"csv={args.output}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Evaluate whether a YOLO shape model detects images as cube.",
    )
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("runs/eval/shape.csv"))
    parser.add_argument("--expected-class-id", type=int, default=0)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--conf", type=float, default=0.25)
    parser.add_argument("--iou", type=float, default=0.7)
    parser.add_argument("--device", default=None)
    return parser


def main() -> int:
    return evaluate_shape_detector(build_parser().parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
