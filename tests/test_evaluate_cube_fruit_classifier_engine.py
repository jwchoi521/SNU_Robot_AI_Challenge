from __future__ import annotations

import json
import sys
from types import SimpleNamespace
from pathlib import Path

import numpy as np
import pytest

from scripts.evaluate_cube_fruit_classifier_engine import (
    _cuda_device_index,
    load_engine_metadata,
    prediction_from_logits,
    preprocess_rgb_for_engine,
)


def test_load_engine_metadata_from_trtexec_export(tmp_path: Path) -> None:
    metadata_path = tmp_path / "classifier_engine_metadata.json"
    metadata_path.write_text(
        json.dumps(
            {
                "classes": ["apple", "orange", "banana", "pineapple", "none"],
                "image_size": 256,
                "threshold": 0.5,
                "input_name": "images",
                "output_name": "logits",
                "normalize_mean": [0.5, 0.5, 0.5],
                "normalize_std": [0.5, 0.5, 0.5],
            }
        ),
        encoding="utf-8",
    )

    metadata = load_engine_metadata(metadata_path)

    assert metadata.classes == ("apple", "orange", "banana", "pineapple", "none")
    assert metadata.image_size == 256
    assert metadata.threshold == 0.5
    assert metadata.input_name == "images"
    assert metadata.output_name == "logits"
    assert metadata.normalize_mean == (0.5, 0.5, 0.5)
    assert metadata.normalize_std == (0.5, 0.5, 0.5)


def test_load_engine_metadata_from_integrated_exporter(tmp_path: Path) -> None:
    metadata_path = tmp_path / "last.json"
    metadata_path.write_text(
        json.dumps(
            {
                "classes": ["apple", "orange", "banana", "pineapple", "none"],
                "checkpoint_image_size": 224,
                "input_name": "input",
                "output_name": "logits",
                "normalization": {
                    "mean": [0.4, 0.5, 0.6],
                    "std": [0.2, 0.3, 0.4],
                },
            }
        ),
        encoding="utf-8",
    )

    metadata = load_engine_metadata(metadata_path)

    assert metadata.image_size == 224
    assert metadata.threshold == 0.7
    assert metadata.input_name == "input"
    assert metadata.normalize_mean == (0.4, 0.5, 0.6)
    assert metadata.normalize_std == (0.2, 0.3, 0.4)


def test_preprocess_rgb_for_engine_normalizes_to_nchw(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_cv2 = SimpleNamespace(
        INTER_AREA=3,
        resize=lambda image, size, interpolation: image,
    )
    monkeypatch.setitem(sys.modules, "cv2", fake_cv2)
    image = np.array([[[0, 127, 255]]], dtype=np.uint8)

    tensor = preprocess_rgb_for_engine(
        image,
        image_size=1,
        normalize_mean=(0.5, 0.5, 0.5),
        normalize_std=(0.5, 0.5, 0.5),
    )

    assert tensor.shape == (1, 3, 1, 1)
    assert tensor.dtype == np.float32
    np.testing.assert_allclose(
        tensor[0, :, 0, 0],
        np.array([-1.0, -0.00392157, 1.0], dtype=np.float32),
        atol=1e-6,
    )


def test_prediction_from_logits_applies_threshold_and_none_class() -> None:
    classes = ("apple", "orange", "banana", "pineapple", "none")

    confident = prediction_from_logits(
        np.array([0.0, 5.0, 0.0, 0.0, 0.0]),
        classes=classes,
        threshold=0.5,
    )
    assert confident.fruit_kind == "orange"
    assert confident.confidence > 0.9

    low_confidence = prediction_from_logits(
        np.array([0.1, 0.2, 0.0, 0.0, 0.0]),
        classes=classes,
        threshold=0.9,
    )
    assert low_confidence.fruit_kind is None

    none_prediction = prediction_from_logits(
        np.array([0.0, 0.0, 0.0, 0.0, 5.0]),
        classes=classes,
        threshold=0.5,
    )
    assert none_prediction.fruit_kind is None


def test_prediction_from_logits_rejects_class_mismatch() -> None:
    with pytest.raises(ValueError, match="output size"):
        prediction_from_logits(
            np.array([1.0, 2.0]),
            classes=("apple", "orange", "banana"),
            threshold=0.5,
        )


def test_cuda_device_index_accepts_common_forms() -> None:
    assert _cuda_device_index(None) == 0
    assert _cuda_device_index("cuda") == 0
    assert _cuda_device_index("cuda:1") == 1
    assert _cuda_device_index("2") == 2

    with pytest.raises(ValueError, match="CUDA device"):
        _cuda_device_index("cpu")
