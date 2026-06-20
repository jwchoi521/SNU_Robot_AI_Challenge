from __future__ import annotations

import argparse
import time
from datetime import datetime
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Collect raw camera images for later YOLO labeling.",
    )
    parser.add_argument("--camera-index", type=int, default=0)
    parser.add_argument("--output-dir", type=Path, default=Path("dataset/raw"))
    parser.add_argument("--session", default=None)
    parser.add_argument("--prefix", default="frame")
    parser.add_argument("--ext", choices=("jpg", "png"), default="jpg")
    parser.add_argument("--width", type=int, default=0)
    parser.add_argument("--height", type=int, default=0)
    parser.add_argument("--interval-sec", type=float, default=1.0)
    parser.add_argument("--max-images", type=int, default=0)
    parser.add_argument("--warmup-frames", type=int, default=10)
    parser.add_argument("--display", action="store_true")
    return parser


def _session_name(value: str | None) -> str:
    if value:
        return value
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _image_path(output_dir: Path, prefix: str, index: int, ext: str) -> Path:
    return output_dir / f"{prefix}_{index:06d}.{ext}"


def main() -> int:
    args = build_parser().parse_args()

    import cv2

    session_dir = args.output_dir / _session_name(args.session)
    session_dir.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(args.camera_index)
    if args.width > 0:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
    if args.height > 0:
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)
    if not cap.isOpened():
        raise RuntimeError(f"camera index {args.camera_index} could not be opened")

    for _ in range(max(0, args.warmup_frames)):
        cap.read()

    print(f"Saving images to {session_dir}")
    print("Press q to stop when --display is enabled.")
    print("Press space or s to save an extra frame when --display is enabled.")

    saved_count = 0
    last_save_at = 0.0

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                print("Camera frame read failed; stopping.")
                break

            now = time.monotonic()
            should_save = args.interval_sec >= 0 and (
                saved_count == 0 or now - last_save_at >= args.interval_sec
            )

            key = -1
            if args.display:
                cv2.imshow("collect_camera", frame)
                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    break
                if key in {ord(" "), ord("s")}:
                    should_save = True

            if should_save:
                saved_count += 1
                last_save_at = now
                path = _image_path(session_dir, args.prefix, saved_count, args.ext)
                if not cv2.imwrite(str(path), frame):
                    raise RuntimeError(f"failed to write image: {path}")
                print(path)

            if args.max_images and saved_count >= args.max_images:
                break
    finally:
        cap.release()
        if args.display:
            cv2.destroyAllWindows()

    print(f"Saved {saved_count} image(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
