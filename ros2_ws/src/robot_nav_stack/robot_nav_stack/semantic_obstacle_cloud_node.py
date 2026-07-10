from __future__ import annotations

import math
import struct
from dataclasses import dataclass

import rclpy
from geometry_msgs.msg import PoseStamped
from rclpy.node import Node
from sensor_msgs.msg import PointCloud2, PointField


@dataclass
class TimedObstacle:
    x: float
    y: float
    z: float
    stamp_sec: float
    hits: int = 1


class SemanticObstacleCloudNode(Node):
    """Convert object poses into a PointCloud2 obstacle source for Nav2.

    Nav2 costmap obstacle layers naturally accept LaserScan/PointCloud2 data.
    Our perception stack produces object poses, so this node expands each pose
    into a small disk of points and publishes it as `/semantic_obstacles`.

    Use `clearing: false` for this source in Nav2. Object detections are sparse,
    so they are good at marking obstacles but should not clear free space.
    """

    def __init__(self) -> None:
        super().__init__("semantic_obstacle_cloud_node")
        self.declare_parameter("input_topic", "/object_pose_map")
        self.declare_parameter("output_topic", "/semantic_obstacles")
        self.declare_parameter("exclude_pose_topic", "/bbox_goal_target_pose")
        self.declare_parameter("frame_id", "map")
        self.declare_parameter("obstacle_radius_m", 0.04)
        self.declare_parameter("point_spacing_m", 0.02)
        self.declare_parameter("ttl_sec", 0.75)
        self.declare_parameter("association_radius_m", 0.12)
        self.declare_parameter("exclude_radius_m", 0.35)
        self.declare_parameter("exclude_pose_max_age_sec", 2.0)
        self.declare_parameter("position_smoothing_alpha", 0.35)
        self.declare_parameter("publish_hz", 10.0)
        self.declare_parameter("z_m", 0.05)

        self.frame_id = str(self.get_parameter("frame_id").value)
        self.obstacles: list[TimedObstacle] = []
        self.excluded_pose: tuple[float, float, float] | None = None
        self._warned_exclude_frame = False

        input_topic = str(self.get_parameter("input_topic").value)
        output_topic = str(self.get_parameter("output_topic").value)
        exclude_topic = str(self.get_parameter("exclude_pose_topic").value).strip()
        publish_hz = float(self.get_parameter("publish_hz").value)

        self.sub = self.create_subscription(PoseStamped, input_topic, self.on_object_pose, 20)
        self.exclude_sub = (
            self.create_subscription(PoseStamped, exclude_topic, self.on_exclude_pose, 10)
            if exclude_topic
            else None
        )
        self.pub = self.create_publisher(PointCloud2, output_topic, 10)
        self.timer = self.create_timer(1.0 / max(publish_hz, 0.1), self.publish_cloud)

    def on_exclude_pose(self, msg: PoseStamped) -> None:
        if msg.header.frame_id and msg.header.frame_id != self.frame_id:
            if not self._warned_exclude_frame:
                self.get_logger().warn(
                    "ignoring semantic obstacle exclusion pose in frame "
                    f"{msg.header.frame_id!r}; expected {self.frame_id!r}"
                )
                self._warned_exclude_frame = True
            return

        stamp = self.get_clock().now().nanoseconds * 1e-9
        self.excluded_pose = (
            float(msg.pose.position.x),
            float(msg.pose.position.y),
            stamp,
        )
        self._prune()

    def on_object_pose(self, msg: PoseStamped) -> None:
        stamp = self.get_clock().now().nanoseconds * 1e-9

        self._prune()
        x = float(msg.pose.position.x)
        y = float(msg.pose.position.y)
        if self._is_excluded(x, y, stamp):
            return

        z = float(self.get_parameter("z_m").value)
        match = self._nearest_obstacle(x, y)
        if match is not None:
            alpha = self._clamp(float(self.get_parameter("position_smoothing_alpha").value), 0.0, 1.0)
            match.x = (1.0 - alpha) * match.x + alpha * x
            match.y = (1.0 - alpha) * match.y + alpha * y
            match.z = z
            match.stamp_sec = stamp
            match.hits += 1
            return

        self.obstacles.append(
            TimedObstacle(
                x=x,
                y=y,
                z=z,
                stamp_sec=stamp,
            )
        )

    def publish_cloud(self) -> None:
        self._prune()
        now_msg = self.get_clock().now().to_msg()
        points: list[tuple[float, float, float]] = []
        radius = float(self.get_parameter("obstacle_radius_m").value)
        spacing = float(self.get_parameter("point_spacing_m").value)

        for obstacle in self.obstacles:
            points.extend(self._disk_points(obstacle.x, obstacle.y, obstacle.z, radius, spacing))

        cloud = self._make_cloud(points)
        cloud.header.stamp = now_msg
        cloud.header.frame_id = self.frame_id
        self.pub.publish(cloud)

    def _prune(self) -> None:
        now = self.get_clock().now().nanoseconds * 1e-9
        ttl = float(self.get_parameter("ttl_sec").value)
        self.obstacles = [
            obs
            for obs in self.obstacles
            if now - obs.stamp_sec <= ttl and not self._is_excluded(obs.x, obs.y, now)
        ]

    def _nearest_obstacle(self, x: float, y: float) -> TimedObstacle | None:
        association_radius = max(0.0, float(self.get_parameter("association_radius_m").value))
        best: TimedObstacle | None = None
        best_dist = association_radius
        for obstacle in self.obstacles:
            if self._is_excluded(obstacle.x, obstacle.y):
                continue
            dist = math.hypot(x - obstacle.x, y - obstacle.y)
            if dist <= best_dist:
                best = obstacle
                best_dist = dist
        return best

    def _is_excluded(self, x: float, y: float, now_sec: float | None = None) -> bool:
        if self.excluded_pose is None:
            return False
        radius = max(0.0, float(self.get_parameter("exclude_radius_m").value))
        if radius <= 0.0:
            return False
        now = now_sec
        if now is None:
            now = self.get_clock().now().nanoseconds * 1e-9
        exclude_x, exclude_y, exclude_stamp = self.excluded_pose
        max_age = float(self.get_parameter("exclude_pose_max_age_sec").value)
        if max_age > 0.0 and now - exclude_stamp > max_age:
            return False
        return math.hypot(x - exclude_x, y - exclude_y) <= radius

    @staticmethod
    def _clamp(value: float, low: float, high: float) -> float:
        return max(low, min(high, value))

    @staticmethod
    def _disk_points(
        cx: float,
        cy: float,
        z: float,
        radius: float,
        spacing: float,
    ) -> list[tuple[float, float, float]]:
        spacing = max(spacing, 0.02)
        cells = int(math.ceil(radius / spacing))
        points = [(cx, cy, z)]
        for iy in range(-cells, cells + 1):
            for ix in range(-cells, cells + 1):
                x = cx + ix * spacing
                y = cy + iy * spacing
                if math.hypot(x - cx, y - cy) <= radius:
                    points.append((x, y, z))
        return points

    def _make_cloud(self, points: list[tuple[float, float, float]]) -> PointCloud2:
        cloud = PointCloud2()
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
    node = SemanticObstacleCloudNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
