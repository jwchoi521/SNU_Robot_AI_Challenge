from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

IMAGE_SUFFIXES = {".bmp", ".jpg", ".jpeg", ".png", ".webp"}
NO_FRUIT_CLASS = "none"
NO_CUBE_DIR = "no_cube_detection"


@dataclass(frozen=True)
class CubeDetection:
    bbox_xyxy: tuple[float, float, float, float]
    confidence: float


def collect_images(source: Path) -> list[Path]:
    if source.is_file() and source.suffix.lower() in IMAGE_SUFFIXES:
        return [source]
    if source.is_file():
        return [
            Path(line.strip())
            for line in source.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    if source.is_dir():
        return sorted(
            path
            for path in source.rglob("*")
            if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
        )
    raise FileNotFoundError(f"source not found: {source}")


def _detect_cube_boxes(
    detector: Any,
    image_path: Path,
    cube_class_id: int,
    imgsz: int,
    conf: float,
    iou: float,
    device: str | None,
) -> list[CubeDetection]:
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
    detections = [
        CubeDetection(
            bbox_xyxy=tuple(float(value) for value in box),  # type: ignore[arg-type]
            confidence=float(confidence),
        )
        for box, class_id, confidence in zip(xyxy, cls, confs)
        if int(class_id) == cube_class_id
    ]
    return sorted(detections, key=lambda detection: detection.confidence, reverse=True)


def _expanded_bbox(
    bbox_xyxy: Sequence[float],
    image_shape: tuple[int, int, int],
    padding_ratio: float,
) -> tuple[float, float, float, float]:
    if padding_ratio <= 0.0:
        return tuple(float(value) for value in bbox_xyxy)  # type: ignore[return-value]

    height, width = image_shape[:2]
    x1, y1, x2, y2 = bbox_xyxy
    pad_x = (x2 - x1) * padding_ratio
    pad_y = (y2 - y1) * padding_ratio
    return (
        max(0.0, x1 - pad_x),
        max(0.0, y1 - pad_y),
        min(float(width), x2 + pad_x),
        min(float(height), y2 + pad_y),
    )


def _best_class(probabilities: dict[str, float]) -> tuple[str, float]:
    if not probabilities:
        return "", 0.0
    return max(probabilities.items(), key=lambda item: item[1])


def _safe_name(text: str) -> str:
    cleaned = "".join(char if char.isalnum() else "_" for char in text)
    return "_".join(part for part in cleaned.split("_") if part)


def _crop_name(
    image_path: Path,
    source_root: Path,
    crop_index: int,
    detector_confidence: float,
    prediction_confidence: float,
) -> str:
    try:
        relative_stem = (
            image_path.resolve()
            .relative_to(source_root.resolve())
            .with_suffix("")
        )
    except ValueError:
        relative_stem = image_path.with_suffix("")
    stem = _safe_name(str(relative_stem))
    return (
        f"{stem}__crop{crop_index:02d}"
        f"__det{detector_confidence:.3f}"
        f"__cls{prediction_confidence:.3f}.jpg"
    )


def _write_rgb_jpg(path: Path, image_rgb: np.ndarray) -> None:
    import cv2

    path.parent.mkdir(parents=True, exist_ok=True)
    image_bgr = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)
    ok, encoded = cv2.imencode(".jpg", image_bgr)
    if not ok:
        raise ValueError(f"failed to encode image: {path}")
    encoded.tofile(path)


def sort_cube_crops(args: argparse.Namespace) -> int:
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

    detector = YOLO(args.detector_model)
    classifier, classes, image_size, checkpoint_threshold = load_fruit_classifier(
        args.classifier_model,
        device=args.device,
    )
    threshold = args.threshold if args.threshold is not None else checkpoint_threshold

    args.output_dir.mkdir(parents=True, exist_ok=True)
    for class_name in (*classes, NO_FRUIT_CLASS, NO_CUBE_DIR):
        (args.output_dir / class_name).mkdir(parents=True, exist_ok=True)

    manifest_path = args.output_dir / "manifest.csv"
    rows = 0
    images_without_cube = 0
    prediction_counts = {class_name: 0 for class_name in (*classes, NO_FRUIT_CLASS)}

    with manifest_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "image",
                "crop_path",
                "crop_index",
                "bbox_xyxy",
                "detector_confidence",
                "prediction",
                "best_class",
                "best_probability",
                "confidence",
                "probabilities_json",
                "error",
            ],
        )
        writer.writeheader()

        for image_number, image_path in enumerate(image_paths, start=1):
            if args.progress_every and (
                image_number == 1 or image_number % args.progress_every == 0
            ):
                print(
                    f"processing {image_number}/{len(image_paths)}: {image_path}",
                    flush=True,
                )

            image_rgb = read_image_rgb(image_path)
            detections = _detect_cube_boxes(
                detector=detector,
                image_path=image_path,
                cube_class_id=args.cube_class_id,
                imgsz=args.imgsz,
                conf=args.detector_conf,
                iou=args.detector_iou,
                device=args.device,
            )
            if args.max_crops:
                detections = detections[: args.max_crops]

            if not detections:
                images_without_cube += 1
                writer.writerow(
                    {
                        "image": str(image_path),
                        "crop_path": "",
                        "crop_index": "",
                        "bbox_xyxy": "",
                        "detector_confidence": "",
                        "prediction": "",
                        "best_class": "",
                        "best_probability": "",
                        "confidence": "",
                        "probabilities_json": "{}",
                        "error": "no_cube_detection",
                    }
                )
                if args.copy_no_cube:
                    target = args.output_dir / NO_CUBE_DIR / image_path.name
                    _write_rgb_jpg(target, image_rgb)
                continue

            for crop_index, detection in enumerate(detections):
                bbox = _expanded_bbox(
                    detection.bbox_xyxy,
                    image_rgb.shape,
                    args.crop_padding,
                )
                crop = crop_rgb(image_rgb, bbox)
                prediction = predict_fruit(
                    model=classifier,
                    image_rgb=crop,
                    classes=classes,
                    image_size=image_size,
                    threshold=threshold,
                    device=args.device,
                )
                best_class, best_probability = _best_class(prediction.probabilities)
                predicted_label = prediction.fruit_kind or NO_FRUIT_CLASS
                prediction_counts[predicted_label] = (
                    prediction_counts.get(predicted_label, 0) + 1
                )

                crop_path = (
                    args.output_dir
                    / predicted_label
                    / _crop_name(
                        image_path=image_path,
                        source_root=args.source,
                        crop_index=crop_index,
                        detector_confidence=detection.confidence,
                        prediction_confidence=prediction.confidence,
                    )
                )
                _write_rgb_jpg(crop_path, crop)
                rows += 1

                writer.writerow(
                    {
                        "image": str(image_path),
                        "crop_path": str(crop_path),
                        "crop_index": crop_index,
                        "bbox_xyxy": " ".join(f"{value:.2f}" for value in bbox),
                        "detector_confidence": round(detection.confidence, 6),
                        "prediction": predicted_label,
                        "best_class": best_class,
                        "best_probability": round(best_probability, 6),
                        "confidence": round(prediction.confidence, 6),
                        "probabilities_json": json.dumps(
                            prediction.probabilities,
                            ensure_ascii=True,
                        ),
                        "error": "",
                    }
                )

    print(f"images={len(image_paths)}")
    print(f"crops_saved={rows}")
    print(f"images_without_cube_detection={images_without_cube}")
    print("prediction_counts:")
    for class_name, count in sorted(prediction_counts.items()):
        print(f"  {class_name}: {count}")
    print(f"output_dir={args.output_dir}")
    print(f"manifest={manifest_path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Detect cube_any boxes, classify each cube crop by fruit kind, "
            "and save crops into prediction folders for visual review."
        ),
    )
    parser.add_argument("--source", type=Path, default=Path("dataset/images"))
    parser.add_argument(
        "--detector-model",
        type=Path,
        default=Path("models/shape_yolo_best.pt"),
    )
    parser.add_argument(
        "--classifier-model",
        type=Path,
        default=Path("models/classifier_1.pt"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("runs/classify/cube_crop_review"),
    )
    parser.add_argument("--cube-class-id", type=int, default=0)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--detector-conf", type=float, default=0.25)
    parser.add_argument("--detector-iou", type=float, default=0.7)
    parser.add_argument(
        "--max-crops",
        type=int,
        default=0,
        help="Maximum cube crops per image. Use 0 to keep every cube_any box.",
    )
    parser.add_argument(
        "--crop-padding",
        type=float,
        default=0.0,
        help="Optional bbox padding ratio before classifier input.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=None,
        help="Override the classifier checkpoint threshold for none decisions.",
    )
    parser.add_argument("--copy-no-cube", action="store_true")
    parser.add_argument(
        "--progress-every",
        type=int,
        default=50,
        help="Print progress every N images. Use 0 to disable progress output.",
    )
    parser.add_argument("--device", default=None)
    return parser


def main() -> int:
    return sort_cube_crops(build_parser().parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
