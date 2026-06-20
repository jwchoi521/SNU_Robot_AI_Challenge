from __future__ import annotations

from pathlib import Path

from scripts.split_dataset import split_labeled_dataset


def _make_labeled_sample(root: Path, name: str) -> None:
    image_path = root / "images" / f"{name}.jpg"
    label_path = root / "labels" / f"{name}.txt"
    image_path.parent.mkdir(parents=True, exist_ok=True)
    label_path.parent.mkdir(parents=True, exist_ok=True)
    image_path.write_bytes(b"fake image bytes")
    label_path.write_text("0 0.5 0.5 0.25 0.25\n")


def test_split_labeled_dataset_copies_images_and_labels(tmp_path: Path) -> None:
    source = tmp_path / "labeled"
    for index in range(10):
        _make_labeled_sample(source, f"sample_{index}")

    data_root = tmp_path / "dataset"
    counts = split_labeled_dataset(
        source_images=source / "images",
        source_labels=source / "labels",
        data_root=data_root,
        train_ratio=0.6,
        val_ratio=0.2,
        test_ratio=0.2,
        seed=7,
    )

    assert counts.train == 6
    assert counts.val == 2
    assert counts.test == 2
    assert len(list((data_root / "images" / "train").glob("*.jpg"))) == 6
    assert len(list((data_root / "labels" / "train").glob("*.txt"))) == 6
    assert len(list((data_root / "images" / "val").glob("*.jpg"))) == 2
    assert len(list((data_root / "labels" / "val").glob("*.txt"))) == 2
    assert len(list((data_root / "images" / "test").glob("*.jpg"))) == 2
    assert len(list((data_root / "labels" / "test").glob("*.txt"))) == 2
