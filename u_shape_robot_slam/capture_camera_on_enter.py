#!/usr/bin/env python3
"""Capture Jetson camera frames every time Enter is pressed.

Typical Jetson CSI usage:
  python3 u_shape_robot_slam/capture_camera_on_enter.py --camera csi --display

Typical USB camera usage:
  python3 u_shape_robot_slam/capture_camera_on_enter.py --camera usb --camera-index 0 --display

Controls:
  Terminal Enter: save the latest frame
  Terminal q + Enter: quit
  Preview window Enter/Space: save the latest frame
  Preview window q/Esc: quit
"""

from __future__ import annotations

import argparse
import csv
import sys
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


def require_cv2() -> Any:
    try:
        import cv2
    except ImportError as exc:
        raise SystemExit(
            "OpenCV is required. On Jetson: sudo apt install python3-opencv "
            "or python3 -m pip install opencv-python"
        ) from exc
    return cv2


def timestamp_for_filename() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]


def default_output_dir() -> Path:
    return Path(__file__).resolve().parent / "data" / "captured_images" / datetime.now().strftime("session_%Y%m%d_%H%M%S")


def build_csi_pipeline(args: argparse.Namespace) -> str:
    return (
        f"nvarguscamerasrc sensor-id={args.camera_index} ! "
        "video/x-raw(memory:NVMM), "
        f"width=(int){args.capture_width}, "
        f"height=(int){args.capture_height}, "
        f"framerate=(fraction){args.fps}/1 ! "
        f"nvvidconv flip-method={args.flip_method} ! "
        "video/x-raw, "
        f"width=(int){args.display_width}, "
        f"height=(int){args.display_height}, "
        "format=(string)BGRx ! "
        "videoconvert ! video/x-raw, format=(string)BGR ! "
        "appsink drop=1 sync=false max-buffers=1"
    )


def open_capture(args: argparse.Namespace) -> Any:
    cv2 = require_cv2()
    if args.camera == "csi":
        return cv2.VideoCapture(build_csi_pipeline(args), cv2.CAP_GSTREAMER)
    if args.camera == "gstreamer":
        if not args.gstreamer:
            raise SystemExit("--gstreamer is required when --camera gstreamer")
        return cv2.VideoCapture(args.gstreamer, cv2.CAP_GSTREAMER)

    capture = cv2.VideoCapture(args.camera_index, cv2.CAP_V4L2)
    capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"UYVY"))
    capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    capture.set(cv2.CAP_PROP_FRAME_WIDTH, args.capture_width)
    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, args.capture_height)
    capture.set(cv2.CAP_PROP_FPS, args.fps)
    return capture
@dataclass
class FrameSnapshot:
    frame: Any
    frame_index: int
    captured_monotonic: float


class CameraReader:
    """Continuously reads frames so Enter saves the current view, not a stale read."""

    def __init__(self, capture: Any) -> None:
        self.capture = capture
        self.lock = threading.Lock()
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self._read_loop, name="camera-reader", daemon=True)
        self.latest_frame: Any | None = None
        self.latest_time = 0.0
        self.frame_index = 0
        self.error: str | None = None

    def start(self) -> None:
        self.thread.start()

    def stop(self) -> None:
        self.stop_event.set()
        self.thread.join(timeout=2.0)

    def snapshot(self) -> FrameSnapshot | None:
        with self.lock:
            if self.latest_frame is None:
                return None
            return FrameSnapshot(self.latest_frame.copy(), self.frame_index, self.latest_time)

    def _read_loop(self) -> None:
        while not self.stop_event.is_set():
            ok, frame = self.capture.read()
            if not ok:
                self.error = "camera frame read failed"
                time.sleep(0.02)
                continue
            with self.lock:
                self.frame_index += 1
                self.latest_frame = frame
                self.latest_time = time.monotonic()


class CaptureLogger:
    def __init__(self, csv_path: Path) -> None:
        self.csv_path = csv_path
        self.handle = csv_path.open("w", newline="", encoding="utf-8")
        self.writer = csv.DictWriter(
            self.handle,
            fieldnames=[
                "image_index",
                "filename",
                "saved_at",
                "camera_frame_index",
                "image_width",
                "image_height",
                "notes",
            ],
        )
        self.writer.writeheader()
        self.handle.flush()

    def close(self) -> None:
        self.handle.close()

    def log(self, image_index: int, path: Path, snapshot: FrameSnapshot, notes: str = "") -> None:
        height, width = snapshot.frame.shape[:2]
        self.writer.writerow(
            {
                "image_index": image_index,
                "filename": path.name,
                "saved_at": datetime.now().isoformat(timespec="milliseconds"),
                "camera_frame_index": snapshot.frame_index,
                "image_width": width,
                "image_height": height,
                "notes": notes,
            }
        )
        self.handle.flush()


def save_snapshot(
    snapshot: FrameSnapshot,
    output_dir: Path,
    image_index: int,
    prefix: str,
    ext: str,
    jpeg_quality: int,
) -> Path:
    cv2 = require_cv2()
    filename = f"{prefix}_{image_index:06d}_{timestamp_for_filename()}.{ext}"
    output_path = output_dir / filename
    if ext.lower() in {"jpg", "jpeg"}:
        ok = cv2.imwrite(str(output_path), snapshot.frame, [cv2.IMWRITE_JPEG_QUALITY, jpeg_quality])
    else:
        ok = cv2.imwrite(str(output_path), snapshot.frame)
    if not ok:
        raise RuntimeError(f"failed to write image: {output_path}")
    return output_path


def stdin_ready() -> bool:
    if sys.platform.startswith("win"):
        try:
            import msvcrt
        except ImportError:
            return False
        return msvcrt.kbhit()

    try:
        import select
    except ImportError:
        return False
    ready, _, _ = select.select([sys.stdin], [], [], 0)
    return bool(ready)


def read_stdin_line_if_ready() -> str | None:
    if not stdin_ready():
        return None
    if sys.platform.startswith("win"):
        # For this script's main target (Jetson/Linux), normal stdin is used.
        # On Windows fallback, let the GUI hotkeys handle captures.
        return None
    return sys.stdin.readline().strip()


def draw_overlay(frame: Any, saved_count: int, output_dir: Path) -> Any:
    cv2 = require_cv2()
    display = frame.copy()
    text_lines = [
        "Enter/Space: save  |  q/Esc: quit",
        f"saved: {saved_count}  dir: {output_dir}",
    ]
    y = 28
    for text in text_lines:
        cv2.putText(display, text, (16, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 3, cv2.LINE_AA)
        cv2.putText(display, text, (16, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1, cv2.LINE_AA)
        y += 30
    return display


def capture_interactive(args: argparse.Namespace) -> int:
    cv2 = require_cv2()
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    logger = CaptureLogger(output_dir / "capture_log.csv")

    capture = open_capture(args)
    if not capture.isOpened():
        raise SystemExit("Could not open camera. Try --camera usb, --camera csi, or check --camera-index.")

    reader = CameraReader(capture)
    reader.start()
    next_index = args.start_index
    saved_count = 0

    print(f"[capture] output_dir: {output_dir}")
    print("[capture] Press Enter to save the current frame.")
    print("[capture] Type q then Enter to quit.")
    if args.display:
        print("[capture] Preview window also supports Enter/Space to save and q/Esc to quit.")

    try:
        deadline = time.monotonic() + max(0.0, args.warmup_sec)
        while time.monotonic() < deadline:
            if reader.snapshot() is not None:
                break
            time.sleep(0.02)

        while True:
            if reader.error and reader.snapshot() is None:
                print(f"[camera] {reader.error}", file=sys.stderr)

            command = read_stdin_line_if_ready()
            if command is not None:
                if command.lower() in {"q", "quit", "exit"}:
                    break
                snapshot = reader.snapshot()
                if snapshot is None:
                    print("[capture] no frame available yet")
                else:
                    path = save_snapshot(snapshot, output_dir, next_index, args.prefix, args.ext, args.jpeg_quality)
                    logger.log(next_index, path, snapshot)
                    saved_count += 1
                    print(f"[capture] saved {path}")
                    next_index += 1
                    if args.max_images and saved_count >= args.max_images:
                        break

            if args.display:
                snapshot = reader.snapshot()
                if snapshot is not None:
                    cv2.imshow(args.window_name, draw_overlay(snapshot.frame, saved_count, output_dir))
                key = cv2.waitKey(30) & 0xFF
                if key in {ord("q"), 27}:
                    break
                if key in {13, 10, 32}:  # Enter or Space in preview window.
                    snapshot = reader.snapshot()
                    if snapshot is not None:
                        path = save_snapshot(snapshot, output_dir, next_index, args.prefix, args.ext, args.jpeg_quality)
                        logger.log(next_index, path, snapshot)
                        saved_count += 1
                        print(f"[capture] saved {path}")
                        next_index += 1
                        if args.max_images and saved_count >= args.max_images:
                            break
            else:
                # Terminal-only mode: avoid busy-wait while still keeping camera fresh.
                time.sleep(0.03)
    except KeyboardInterrupt:
        print()
    finally:
        reader.stop()
        capture.release()
        logger.close()
        if args.display:
            cv2.destroyAllWindows()

    print(f"[capture] done. saved_count={saved_count}, output_dir={output_dir}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Save a camera image every time Enter is pressed.")
    parser.add_argument("--camera", choices=("usb", "csi", "gstreamer"), default="csi")
    parser.add_argument("--camera-index", type=int, default=0, help="USB index or CSI sensor-id")
    parser.add_argument("--gstreamer", default=None, help="custom GStreamer pipeline when --camera gstreamer")
    parser.add_argument("--capture-width", type=int, default=1280)
    parser.add_argument("--capture-height", type=int, default=720)
    parser.add_argument("--display-width", type=int, default=1280, help="CSI pipeline output width")
    parser.add_argument("--display-height", type=int, default=720, help="CSI pipeline output height")
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--flip-method", type=int, default=0, help="Jetson nvvidconv flip-method")
    parser.add_argument("--display", action="store_true", help="show a live preview window")
    parser.add_argument("--window-name", default="camera capture")
    parser.add_argument("--output-dir", type=Path, default=default_output_dir())
    parser.add_argument("--prefix", default="frame")
    parser.add_argument("--ext", choices=("jpg", "png"), default="jpg")
    parser.add_argument("--jpeg-quality", type=int, default=95)
    parser.add_argument("--start-index", type=int, default=1)
    parser.add_argument("--max-images", type=int, default=0, help="0 means unlimited")
    parser.add_argument("--warmup-sec", type=float, default=2.0)
    return parser


def main() -> int:
    return capture_interactive(build_parser().parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
