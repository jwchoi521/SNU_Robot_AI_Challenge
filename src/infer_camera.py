from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from src.postprocess import (
        Detection,
        FrameTarget,
        TargetConfirmationTracker,
        postprocess_detections,
    )
except ModuleNotFoundError:
    from postprocess import (  # type: ignore[no-redef]
        Detection,
        FrameTarget,
        TargetConfirmationTracker,
        postprocess_detections,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run YOLO camera inference with robot post-processing.",
    )
    parser.add_argument("--model", required=True)
    parser.add_argument("--camera-index", type=int, default=0)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--conf", type=float, default=0.25)
    parser.add_argument("--iou", type=float, default=0.7)
    parser.add_argument("--device", default=None)
    parser.add_argument("--h-fov-deg", type=float, default=69.4)
    parser.add_argument("--confirm-frames", type=int, default=3)
    parser.add_argument("--max-frames", type=int, default=0)
    parser.add_argument("--display", action="store_true")
    parser.add_argument("--save-jsonl", type=Path, default=None)
    return parser


def detections_from_result(result: object) -> list[Detection]:
    boxes = getattr(result, "boxes", None)
    if boxes is None or len(boxes) == 0:
        return []

    xyxy = boxes.xyxy.cpu().numpy()
    cls = boxes.cls.cpu().numpy()
    conf = boxes.conf.cpu().numpy()
    return [
        Detection(
            class_id=int(class_id),
            confidence=float(confidence),
            bbox_xyxy=tuple(float(value) for value in box),  # type: ignore[arg-type]
        )
        for box, class_id, confidence in zip(xyxy, cls, conf)
    ]


def main() -> int:
    args = build_parser().parse_args()

    import cv2
    from ultralytics import YOLO

    model = YOLO(args.model)
    cap = cv2.VideoCapture(args.camera_index)
    if not cap.isOpened():
        raise RuntimeError(f"camera index {args.camera_index} could not be opened")

    tracker = TargetConfirmationTracker(confirm_frames=args.confirm_frames)
    jsonl_handle = (
        args.save_jsonl.open("w", encoding="utf-8") if args.save_jsonl else None
    )

    try:
        frame_index = 0
        while True:
            ok, frame = cap.read()
            if not ok:
                break

            frame_index += 1
            result = model.predict(
                frame,
                imgsz=args.imgsz,
                conf=args.conf,
                iou=args.iou,
                device=args.device,
                verbose=False,
            )[0]
            detections = detections_from_result(result)
            targets = postprocess_detections(
                detections,
                image_width=frame.shape[1],
                horizontal_fov_deg=args.h_fov_deg,
            )
            targets = tracker.update(targets)

            payload = {
                "frame_index": frame_index,
                "targets": [target.as_dict() for target in targets],
            }
            print(json.dumps(payload, ensure_ascii=True))
            if jsonl_handle is not None:
                jsonl_handle.write(json.dumps(payload) + "\n")

            if args.display:
                _draw_targets(frame, targets)
                cv2.imshow("robot_object_detector", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

            if args.max_frames and frame_index >= args.max_frames:
                break
    finally:
        cap.release()
        if jsonl_handle is not None:
            jsonl_handle.close()
        if args.display:
            cv2.destroyAllWindows()

    return 0


def _draw_targets(frame: object, targets: list[FrameTarget]) -> None:
    import cv2

    for target in targets:
        x1, y1, x2, y2 = (int(value) for value in target.bbox_xyxy)
        if target.target_confirmed and target.pick_allowed:
            color = (0, 220, 0)
        elif target.pick_allowed:
            color = (0, 220, 220)
        else:
            color = (160, 160, 160)

        label = (
            f"{target.object_kind}"
            f" {target.bearing_deg:+.1f}deg"
            f" conf={target.confidence:.2f}"
        )
        if target.fruit_kind:
            label = f"{label} {target.fruit_kind}"
        if target.target_confirmed:
            label = f"{label} confirmed"

        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        cv2.putText(
            frame,
            label,
            (x1, max(20, y1 - 8)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            color,
            1,
            cv2.LINE_AA,
        )


if __name__ == "__main__":
    raise SystemExit(main())
