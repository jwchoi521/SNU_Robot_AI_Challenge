from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import numpy as np
import torch
from torch import nn


FRUIT_CLASSES: tuple[str, ...] = ("apple", "orange", "banana", "pineapple")
DEFAULT_FRUIT_THRESHOLD = 0.7
NORMALIZE_MEAN = np.array([0.5, 0.5, 0.5], dtype=np.float32)
NORMALIZE_STD = np.array([0.5, 0.5, 0.5], dtype=np.float32)


@dataclass(frozen=True)
class FruitPrediction:
    fruit_kind: str | None
    confidence: float
    probabilities: dict[str, float]

    def as_dict(self) -> dict[str, object]:
        return {
            "fruit_kind": self.fruit_kind,
            "confidence": round(self.confidence, 4),
            "probabilities": {
                name: round(probability, 4)
                for name, probability in self.probabilities.items()
            },
        }


class FruitClassifier(nn.Module):
    def __init__(self, num_classes: int = len(FRUIT_CLASSES)) -> None:
        super().__init__()
        self.features = nn.Sequential(
            _conv_block(3, 32),
            nn.MaxPool2d(2),
            _conv_block(32, 64),
            nn.MaxPool2d(2),
            _conv_block(64, 128),
            nn.MaxPool2d(2),
            _conv_block(128, 256),
            nn.AdaptiveAvgPool2d((1, 1)),
        )
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Dropout(p=0.25),
            nn.Linear(256, num_classes),
        )

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        return self.classifier(self.features(inputs))


def _conv_block(in_channels: int, out_channels: int) -> nn.Sequential:
    return nn.Sequential(
        nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1, bias=False),
        nn.BatchNorm2d(out_channels),
        nn.SiLU(inplace=True),
    )


def read_image_rgb(path: Path) -> np.ndarray:
    import cv2

    image_bgr = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image_bgr is None:
        raise ValueError(f"image could not be read: {path}")
    return cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)


def crop_rgb(image_rgb: np.ndarray, bbox_xyxy: Sequence[float]) -> np.ndarray:
    height, width = image_rgb.shape[:2]
    x1, y1, x2, y2 = (int(round(value)) for value in bbox_xyxy)
    left = max(0, min(width, x1))
    top = max(0, min(height, y1))
    right = max(0, min(width, x2))
    bottom = max(0, min(height, y2))
    if right <= left or bottom <= top:
        raise ValueError(f"invalid crop bbox: {tuple(bbox_xyxy)}")
    return image_rgb[top:bottom, left:right]


def preprocess_rgb(image_rgb: np.ndarray, image_size: int) -> torch.Tensor:
    import cv2

    resized = cv2.resize(
        image_rgb,
        (image_size, image_size),
        interpolation=cv2.INTER_AREA,
    )
    normalized = resized.astype(np.float32) / 255.0
    normalized = (normalized - NORMALIZE_MEAN) / NORMALIZE_STD
    return torch.from_numpy(normalized.transpose(2, 0, 1)).float()


def load_fruit_classifier(
    checkpoint_path: Path,
    device: str | torch.device | None = None,
) -> tuple[FruitClassifier, tuple[str, ...], int, float]:
    selected_device = torch.device(
        device or ("cuda" if torch.cuda.is_available() else "cpu"),
    )
    checkpoint = torch.load(checkpoint_path, map_location=selected_device)
    classes = tuple(checkpoint.get("classes", FRUIT_CLASSES))
    image_size = int(checkpoint.get("image_size", 100))
    threshold = float(checkpoint.get("threshold", DEFAULT_FRUIT_THRESHOLD))
    model = FruitClassifier(num_classes=len(classes))
    model.load_state_dict(checkpoint["model_state"])
    model.to(selected_device)
    model.eval()
    return model, classes, image_size, threshold


@torch.no_grad()
def predict_fruit(
    model: FruitClassifier,
    image_rgb: np.ndarray,
    classes: Sequence[str] = FRUIT_CLASSES,
    image_size: int = 100,
    threshold: float = DEFAULT_FRUIT_THRESHOLD,
    device: str | torch.device | None = None,
) -> FruitPrediction:
    selected_device = torch.device(device or next(model.parameters()).device)
    tensor = preprocess_rgb(image_rgb, image_size).unsqueeze(0).to(selected_device)
    probabilities = torch.softmax(model(tensor), dim=1)[0].cpu().numpy()
    best_index = int(probabilities.argmax())
    confidence = float(probabilities[best_index])
    fruit_kind = str(classes[best_index]) if confidence >= threshold else None
    return FruitPrediction(
        fruit_kind=fruit_kind,
        confidence=confidence,
        probabilities={
            str(class_name): float(probability)
            for class_name, probability in zip(classes, probabilities)
        },
    )
