from __future__ import annotations

import json
from dataclasses import dataclass

import rclpy
from geometry_msgs.msg import PoseStamped
from rclpy.duration import Duration
from rclpy.node import Node
from rclpy.time import Time
from std_msgs.msg import String
from tf2_ros import Buffer, TransformException, TransformListener

from .bbox_model import HomographyResidualBboxEstimator
from .core import BBox, Detection, Pose2D, quaternion_from_yaw, wrap_angle, yaw_from_quaternion


@dataclass
class PendingLocalization:
    detection: Detection
    object_source: Pose2D
    enqueued_sec: float


class ObjectLocalizerNode(Node):
    """Convert camera detections into map-frame object poses.

    Important: detection JSON must contain the original image timestamp. This
    node uses tf2 at that timestamp, so YOLO inference delay does not shift the
    object position.
    """

    def __init__(self) -> None:
        super().__init__("object_localizer_node")
        self.declare_parameter("model_path", "")
        self.declare_parameter("detections_topic", "/detections_json")
        self.declare_parameter("object_pose_topic", "/object_pose_map")
        self.declare_parameter("target_frame", "map")
        self.declare_parameter("source_frame", "")
        self.declare_parameter("lidar_frame", "lidar")
        self.declare_parameter("tf_lookup_timeout_sec", 0.0)
        self.declare_parameter("fallback_to_latest_tf", False)
        self.declare_parameter("latest_tf_max_extrapolation_sec", 3.0)
        self.declare_parameter("pending_detection_timeout_sec", 0.5)
        self.declare_parameter("pending_tf_retry_period_sec", 0.05)
        self.declare_parameter("max_pending_detections", 10)

        model_path = self.get_parameter("model_path").get_parameter_value().string_value
        if not model_path:
            raise RuntimeError("model_path parameter is required")

        self.target_frame = str(self.get_parameter("target_frame").value)
        source_frame = str(self.get_parameter("source_frame").value).strip()
        self.source_frame = source_frame or str(self.get_parameter("lidar_frame").value)
        self.tf_lookup_timeout_sec = float(self.get_parameter("tf_lookup_timeout_sec").value)
        self.fallback_to_latest_tf = bool(self.get_parameter("fallback_to_latest_tf").value)
        self.latest_tf_max_extrapolation_sec = float(
            self.get_parameter("latest_tf_max_extrapolation_sec").value
        )
        self._warned_latest_tf_fallback = False
        self.pending_detection_timeout_sec = float(
            self.get_parameter("pending_detection_timeout_sec").value
        )
        self.max_pending_detections = max(
            1, int(self.get_parameter("max_pending_detections").value)
        )
        self.pending_detections: list[PendingLocalization] = []
        self._warned_pending_tf_wait = False
        self.estimator = HomographyResidualBboxEstimator(model_path)

        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self, spin_thread=True)

        detections_topic = str(self.get_parameter("detections_topic").value)
        object_pose_topic = str(self.get_parameter("object_pose_topic").value)
        self.sub = self.create_subscription(String, detections_topic, self.on_detection_json, 10)
        self.pub = self.create_publisher(PoseStamped, object_pose_topic, 10)
        retry_period = max(0.01, float(self.get_parameter("pending_tf_retry_period_sec").value))
        self.retry_timer = self.create_timer(retry_period, self._retry_pending_detections)

    def on_detection_json(self, msg: String) -> None:
        try:
            detection = self._parse_detection(msg.data)
            object_source = self.estimator.predict_lidar_pose(detection)
        except (ValueError, KeyError) as exc:
            self.get_logger().warn(f"failed to localize object: {exc}")
            return

        self._localize_or_queue(detection, object_source)

    def _localize_or_queue(self, detection: Detection, object_source: Pose2D) -> None:
        try:
            object_map = self._transform_source_to_map(object_source, detection.stamp)
        except TransformException as exc:
            if self._should_wait_for_transform(exc):
                self._enqueue_pending_detection(detection, object_source, exc)
                return
            self.get_logger().warn(f"failed to localize object: {exc}")
            return

        self._publish_object_pose(detection, object_map)

    def _publish_object_pose(self, detection: Detection, object_map: Pose2D) -> None:
        out = PoseStamped()
        out.header.frame_id = self.target_frame
        out.header.stamp = Time(seconds=detection.stamp).to_msg()
        out.pose.position.x = object_map.x
        out.pose.position.y = object_map.y
        out.pose.position.z = 0.0
        qx, qy, qz, qw = quaternion_from_yaw(object_map.theta)
        out.pose.orientation.x = qx
        out.pose.orientation.y = qy
        out.pose.orientation.z = qz
        out.pose.orientation.w = qw
        self.pub.publish(out)

    def _retry_pending_detections(self) -> None:
        if not self.pending_detections:
            return

        pending = self.pending_detections
        self.pending_detections = []
        now_sec = self._now_sec()

        for item in pending:
            age_sec = now_sec - item.enqueued_sec
            try:
                object_map = self._transform_source_to_map(
                    item.object_source, item.detection.stamp
                )
            except TransformException as exc:
                if (
                    age_sec <= self.pending_detection_timeout_sec
                    and self._should_wait_for_transform(exc)
                ):
                    self.pending_detections.append(item)
                    continue

                self.get_logger().warn(
                    "dropping pending object localization after "
                    f"{age_sec:.3f}s without exact TF at stamp "
                    f"{item.detection.stamp:.6f}: {exc}"
                )
                continue

            self._publish_object_pose(item.detection, object_map)

    def _enqueue_pending_detection(
        self,
        detection: Detection,
        object_source: Pose2D,
        exc: TransformException,
    ) -> None:
        if self.pending_detection_timeout_sec <= 0.0:
            self.get_logger().warn(f"failed to localize object: {exc}")
            return

        if len(self.pending_detections) >= self.max_pending_detections:
            dropped = self.pending_detections.pop(0)
            self.get_logger().warn(
                "dropping oldest pending object localization because queue is full "
                f"(stamp={dropped.detection.stamp:.6f}, "
                f"max_pending_detections={self.max_pending_detections})"
            )

        self.pending_detections.append(
            PendingLocalization(
                detection=detection,
                object_source=object_source,
                enqueued_sec=self._now_sec(),
            )
        )
        if not self._warned_pending_tf_wait:
            self.get_logger().warn(
                "TF at detection stamp is not available yet; waiting for exact TF "
                f"for up to {self.pending_detection_timeout_sec:.3f}s before dropping. "
                f"First error: {exc}"
            )
            self._warned_pending_tf_wait = True

    def _parse_detection(self, data: str) -> Detection:
        payload = json.loads(data)
        bbox = payload["bbox"]
        return Detection(
            stamp=float(payload["stamp"]),
            bbox=BBox(
                cx=float(bbox["cx"]),
                cy=float(bbox["cy"]),
                w=float(bbox["w"]),
                h=float(bbox["h"]),
            ),
            object_type=str(payload["object_type"]),
            confidence=float(payload.get("confidence", 1.0)),
        )

    def _transform_source_to_map(self, object_source: Pose2D, stamp: float) -> Pose2D:
        transform = self._lookup_map_source_transform(stamp)
        t = transform.transform.translation
        q = transform.transform.rotation
        source_map = Pose2D(
            x=t.x,
            y=t.y,
            theta=yaw_from_quaternion(q.x, q.y, q.z, q.w),
        )

        # 2D transform: map_T_source * source_point.
        import math

        c = math.cos(source_map.theta)
        s = math.sin(source_map.theta)
        x = source_map.x + c * object_source.x - s * object_source.y
        y = source_map.y + s * object_source.x + c * object_source.y
        if math.hypot(object_source.x, object_source.y) > 1e-6:
            theta = wrap_angle(source_map.theta + math.atan2(object_source.y, object_source.x))
        else:
            theta = source_map.theta
        return Pose2D(x=x, y=y, theta=theta)

    def _lookup_map_source_transform(self, stamp: float):
        try:
            return self.tf_buffer.lookup_transform(
                self.target_frame,
                self.source_frame,
                Time(seconds=stamp),
                timeout=Duration(seconds=self.tf_lookup_timeout_sec),
            )
        except TransformException as exc:
            if not self.fallback_to_latest_tf:
                raise

            transform = self.tf_buffer.lookup_transform(
                self.target_frame,
                self.source_frame,
                Time(),
                timeout=Duration(seconds=self.tf_lookup_timeout_sec),
            )
            latest_stamp = self._stamp_to_seconds(transform.header.stamp)
            extrapolation_sec = stamp - latest_stamp
            if extrapolation_sec < 0.0:
                raise TransformException(
                    "latest TF fallback only handles future extrapolation: "
                    f"detection stamp {stamp:.6f}, latest TF stamp {latest_stamp:.6f}. "
                    f"Original error: {exc}"
                )
            max_extrapolation_sec = self.latest_tf_max_extrapolation_sec
            if max_extrapolation_sec >= 0.0 and extrapolation_sec > max_extrapolation_sec:
                raise TransformException(
                    "latest TF fallback is too stale: "
                    f"detection stamp {stamp:.6f}, latest TF stamp {latest_stamp:.6f}, "
                    f"extrapolation {extrapolation_sec:.3f}s > "
                    f"limit {max_extrapolation_sec:.3f}s. Original error: {exc}"
                )
            if not self._warned_latest_tf_fallback:
                self.get_logger().warn(
                    f"TF at detection stamp was unavailable; using latest "
                    f"{self.target_frame}->{self.source_frame} TF "
                    f"as fallback ({max(0.0, extrapolation_sec):.3f}s newer "
                    f"than latest TF). Original error: {exc}"
                )
                self._warned_latest_tf_fallback = True
            return transform

    @staticmethod
    def _stamp_to_seconds(stamp) -> float:
        return float(stamp.sec) + float(stamp.nanosec) * 1e-9

    @staticmethod
    def _should_wait_for_transform(exc: TransformException) -> bool:
        return "future" in str(exc).lower()

    def _now_sec(self) -> float:
        return self.get_clock().now().nanoseconds * 1e-9


def main() -> None:
    rclpy.init()
    node = ObjectLocalizerNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
