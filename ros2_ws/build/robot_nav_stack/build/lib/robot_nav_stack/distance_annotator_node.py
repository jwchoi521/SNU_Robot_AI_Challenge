from __future__ import annotations

from math import hypot, isfinite

import cv2
import message_filters
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image

from robot_object_detector_ros.msg import (
    Detection2D,
    Detection2DArray,
    FruitClassification,
    FruitClassificationArray,
)

from .bbox_model import HomographyResidualBboxEstimator
from .core import BBox, Detection


class DistanceAnnotatorNode(Node):
    """Draw YOLO/classifier labels with bbox-model distance estimates."""

    def __init__(self) -> None:
        super().__init__("distance_annotator_node")

        self.declare_parameter("model_path", "")
        self.declare_parameter("image_topic", "/camera/image_raw")
        self.declare_parameter("detections_topic", "/shape_yolo/detections")
        self.declare_parameter("classifications_topic", "/cube_fruit/classifications")
        self.declare_parameter("annotated_topic", "/cube_fruit/annotated_image_distance")
        self.declare_parameter("queue_size", 10)
        self.declare_parameter("sync_slop_sec", 0.15)
        self.declare_parameter("classification_iou_threshold", 0.7)
        self.declare_parameter("cube_class_id", 0)
        self.declare_parameter("no_fruit_class", "none")
        self.declare_parameter("draw_unclassified_detections", True)

        model_path = str(self.get_parameter("model_path").value)
        if not model_path:
            raise RuntimeError("model_path parameter is required")

        self._estimator = HomographyResidualBboxEstimator(model_path)
        self._warned_distance_failure = False
        self._classification_iou_threshold = float(
            self.get_parameter("classification_iou_threshold").value
        )
        self._cube_class_id = int(self.get_parameter("cube_class_id").value)
        self._no_fruit_class = str(self.get_parameter("no_fruit_class").value)
        self._draw_unclassified = bool(
            self.get_parameter("draw_unclassified_detections").value
        )

        image_topic = str(self.get_parameter("image_topic").value)
        detections_topic = str(self.get_parameter("detections_topic").value)
        classifications_topic = str(self.get_parameter("classifications_topic").value)
        annotated_topic = str(self.get_parameter("annotated_topic").value)
        queue_size = int(self.get_parameter("queue_size").value)
        sync_slop_sec = float(self.get_parameter("sync_slop_sec").value)

        self._image_sub = message_filters.Subscriber(
            self,
            Image,
            image_topic,
            qos_profile=qos_profile_sensor_data,
        )
        self._detections_sub = message_filters.Subscriber(
            self, Detection2DArray, detections_topic
        )
        self._classifications_sub = message_filters.Subscriber(
            self, FruitClassificationArray, classifications_topic
        )
        self._sync = message_filters.ApproximateTimeSynchronizer(
            [self._image_sub, self._detections_sub, self._classifications_sub],
            queue_size=queue_size,
            slop=sync_slop_sec,
        )
        self._sync.registerCallback(self._on_synchronized)
        self._publisher = self.create_publisher(Image, annotated_topic, 10)

        self.get_logger().info(
            "publishing distance overlay "
            f"{image_topic} + {detections_topic} + {classifications_topic} -> "
            f"{annotated_topic}"
        )

    def _on_synchronized(
        self,
        image_msg: Image,
        detections_msg: Detection2DArray,
        classifications_msg: FruitClassificationArray,
    ) -> None:
        try:
            image = _image_msg_to_bgr8(image_msg)
        except ValueError as exc:
            self.get_logger().warn(f"image conversion failed: {exc}")
            return

        annotated = image.copy()
        classifications = list(classifications_msg.classifications)
        stamp_sec = _stamp_to_seconds(detections_msg.header.stamp)

        for detection in detections_msg.detections:
            classification = self._match_classification(detection, classifications)
            if classification is None and not self._draw_unclassified:
                continue

            rect = _clamp_rect(detection, annotated.shape[1], annotated.shape[0])
            if rect is None:
                continue

            distance_m = self._estimate_distance_m(detection, stamp_sec)
            label, color = self._label_and_color(detection, classification, distance_m)
            _draw_box_label(annotated, rect, label, color)

        self._publisher.publish(_bgr8_to_image_msg(annotated, image_msg))

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
        if best is None or best_iou < self._classification_iou_threshold:
            return None
        return best

    def _estimate_distance_m(self, detection_msg: Detection2D, stamp_sec: float) -> float | None:
        x1 = float(detection_msg.x1)
        y1 = float(detection_msg.y1)
        x2 = float(detection_msg.x2)
        y2 = float(detection_msg.y2)
        w = x2 - x1
        h = y2 - y1
        if w <= 0.0 or h <= 0.0:
            return None

        object_type = detection_msg.class_name or str(int(detection_msg.class_id))
        detection = Detection(
            stamp=stamp_sec,
            bbox=BBox(cx=x1 + 0.5 * w, cy=y1 + 0.5 * h, w=w, h=h),
            object_type=object_type,
            confidence=float(detection_msg.confidence),
        )
        try:
            pose = self._estimator.predict_lidar_pose(detection)
        except Exception as exc:  # noqa: BLE001 - keep overlay alive during model issues.
            if not self._warned_distance_failure:
                self.get_logger().warn(f"distance estimate failed: {exc}")
                self._warned_distance_failure = True
            return None

        distance_m = hypot(float(pose.x), float(pose.y))
        if not isfinite(distance_m):
            return None
        return distance_m

    def _label_and_color(
        self,
        detection: Detection2D,
        classification: FruitClassification | None,
        distance_m: float | None,
    ) -> tuple[str, tuple[int, int, int]]:
        if classification is not None:
            has_fruit = (
                classification.pick_allowed
                and classification.fruit_kind
                and classification.fruit_kind != self._no_fruit_class
            )
            name = classification.fruit_kind if has_fruit else "unknown_cube"
            label = f"{name} {float(classification.confidence):.2f}"
            color = (0, 220, 0) if has_fruit else (160, 160, 160)
        else:
            name = detection.class_name or str(int(detection.class_id))
            label = f"{name} {float(detection.confidence):.2f}"
            color = (0, 220, 0) if int(detection.class_id) == self._cube_class_id else (0, 180, 255)

        if distance_m is not None:
            label += f" {distance_m:.2f}m"
        return label, color


def _stamp_to_seconds(stamp) -> float:
    return float(stamp.sec) + float(stamp.nanosec) * 1e-9


def _image_msg_to_bgr8(msg: Image):
    encoding = msg.encoding.lower()
    if encoding not in ("bgr8", "rgb8"):
        raise ValueError(f"unsupported image encoding {msg.encoding!r}; expected bgr8/rgb8")

    channels = 3
    row_bytes = int(msg.width) * channels
    step = int(msg.step) or row_bytes
    if step < row_bytes:
        raise ValueError(
            f"image step {step} is smaller than width*channels {row_bytes}"
        )

    data = np.frombuffer(msg.data, dtype=np.uint8)
    expected = int(msg.height) * step
    if data.size < expected:
        raise ValueError(
            f"image data has {data.size} bytes, expected at least {expected}"
        )

    rows = data[:expected].reshape((int(msg.height), step))
    image = rows[:, :row_bytes].reshape((int(msg.height), int(msg.width), channels))
    if encoding == "rgb8":
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    return image.copy()


def _bgr8_to_image_msg(image, source_msg: Image) -> Image:
    if image.ndim != 3 or image.shape[2] != 3:
        raise ValueError("expected HxWx3 BGR image")

    msg = Image()
    msg.header = source_msg.header
    msg.height = int(image.shape[0])
    msg.width = int(image.shape[1])
    msg.encoding = "bgr8"
    msg.is_bigendian = False
    msg.step = int(image.shape[1]) * 3
    msg.data = image.tobytes()
    return msg


def _bbox_iou(lhs: Detection2D, rhs: Detection2D) -> float:
    left = max(float(lhs.x1), float(rhs.x1))
    top = max(float(lhs.y1), float(rhs.y1))
    right = min(float(lhs.x2), float(rhs.x2))
    bottom = min(float(lhs.y2), float(rhs.y2))
    inter_w = max(0.0, right - left)
    inter_h = max(0.0, bottom - top)
    intersection = inter_w * inter_h
    lhs_area = max(0.0, float(lhs.x2) - float(lhs.x1)) * max(
        0.0, float(lhs.y2) - float(lhs.y1)
    )
    rhs_area = max(0.0, float(rhs.x2) - float(rhs.x1)) * max(
        0.0, float(rhs.y2) - float(rhs.y1)
    )
    union = lhs_area + rhs_area - intersection
    if union <= 0.0:
        return 0.0
    return intersection / union


def _clamp_rect(
    detection: Detection2D,
    image_width: int,
    image_height: int,
) -> tuple[int, int, int, int] | None:
    x1 = max(0, min(image_width - 1, int(round(min(detection.x1, detection.x2)))))
    y1 = max(0, min(image_height - 1, int(round(min(detection.y1, detection.y2)))))
    x2 = max(0, min(image_width, int(round(max(detection.x1, detection.x2)))))
    y2 = max(0, min(image_height, int(round(max(detection.y1, detection.y2)))))
    if x2 <= x1 or y2 <= y1:
        return None
    return (x1, y1, x2 - x1, y2 - y1)


def _draw_box_label(
    image,
    rect: tuple[int, int, int, int],
    label: str,
    color: tuple[int, int, int],
) -> None:
    x, y, w, h = rect
    cv2.rectangle(image, (x, y), (x + w, y + h), color, 2)

    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.5
    thickness = 1
    (text_w, text_h), baseline = cv2.getTextSize(label, font, font_scale, thickness)
    image_h, image_w = image.shape[:2]

    label_x = max(0, min(x, image_w - text_w - 6))
    text_y = y - 6
    if text_y - text_h - baseline < 0:
        text_y = min(image_h - 2, y + text_h + baseline + 6)

    bg_left = label_x
    bg_top = max(0, text_y - text_h - baseline - 2)
    bg_right = min(image_w - 1, label_x + text_w + 5)
    bg_bottom = min(image_h - 1, text_y + baseline + 2)
    cv2.rectangle(image, (bg_left, bg_top), (bg_right, bg_bottom), (0, 0, 0), -1)
    cv2.putText(
        image,
        label,
        (label_x + 2, text_y),
        font,
        font_scale,
        color,
        thickness,
        cv2.LINE_AA,
    )


def main() -> None:
    rclpy.init()
    node = DistanceAnnotatorNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
