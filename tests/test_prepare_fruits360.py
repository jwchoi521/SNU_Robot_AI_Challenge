from __future__ import annotations

from pathlib import Path

from scripts.prepare_fruits360 import (
    _fruit_from_folder_name,
    prepare_fruits360_dataset,
)


def test_fruit_folder_mapping_does_not_confuse_pineapple_with_apple() -> None:
    assert _fruit_from_folder_name("Apple Braeburn") == "apple"
    assert _fruit_from_folder_name("Pineapple Mini") == "pineapple"
    assert _fruit_from_folder_name("Banana Red") == "banana"
    assert _fruit_from_folder_name("Orange") == "orange"
    assert _fruit_from_folder_name("Pear") is None


def test_prepare_fruits360_dataset_filters_target_fruits(tmp_path: Path) -> None:
    source = tmp_path / "fruits-360"
    for split in ("Training", "Test"):
        for folder in ("Apple Red 1", "Pineapple", "Pear"):
            class_dir = source / split / folder
            class_dir.mkdir(parents=True)
            (class_dir / "sample_1.jpg").write_bytes(b"fake image bytes")
            if split == "Training":
                (class_dir / "sample_2.jpg").write_bytes(b"fake image bytes")

    output = tmp_path / "prepared"
    counts = prepare_fruits360_dataset(
        source_root=source,
        output_root=output,
        val_ratio=0.5,
        test_ratio=0.0,
        seed=7,
        clear=True,
    )

    assert counts["train"]["apple"] == 1
    assert counts["val"]["apple"] == 1
    assert counts["test"]["apple"] == 1
    assert counts["val"]["pineapple"] == 1
    assert not (output / "val" / "pear").exists()
