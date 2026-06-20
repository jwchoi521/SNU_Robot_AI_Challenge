from __future__ import annotations

import argparse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Export a YOLO model to a TensorRT engine.",
    )
    parser.add_argument("--model", required=True, help="Path to a .pt model.")
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--device", default=0)
    parser.add_argument("--half", action="store_true")
    parser.add_argument("--dynamic", action="store_true")
    parser.add_argument("--simplify", action="store_true")
    parser.add_argument("--workspace", type=float, default=None)
    return parser


def main() -> int:
    args = build_parser().parse_args()

    from ultralytics import YOLO

    model = YOLO(args.model)
    exported_path = model.export(
        format="engine",
        imgsz=args.imgsz,
        device=args.device,
        half=args.half,
        dynamic=args.dynamic,
        simplify=args.simplify,
        workspace=args.workspace,
    )
    print(exported_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
