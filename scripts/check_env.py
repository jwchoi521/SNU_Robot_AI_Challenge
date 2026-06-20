from __future__ import annotations

import argparse
import importlib.metadata
import importlib.util
import json
import platform
import sys
from dataclasses import dataclass


REQUIRED_MODULES = (
    ("ultralytics", "ultralytics"),
    ("cv2", "opencv-python"),
    ("numpy", "numpy"),
    ("yaml", "pyyaml"),
    ("tqdm", "tqdm"),
)


@dataclass(frozen=True)
class CheckResult:
    name: str
    ok: bool
    detail: str


def _package_version(distribution_name: str) -> str:
    try:
        return importlib.metadata.version(distribution_name)
    except importlib.metadata.PackageNotFoundError:
        return "unknown"


def check_imports() -> list[CheckResult]:
    results: list[CheckResult] = []
    for import_name, distribution_name in REQUIRED_MODULES:
        spec = importlib.util.find_spec(import_name)
        if spec is None:
            results.append(CheckResult(import_name, False, "not installed"))
            continue
        version = _package_version(distribution_name)
        results.append(CheckResult(import_name, True, version))
    return results


def check_cuda(require_cuda: bool) -> CheckResult:
    try:
        import torch
    except ModuleNotFoundError:
        ok = not require_cuda
        return CheckResult("cuda", ok, "torch not installed")

    available = bool(torch.cuda.is_available())
    if not available:
        return CheckResult("cuda", not require_cuda, "not available")

    device_name = torch.cuda.get_device_name(0)
    return CheckResult("cuda", True, device_name)


def check_camera(camera_index: int) -> CheckResult:
    cv2_spec = importlib.util.find_spec("cv2")
    if cv2_spec is None:
        return CheckResult("camera", False, "opencv-python is not installed")

    import cv2

    cap = cv2.VideoCapture(camera_index)
    try:
        if not cap.isOpened():
            return CheckResult("camera", False, f"index {camera_index} not opened")
        ok, _frame = cap.read()
        if not ok:
            return CheckResult("camera", False, f"index {camera_index} did not read")
        return CheckResult("camera", True, f"index {camera_index} readable")
    finally:
        cap.release()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check the local YOLO robot object detector environment.",
    )
    parser.add_argument("--require-cuda", action="store_true")
    parser.add_argument("--check-camera", action="store_true")
    parser.add_argument("--camera-index", type=int, default=0)
    parser.add_argument("--json", action="store_true", dest="as_json")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    results = check_imports()
    results.append(check_cuda(args.require_cuda))
    if args.check_camera:
        results.append(check_camera(args.camera_index))

    payload = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "checks": [result.__dict__ for result in results],
    }

    if args.as_json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"Python:   {payload['python']}")
        print(f"Platform: {payload['platform']}")
        for result in results:
            marker = "OK" if result.ok else "FAIL"
            print(f"{marker:4} {result.name:12} {result.detail}")

    return 0 if all(result.ok for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
