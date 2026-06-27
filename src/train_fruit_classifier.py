from __future__ import annotations

import argparse
import json
import random
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset

try:
    from src.fruit_classifier import (
        DEFAULT_FRUIT_THRESHOLD,
        FRUIT_CLASSES,
        FruitClassifier,
        preprocess_rgb,
        read_image_rgb,
    )
except ModuleNotFoundError:
    from fruit_classifier import (  # type: ignore[no-redef]
        DEFAULT_FRUIT_THRESHOLD,
        FRUIT_CLASSES,
        FruitClassifier,
        preprocess_rgb,
        read_image_rgb,
    )


IMAGE_SUFFIXES = {".bmp", ".jpg", ".jpeg", ".png", ".webp"}


@dataclass(frozen=True)
class EpochMetrics:
    epoch: int
    train_loss: float
    train_accuracy: float
    val_loss: float
    val_accuracy: float


class FruitImageFolder(Dataset):
    def __init__(
        self,
        root: Path,
        split: str,
        image_size: int,
        augment: bool = False,
    ) -> None:
        self.root = root / split
        self.image_size = image_size
        self.augment = augment
        self.samples: list[tuple[Path, int]] = []
        for class_index, class_name in enumerate(FRUIT_CLASSES):
            class_dir = self.root / class_name
            if not class_dir.exists():
                continue
            self.samples.extend(
                (path, class_index)
                for path in sorted(class_dir.rglob("*"))
                if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
            )
        if not self.samples:
            raise ValueError(f"no fruit images found in {self.root}")

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, index: int) -> tuple[torch.Tensor, int]:
        path, label = self.samples[index]
        image_rgb = read_image_rgb(path)
        if self.augment:
            image_rgb = _augment_image(image_rgb)
        return preprocess_rgb(image_rgb, self.image_size), label


def _augment_image(image_rgb: np.ndarray) -> np.ndarray:
    augmented = image_rgb
    if random.random() < 0.5:
        augmented = np.ascontiguousarray(augmented[:, ::-1])
    brightness = random.uniform(0.9, 1.1)
    contrast = random.uniform(0.9, 1.1)
    adjusted = augmented.astype(np.float32) * contrast
    adjusted = (adjusted - 127.5) * brightness + 127.5
    return np.clip(adjusted, 0, 255).astype(np.uint8)


def _resolve_device(device: str | None) -> torch.device:
    if device:
        return torch.device(device)
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def _seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def _make_loader(
    dataset: Dataset[tuple[torch.Tensor, int]],
    batch_size: int,
    workers: int,
    shuffle: bool,
) -> DataLoader[tuple[torch.Tensor, int]]:
    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        num_workers=workers,
        pin_memory=torch.cuda.is_available(),
    )


def _run_epoch(
    model: FruitClassifier,
    loader: DataLoader[tuple[torch.Tensor, int]],
    criterion: nn.Module,
    device: torch.device,
    optimizer: torch.optim.Optimizer | None = None,
) -> tuple[float, float]:
    training = optimizer is not None
    model.train(training)
    total_loss = 0.0
    total_correct = 0
    total_samples = 0

    for inputs, labels in loader:
        inputs = inputs.to(device)
        labels = labels.to(device)
        if training:
            optimizer.zero_grad(set_to_none=True)

        with torch.set_grad_enabled(training):
            logits = model(inputs)
            loss = criterion(logits, labels)
            if training:
                loss.backward()
                optimizer.step()

        batch_size = labels.shape[0]
        total_loss += float(loss.item()) * batch_size
        total_correct += int((logits.argmax(dim=1) == labels).sum().item())
        total_samples += batch_size

    return total_loss / total_samples, total_correct / total_samples


def train_classifier(args: argparse.Namespace) -> list[EpochMetrics]:
    _seed_everything(args.seed)
    device = _resolve_device(args.device)
    train_dataset = FruitImageFolder(
        root=args.data_root,
        split="train",
        image_size=args.imgsz,
        augment=True,
    )
    val_dataset = FruitImageFolder(
        root=args.data_root,
        split="val",
        image_size=args.imgsz,
    )
    train_loader = _make_loader(
        train_dataset,
        batch_size=args.batch,
        workers=args.workers,
        shuffle=True,
    )
    val_loader = _make_loader(
        val_dataset,
        batch_size=args.batch,
        workers=args.workers,
        shuffle=False,
    )

    model = FruitClassifier(num_classes=len(FRUIT_CLASSES)).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=args.lr,
        weight_decay=args.weight_decay,
    )

    args.output.mkdir(parents=True, exist_ok=True)
    best_accuracy = -1.0
    metrics: list[EpochMetrics] = []

    for epoch in range(1, args.epochs + 1):
        train_loss, train_accuracy = _run_epoch(
            model,
            train_loader,
            criterion,
            device,
            optimizer,
        )
        val_loss, val_accuracy = _run_epoch(model, val_loader, criterion, device)
        epoch_metrics = EpochMetrics(
            epoch=epoch,
            train_loss=train_loss,
            train_accuracy=train_accuracy,
            val_loss=val_loss,
            val_accuracy=val_accuracy,
        )
        metrics.append(epoch_metrics)
        print(
            f"epoch={epoch:03d} "
            f"train_loss={train_loss:.4f} train_acc={train_accuracy:.4f} "
            f"val_loss={val_loss:.4f} val_acc={val_accuracy:.4f}"
        )

        checkpoint = {
            "model_state": model.state_dict(),
            "classes": list(FRUIT_CLASSES),
            "image_size": args.imgsz,
            "threshold": args.threshold,
            "epoch": epoch,
            "val_accuracy": val_accuracy,
        }
        torch.save(checkpoint, args.output / "last.pt")
        if val_accuracy > best_accuracy:
            best_accuracy = val_accuracy
            torch.save(checkpoint, args.output / "best.pt")

    metrics_path = args.output / "metrics.json"
    metrics_path.write_text(
        json.dumps([asdict(item) for item in metrics], indent=2),
        encoding="utf-8",
    )
    return metrics


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Train a 4-class fruit classifier for cube crops.",
    )
    parser.add_argument("--data-root", type=Path, default=Path("dataset/fruits360"))
    parser.add_argument("--output", type=Path, default=Path("runs/classify/fruits360"))
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--batch", type=int, default=64)
    parser.add_argument("--imgsz", type=int, default=100)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--device", default=None)
    parser.add_argument("--workers", type=int, default=0)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--threshold", type=float, default=DEFAULT_FRUIT_THRESHOLD)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    train_classifier(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
