from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any


INPUT_NAME = "images"
OUTPUT_NAME = "logits"
TRTEXEC_CANDIDATES = (
    "/usr/src/tensorrt/bin/trtexec",
    "/usr/bin/trtexec",
)


def _default_output_path(model_path: Path, suffix: str) -> Path:
    return model_path.with_suffix(suffix)


def _resolve_device(device: str | None) -> str:
    import torch

    if device is None:
        return "cuda:0" if torch.cuda.is_available() else "cpu"
    if device.isdigit():
        return f"cuda:{device}"
    return device


def _find_trtexec(explicit_path: Path | None) -> Path:
    if explicit_path is not None:
        if explicit_path.exists():
            return explicit_path
        raise FileNotFoundError(f"trtexec not found: {explicit_path}")

    found = shutil.which("trtexec")
    if found:
        return Path(found)

    for candidate in TRTEXEC_CANDIDATES:
        path = Path(candidate)
        if path.exists():
            return path

    raise FileNotFoundError(
        "trtexec not found. Install TensorRT tools or pass --trtexec."
    )


def _validate_dynamic_batches(
    min_batch: int,
    opt_batch: int,
    max_batch: int,
) -> None:
    if min_batch <= 0 or opt_batch <= 0 or max_batch <= 0:
        raise ValueError("dynamic batch sizes must be positive")
    if not min_batch <= opt_batch <= max_batch:
        raise ValueError(
            "dynamic batch sizes must satisfy min_batch <= opt_batch <= max_batch"
        )


def _trtexec_command(
    trtexec: Path,
    onnx_path: Path,
    engine_path: Path,
    image_size: int,
    batch: int,
    half: bool,
    dynamic_batch: bool,
    min_batch: int,
    opt_batch: int,
    max_batch: int,
    workspace_mib: int | None,
    verbose: bool,
) -> list[str]:
    command = [
        str(trtexec),
        f"--onnx={onnx_path}",
        f"--saveEngine={engine_path}",
    ]
    if half:
        command.append("--fp16")
    if dynamic_batch:
        _validate_dynamic_batches(min_batch, opt_batch, max_batch)
        command.extend(
            [
                f"--minShapes={INPUT_NAME}:{min_batch}x3x{image_size}x{image_size}",
                f"--optShapes={INPUT_NAME}:{opt_batch}x3x{image_size}x{image_size}",
                f"--maxShapes={INPUT_NAME}:{max_batch}x3x{image_size}x{image_size}",
            ]
        )
    if workspace_mib is not None:
        command.append(f"--memPoolSize=workspace:{workspace_mib}")
    if verbose:
        command.append("--verbose")
    return command


def _load_classifier(
    checkpoint_path: Path,
    device: str,
) -> tuple[Any, dict[str, Any]]:
    import torch

    try:
        from src.fruit_classifier import FruitClassifier
    except ModuleNotFoundError:
        from fruit_classifier import FruitClassifier  # type: ignore[no-redef]

    checkpoint = torch.load(checkpoint_path, map_location=device)
    classes = tuple(checkpoint["classes"])
    image_size = int(checkpoint.get("image_size", 100))
    threshold = float(checkpoint.get("threshold", 0.7))
    model = FruitClassifier(num_classes=len(classes))
    model.load_state_dict(checkpoint["model_state"])
    model.to(device)
    model.eval()
    return model, {
        "classes": list(classes),
        "image_size": image_size,
        "threshold": threshold,
        "checkpoint_epoch": checkpoint.get("epoch"),
        "checkpoint_val_accuracy": checkpoint.get("val_accuracy"),
    }


def _export_onnx(
    model: Any,
    onnx_path: Path,
    image_size: int,
    batch: int,
    device: str,
    opset: int,
    dynamic_batch: bool,
) -> None:
    import torch

    onnx_path.parent.mkdir(parents=True, exist_ok=True)
    dummy_input = torch.zeros(batch, 3, image_size, image_size, device=device)
    dynamic_axes = None
    if dynamic_batch:
        dynamic_axes = {
            INPUT_NAME: {0: "batch"},
            OUTPUT_NAME: {0: "batch"},
        }
    torch.onnx.export(
        model,
        dummy_input,
        onnx_path,
        input_names=[INPUT_NAME],
        output_names=[OUTPUT_NAME],
        opset_version=opset,
        dynamic_axes=dynamic_axes,
        do_constant_folding=True,
    )


def _write_metadata(
    metadata_path: Path,
    metadata: dict[str, Any],
) -> None:
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(
        json.dumps(metadata, indent=2),
        encoding="utf-8",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Export a fruit classifier checkpoint to ONNX or TensorRT engine.",
    )
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument(
        "--format",
        choices=("onnx", "engine", "both"),
        default="engine",
        help="Export ONNX only, TensorRT engine, or both.",
    )
    parser.add_argument("--output-onnx", type=Path, default=None)
    parser.add_argument("--output-engine", type=Path, default=None)
    parser.add_argument(
        "--metadata",
        type=Path,
        default=None,
        help="Path for JSON metadata. Defaults next to the engine or ONNX.",
    )
    parser.add_argument(
        "--imgsz",
        type=int,
        default=None,
        help="Classifier input size. Defaults to checkpoint image_size.",
    )
    parser.add_argument("--batch", type=int, default=1)
    parser.add_argument("--device", default=None)
    parser.add_argument("--opset", type=int, default=17)
    parser.add_argument(
        "--half",
        action="store_true",
        help="Build the TensorRT engine with FP16. The ONNX graph stays FP32.",
    )
    parser.add_argument("--dynamic-batch", action="store_true")
    parser.add_argument("--min-batch", type=int, default=1)
    parser.add_argument("--opt-batch", type=int, default=None)
    parser.add_argument("--max-batch", type=int, default=None)
    parser.add_argument("--workspace-mib", type=int, default=None)
    parser.add_argument("--trtexec", type=Path, default=None)
    parser.add_argument("--verbose", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.batch <= 0:
        raise ValueError("--batch must be positive")

    device = _resolve_device(args.device)
    model, checkpoint_metadata = _load_classifier(args.model, device=device)
    checkpoint_image_size = int(checkpoint_metadata["image_size"])
    image_size = args.imgsz or checkpoint_image_size
    if image_size <= 0:
        raise ValueError("--imgsz must be positive")
    if args.imgsz is not None and args.imgsz != checkpoint_image_size:
        print(
            "WARN checkpoint image_size="
            f"{checkpoint_image_size}, exporting with imgsz={args.imgsz}"
        )

    onnx_path = args.output_onnx or _default_output_path(args.model, ".onnx")
    engine_path = args.output_engine or _default_output_path(args.model, ".engine")
    export_engine = args.format in {"engine", "both"}
    export_onnx = args.format in {"onnx", "both"} or export_engine

    opt_batch = args.opt_batch if args.opt_batch is not None else args.batch
    max_batch = args.max_batch if args.max_batch is not None else max(args.batch, opt_batch)

    if export_onnx:
        _export_onnx(
            model=model,
            onnx_path=onnx_path,
            image_size=image_size,
            batch=args.batch,
            device=device,
            opset=args.opset,
            dynamic_batch=args.dynamic_batch,
        )
        print(f"onnx={onnx_path}")

    if export_engine:
        trtexec = _find_trtexec(args.trtexec)
        engine_path.parent.mkdir(parents=True, exist_ok=True)
        command = _trtexec_command(
            trtexec=trtexec,
            onnx_path=onnx_path,
            engine_path=engine_path,
            image_size=image_size,
            batch=args.batch,
            half=args.half,
            dynamic_batch=args.dynamic_batch,
            min_batch=args.min_batch,
            opt_batch=opt_batch,
            max_batch=max_batch,
            workspace_mib=args.workspace_mib,
            verbose=args.verbose,
        )
        print("trtexec=" + " ".join(command))
        subprocess.run(command, check=True)
        print(f"engine={engine_path}")

    metadata_path = args.metadata
    if metadata_path is None:
        metadata_path = (
            engine_path.with_suffix(".json")
            if export_engine
            else onnx_path.with_suffix(".json")
        )
    _write_metadata(
        metadata_path,
        {
            **checkpoint_metadata,
            "source_checkpoint": str(args.model),
            "onnx": str(onnx_path),
            "engine": str(engine_path) if export_engine else None,
            "input_name": INPUT_NAME,
            "output_name": OUTPUT_NAME,
            "input_shape": [args.batch, 3, image_size, image_size],
            "dynamic_batch": args.dynamic_batch,
            "half": args.half,
            "normalize_mean": [0.5, 0.5, 0.5],
            "normalize_std": [0.5, 0.5, 0.5],
        },
    )
    print(f"metadata={metadata_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
