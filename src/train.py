from __future__ import annotations

import argparse
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Train a YOLO detector.")
    parser.add_argument("--model", default="yolo11n.pt")
    parser.add_argument("--data", type=Path, default=Path("dataset/data.yaml"))
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--batch", type=int, default=16)
    parser.add_argument("--device", default=None)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--project", default="runs/detect")
    parser.add_argument("--name", default="robot_yolo")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument(
        "--from-scratch",
        action="store_true",
        help="Use the matching YOLO architecture YAML instead of pretrained weights.",
    )
    return parser


def _model_source(model: str, from_scratch: bool) -> str:
    if not from_scratch:
        return model
    path = Path(model)
    if path.suffix == ".pt":
        return str(path.with_suffix(".yaml"))
    return model


def main() -> int:
    args = build_parser().parse_args()

    from ultralytics import YOLO

    model = YOLO(_model_source(args.model, args.from_scratch))
    model.train(
        data=str(args.data),
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
        workers=args.workers,
        project=args.project,
        name=args.name,
        seed=args.seed,
        resume=args.resume,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
