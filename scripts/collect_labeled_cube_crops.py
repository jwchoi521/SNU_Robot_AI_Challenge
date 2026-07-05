from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import numpy as np


IMAGE_SUFFIXES = (".jpg", ".jpeg", ".png", ".bmp", ".webp")


@dataclass(frozen=True)
class LabelBox:
    label_path: Path
    image_path: Path
    line_number: int
    bbox_xyxy: tuple[float, float, float, float]


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


def _image_path_for_label(
    label_path: Path,
    labels_root: Path,
    images_root: Path,
) -> Path | None:
    relative = label_path.relative_to(labels_root).with_suffix("")
    for suffix in IMAGE_SUFFIXES:
        image_path = images_root / relative.with_suffix(suffix)
        if image_path.exists():
            return image_path
    return None


def _yolo_to_xyxy(
    values: Sequence[float],
    image_width: int,
    image_height: int,
) -> tuple[float, float, float, float]:
    x_center, y_center, width, height = values
    x1 = (x_center - width / 2.0) * image_width
    y1 = (y_center - height / 2.0) * image_height
    x2 = (x_center + width / 2.0) * image_width
    y2 = (y_center + height / 2.0) * image_height
    return (
        max(0.0, min(float(image_width), x1)),
        max(0.0, min(float(image_height), y1)),
        max(0.0, min(float(image_width), x2)),
        max(0.0, min(float(image_height), y2)),
    )


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
    images_root: Path,
    crop_index: int,
) -> str:
    try:
        relative_stem = image_path.resolve().relative_to(images_root.resolve())
    except ValueError:
        relative_stem = image_path
    stem = _safe_name(str(relative_stem.with_suffix("")))
    return f"{stem}__cube{crop_index:02d}.jpg"


def _iter_class_boxes(
    labels_root: Path,
    images_root: Path,
    class_id: int,
) -> tuple[list[LabelBox], int]:
    boxes: list[LabelBox] = []
    labels_without_images = 0
    for label_path in sorted(labels_root.rglob("*.txt")):
        image_path = _image_path_for_label(label_path, labels_root, images_root)
        if image_path is None:
            labels_without_images += 1
            continue

        image_rgb = _read_rgb(image_path)
        image_height, image_width = image_rgb.shape[:2]
        for line_number, raw_line in enumerate(
            label_path.read_text(encoding="utf-8").splitlines(),
            start=1,
        ):
            line = raw_line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) != 5:
                raise ValueError(f"{label_path}:{line_number}: expected 5 columns")
            if int(parts[0]) != class_id:
                continue
            bbox = _yolo_to_xyxy(
                [float(value) for value in parts[1:]],
                image_width=image_width,
                image_height=image_height,
            )
            if bbox[2] > bbox[0] and bbox[3] > bbox[1]:
                boxes.append(
                    LabelBox(
                        label_path=label_path,
                        image_path=image_path,
                        line_number=line_number,
                        bbox_xyxy=bbox,
                    )
                )
    return boxes, labels_without_images


def collect_labeled_cube_crops(args: argparse.Namespace) -> int:
    images_root = args.images_root.resolve()
    labels_root = args.labels_root.resolve()
    output_dir = args.output_dir.resolve()
    crop_dir = output_dir / args.class_name
    manifest_path = output_dir / "manifest.csv"

    if not images_root.exists():
        raise FileNotFoundError(f"images root not found: {images_root}")
    if not labels_root.exists():
        raise FileNotFoundError(f"labels root not found: {labels_root}")

    boxes, labels_without_images = _iter_class_boxes(
        labels_root=labels_root,
        images_root=images_root,
        class_id=args.class_id,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    crop_dir.mkdir(parents=True, exist_ok=True)

    crops_saved = 0
    with manifest_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "image",
                "label",
                "label_line",
                "crop_path",
                "crop_index",
                "bbox_xyxy",
            ],
        )
        writer.writeheader()

        for crop_index, box in enumerate(boxes):
            if args.progress_every and (
                crop_index == 0 or (crop_index + 1) % args.progress_every == 0
            ):
                print(
                    f"processing crop {crop_index + 1}/{len(boxes)}: "
                    f"{box.image_path}",
                    flush=True,
                )

            image_rgb = _read_rgb(box.image_path)
            bbox = _expanded_bbox(box.bbox_xyxy, image_rgb.shape, args.crop_padding)
            crop = _crop_rgb(image_rgb, bbox)
            crop_path = crop_dir / _crop_name(box.image_path, images_root, crop_index)
            _write_rgb_jpg(crop_path, crop)
            crops_saved += 1
            writer.writerow(
                {
                    "image": str(box.image_path),
                    "label": str(box.label_path),
                    "label_line": box.line_number,
                    "crop_path": str(crop_path),
                    "crop_index": crop_index,
                    "bbox_xyxy": " ".join(f"{value:.2f}" for value in bbox),
                }
            )

    print(f"labels_without_images={labels_without_images}")
    print(f"crops_saved={crops_saved}")
    print(f"output_dir={output_dir}")
    print(f"crop_dir={crop_dir}")
    print(f"manifest={manifest_path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Collect cube_any crops from YOLO label files.",
    )
    parser.add_argument("--images-root", type=Path, default=Path("dataset/images_new"))
    parser.add_argument("--labels-root", type=Path, default=Path("dataset/labels_new"))
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("runs/collect/cube_any_crops_from_labels_new"),
    )
    parser.add_argument("--class-id", type=int, default=0)
    parser.add_argument("--class-name", default="cube_any")
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
        help="Print progress every N crops. Use 0 to disable progress output.",
    )
    return parser


def main() -> int:
    return collect_labeled_cube_crops(build_parser().parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
