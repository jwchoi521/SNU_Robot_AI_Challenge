from __future__ import annotations

import json

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from robot_object_detector_ros.msg import Detection2DArray


class YoloDetectionAdapterNode(Node):
    """Convert TensorRT YOLO detections into robot_nav_stack detection JSON."""

    def __init__(self) -> None:
        super().__init__("yolo_detection_adapter_node")
        self.declare_parameter("input_topic", "/shape_yolo/detections")
        self.declare_parameter("output_topic", "/detections_json")
        self.declare_parameter("min_confidence", 0.0)
        self.declare_parameter("use_current_time_when_stamp_zero", True)
        self.declare_parameter("stamp_mode", "auto")
        self.declare_parameter("max_header_stamp_offset_sec", 2.0)

        input_topic = str(self.get_parameter("input_topic").value)
        output_topic = str(self.get_parameter("output_topic").value)
        self.min_confidence = float(self.get_parameter("min_confidence").value)
        self.use_current_time_when_stamp_zero = bool(
            self.get_parameter("use_current_time_when_stamp_zero").value
        )
        self.stamp_mode = str(self.get_parameter("stamp_mode").value).lower()
        self.max_header_stamp_offset_sec = float(
            self.get_parameter("max_header_stamp_offset_sec").value
        )
        self._warned_bad_stamp = False
        self._warned_unknown_stamp_mode = False

        self.sub = self.create_subscription(
            Detection2DArray,
            input_topic,
            self.on_detections,
            10,
        )
        self.pub = self.create_publisher(String, output_topic, 10)

        self.get_logger().info(
            f"adapting {input_topic} Detection2DArray messages to {output_topic} JSON "
            f"(stamp_mode={self.stamp_mode})"
        )

    def on_detections(self, msg: Detection2DArray) -> None:
        stamp = self._select_stamp_seconds(msg.header.stamp)

        for detection in msg.detections:
            confidence = float(detection.confidence)
            if confidence < self.min_confidence:
                continue

            x1 = float(detection.x1)
            y1 = float(detection.y1)
            x2 = float(detection.x2)
            y2 = float(detection.y2)
            w = x2 - x1
            h = y2 - y1
            if w <= 0.0 or h <= 0.0:
                self.get_logger().warn(
                    f"skipping invalid bbox: x1={x1:.1f}, y1={y1:.1f}, "
                    f"x2={x2:.1f}, y2={y2:.1f}"
                )
                continue

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
                "confidence": confidence,
                "class_id": int(detection.class_id),
            }

            out = String()
            out.data = json.dumps(payload, separators=(",", ":"))
            self.pub.publish(out)

    @staticmethod
    def _stamp_to_seconds(stamp) -> float:
        return float(stamp.sec) + float(stamp.nanosec) * 1e-9

    def _select_stamp_seconds(self, header_stamp) -> float:
        now = self.get_clock().now().nanoseconds * 1e-9
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


def main() -> None:
    rclpy.init()
    node = YoloDetectionAdapterNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
