from __future__ import annotations

import argparse
from pathlib import Path
import struct


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
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional destination for the exported .engine file.",
    )
    return parser


def write_runtime_engine(exported_engine: Path, output: Path) -> None:
    data = exported_engine.read_bytes()
    if data.startswith(b"ftrt"):
        output.write_bytes(data)
        return

    if len(data) < 8:
        raise ValueError(f"exported engine is too small: {exported_engine}")

    metadata_size = struct.unpack("<I", data[:4])[0]
    plan_offset = 4 + metadata_size
    if plan_offset >= len(data) or not data[plan_offset:].startswith(b"ftrt"):
        raise ValueError(
            "exported engine does not contain a raw TensorRT plan after metadata",
        )
    output.write_bytes(data[plan_offset:])


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
    exported_engine = Path(exported_path)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        if exported_engine.resolve() != args.output.resolve():
            write_runtime_engine(exported_engine, args.output)
            exported_engine.unlink()
        else:
            temporary_output = args.output.with_suffix(f"{args.output.suffix}.raw")
            write_runtime_engine(exported_engine, temporary_output)
            temporary_output.replace(args.output)
        exported_engine = args.output
    print(exported_engine)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
