from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml


EXPECTED_NAMES = {
    0: "cube_any",
    1: "octahedron",
    2: "dodecahedron",
    3: "icosahedron",
    4: "apple_sticker",
    5: "orange_sticker",
    6: "banana_sticker",
    7: "pineapple_sticker",
}
SHAPE_NAMES = {
    0: "cube_any",
    1: "octahedron",
    2: "dodecahedron",
    3: "icosahedron",
}
NAME_PROFILES = {
    "robot8": EXPECTED_NAMES,
    "shape4": SHAPE_NAMES,
}

IMAGE_SUFFIXES = {".bmp", ".jpg", ".jpeg", ".png", ".webp"}


def _normalize_names(raw_names: Any) -> dict[int, str]:
    if isinstance(raw_names, list):
        return {idx: str(name) for idx, name in enumerate(raw_names)}
    if isinstance(raw_names, dict):
        return {int(idx): str(name) for idx, name in raw_names.items()}
    raise TypeError("data.yaml names must be a list or mapping")


def _resolve_dataset_root(data_yaml: Path, config: dict[str, Any]) -> Path:
    raw_path = Path(str(config.get("path", data_yaml.parent)))
    if raw_path.is_absolute():
        return raw_path

    candidates = (
        data_yaml.parent / raw_path,
        data_yaml.parent.parent / raw_path,
        Path.cwd() / raw_path,
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    return candidates[0].resolve()


def _label_dir_for(image_dir: Path) -> Path:
    parts = list(image_dir.parts)
    if "images" in parts:
        parts[parts.index("images")] = "labels"
        return Path(*parts)
    return image_dir.parent.parent / "labels" / image_dir.name


def _iter_images(image_dir: Path) -> list[Path]:
    if not image_dir.exists():
        return []
    return sorted(
        path
        for path in image_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
    )


def _validate_label_file(path: Path, expected_names: dict[int, str]) -> list[str]:
    errors: list[str] = []
    for line_number, raw_line in enumerate(path.read_text().splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue

        parts = line.split()
        if len(parts) != 5:
            errors.append(f"{path}:{line_number}: expected 5 YOLO columns")
            continue

        try:
            class_id = int(parts[0])
            values = [float(value) for value in parts[1:]]
        except ValueError:
            errors.append(f"{path}:{line_number}: non-numeric label value")
            continue

        if class_id not in expected_names:
            allowed = f"0..{len(expected_names) - 1}"
            errors.append(f"{path}:{line_number}: class id {class_id} is not {allowed}")
        if any(value < 0.0 or value > 1.0 for value in values):
            errors.append(f"{path}:{line_number}: bbox values must be in 0..1")
        if values[2] <= 0.0 or values[3] <= 0.0:
            errors.append(f"{path}:{line_number}: width and height must be positive")
    return errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate the YOLO dataset layout.")
    parser.add_argument("--data", type=Path, default=Path("dataset/data.yaml"))
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings such as missing labels as errors.",
    )
    parser.add_argument(
        "--require-non-empty",
        action="store_true",
        help="Fail when train or val contains no images.",
    )
    parser.add_argument(
        "--profile",
        choices=tuple(NAME_PROFILES),
        default="robot8",
        help="Expected class mapping profile.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    data_yaml = args.data.resolve()
    errors: list[str] = []
    warnings: list[str] = []

    if not data_yaml.exists():
        print(f"FAIL data yaml not found: {data_yaml}")
        return 1

    config = yaml.safe_load(data_yaml.read_text()) or {}
    expected_names = NAME_PROFILES[args.profile]
    names = _normalize_names(config.get("names"))
    if names != expected_names:
        errors.append(f"{data_yaml}: names must match the {args.profile} mapping")

    dataset_root = _resolve_dataset_root(data_yaml, config)
    print(f"Dataset root: {dataset_root}")

    total_images = 0
    total_labels = 0
    for split in ("train", "val", "test"):
        split_value = config.get(split)
        if not split_value:
            if split != "test":
                errors.append(f"{data_yaml}: missing required '{split}' entry")
            continue

        image_dir = (dataset_root / str(split_value)).resolve()
        label_dir = _label_dir_for(image_dir)
        images = _iter_images(image_dir)
        labels = sorted(label_dir.rglob("*.txt")) if label_dir.exists() else []
        total_images += len(images)
        total_labels += len(labels)

        print(
            f"{split:5} images={len(images):5} labels={len(labels):5} "
            f"image_dir={image_dir}"
        )

        if not image_dir.exists():
            errors.append(f"{split}: image directory not found: {image_dir}")
        if not label_dir.exists():
            errors.append(f"{split}: label directory not found: {label_dir}")
        if args.require_non_empty and split in {"train", "val"} and not images:
            errors.append(f"{split}: no images found")

        image_stems = {path.relative_to(image_dir).with_suffix("") for path in images}
        label_stems = {path.relative_to(label_dir).with_suffix("") for path in labels}
        missing_labels = sorted(image_stems - label_stems)
        orphan_labels = sorted(label_stems - image_stems)

        for stem in missing_labels:
            warnings.append(f"{split}: missing label for image {stem}")
        for stem in orphan_labels:
            warnings.append(f"{split}: label without image {stem}")
        for label_path in labels:
            errors.extend(_validate_label_file(label_path, expected_names))

    if total_images == 0:
        warnings.append("dataset contains no image files yet")
    if total_labels == 0:
        warnings.append("dataset contains no label files yet")

    for warning in warnings:
        print(f"WARN {warning}")
    for error in errors:
        print(f"FAIL {error}")

    if errors or (args.strict and warnings):
        return 1
    print("OK dataset checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
