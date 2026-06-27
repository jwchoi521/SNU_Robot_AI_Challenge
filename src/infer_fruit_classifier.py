from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from src.fruit_classifier import (
        crop_rgb,
        load_fruit_classifier,
        predict_fruit,
        read_image_rgb,
    )
except ModuleNotFoundError:
    from fruit_classifier import (  # type: ignore[no-redef]
        crop_rgb,
        load_fruit_classifier,
        predict_fruit,
        read_image_rgb,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Classify a fruit from an image or cube crop.",
    )
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--image", type=Path, required=True)
    parser.add_argument(
        "--bbox",
        type=float,
        nargs=4,
        metavar=("X1", "Y1", "X2", "Y2"),
        default=None,
        help="Optional cube bbox crop in xyxy pixels.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=None,
        help="Override the checkpoint threshold for no-fruit decisions.",
    )
    parser.add_argument("--device", default=None)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    model, classes, image_size, checkpoint_threshold = load_fruit_classifier(
        args.model,
        device=args.device,
    )
    image_rgb = read_image_rgb(args.image)
    if args.bbox is not None:
        image_rgb = crop_rgb(image_rgb, args.bbox)
    prediction = predict_fruit(
        model=model,
        image_rgb=image_rgb,
        classes=classes,
        image_size=image_size,
        threshold=args.threshold
        if args.threshold is not None
        else checkpoint_threshold,
        device=args.device,
    )
    print(json.dumps(prediction.as_dict(), ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
