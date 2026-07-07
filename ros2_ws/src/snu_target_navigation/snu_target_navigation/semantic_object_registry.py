from __future__ import annotations

import struct
from dataclasses import dataclass
from math import atan2, cos, hypot, isfinite, radians, sin

import rclpy
from geometry_msgs.msg import PoseStamped
from rclpy.duration import Duration
from rclpy.node import Node
from rclpy.time import Time
from sensor_msgs.msg import PointCloud2, PointField
from snu_robot_interfaces.msg import PerceivedObject, PerceivedObjectArray
from tf2_ros import Buffer, TransformException, TransformListener


@dataclass
class ObjectEntry:
    role: int
    object_kind: str
    fruit_kind: str
    x: float
    y: float
    radius: float
    confidence: float
    seen_count: int
    last_seen_sec: float
    target_confirmed: bool
    pick_allowed: bool


class SemanticObjectRegistry(Node):
    """Keep map-frame memory of camera/IR objects for navigation."""

    def __init__(self) -> None:
        super().__init__("semantic_object_registry")

        self.declare_parameter("input_topic", "/perception/objects")
        self.declare_parameter("obstacle_cloud_topic", "/semantic_obstacles")
        self.declare_parameter("target_pose_topic", "/target_pose_map")
        self.declare_parameter("map_frame", "map")
        self.declare_parameter("observation_frame", "base_link")
        self.declare_parameter("bearing_positive_is_left", False)
        self.declare_parameter("min_distance_m", 0.10)
        self.declare_parameter("max_distance_m", 2.50)
        self.declare_parameter("min_confidence", 0.25)
        self.declare_parameter("merge_distance_m", 0.25)
        self.declare_parameter("obstacle_ttl_sec", 30.0)
        self.declare_parameter("target_ttl_sec", 60.0)
        self.declare_parameter("publish_rate_hz", 5.0)
        self.declare_parameter("default_obstacle_radius_m", 0.18)
        self.declare_parameter("require_confirmed_targets", True)
        self.declare_parameter("require_confirmed_obstacles", False)

        self._map_frame = str(self.get_parameter("map_frame").value)
        self._observation_frame = str(self.get_parameter("observation_frame").value)
        self._bearing_positive_is_left = bool(
            self.get_parameter("bearing_positive_is_left").value
        )
        self._min_distance_m = float(self.get_parameter("min_distance_m").value)
        self._max_distance_m = float(self.get_parameter("max_distance_m").value)
        self._min_confidence = float(self.get_parameter("min_confidence").value)
        self._merge_distance_m = float(self.get_parameter("merge_distance_m").value)
        self._obstacle_ttl_sec = float(self.get_parameter("obstacle_ttl_sec").value)
        self._target_ttl_sec = float(self.get_parameter("target_ttl_sec").value)
        self._default_obstacle_radius_m = float(
            self.get_parameter("default_obstacle_radius_m").value
        )
        self._require_confirmed_targets = bool(
            self.get_parameter("require_confirmed_targets").value
        )
        self._require_confirmed_obstacles = bool(
            self.get_parameter("require_confirmed_obstacles").value
        )

        self._tf_buffer = Buffer()
        self._tf_listener = TransformListener(self._tf_buffer, self)
        self._entries: list[ObjectEntry] = []

        self._obstacle_publisher = self.create_publisher(
            PointCloud2,
            str(self.get_parameter("obstacle_cloud_topic").value),
            10,
        )
        self._target_publisher = self.create_publisher(
            PoseStamped,
            str(self.get_parameter("target_pose_topic").value),
            10,
        )
        self._subscription = self.create_subscription(
            PerceivedObjectArray,
            str(self.get_parameter("input_topic").value),
            self._on_objects,
            10,
        )

        publish_rate_hz = float(self.get_parameter("publish_rate_hz").value)
        self._timer = self.create_timer(1.0 / max(0.1, publish_rate_hz), self._publish)
        self.get_logger().info("Semantic object registry is storing objects in map frame")

    def _on_objects(self, msg: PerceivedObjectArray) -> None:
        stamp = Time.from_msg(msg.header.stamp)
        if msg.header.stamp.sec == 0 and msg.header.stamp.nanosec == 0:
            stamp = Time()

        try:
            transform = self._tf_buffer.lookup_transform(
                self._map_frame,
                self._observation_frame,
                stamp,
                timeout=Duration(seconds=0.1),
            )
        except TransformException as exc:
            self.get_logger().warn(f"Skipping semantic objects; TF unavailable: {exc}")
            return

        now_sec = self.get_clock().now().nanoseconds * 1.0e-9
        for obj in msg.objects:
            if not self._should_store(obj):
                continue

            base_x, base_y = self._object_xy(obj)
            map_x, map_y = _transform_xy(transform, base_x, base_y)
            radius = float(obj.obstacle_radius_m) or self._default_obstacle_radius_m
            self._upsert(obj, map_x, map_y, radius, now_sec)

    def _should_store(self, obj: PerceivedObject) -> bool:
        if obj.navigation_role not in (
            PerceivedObject.ROLE_TARGET,
            PerceivedObject.ROLE_OBSTACLE,
        ):
            return False
        if obj.navigation_role == PerceivedObject.ROLE_TARGET:
            if not obj.pick_allowed:
                return False
            if self._require_confirmed_targets and not obj.target_confirmed:
                return False
        if obj.navigation_role == PerceivedObject.ROLE_OBSTACLE:
            if self._require_confirmed_obstacles and not obj.target_confirmed:
                return False
        if float(obj.confidence) < self._min_confidence:
            return False
        distance_m = float(obj.distance_m)
        return (
            obj.has_distance
            and isfinite(distance_m)
            and self._min_distance_m <= distance_m <= self._max_distance_m
        )

    def _object_xy(self, obj: PerceivedObject) -> tuple[float, float]:
        bearing_rad = radians(float(obj.bearing_deg))
        distance_m = float(obj.distance_m)
        lateral_sign = 1.0 if self._bearing_positive_is_left else -1.0
        return (
            distance_m * cos(bearing_rad),
            lateral_sign * distance_m * sin(bearing_rad),
        )

    def _upsert(
        self,
        obj: PerceivedObject,
        x: float,
        y: float,
        radius: float,
        now_sec: float,
    ) -> None:
        entry = self._find_match(obj, x, y)
        if entry is None:
            self._entries.append(
                ObjectEntry(
                    role=int(obj.navigation_role),
                    object_kind=str(obj.object_kind),
                    fruit_kind=str(obj.fruit_kind),
                    x=x,
                    y=y,
                    radius=radius,
                    confidence=float(obj.confidence),
                    seen_count=1,
                    last_seen_sec=now_sec,
                    target_confirmed=bool(obj.target_confirmed),
                    pick_allowed=bool(obj.pick_allowed),
                )
            )
            return

        alpha = 0.35
        entry.x = (1.0 - alpha) * entry.x + alpha * x
        entry.y = (1.0 - alpha) * entry.y + alpha * y
        entry.radius = max(entry.radius, radius)
        entry.confidence = max(entry.confidence * 0.95, float(obj.confidence))
        entry.seen_count += 1
        entry.last_seen_sec = now_sec
        entry.target_confirmed = entry.target_confirmed or bool(obj.target_confirmed)
        entry.pick_allowed = entry.pick_allowed or bool(obj.pick_allowed)

    def _find_match(self, obj: PerceivedObject, x: float, y: float) -> ObjectEntry | None:
        best: ObjectEntry | None = None
        best_dist = self._merge_distance_m
        for entry in self._entries:
            if entry.role != int(obj.navigation_role):
                continue
            if entry.object_kind != str(obj.object_kind):
                continue
            if entry.fruit_kind != str(obj.fruit_kind):
                continue
            dist = hypot(entry.x - x, entry.y - y)
            if dist <= best_dist:
                best = entry
                best_dist = dist
        return best

    def _publish(self) -> None:
        now_sec = self.get_clock().now().nanoseconds * 1.0e-9
        self._entries = [
            entry for entry in self._entries if not self._is_expired(entry, now_sec)
        ]

        obstacle_points: list[tuple[float, float, float]] = []
        targets: list[ObjectEntry] = []
        for entry in self._entries:
            if entry.role == PerceivedObject.ROLE_OBSTACLE:
                obstacle_points.extend(_expanded_points(entry.x, entry.y, entry.radius))
            elif entry.role == PerceivedObject.ROLE_TARGET:
                targets.append(entry)

        stamp = self.get_clock().now().to_msg()
        self._obstacle_publisher.publish(
            _make_cloud(stamp, self._map_frame, obstacle_points)
        )

        target = self._select_target(targets)
        if target is not None:
            pose = PoseStamped()
            pose.header.stamp = stamp
            pose.header.frame_id = self._map_frame
            pose.pose.position.x = target.x
            pose.pose.position.y = target.y
            pose.pose.orientation.w = 1.0
            self._target_publisher.publish(pose)

    def _is_expired(self, entry: ObjectEntry, now_sec: float) -> bool:
        ttl = (
            self._target_ttl_sec
            if entry.role == PerceivedObject.ROLE_TARGET
            else self._obstacle_ttl_sec
        )
        return now_sec - entry.last_seen_sec > ttl

    def _select_target(self, targets: list[ObjectEntry]) -> ObjectEntry | None:
        if not targets:
            return None
        return max(targets, key=lambda item: (item.seen_count, item.confidence))


def _transform_xy(transform, x: float, y: float) -> tuple[float, float]:
    translation = transform.transform.translation
    yaw = _yaw_from_quaternion(transform.transform.rotation)
    return (
        translation.x + cos(yaw) * x - sin(yaw) * y,
        translation.y + sin(yaw) * x + cos(yaw) * y,
    )


def _yaw_from_quaternion(quat) -> float:
    return atan2(
        2.0 * (quat.w * quat.z + quat.x * quat.y),
        1.0 - 2.0 * (quat.y * quat.y + quat.z * quat.z),
    )


def _expanded_points(x: float, y: float, radius: float) -> list[tuple[float, float, float]]:
    if radius <= 0.0:
        return [(x, y, 0.0)]
    return [
        (x, y, 0.0),
        (x + radius, y, 0.0),
        (x - radius, y, 0.0),
        (x, y + radius, 0.0),
        (x, y - radius, 0.0),
    ]


def _make_cloud(stamp, frame_id: str, points: list[tuple[float, float, float]]) -> PointCloud2:
    cloud = PointCloud2()
    cloud.header.stamp = stamp
    cloud.header.frame_id = frame_id
    cloud.height = 1
    cloud.width = len(points)
    cloud.fields = [
        PointField(name="x", offset=0, datatype=PointField.FLOAT32, count=1),
        PointField(name="y", offset=4, datatype=PointField.FLOAT32, count=1),
        PointField(name="z", offset=8, datatype=PointField.FLOAT32, count=1),
    ]
    cloud.is_bigendian = False
    cloud.point_step = 12
    cloud.row_step = cloud.point_step * cloud.width
    cloud.is_dense = True
    cloud.data = b"".join(struct.pack("<fff", *point) for point in points)
    return cloud


def main() -> None:
    rclpy.init()
    node = SemanticObjectRegistry()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
