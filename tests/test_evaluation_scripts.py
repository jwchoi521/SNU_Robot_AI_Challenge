from __future__ import annotations

from pathlib import Path

from scripts.evaluate_cube_fruit_classifier import (
    collect_images as collect_classifier_images,
)
from scripts.evaluate_cube_fruit_classifier import truth_from_parent
from scripts.evaluate_shape_detector import collect_images as collect_detector_images


def test_collect_images_recurses_directories(tmp_path: Path) -> None:
    image_dir = tmp_path / "images" / "apple"
    image_dir.mkdir(parents=True)
    first = image_dir / "first.jpg"
    second = image_dir / "second.png"
    ignored = image_dir / "notes.txt"
    first.write_bytes(b"fake")
    second.write_bytes(b"fake")
    ignored.write_text("ignore me")

    assert collect_detector_images(tmp_path / "images") == [first, second]
    assert collect_classifier_images(tmp_path / "images") == [first, second]


def test_collect_images_reads_list_files(tmp_path: Path) -> None:
    first = tmp_path / "first.jpg"
    second = tmp_path / "second.jpg"
    first.write_bytes(b"fake")
    second.write_bytes(b"fake")
    image_list = tmp_path / "images.txt"
    image_list.write_text(f"{first}\n\n{second}\n")

    assert collect_detector_images(image_list) == [first, second]
    assert collect_classifier_images(image_list) == [first, second]


def test_truth_from_parent_matches_known_classes(tmp_path: Path) -> None:
    image_path = tmp_path / "apple" / "sample.jpg"
    image_path.parent.mkdir()
    image_path.write_bytes(b"fake")

    assert truth_from_parent(image_path, ("apple", "orange", "none")) == "apple"
    assert truth_from_parent(image_path, ("banana", "none")) is None
