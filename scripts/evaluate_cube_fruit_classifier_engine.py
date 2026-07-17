from __future__ import annotations

import argparse
import csv
import importlib
import json
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.evaluate_cube_fruit_classifier import (  # noqa: E402
    NO_FRUIT_CLASS,
    _bbox_text,
    _detect_cube_boxes,
    collect_images,
    truth_from_parent,
)


DEFAULT_CLASSES = ("apple", "orange", "banana", "pineapple", NO_FRUIT_CLASS)
DEFAULT_IMAGE_SIZE = 256
DEFAULT_THRESHOLD = 0.7
DEFAULT_INPUT_NAME = "images"
DEFAULT_OUTPUT_NAME = "logits"
DEFAULT_NORMALIZE_MEAN = (0.5, 0.5, 0.5)
DEFAULT_NORMALIZE_STD = (0.5, 0.5, 0.5)


@dataclass(frozen=True)
class EngineMetadata:
    classes: tuple[str, ...]
    image_size: int
    threshold: float
    input_name: str
    output_name: str
    normalize_mean: tuple[float, float, float]
    normalize_std: tuple[float, float, float]


@dataclass(frozen=True)
class EnginePrediction:
    fruit_kind: str | None
    confidence: float
    probabilities: dict[str, float]


def _sequence_of_three(
    values: Sequence[Any] | None,
    default: tuple[float, float, float],
) -> tuple[float, float, float]:
    if values is None:
        return default
    converted = tuple(float(value) for value in values)
    if len(converted) != 3:
        raise ValueError(f"expected three normalization values, got {values}")
    return converted  # type: ignore[return-value]


def _metadata_path_for_engine(engine_path: Path) -> Path:
    return engine_path.with_suffix(".json")


def load_engine_metadata(metadata_path: Path) -> EngineMetadata:
    data = json.loads(metadata_path.read_text(encoding="utf-8"))
    classes = tuple(str(class_name) for class_name in data.get("classes", ()))
    if not classes:
        classes = DEFAULT_CLASSES

    input_shape = data.get("input_shape", ())
    input_size_from_shape = None
    if isinstance(input_shape, list) and len(input_shape) >= 4:
        input_size_from_shape = int(input_shape[-1])

    normalization = data.get("normalization", {})
    normalize_mean = data.get("normalize_mean")
    normalize_std = data.get("normalize_std")
    if isinstance(normalization, dict):
        normalize_mean = normalize_mean or normalization.get("mean")
        normalize_std = normalize_std or normalization.get("std")

    return EngineMetadata(
        classes=classes,
        image_size=int(
            data.get(
                "image_size",
                data.get("checkpoint_image_size", input_size_from_shape or DEFAULT_IMAGE_SIZE),
            )
        ),
        threshold=float(data.get("threshold", DEFAULT_THRESHOLD)),
        input_name=str(data.get("input_name", DEFAULT_INPUT_NAME)),
        output_name=str(data.get("output_name", DEFAULT_OUTPUT_NAME)),
        normalize_mean=_sequence_of_three(normalize_mean, DEFAULT_NORMALIZE_MEAN),
        normalize_std=_sequence_of_three(normalize_std, DEFAULT_NORMALIZE_STD),
    )


def preprocess_rgb_for_engine(
    image_rgb: np.ndarray,
    image_size: int,
    normalize_mean: Sequence[float],
    normalize_std: Sequence[float],
) -> np.ndarray:
    import cv2

    resized = cv2.resize(
        image_rgb,
        (image_size, image_size),
        interpolation=cv2.INTER_AREA,
    )
    normalized = resized.astype(np.float32) / 255.0
    mean = np.asarray(normalize_mean, dtype=np.float32)
    std = np.asarray(normalize_std, dtype=np.float32)
    normalized = (normalized - mean) / std
    chw = normalized.transpose(2, 0, 1)
    return np.ascontiguousarray(chw[None, :, :, :], dtype=np.float32)


def softmax(logits: np.ndarray) -> np.ndarray:
    values = np.asarray(logits, dtype=np.float32).reshape(-1)
    values = values - np.max(values)
    exp_values = np.exp(values)
    return exp_values / np.sum(exp_values)


def prediction_from_logits(
    logits: np.ndarray,
    classes: Sequence[str],
    threshold: float,
) -> EnginePrediction:
    probabilities_array = softmax(logits)
    if len(probabilities_array) != len(classes):
        raise ValueError(
            "classifier output size does not match classes: "
            f"{len(probabilities_array)} != {len(classes)}"
        )
    best_index = int(probabilities_array.argmax())
    best_class = str(classes[best_index])
    confidence = float(probabilities_array[best_index])
    fruit_kind = (
        best_class
        if best_class != NO_FRUIT_CLASS and confidence >= threshold
        else None
    )
    return EnginePrediction(
        fruit_kind=fruit_kind,
        confidence=confidence,
        probabilities={
            str(class_name): float(probability)
            for class_name, probability in zip(classes, probabilities_array)
        },
    )


def _best_class(probabilities: dict[str, float]) -> tuple[str, float]:
    if not probabilities:
        return "", 0.0
    class_name, probability = max(probabilities.items(), key=lambda item: item[1])
    return class_name, probability


def _cuda_device_index(device: str | int | None) -> int:
    if device is None:
        return 0
    text = str(device).strip().lower()
    if text == "cuda":
        return 0
    if text.startswith("cuda:"):
        return int(text.split(":", 1)[1])
    if text.isdigit():
        return int(text)
    raise ValueError(f"TensorRT evaluator needs a CUDA device, got: {device}")


def _check_cuda(result: Any) -> Any:
    if isinstance(result, tuple):
        status = result[0]
        payload = result[1:]
    else:
        status = result
        payload = ()
    if int(status) != 0:
        raise RuntimeError(f"CUDA runtime call failed with status {status}")
    if not payload:
        return None
    if len(payload) == 1:
        return payload[0]
    return payload


def _trt_dtype_to_numpy(trt_module: Any, dtype: Any) -> np.dtype:
    try:
        return np.dtype(trt_module.nptype(dtype))
    except Exception:
        return np.dtype(np.float32)


def _import_cudart() -> Any:
    errors: list[str] = []
    for module_name in (
        "cuda.cudart",
        "cuda.bindings.runtime",
        "cuda.bindings.cudart",
    ):
        try:
            return importlib.import_module(module_name)
        except ImportError as exc:
            errors.append(f"{module_name}: {exc}")

    try:
        from cuda import cudart

        return cudart
    except ImportError as exc:
        errors.append(f"from cuda import cudart: {exc}")

    raise ModuleNotFoundError(
        "TensorRT engine evaluation requires CUDA runtime Python bindings. "
        "Tried cuda.cudart, cuda.bindings.runtime, cuda.bindings.cudart, "
        f"and from cuda import cudart. Errors: {'; '.join(errors)}"
    )


class TensorRTClassifier:
    def __init__(
        self,
        engine_path: Path,
        metadata: EngineMetadata,
        device: str | int | None,
    ) -> None:
        try:
            import tensorrt as trt
            cudart = _import_cudart()
        except (ImportError, ModuleNotFoundError) as exc:
            raise ModuleNotFoundError(
                "TensorRT engine evaluation requires TensorRT Python bindings "
                "and CUDA runtime Python bindings on the Jetson."
            ) from exc

        self.trt = trt
        self.cudart = cudart
        self.metadata = metadata
        _check_cuda(cudart.cudaSetDevice(_cuda_device_index(device)))

        logger = trt.Logger(trt.Logger.WARNING)
        runtime = trt.Runtime(logger)
        engine_bytes = engine_path.read_bytes()
        self.engine = runtime.deserialize_cuda_engine(engine_bytes)
        if self.engine is None:
            raise RuntimeError(f"failed to deserialize TensorRT engine: {engine_path}")
        self.context = self.engine.create_execution_context()
        if self.context is None:
            raise RuntimeError("failed to create TensorRT execution context")

        if hasattr(self.engine, "num_io_tensors"):
            self._init_tensor_api(metadata)
        else:
            self._init_binding_api(metadata)

    def _init_tensor_api(self, metadata: EngineMetadata) -> None:
        names = [
            self.engine.get_tensor_name(index)
            for index in range(self.engine.num_io_tensors)
        ]
        input_names = [
            name
            for name in names
            if self.engine.get_tensor_mode(name) == self.trt.TensorIOMode.INPUT
        ]
        output_names = [
            name
            for name in names
            if self.engine.get_tensor_mode(name) == self.trt.TensorIOMode.OUTPUT
        ]
        self.input_name = (
            metadata.input_name if metadata.input_name in names else input_names[0]
        )
        self.output_name = (
            metadata.output_name if metadata.output_name in names else output_names[0]
        )
        self.output_dtype = _trt_dtype_to_numpy(
            self.trt,
            self.engine.get_tensor_dtype(self.output_name),
        )
        self.uses_tensor_api = True

    def _init_binding_api(self, metadata: EngineMetadata) -> None:
        names = [
            self.engine.get_binding_name(index)
            for index in range(self.engine.num_bindings)
        ]
        input_indices = [
            index
            for index in range(self.engine.num_bindings)
            if self.engine.binding_is_input(index)
        ]
        output_indices = [
            index
            for index in range(self.engine.num_bindings)
            if not self.engine.binding_is_input(index)
        ]
        self.input_name = (
            metadata.input_name if metadata.input_name in names else names[input_indices[0]]
        )
        self.output_name = (
            metadata.output_name if metadata.output_name in names else names[output_indices[0]]
        )
        self.input_index = self.engine.get_binding_index(self.input_name)
        self.output_index = self.engine.get_binding_index(self.output_name)
        self.output_dtype = _trt_dtype_to_numpy(
            self.trt,
            self.engine.get_binding_dtype(self.output_index),
        )
        self.uses_tensor_api = False

    def infer(self, input_array: np.ndarray) -> np.ndarray:
        input_array = np.ascontiguousarray(input_array, dtype=np.float32)
        if self.uses_tensor_api:
            return self._infer_tensor_api(input_array)
        return self._infer_binding_api(input_array)

    def _infer_tensor_api(self, input_array: np.ndarray) -> np.ndarray:
        input_shape = tuple(int(value) for value in input_array.shape)
        self.context.set_input_shape(self.input_name, input_shape)
        output_shape = tuple(
            int(value) for value in self.context.get_tensor_shape(self.output_name)
        )
        if any(dim <= 0 for dim in output_shape):
            raise RuntimeError(f"unresolved TensorRT output shape: {output_shape}")
        output_array = np.empty(output_shape, dtype=self.output_dtype)

        input_device = _check_cuda(self.cudart.cudaMalloc(input_array.nbytes))
        output_device = _check_cuda(self.cudart.cudaMalloc(output_array.nbytes))
        stream = _check_cuda(self.cudart.cudaStreamCreate())
        try:
            _check_cuda(
                self.cudart.cudaMemcpyAsync(
                    input_device,
                    input_array.ctypes.data,
                    input_array.nbytes,
                    self.cudart.cudaMemcpyKind.cudaMemcpyHostToDevice,
                    stream,
                )
            )
            self.context.set_tensor_address(self.input_name, int(input_device))
            self.context.set_tensor_address(self.output_name, int(output_device))
            if not self.context.execute_async_v3(stream_handle=stream):
                raise RuntimeError("TensorRT execute_async_v3 failed")
            _check_cuda(
                self.cudart.cudaMemcpyAsync(
                    output_array.ctypes.data,
                    output_device,
                    output_array.nbytes,
                    self.cudart.cudaMemcpyKind.cudaMemcpyDeviceToHost,
                    stream,
                )
            )
            _check_cuda(self.cudart.cudaStreamSynchronize(stream))
        finally:
            _check_cuda(self.cudart.cudaStreamDestroy(stream))
            _check_cuda(self.cudart.cudaFree(input_device))
            _check_cuda(self.cudart.cudaFree(output_device))
        return output_array.reshape(-1)

    def _infer_binding_api(self, input_array: np.ndarray) -> np.ndarray:
        input_shape = tuple(int(value) for value in input_array.shape)
        if hasattr(self.context, "set_binding_shape"):
            self.context.set_binding_shape(self.input_index, input_shape)
        output_shape = tuple(
            int(value) for value in self.context.get_binding_shape(self.output_index)
        )
        if any(dim <= 0 for dim in output_shape):
            output_shape = tuple(
                int(value)
                for value in self.engine.get_binding_shape(self.output_index)
            )
        if any(dim <= 0 for dim in output_shape):
            raise RuntimeError(f"unresolved TensorRT output shape: {output_shape}")

        output_array = np.empty(output_shape, dtype=self.output_dtype)
        input_device = _check_cuda(self.cudart.cudaMalloc(input_array.nbytes))
        output_device = _check_cuda(self.cudart.cudaMalloc(output_array.nbytes))
        bindings = [0] * self.engine.num_bindings
        bindings[self.input_index] = int(input_device)
        bindings[self.output_index] = int(output_device)
        try:
            _check_cuda(
                self.cudart.cudaMemcpy(
                    input_device,
                    input_array.ctypes.data,
                    input_array.nbytes,
                    self.cudart.cudaMemcpyKind.cudaMemcpyHostToDevice,
                )
            )
            if not self.context.execute_v2(bindings):
                raise RuntimeError("TensorRT execute_v2 failed")
            _check_cuda(
                self.cudart.cudaMemcpy(
                    output_array.ctypes.data,
                    output_device,
                    output_array.nbytes,
                    self.cudart.cudaMemcpyKind.cudaMemcpyDeviceToHost,
                )
            )
        finally:
            _check_cuda(self.cudart.cudaFree(input_device))
            _check_cuda(self.cudart.cudaFree(output_device))
        return output_array.reshape(-1)


def _resolve_metadata(args: argparse.Namespace) -> EngineMetadata:
    metadata_path = args.metadata or _metadata_path_for_engine(args.engine)
    if not metadata_path.exists():
        raise FileNotFoundError(
            f"metadata not found: {metadata_path}. Pass --metadata for the engine JSON."
        )
    metadata = load_engine_metadata(metadata_path)
    if args.input_size is not None:
        metadata = EngineMetadata(
            classes=metadata.classes,
            image_size=args.input_size,
            threshold=metadata.threshold,
            input_name=metadata.input_name,
            output_name=metadata.output_name,
            normalize_mean=metadata.normalize_mean,
            normalize_std=metadata.normalize_std,
        )
    return metadata


def evaluate_cube_fruit_classifier_engine(args: argparse.Namespace) -> int:
    from src.fruit_classifier import crop_rgb, read_image_rgb

    metadata = _resolve_metadata(args)
    threshold = args.threshold if args.threshold is not None else metadata.threshold
    image_paths = collect_images(args.source)
    if not image_paths:
        raise ValueError(f"no images found in {args.source}")

    classifier = TensorRTClassifier(args.engine, metadata, device=args.device)
    detector = None
    if args.detector_model:
        from ultralytics import YOLO

        detector = YOLO(args.detector_model)
    class_names_for_truth = tuple(metadata.classes) + (NO_FRUIT_CLASS,)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    prediction_counts: Counter[str] = Counter()
    truth_counts: Counter[str] = Counter()
    correct = 0
    labeled = 0
    rows = 0
    images_without_cube = 0

    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "image",
                "crop_index",
                "bbox_xyxy",
                "truth",
                "prediction",
                "best_class",
                "best_probability",
                "confidence",
                "correct",
                "probabilities_json",
                "error",
            ],
        )
        writer.writeheader()

        for image_path in image_paths:
            truth = (
                truth_from_parent(image_path, class_names_for_truth)
                if args.labels_from_parent
                else None
            )
            if truth is not None:
                truth_counts[truth] += 1

            image_rgb = read_image_rgb(image_path)
            if detector is not None:
                crop_boxes = _detect_cube_boxes(
                    detector=detector,
                    image_path=image_path,
                    cube_class_id=args.cube_class_id,
                    imgsz=args.imgsz,
                    conf=args.detector_conf,
                    iou=args.detector_iou,
                    device=args.device,
                )
                if args.max_crops:
                    crop_boxes = crop_boxes[: args.max_crops]
            elif args.bbox is not None:
                crop_boxes = [tuple(args.bbox)]
            else:
                height, width = image_rgb.shape[:2]
                crop_boxes = [(0.0, 0.0, float(width), float(height))]

            if not crop_boxes:
                images_without_cube += 1
                writer.writerow(
                    {
                        "image": str(image_path),
                        "crop_index": "",
                        "bbox_xyxy": "",
                        "truth": truth or "",
                        "prediction": "",
                        "best_class": "",
                        "best_probability": "",
                        "confidence": "",
                        "correct": "",
                        "probabilities_json": "{}",
                        "error": "no_cube_detection",
                    }
                )
                continue

            for crop_index, bbox in enumerate(crop_boxes):
                crop = crop_rgb(image_rgb, bbox)
                engine_input = preprocess_rgb_for_engine(
                    crop,
                    image_size=metadata.image_size,
                    normalize_mean=metadata.normalize_mean,
                    normalize_std=metadata.normalize_std,
                )
                logits = classifier.infer(engine_input)
                prediction = prediction_from_logits(
                    logits,
                    classes=metadata.classes,
                    threshold=threshold,
                )
                best_class, best_probability = _best_class(prediction.probabilities)
                predicted_label = prediction.fruit_kind or NO_FRUIT_CLASS
                prediction_counts[predicted_label] += 1
                is_correct = truth is not None and predicted_label == truth
                if truth is not None:
                    labeled += 1
                    correct += int(is_correct)
                rows += 1
                writer.writerow(
                    {
                        "image": str(image_path),
                        "crop_index": crop_index,
                        "bbox_xyxy": _bbox_text(bbox),
                        "truth": truth or "",
                        "prediction": predicted_label,
                        "best_class": best_class,
                        "best_probability": round(best_probability, 6),
                        "confidence": round(prediction.confidence, 6),
                        "correct": is_correct if truth is not None else "",
                        "probabilities_json": json.dumps(prediction.probabilities),
                        "error": "",
                    }
                )

    print(f"engine={args.engine}")
    print(f"classes={','.join(metadata.classes)}")
    print(f"image_size={metadata.image_size}")
    print(f"input_name={metadata.input_name}")
    print(f"output_name={metadata.output_name}")
    print(f"images={len(image_paths)}")
    print(f"crops_classified={rows}")
    print(f"images_without_cube_detection={images_without_cube}")
    if labeled:
        print(f"accuracy={correct / labeled:.4f} correct={correct}/{labeled}")
    print("prediction_counts:")
    for class_name, count in sorted(prediction_counts.items()):
        print(f"  {class_name}: {count}")
    if truth_counts:
        print("truth_counts:")
        for class_name, count in sorted(truth_counts.items()):
            print(f"  {class_name}: {count}")
    print(f"csv={args.output}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Evaluate a TensorRT fruit classifier engine on cube crops.",
    )
    parser.add_argument("--engine", type=Path, required=True)
    parser.add_argument(
        "--metadata",
        type=Path,
        default=None,
        help="Classifier engine metadata JSON. Defaults to engine path with .json.",
    )
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("runs/eval/cube_fruit_classifier_engine.csv"),
    )
    parser.add_argument("--detector-model", type=Path, default=None)
    parser.add_argument("--cube-class-id", type=int, default=0)
    parser.add_argument("--bbox", type=float, nargs=4, default=None)
    parser.add_argument("--labels-from-parent", action="store_true")
    parser.add_argument("--threshold", type=float, default=None)
    parser.add_argument(
        "--input-size",
        type=int,
        default=None,
        help="Override classifier input size from metadata.",
    )
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--detector-conf", type=float, default=0.25)
    parser.add_argument("--detector-iou", type=float, default=0.7)
    parser.add_argument("--max-crops", type=int, default=1)
    parser.add_argument("--device", default="0")
    return parser


def main() -> int:
    return evaluate_cube_fruit_classifier_engine(build_parser().parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
