from __future__ import annotations

from src.train import _model_source


def test_from_scratch_uses_yolo_architecture_yaml() -> None:
    assert _model_source("yolo11n.pt", from_scratch=True) == "yolo11n.yaml"


def test_pretrained_training_keeps_model_source() -> None:
    assert _model_source("yolo11n.pt", from_scratch=False) == "yolo11n.pt"
