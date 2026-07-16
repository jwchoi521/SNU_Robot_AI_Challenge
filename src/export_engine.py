from __future__ import annotations

import argparse
import json
from pathlib import Path


def _load_torch_checkpoint(path: Path) -> dict[str, object] | None:
    import torch

    try:
        checkpoint = torch.load(path, map_location="cpu")
    except Exception:
        return None
    if isinstance(checkpoint, dict):
        return checkpoint
    return None


def _export_fruit_classifier(
    checkpoint: dict[str, object],
    model_path: Path,
    imgsz: int,
    half: bool,
    dynamic: bool,
    workspace: float | None,
) -> Path:
    import torch

    try:
        from src.fruit_classifier import (
            DEFAULT_FRUIT_THRESHOLD,
            NORMALIZE_MEAN,
            NORMALIZE_STD,
            FruitClassifier,
        )
    except ModuleNotFoundError:
        from fruit_classifier import (  # type: ignore[no-redef]
            DEFAULT_FRUIT_THRESHOLD,
            NORMALIZE_MEAN,
            NORMALIZE_STD,
            FruitClassifier,
        )

    model_state = checkpoint.get("model_state")
    if not isinstance(model_state, dict):
        raise TypeError(f"classifier checkpoint has no model_state: {model_path}")

    classes = tuple(str(item) for item in checkpoint.get("classes", ()))
    if not classes:
        raise ValueError(f"classifier checkpoint has no classes: {model_path}")

    model = FruitClassifier(num_classes=len(classes))
    model.load_state_dict(model_state)
    model.eval()

    onnx_path = model_path.with_suffix(".onnx")
    engine_path = model_path.with_suffix(".engine")
    metadata_path = model_path.with_suffix(".json")
    input_shape = (1, 3, imgsz, imgsz)
    dummy_input = torch.zeros(input_shape, dtype=torch.float32)

    dynamic_axes = None
    if dynamic:
        dynamic_axes = {
            "input": {0: "batch", 2: "height", 3: "width"},
            "logits": {0: "batch"},
        }

    torch.onnx.export(
        model,
        dummy_input,
        onnx_path,
        input_names=["input"],
        output_names=["logits"],
        dynamic_axes=dynamic_axes,
        opset_version=18,
        do_constant_folding=True,
    )
    print(f"ONNX saved as {onnx_path}")

    _build_tensorrt_engine(
        onnx_path=onnx_path,
        engine_path=engine_path,
        input_shape=input_shape,
        half=half,
        dynamic=dynamic,
        workspace=workspace,
    )

    metadata = {
        "classes": list(classes),
        "checkpoint_image_size": int(checkpoint.get("image_size", imgsz)),
        "image_size": imgsz,
        "threshold": float(checkpoint.get("threshold", DEFAULT_FRUIT_THRESHOLD)),
        "input_name": "input",
        "output_name": "logits",
        "normalization": {
            "mean": [float(value) for value in NORMALIZE_MEAN.tolist()],
            "std": [float(value) for value in NORMALIZE_STD.tolist()],
        },
    }
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(f"Metadata saved as {metadata_path}")
    return engine_path


def _build_tensorrt_engine(
    onnx_path: Path,
    engine_path: Path,
    input_shape: tuple[int, int, int, int],
    half: bool,
    dynamic: bool,
    workspace: float | None,
) -> None:
    import tensorrt as trt

    logger = trt.Logger(trt.Logger.INFO)
    builder = trt.Builder(logger)
    network_flags = 1 << int(trt.NetworkDefinitionCreationFlag.EXPLICIT_BATCH)
    network = builder.create_network(network_flags)
    parser = trt.OnnxParser(network, logger)

    if not parser.parse_from_file(str(onnx_path)):
        errors = "\n".join(
            str(parser.get_error(index)) for index in range(parser.num_errors)
        )
        raise RuntimeError(f"TensorRT ONNX parse failed:\n{errors}")

    config = builder.create_builder_config()
    if workspace is not None:
        workspace_bytes = int(workspace * (1 << 30))
        config.set_memory_pool_limit(trt.MemoryPoolType.WORKSPACE, workspace_bytes)
    if half:
        if not builder.platform_has_fast_fp16:
            print("TensorRT: FP16 requested, but platform_has_fast_fp16 is false")
        config.set_flag(trt.BuilderFlag.FP16)

    if dynamic:
        profile = builder.create_optimization_profile()
        input_name = network.get_input(0).name
        min_shape = (
            1,
            input_shape[1],
            max(32, input_shape[2] // 2),
            max(32, input_shape[3] // 2),
        )
        profile.set_shape(input_name, min_shape, input_shape, input_shape)
        config.add_optimization_profile(profile)

    print(
        "TensorRT: building "
        f"{'FP16' if half else 'FP32'} engine as {engine_path}"
    )
    serialized_engine = builder.build_serialized_network(network, config)
    if serialized_engine is None:
        raise RuntimeError("TensorRT engine build failed")
    engine_path.write_bytes(bytes(serialized_engine))
    print(f"TensorRT engine saved as {engine_path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Export a YOLO or fruit classifier model to a TensorRT engine.",
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
    model_path = Path(args.model)

    checkpoint = _load_torch_checkpoint(model_path)
    if checkpoint is not None and "model_state" in checkpoint:
        exported_path = _export_fruit_classifier(
            checkpoint=checkpoint,
            model_path=model_path,
            imgsz=args.imgsz,
            half=args.half,
            dynamic=args.dynamic,
            workspace=args.workspace,
        )
        print(exported_path)
        return 0

    from ultralytics import YOLO

    model = YOLO(model_path)
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
