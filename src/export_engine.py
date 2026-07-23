from __future__ import annotations

import argparse
import json
from pathlib import Path


def _strip_ultralytics_engine_metadata(engine_path: Path) -> Path:
    payload = engine_path.read_bytes()
    if len(payload) < 4:
        raise ValueError(f"engine is too small to contain metadata: {engine_path}")

    metadata_length = int.from_bytes(
        payload[:4],
        byteorder="little",
        signed=True,
    )
    metadata_end = 4 + metadata_length
    if metadata_length <= 0 or metadata_end >= len(payload):
        raise ValueError(
            f"engine does not contain an Ultralytics metadata prefix: {engine_path}"
        )

    try:
        metadata = json.loads(payload[4:metadata_end].decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(
            f"engine does not contain valid Ultralytics metadata: {engine_path}"
        ) from exc
    if not isinstance(metadata, dict) or not {"names", "task"} <= metadata.keys():
        raise ValueError(
            f"engine metadata is not an Ultralytics YOLO payload: {engine_path}"
        )

    engine_payload = payload[metadata_end:]
    metadata_path = engine_path.with_name(f"{engine_path.name}.metadata.json")
    temporary_path = engine_path.with_name(f"{engine_path.name}.tmp")
    try:
        temporary_path.write_bytes(engine_payload)
        metadata_path.write_text(
            json.dumps(metadata, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary_path.replace(engine_path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()

    print(f"Raw TensorRT engine saved as {engine_path}")
    print(f"Ultralytics metadata saved as {metadata_path}")
    return metadata_path


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
    parser.add_argument(
        "--strip-metadata",
        action="store_true",
        help=(
            "Remove the Ultralytics metadata prefix from a YOLO TensorRT engine "
            "and save that metadata in a sidecar .engine.metadata.json file."
        ),
    )
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
    if args.strip_metadata:
        _strip_ultralytics_engine_metadata(Path(exported_path))
    print(exported_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
