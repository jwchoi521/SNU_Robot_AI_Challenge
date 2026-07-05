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


def _iter_images(class_dir: Path) -> list[Path]:
    return sorted(
        path
        for path in class_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
    )


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


def _safe_clear_output(output_root: Path) -> None:
    output_root = output_root.resolve()
    if output_root.anchor == str(output_root):
        raise ValueError(f"refusing to clear filesystem root: {output_root}")
    if output_root.exists():
        shutil.rmtree(output_root)


def _copy_split_items(
    class_items: dict[str, dict[str, list[Path]]],
    source_root: Path,
    output_root: Path,
) -> dict[str, SplitCounts]:
    counts: dict[str, SplitCounts] = {}
    for class_name, split_items in class_items.items():
        split_counts: dict[str, int] = {}
        for split, paths in split_items.items():
            split_counts[split] = len(paths)
            for source_path in paths:
                relative = source_path.relative_to(source_root / class_name)
                target = output_root / split / class_name / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_path, target)
        counts[class_name] = SplitCounts(
            train=split_counts["train"],
            val=split_counts["val"],
            test=split_counts["test"],
        )
    return counts


def split_imagefolder_dataset(
    source_root: Path,
    output_root: Path,
    train_ratio: float,
    val_ratio: float,
    test_ratio: float,
    seed: int,
    clear: bool = False,
) -> dict[str, SplitCounts]:
    source_root = source_root.resolve()
    output_root = output_root.resolve()
    if not source_root.exists():
        raise FileNotFoundError(f"source root not found: {source_root}")

    class_dirs = sorted(path for path in source_root.iterdir() if path.is_dir())
    if not class_dirs:
        raise ValueError(f"no class directories found in {source_root}")

    if clear:
        _safe_clear_output(output_root)

    class_items: dict[str, dict[str, list[Path]]] = {}
    for class_dir in class_dirs:
        images = _iter_images(class_dir)
        if not images:
            continue
        class_items[class_dir.name] = _split_items(
            images,
            train_ratio=train_ratio,
            val_ratio=val_ratio,
            test_ratio=test_ratio,
            seed=seed,
        )
    if not class_items:
        raise ValueError(f"no images found in class directories under {source_root}")
    return _copy_split_items(class_items, source_root, output_root)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Split an ImageFolder dataset into train/val/test folders.",
    )
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--train-ratio", type=float, default=0.7)
    parser.add_argument("--val-ratio", type=float, default=0.15)
    parser.add_argument("--test-ratio", type=float, default=0.15)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--clear", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    counts = split_imagefolder_dataset(
        source_root=args.source_root,
        output_root=args.output_root,
        train_ratio=args.train_ratio,
        val_ratio=args.val_ratio,
        test_ratio=args.test_ratio,
        seed=args.seed,
        clear=args.clear,
    )
    for class_name, split_counts in counts.items():
        total = split_counts.train + split_counts.val + split_counts.test
        print(
            f"{class_name}: total={total} "
            f"train={split_counts.train} "
            f"val={split_counts.val} "
            f"test={split_counts.test}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
