from __future__ import annotations

import argparse
import random
import shutil
from dataclasses import dataclass
from pathlib import Path


IMAGE_SUFFIXES = {".bmp", ".jpg", ".jpeg", ".png", ".webp"}
SPLITS = ("train", "val", "test")


@dataclass(frozen=True)
class SplitCounts:
    train: int
    val: int
    test: int


def _iter_images(image_dir: Path) -> list[Path]:
    return sorted(
        path
        for path in image_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
    )


def _default_label_dir(image_dir: Path) -> Path:
    if image_dir.name == "images":
        return image_dir.with_name("labels")
    return image_dir.parent / "labels"


def _split_items(
    items: list[Path],
    train_ratio: float,
    val_ratio: float,
    test_ratio: float,
    seed: int,
) -> dict[str, list[Path]]:
    total_ratio = train_ratio + val_ratio + test_ratio
    if total_ratio <= 0:
        raise ValueError("split ratios must sum to a positive value")

    normalized_train = train_ratio / total_ratio
    normalized_val = val_ratio / total_ratio

    shuffled = list(items)
    random.Random(seed).shuffle(shuffled)

    train_end = round(len(shuffled) * normalized_train)
    val_end = train_end + round(len(shuffled) * normalized_val)
    return {
        "train": shuffled[:train_end],
        "val": shuffled[train_end:val_end],
        "test": shuffled[val_end:],
    }


def _safe_clear_split_dirs(data_root: Path) -> None:
    root = data_root.resolve()
    for parent_name in ("images", "labels"):
        parent = (root / parent_name).resolve()
        if root not in parent.parents:
            raise ValueError(f"refusing to clear path outside data root: {parent}")
        for split in SPLITS:
            target = (parent / split).resolve()
            if target.exists():
                shutil.rmtree(target)


def _copy_or_move(source: Path, target: Path, move: bool) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if move:
        shutil.move(str(source), str(target))
    else:
        shutil.copy2(source, target)


def split_labeled_dataset(
    source_images: Path,
    source_labels: Path,
    data_root: Path,
    train_ratio: float,
    val_ratio: float,
    test_ratio: float,
    seed: int,
    move: bool = False,
    clear: bool = False,
    allow_missing_labels: bool = False,
) -> SplitCounts:
    source_images = source_images.resolve()
    source_labels = source_labels.resolve()
    data_root = data_root.resolve()

    if not source_images.exists():
        raise FileNotFoundError(f"source image directory not found: {source_images}")
    if not source_labels.exists():
        raise FileNotFoundError(f"source label directory not found: {source_labels}")

    images = _iter_images(source_images)
    if not images:
        raise ValueError(f"no images found in {source_images}")

    split_map = _split_items(images, train_ratio, val_ratio, test_ratio, seed)
    missing_labels: list[Path] = []
    if not allow_missing_labels:
        for image_path in images:
            relative = image_path.relative_to(source_images)
            label_path = (source_labels / relative).with_suffix(".txt")
            if not label_path.exists():
                missing_labels.append(label_path)

    if missing_labels:
        sample = "\n".join(str(path) for path in missing_labels[:5])
        raise FileNotFoundError(f"missing label files:\n{sample}")

    if clear:
        _safe_clear_split_dirs(data_root)

    counts: dict[str, int] = {}
    for split, split_images in split_map.items():
        counts[split] = len(split_images)
        for image_path in split_images:
            relative = image_path.relative_to(source_images)
            label_path = (source_labels / relative).with_suffix(".txt")
            target_image = data_root / "images" / split / relative
            target_label = (data_root / "labels" / split / relative).with_suffix(".txt")

            _copy_or_move(image_path, target_image, move=move)
            if label_path.exists():
                _copy_or_move(label_path, target_label, move=move)
            elif allow_missing_labels:
                target_label.parent.mkdir(parents=True, exist_ok=True)
                target_label.write_text("")

    return SplitCounts(
        train=counts["train"],
        val=counts["val"],
        test=counts["test"],
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Split a labeled YOLO image/label folder into train/val/test.",
    )
    parser.add_argument("--source-images", type=Path, required=True)
    parser.add_argument("--source-labels", type=Path, default=None)
    parser.add_argument("--data-root", type=Path, default=Path("dataset"))
    parser.add_argument("--train-ratio", type=float, default=0.8)
    parser.add_argument("--val-ratio", type=float, default=0.2)
    parser.add_argument("--test-ratio", type=float, default=0.0)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--move", action="store_true")
    parser.add_argument("--clear", action="store_true")
    parser.add_argument("--allow-missing-labels", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    source_labels = args.source_labels or _default_label_dir(args.source_images)
    counts = split_labeled_dataset(
        source_images=args.source_images,
        source_labels=source_labels,
        data_root=args.data_root,
        train_ratio=args.train_ratio,
        val_ratio=args.val_ratio,
        test_ratio=args.test_ratio,
        seed=args.seed,
        move=args.move,
        clear=args.clear,
        allow_missing_labels=args.allow_missing_labels,
    )
    print(
        "Split complete: "
        f"train={counts.train} val={counts.val} test={counts.test}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
