from __future__ import annotations

import struct
from math import cos, isfinite, radians, sin

import rclpy
from geometry_msgs.msg import PoseStamped
from rclpy.node import Node
from sensor_msgs.msg import PointCloud2, PointField
from snu_robot_interfaces.msg import PerceivedObject, PerceivedObjectArray


class SemanticObjectProjector(Node):
    """Project camera/IR objects into target and obstacle geometry."""

    def __init__(self) -> None:
        super().__init__("semantic_object_projector")

        self.declare_parameter("input_topic", "/perception/objects")
        self.declare_parameter("target_pose_topic", "/target_pose_base")
        self.declare_parameter("obstacle_cloud_topic", "/semantic_obstacles")
        self.declare_parameter("base_frame", "base_link")
        self.declare_parameter("bearing_positive_is_left", False)
        self.declare_parameter("min_distance_m", 0.10)
        self.declare_parameter("max_distance_m", 2.50)
        self.declare_parameter("min_confidence", 0.25)
        self.declare_parameter("prefer_closest_target", True)
        self.declare_parameter("require_confirmed_targets", True)
        self.declare_parameter("require_confirmed_obstacles", False)
        self.declare_parameter("default_obstacle_radius_m", 0.18)

        input_topic = self.get_parameter("input_topic").value
        target_pose_topic = self.get_parameter("target_pose_topic").value
        obstacle_cloud_topic = self.get_parameter("obstacle_cloud_topic").value

        self._base_frame = str(self.get_parameter("base_frame").value)
        self._bearing_positive_is_left = bool(
            self.get_parameter("bearing_positive_is_left").value
        )
        self._min_distance_m = float(self.get_parameter("min_distance_m").value)
        self._max_distance_m = float(self.get_parameter("max_distance_m").value)
        self._min_confidence = float(self.get_parameter("min_confidence").value)
        self._prefer_closest_target = bool(
            self.get_parameter("prefer_closest_target").value
        )
        self._require_confirmed_targets = bool(
            self.get_parameter("require_confirmed_targets").value
        )
        self._require_confirmed_obstacles = bool(
            self.get_parameter("require_confirmed_obstacles").value
        )
        self._default_obstacle_radius_m = float(
            self.get_parameter("default_obstacle_radius_m").value
        )

        self._target_publisher = self.create_publisher(
            PoseStamped, str(target_pose_topic), 10
        )
        self._obstacle_publisher = self.create_publisher(
            PointCloud2, str(obstacle_cloud_topic), 10
        )
        self._subscription = self.create_subscription(
            PerceivedObjectArray,
            str(input_topic),
            self._on_objects,
            10,
        )

        self.get_logger().info(
            f"Projecting semantic objects from {input_topic}; "
            f"target pose -> {target_pose_topic}, obstacles -> {obstacle_cloud_topic}"
        )

    def _on_objects(self, msg: PerceivedObjectArray) -> None:
        target = self._select_target(msg.objects)
        if target is not None:
            target_pose = self._object_to_pose(target)
            target_pose.header.stamp = msg.header.stamp
            target_pose.header.frame_id = self._base_frame
            self._target_publisher.publish(target_pose)

        obstacle_points = self._obstacle_points(msg.objects)
        cloud = self._make_obstacle_cloud(msg, obstacle_points)
        self._obstacle_publisher.publish(cloud)

    def _select_target(
        self, objects: list[PerceivedObject] | tuple[PerceivedObject, ...]
    ) -> PerceivedObject | None:
        candidates = [
            obj
            for obj in objects
            if obj.navigation_role == PerceivedObject.ROLE_TARGET
            and obj.pick_allowed
            and (obj.target_confirmed or not self._require_confirmed_targets)
            and self._has_valid_distance(obj)
            and float(obj.confidence) >= self._min_confidence
        ]
        if not candidates:
            return None

        if self._prefer_closest_target:
            return min(candidates, key=lambda obj: float(obj.distance_m))
        return max(candidates, key=lambda obj: float(obj.confidence))

    def _obstacle_points(
        self, objects: list[PerceivedObject] | tuple[PerceivedObject, ...]
    ) -> list[tuple[float, float, float]]:
        points: list[tuple[float, float, float]] = []
        for obj in objects:
            if obj.navigation_role != PerceivedObject.ROLE_OBSTACLE:
                continue
            if self._require_confirmed_obstacles and not obj.target_confirmed:
                continue
            if not self._has_valid_distance(obj):
                continue
            if float(obj.confidence) < self._min_confidence:
                continue

            x, y = self._object_xy(obj)
            radius = float(obj.obstacle_radius_m) or self._default_obstacle_radius_m
            points.extend(_expanded_points(x, y, radius))
        return points

    def _has_valid_distance(self, obj: PerceivedObject) -> bool:
        distance_m = float(obj.distance_m)
        return (
            obj.has_distance
            and isfinite(distance_m)
            and self._min_distance_m <= distance_m <= self._max_distance_m
        )

    def _object_to_pose(self, obj: PerceivedObject) -> PoseStamped:
        x, y = self._object_xy(obj)
        pose = PoseStamped()
        pose.pose.position.x = x
        pose.pose.position.y = y
        pose.pose.position.z = 0.0
        pose.pose.orientation.w = 1.0
        return pose

    def _object_xy(self, obj: PerceivedObject) -> tuple[float, float]:
        bearing_rad = radians(float(obj.bearing_deg))
        distance_m = float(obj.distance_m)
        lateral_sign = 1.0 if self._bearing_positive_is_left else -1.0
        return (
            distance_m * cos(bearing_rad),
            lateral_sign * distance_m * sin(bearing_rad),
        )

    def _make_obstacle_cloud(
        self,
        msg: PerceivedObjectArray,
        points: list[tuple[float, float, float]],
    ) -> PointCloud2:
        cloud = PointCloud2()
        cloud.header.stamp = msg.header.stamp
        cloud.header.frame_id = self._base_frame
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


def main() -> None:
    rclpy.init()
    node = SemanticObjectProjector()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
