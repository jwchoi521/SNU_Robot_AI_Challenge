from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

import numpy as np


IMAGE_SUFFIXES = {".bmp", ".jpg", ".jpeg", ".png", ".webp"}


@dataclass(frozen=True)
class DetectionCrop:
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


def _read_rgb(path: Path) -> np.ndarray:
    import cv2

    buffer = np.fromfile(path, dtype=np.uint8)
    image_bgr = cv2.imdecode(buffer, cv2.IMREAD_COLOR)
    if image_bgr is None:
        raise ValueError(f"image could not be read: {path}")
    return cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)


def _write_rgb_jpg(path: Path, image_rgb: np.ndarray) -> None:
    import cv2

    path.parent.mkdir(parents=True, exist_ok=True)
    image_bgr = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)
    ok, encoded = cv2.imencode(".jpg", image_bgr)
    if not ok:
        raise ValueError(f"failed to encode image: {path}")
    encoded.tofile(path)


def _detect_class_boxes(
    detector: Any,
    image_path: Path,
    class_id: int,
    imgsz: int,
    conf: float,
    iou: float,
    device: str | None,
) -> list[DetectionCrop]:
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
        DetectionCrop(
            bbox_xyxy=tuple(float(value) for value in box),  # type: ignore[arg-type]
            confidence=float(confidence),
        )
        for box, class_id_value, confidence in zip(xyxy, cls, confs)
        if int(class_id_value) == class_id
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


def _crop_rgb(image_rgb: np.ndarray, bbox_xyxy: Sequence[float]) -> np.ndarray:
    height, width = image_rgb.shape[:2]
    x1, y1, x2, y2 = (int(round(value)) for value in bbox_xyxy)
    left = max(0, min(width, x1))
    top = max(0, min(height, y1))
    right = max(0, min(width, x2))
    bottom = max(0, min(height, y2))
    if right <= left or bottom <= top:
        raise ValueError(f"invalid crop bbox: {tuple(bbox_xyxy)}")
    return image_rgb[top:bottom, left:right]


def _safe_name(text: str) -> str:
    cleaned = "".join(char if char.isalnum() else "_" for char in text)
    return "_".join(part for part in cleaned.split("_") if part)


def _crop_name(
    image_path: Path,
    source_root: Path,
    crop_index: int,
    confidence: float,
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
    return f"{stem}__crop{crop_index:02d}__det{confidence:.3f}.jpg"


def collect_cube_crops(args: argparse.Namespace) -> int:
    from ultralytics import YOLO

    image_paths = collect_images(args.source)
    if not image_paths:
        raise ValueError(f"no images found in {args.source}")

    detector = YOLO(args.model)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = args.output_dir / "manifest.csv"
    crop_dir = args.output_dir / "cube_any"
    crop_dir.mkdir(parents=True, exist_ok=True)

    crops_saved = 0
    images_without_detection = 0
    with manifest_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "image",
                "crop_path",
                "crop_index",
                "bbox_xyxy",
                "detector_confidence",
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

            image_rgb = _read_rgb(image_path)
            detections = _detect_class_boxes(
                detector=detector,
                image_path=image_path,
                class_id=args.class_id,
                imgsz=args.imgsz,
                conf=args.conf,
                iou=args.iou,
                device=args.device,
            )
            if args.max_crops:
                detections = detections[: args.max_crops]

            if not detections:
                images_without_detection += 1
                writer.writerow(
                    {
                        "image": str(image_path),
                        "crop_path": "",
                        "crop_index": "",
                        "bbox_xyxy": "",
                        "detector_confidence": "",
                        "error": "no_detection",
                    }
                )
                continue

            for crop_index, detection in enumerate(detections):
                bbox = _expanded_bbox(
                    detection.bbox_xyxy,
                    image_rgb.shape,
                    args.crop_padding,
                )
                crop = _crop_rgb(image_rgb, bbox)
                crop_path = crop_dir / _crop_name(
                    image_path,
                    args.source,
                    crop_index,
                    detection.confidence,
                )
                _write_rgb_jpg(crop_path, crop)
                crops_saved += 1
                writer.writerow(
                    {
                        "image": str(image_path),
                        "crop_path": str(crop_path),
                        "crop_index": crop_index,
                        "bbox_xyxy": " ".join(f"{value:.2f}" for value in bbox),
                        "detector_confidence": round(detection.confidence, 6),
                        "error": "",
                    }
                )

    print(f"images={len(image_paths)}")
    print(f"crops_saved={crops_saved}")
    print(f"images_without_detection={images_without_detection}")
    print(f"output_dir={args.output_dir}")
    print(f"crop_dir={crop_dir}")
    print(f"manifest={manifest_path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Collect YOLO-predicted cube_any crops into one folder.",
    )
    parser.add_argument("--source", type=Path, default=Path("dataset/images_new"))
    parser.add_argument("--model", type=Path, default=Path("models/shape_yolo_best.pt"))
    parser.add_argument("--output-dir", type=Path, default=Path("dataset/cube_any_crops"))
    parser.add_argument("--class-id", type=int, default=0)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--conf", type=float, default=0.25)
    parser.add_argument("--iou", type=float, default=0.7)
    parser.add_argument(
        "--max-crops",
        type=int,
        default=0,
        help="Maximum crops per image. Use 0 to keep every matching detection.",
    )
    parser.add_argument(
        "--crop-padding",
        type=float,
        default=0.0,
        help="Optional bbox padding ratio before saving crops.",
    )
    parser.add_argument(
        "--progress-every",
        type=int,
        default=50,
        help="Print progress every N images. Use 0 to disable progress output.",
    )
    parser.add_argument("--device", default=None)
    return parser


def main() -> int:
    return collect_cube_crops(build_parser().parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
