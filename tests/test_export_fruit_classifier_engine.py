from __future__ import annotations

from pathlib import Path

import pytest

from src.export_fruit_classifier_engine import (
    INPUT_NAME,
    _default_output_path,
    _trtexec_command,
    _validate_dynamic_batches,
    build_parser,
)


def test_parser_defaults_to_engine_export() -> None:
    args = build_parser().parse_args(["--model", "runs/classify/best.pt"])

    assert args.format == "engine"
    assert args.batch == 1
    assert args.imgsz is None
    assert not args.half


def test_default_output_path_replaces_checkpoint_suffix() -> None:
    assert _default_output_path(Path("runs/classify/best.pt"), ".engine") == Path(
        "runs/classify/best.engine"
    )


def test_static_trtexec_command_uses_fp16_without_dynamic_shapes() -> None:
    command = _trtexec_command(
        trtexec=Path("/usr/src/tensorrt/bin/trtexec"),
        onnx_path=Path("best.onnx"),
        engine_path=Path("best.engine"),
        image_size=256,
        batch=1,
        half=True,
        dynamic_batch=False,
        min_batch=1,
        opt_batch=1,
        max_batch=1,
        workspace_mib=1024,
        verbose=False,
    )

    assert "--fp16" in command
    assert "--memPoolSize=workspace:1024" in command
    assert not any(item.startswith("--minShapes") for item in command)
    assert not any(item.startswith("--optShapes") for item in command)
    assert not any(item.startswith("--maxShapes") for item in command)


def test_dynamic_trtexec_command_sets_batch_profiles() -> None:
    command = _trtexec_command(
        trtexec=Path("trtexec"),
        onnx_path=Path("best.onnx"),
        engine_path=Path("best.engine"),
        image_size=256,
        batch=1,
        half=False,
        dynamic_batch=True,
        min_batch=1,
        opt_batch=4,
        max_batch=8,
        workspace_mib=None,
        verbose=True,
    )

    assert f"--minShapes={INPUT_NAME}:1x3x256x256" in command
    assert f"--optShapes={INPUT_NAME}:4x3x256x256" in command
    assert f"--maxShapes={INPUT_NAME}:8x3x256x256" in command
    assert "--verbose" in command


def test_dynamic_batch_validation_rejects_inverted_profile() -> None:
    with pytest.raises(ValueError, match="min_batch <= opt_batch <= max_batch"):
        _validate_dynamic_batches(min_batch=4, opt_batch=2, max_batch=8)
