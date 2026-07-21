from __future__ import annotations

import json
from dataclasses import dataclass

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from robot_object_detector_ros.msg import (
    Detection2D,
    Detection2DArray,
    FruitClassification,
    FruitClassificationArray,
)

from .exact_frame_sync import ExactFrameSynchronizer, FrameKey


@dataclass
class PendingCubeFrame:
    stamp_sec: float
    detections: list[Detection2D]


class YoloDetectionAdapterNode(Node):
    """Convert TensorRT YOLO detections into robot_nav_stack detection JSON."""

    def __init__(self) -> None:
        super().__init__("yolo_detection_adapter_node")
        self.declare_parameter("input_topic", "/shape_yolo/detections")
        self.declare_parameter("output_topic", "/detections_json")
        self.declare_parameter("classifications_topic", "/cube_fruit/classifications")
        self.declare_parameter("min_confidence", 0.0)
        self.declare_parameter("max_detections_per_frame", 0)
        self.declare_parameter("max_output_hz", 0.0)
        self.declare_parameter("use_current_time_when_stamp_zero", True)
        self.declare_parameter("stamp_mode", "header")
        self.declare_parameter("max_header_stamp_offset_sec", 2.0)
        self.declare_parameter("classification_iou_threshold", 0.7)
        self.declare_parameter("classification_max_age_sec", 1.0)
        self.declare_parameter("max_pending_cube_frames", 10)
        self.declare_parameter("cube_class_id", 0)
        self.declare_parameter("no_fruit_class", "none")

        input_topic = str(self.get_parameter("input_topic").value)
        output_topic = str(self.get_parameter("output_topic").value)
        classifications_topic = str(self.get_parameter("classifications_topic").value)
        self.min_confidence = float(self.get_parameter("min_confidence").value)
        self.max_detections_per_frame = int(
            self.get_parameter("max_detections_per_frame").value
        )
        self.max_output_hz = float(self.get_parameter("max_output_hz").value)
        self.use_current_time_when_stamp_zero = bool(
            self.get_parameter("use_current_time_when_stamp_zero").value
        )
        self.stamp_mode = str(self.get_parameter("stamp_mode").value).lower()
        self.max_header_stamp_offset_sec = float(
            self.get_parameter("max_header_stamp_offset_sec").value
        )
        self.classification_iou_threshold = float(
            self.get_parameter("classification_iou_threshold").value
        )
        # Kept for parameter compatibility; now this is the maximum time a
        # cube detection waits for its exact-frame classifier result.
        self.classification_max_age_sec = float(
            self.get_parameter("classification_max_age_sec").value
        )
        self.max_pending_cube_frames = max(
            1,
            int(self.get_parameter("max_pending_cube_frames").value),
        )
        self.cube_class_id = int(self.get_parameter("cube_class_id").value)
        self.no_fruit_class = str(self.get_parameter("no_fruit_class").value)
        self._warned_bad_stamp = False
        self._warned_unknown_stamp_mode = False
        self._warned_unmatched_cube = False
        self._last_publish_sec: float | None = None
        self._cube_frame_sync = ExactFrameSynchronizer[
            PendingCubeFrame,
            list[FruitClassification],
        ](max_pending_frames=self.max_pending_cube_frames)

        self.sub = self.create_subscription(
            Detection2DArray,
            input_topic,
            self.on_detections,
            10,
        )
        self.classifications_sub = self.create_subscription(
            FruitClassificationArray,
            classifications_topic,
            self.on_classifications,
            10,
        )
        self.pub = self.create_publisher(String, output_topic, 10)
        self.create_timer(0.1, self._expire_pending_cube_frames)

        self.get_logger().info(
            f"adapting {input_topic} Detection2DArray messages to {output_topic} JSON "
            f"(stamp_mode={self.stamp_mode}, min_confidence={self.min_confidence:.2f}, "
            f"max_detections_per_frame={self.max_detections_per_frame}, "
            f"max_output_hz={self.max_output_hz:.2f}, "
            f"classifications={classifications_topic}, "
            "cube_sync=exact_header_stamp)"
        )

    def on_classifications(self, msg: FruitClassificationArray) -> None:
        matched = self._cube_frame_sync.add_right(
            self._frame_key(msg.header.stamp),
            list(msg.classifications),
            self._now_seconds(),
        )
        if matched is not None:
            self._publish_classified_cubes(*matched)

    def on_detections(self, msg: Detection2DArray) -> None:
        stamp = self._select_stamp_seconds(msg.header.stamp)
        min_confidence = float(self.get_parameter("min_confidence").value)
        max_detections = int(self.get_parameter("max_detections_per_frame").value)
        max_output_hz = float(self.get_parameter("max_output_hz").value)
        now_sec = self._now_seconds()
        if (
            max_output_hz > 0.0
            and self._last_publish_sec is not None
            and now_sec - self._last_publish_sec < 1.0 / max_output_hz
        ):
            return

        candidates: list[Detection2D] = []
        for detection in sorted(
            msg.detections,
            key=lambda item: (
                float(item.y1) + 0.83 * (float(item.y2) - float(item.y1)),
                float(item.confidence),
            ),
            reverse=True,
        ):
            if float(detection.confidence) < min_confidence:
                continue
            if not self._valid_bbox(detection):
                continue
            candidates.append(detection)
            if max_detections > 0 and len(candidates) >= max_detections:
                break

        if not candidates:
            return

        # Throttle when the frame is accepted. Cubes are published later, only
        # after a classifier result carrying this exact source header stamp.
        self._last_publish_sec = now_sec
        cubes = [detection for detection in candidates if self._is_cube(detection)]
        for detection in candidates:
            if not self._is_cube(detection):
                self._publish_detection(detection, stamp, classification=None)

        if not cubes:
            return

        matched = self._cube_frame_sync.add_left(
            self._frame_key(msg.header.stamp),
            PendingCubeFrame(stamp_sec=stamp, detections=cubes),
            now_sec,
        )
        if matched is not None:
            self._publish_classified_cubes(*matched)

    def _publish_classified_cubes(
        self,
        pending: PendingCubeFrame,
        classifications: list[FruitClassification],
    ) -> None:
        for detection in pending.detections:
            classification = self._match_classification(detection, classifications)
            if classification is None:
                if not self._warned_unmatched_cube:
                    self.get_logger().warn(
                        "dropping cube_any detection because the classifier result "
                        "for the same frame did not contain a matching cube bbox"
                    )
                    self._warned_unmatched_cube = True
                continue

            self._warned_unmatched_cube = False
            self._publish_detection(detection, pending.stamp_sec, classification)

    def _publish_detection(
        self,
        detection: Detection2D,
        stamp: float,
        classification: FruitClassification | None,
    ) -> None:
        x1 = float(detection.x1)
        y1 = float(detection.y1)
        x2 = float(detection.x2)
        y2 = float(detection.y2)
        w = x2 - x1
        h = y2 - y1
        object_type = detection.class_name or str(int(detection.class_id))
        payload = {
            "stamp": stamp,
            "bbox": {
                "cx": x1 + 0.5 * w,
                "cy": y1 + 0.5 * h,
                "w": w,
                "h": h,
            },
            "object_type": object_type,
            "confidence": float(detection.confidence),
            "class_id": int(detection.class_id),
        }
        if classification is not None:
            payload["fruit_kind"] = classification.fruit_kind or self.no_fruit_class
            payload["fruit_confidence"] = float(classification.confidence)
            payload["pick_allowed"] = bool(classification.pick_allowed)

        out = String()
        out.data = json.dumps(payload, separators=(",", ":"))
        self.pub.publish(out)

    def _expire_pending_cube_frames(self) -> None:
        expired_cubes, _ = self._cube_frame_sync.expire(
            self._now_seconds(),
            self.classification_max_age_sec,
        )
        dropped = sum(len(frame.detections) for frame in expired_cubes)
        if dropped:
            self.get_logger().warn(
                "dropping cube_any detections because the exact-frame classifier "
                f"result did not arrive within {self.classification_max_age_sec:.2f}s; "
                f"dropped={dropped}"
            )

    def _valid_bbox(self, detection: Detection2D) -> bool:
        x1 = float(detection.x1)
        y1 = float(detection.y1)
        x2 = float(detection.x2)
        y2 = float(detection.y2)
        if x2 > x1 and y2 > y1:
            return True
        self.get_logger().warn(
            f"skipping invalid bbox: x1={x1:.1f}, y1={y1:.1f}, "
            f"x2={x2:.1f}, y2={y2:.1f}"
        )
        return False

    def _is_cube(self, detection: Detection2D) -> bool:
        return (
            int(detection.class_id) == self.cube_class_id
            or detection.class_name.strip().lower() == "cube_any"
        )

    @staticmethod
    def _frame_key(stamp) -> FrameKey:
        return int(stamp.sec), int(stamp.nanosec)

    @staticmethod
    def _stamp_to_seconds(stamp) -> float:
        return float(stamp.sec) + float(stamp.nanosec) * 1e-9

    def _now_seconds(self) -> float:
        return self.get_clock().now().nanoseconds * 1e-9

    def _select_stamp_seconds(self, header_stamp) -> float:
        now = self._now_seconds()
        header = self._stamp_to_seconds(header_stamp)
        mode = self.stamp_mode

        if mode not in ("auto", "header", "now"):
            if not self._warned_unknown_stamp_mode:
                self.get_logger().warn(
                    f"unknown stamp_mode={mode!r}; falling back to auto"
                )
                self._warned_unknown_stamp_mode = True
            mode = "auto"

        if mode == "now":
            return now

        if mode == "header":
            if header <= 0.0 and self.use_current_time_when_stamp_zero:
                return now
            return header

        # auto: keep valid source stamps, but repair zero or obviously different clocks.
        if header <= 0.0:
            return now if self.use_current_time_when_stamp_zero else header

        offset = abs(now - header)
        if self.max_header_stamp_offset_sec > 0.0 and offset > self.max_header_stamp_offset_sec:
            if not self._warned_bad_stamp:
                self.get_logger().warn(
                    "detection header stamp is far from this node clock "
                    f"({offset:.3f}s); using current ROS time for detection JSON"
                )
                self._warned_bad_stamp = True
            return now

        return header

    def _match_classification(
        self,
        detection: Detection2D,
        classifications: list[FruitClassification],
    ) -> FruitClassification | None:
        best: FruitClassification | None = None
        best_iou = 0.0
        for classification in classifications:
            iou = _bbox_iou(detection, classification.cube)
            if iou > best_iou:
                best = classification
                best_iou = iou

        if best is None or best_iou < self.classification_iou_threshold:
            return None
        return best


def _bbox_iou(a: Detection2D, b: Detection2D) -> float:
    ax1, ay1, ax2, ay2 = float(a.x1), float(a.y1), float(a.x2), float(a.y2)
    bx1, by1, bx2, by2 = float(b.x1), float(b.y1), float(b.x2), float(b.y2)
    inter_x1 = max(ax1, bx1)
    inter_y1 = max(ay1, by1)
    inter_x2 = min(ax2, bx2)
    inter_y2 = min(ay2, by2)
    inter_w = max(0.0, inter_x2 - inter_x1)
    inter_h = max(0.0, inter_y2 - inter_y1)
    inter_area = inter_w * inter_h
    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    union = area_a + area_b - inter_area
    if union <= 0.0:
        return 0.0
    return inter_area / union


def main() -> None:
    rclpy.init()
    node = YoloDetectionAdapterNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
