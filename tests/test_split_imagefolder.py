from __future__ import annotations

from pathlib import Path

from scripts.split_imagefolder import split_imagefolder_dataset


def _touch_images(class_dir: Path, count: int) -> None:
    class_dir.mkdir(parents=True)
    for index in range(count):
        (class_dir / f"sample_{index:03d}.jpg").write_bytes(b"fake image bytes")


def test_balance_to_min_preserves_raw_when_output_contains_source(tmp_path: Path) -> None:
    source = tmp_path / "raw"
    _touch_images(source / "apple", 5)
    _touch_images(source / "pineapple", 2)
    stale = tmp_path / "train" / "apple" / "old.jpg"
    stale.parent.mkdir(parents=True)
    stale.write_bytes(b"old")

    counts = split_imagefolder_dataset(
        source_root=source,
        output_root=tmp_path,
        train_ratio=1.0,
        val_ratio=0.0,
        test_ratio=0.0,
        seed=42,
        clear=True,
        balance_to_min=True,
    )

    assert source.exists()
    assert not stale.exists()
    assert counts["apple"].train == 2
    assert counts["pineapple"].train == 2
    assert len(list((tmp_path / "train" / "apple").glob("*.jpg"))) == 2
    assert len(list((tmp_path / "train" / "pineapple").glob("*.jpg"))) == 2


def test_oversample_train_to_max_duplicates_minority_train_images(tmp_path: Path) -> None:
    source = tmp_path / "raw"
    _touch_images(source / "apple", 5)
    _touch_images(source / "pineapple", 2)

    counts = split_imagefolder_dataset(
        source_root=source,
        output_root=tmp_path,
        train_ratio=1.0,
        val_ratio=0.0,
        test_ratio=0.0,
        seed=42,
        clear=True,
        oversample_train_to_max=True,
    )

    pineapple_train = list((tmp_path / "train" / "pineapple").glob("*.jpg"))
    assert counts["apple"].train == 5
    assert counts["pineapple"].train == 5
    assert len(pineapple_train) == 5
    assert any("__dup" in path.stem for path in pineapple_train)
