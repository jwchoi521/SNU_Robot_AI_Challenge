from __future__ import annotations

import argparse
import random
import shutil
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path


FRUIT_CLASSES = ("apple", "orange", "banana", "pineapple")
IMAGE_SUFFIXES = {".bmp", ".jpg", ".jpeg", ".png", ".webp"}


@dataclass(frozen=True)
class ImageRecord:
    path: Path
    fruit: str
    source_class: str


def _fruit_from_folder_name(name: str) -> str | None:
    normalized = name.lower().replace("_", " ").replace("-", " ")
    padded = f" {normalized} "
    if "pineapple" in padded:
        return "pineapple"
    if "banana" in padded:
        return "banana"
    if "orange" in padded:
        return "orange"
    if " apple " in padded or normalized.startswith("apple"):
        return "apple"
    return None


def _iter_images(folder: Path) -> list[Path]:
    return sorted(
        path
        for path in folder.rglob("*")
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
    )


def _collect_split(
    source_root: Path,
    split_names: tuple[str, ...],
) -> list[ImageRecord]:
    split_dir = next(
        (source_root / name for name in split_names if (source_root / name).exists()),
        None,
    )
    if split_dir is None:
        return []

    records: list[ImageRecord] = []
    for class_dir in sorted(path for path in split_dir.iterdir() if path.is_dir()):
        fruit = _fruit_from_folder_name(class_dir.name)
        if fruit is None:
            continue
        records.extend(
            ImageRecord(path=image_path, fruit=fruit, source_class=class_dir.name)
            for image_path in _iter_images(class_dir)
        )
    return records


def _collect_unsplit(source_root: Path) -> list[ImageRecord]:
    records: list[ImageRecord] = []
    for class_dir in sorted(path for path in source_root.iterdir() if path.is_dir()):
        fruit = _fruit_from_folder_name(class_dir.name)
        if fruit is None:
            continue
        records.extend(
            ImageRecord(path=image_path, fruit=fruit, source_class=class_dir.name)
            for image_path in _iter_images(class_dir)
        )
    return records


def _split_by_class(
    records: list[ImageRecord],
    ratio: float,
    seed: int,
) -> tuple[list[ImageRecord], list[ImageRecord]]:
    if ratio <= 0.0:
        return records, []
    grouped: dict[str, list[ImageRecord]] = defaultdict(list)
    for record in records:
        grouped[record.fruit].append(record)

    first: list[ImageRecord] = []
    second: list[ImageRecord] = []
    rng = random.Random(seed)
    for fruit_records in grouped.values():
        shuffled = list(fruit_records)
        rng.shuffle(shuffled)
        second_count = round(len(shuffled) * ratio)
        if len(shuffled) > 1 and second_count == 0:
            second_count = 1
        second.extend(shuffled[:second_count])
        first.extend(shuffled[second_count:])
    return sorted(first, key=lambda item: str(item.path)), sorted(
        second,
        key=lambda item: str(item.path),
    )


def _safe_clear_output(output_root: Path) -> None:
    output_root = output_root.resolve()
    if output_root.anchor == str(output_root):
        raise ValueError(f"refusing to clear filesystem root: {output_root}")
    if output_root.exists():
        shutil.rmtree(output_root)


def _copy_records(records: list[ImageRecord], output_root: Path, split: str) -> int:
    copied = 0
    for record in records:
        target_name = f"{record.source_class}__{record.path.name}"
        target = output_root / split / record.fruit / target_name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(record.path, target)
        copied += 1
    return copied


def prepare_fruits360_dataset(
    source_root: Path,
    output_root: Path,
    val_ratio: float,
    test_ratio: float,
    seed: int,
    clear: bool = False,
) -> dict[str, dict[str, int]]:
    source_root = source_root.resolve()
    output_root = output_root.resolve()

    if not source_root.exists():
        raise FileNotFoundError(f"source root not found: {source_root}")
    if clear:
        _safe_clear_output(output_root)

    train_records = _collect_split(source_root, ("Training", "training", "train"))
    val_records = _collect_split(source_root, ("Validation", "validation", "val"))
    test_records = _collect_split(source_root, ("Test", "test"))

    if not train_records and not val_records and not test_records:
        train_records = _collect_unsplit(source_root)
        train_records, test_records = _split_by_class(train_records, test_ratio, seed)

    if not val_records:
        train_records, val_records = _split_by_class(train_records, val_ratio, seed)

    split_records = {
        "train": train_records,
        "val": val_records,
        "test": test_records,
    }

    counts: dict[str, dict[str, int]] = {}
    for split, records in split_records.items():
        counts[split] = {fruit: 0 for fruit in FRUIT_CLASSES}
        _copy_records(records, output_root, split)
        for record in records:
            counts[split][record.fruit] += 1
    return counts


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Prepare a 4-class apple/orange/banana/pineapple dataset "
            "from Fruits 360."
        ),
    )
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, default=Path("dataset/fruits360"))
    parser.add_argument("--val-ratio", type=float, default=0.1)
    parser.add_argument(
        "--test-ratio",
        type=float,
        default=0.0,
        help="Only used when the source root has no Test split.",
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--clear", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    counts = prepare_fruits360_dataset(
        source_root=args.source_root,
        output_root=args.output_root,
        val_ratio=args.val_ratio,
        test_ratio=args.test_ratio,
        seed=args.seed,
        clear=args.clear,
    )
    for split, split_counts in counts.items():
        total = sum(split_counts.values())
        details = " ".join(
            f"{fruit}={split_counts[fruit]}" for fruit in FRUIT_CLASSES
        )
        print(f"{split}: total={total} {details}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
