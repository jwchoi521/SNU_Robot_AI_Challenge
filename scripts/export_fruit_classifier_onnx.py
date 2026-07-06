from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import torch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.fruit_classifier import load_fruit_classifier  # noqa: E402


def export_fruit_classifier_onnx(args: argparse.Namespace) -> Path:
    model, classes, image_size, threshold = load_fruit_classifier(
        args.model,
        device=args.device,
    )
    model.eval()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    export_image_size = args.imgsz if args.imgsz is not None else image_size
    if export_image_size <= 0:
        raise ValueError("--imgsz must be positive")

    dummy = torch.zeros(
        (1, 3, export_image_size, export_image_size),
        dtype=torch.float32,
        device=next(model.parameters()).device,
    )
    dynamic_axes = None
    if args.dynamic_batch:
        dynamic_axes = {
            "input": {0: "batch"},
            "logits": {0: "batch"},
        }

    torch.onnx.export(
        model,
        dummy,
        args.output,
        input_names=["input"],
        output_names=["logits"],
        dynamic_axes=dynamic_axes,
        opset_version=args.opset,
        dynamo=False,
        external_data=False,
    )

    metadata = {
        "classes": list(classes),
        "checkpoint_image_size": image_size,
        "image_size": export_image_size,
        "threshold": threshold,
        "input_name": "input",
        "output_name": "logits",
        "normalization": {
            "mean": [0.5, 0.5, 0.5],
            "std": [0.5, 0.5, 0.5],
        },
    }
    metadata_path = args.output.with_suffix(".json")
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(args.output)
    print(metadata_path)
    return args.output


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Export the cube fruit classifier checkpoint to ONNX.",
    )
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("models/cube_fruit_classifier.onnx"))
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--opset", type=int, default=17)
    parser.add_argument(
        "--imgsz",
        type=int,
        default=None,
        help="Override the checkpoint image_size for a fixed-size ONNX export.",
    )
    parser.add_argument("--dynamic-batch", action="store_true")
    return parser


def main() -> int:
    export_fruit_classifier_onnx(build_parser().parse_args())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
