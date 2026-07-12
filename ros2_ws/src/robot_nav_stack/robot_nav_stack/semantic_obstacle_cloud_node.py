from __future__ import annotations

import math
import struct
from dataclasses import dataclass

import rclpy
from geometry_msgs.msg import PoseStamped
from nav2_msgs.srv import ClearEntireCostmap
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
    into a small disk of points and publishes it as `/semantic_obstacle_cloud`.

    Use `clearing: false` for this source in Nav2. Object detections are sparse,
    so they are good at marking obstacles but should not clear free space.
    """

    def __init__(self) -> None:
        super().__init__("semantic_obstacle_cloud_node")
        # target이 아닌 물체만 입력받아 Nav2 costmap 장애물로 만든다.
        self.declare_parameter("input_topic", "/obstacle_object_pose_map")
        self.declare_parameter("output_topic", "/semantic_obstacle_cloud")
        self.declare_parameter("frame_id", "map")
        self.declare_parameter("obstacle_radius_m", 0.05)
        self.declare_parameter("point_spacing_m", 0.01)
        self.declare_parameter("ttl_sec", 15.0)
        self.declare_parameter("association_radius_m", 0.12)
        self.declare_parameter("position_smoothing_alpha", 0.35)
        self.declare_parameter("publish_hz", 10.0)
        self.declare_parameter("z_m", 0.05)
        self.declare_parameter("clear_costmaps_on_expiry", True)
        self.declare_parameter("clear_costmap_cooldown_sec", 1.0)
        self.declare_parameter(
            "local_clear_service",
            "/local_costmap/clear_entirely_local_costmap",
        )
        self.declare_parameter(
            "global_clear_service",
            "/global_costmap/clear_entirely_global_costmap",
        )

        self.frame_id = str(self.get_parameter("frame_id").value)
        self.obstacles: list[TimedObstacle] = []
        self._last_clear_request_sec = float("-inf")
        self._warned_clear_services_unavailable = False
        self._clear_futures = []

        input_topic = str(self.get_parameter("input_topic").value)
        output_topic = str(self.get_parameter("output_topic").value)
        publish_hz = float(self.get_parameter("publish_hz").value)

        self.sub = self.create_subscription(PoseStamped, input_topic, self.on_object_pose, 20)
        self.pub = self.create_publisher(PointCloud2, output_topic, 10)
        self._clear_clients = [
            self.create_client(
                ClearEntireCostmap,
                str(self.get_parameter("local_clear_service").value),
            ),
            self.create_client(
                ClearEntireCostmap,
                str(self.get_parameter("global_clear_service").value),
            ),
        ]
        self._pending_clear_client_indices: set[int] = set()
        self.timer = self.create_timer(1.0 / max(publish_hz, 0.1), self.publish_cloud)

    def on_object_pose(self, msg: PoseStamped) -> None:
        stamp = self._stamp_to_sec(msg.header.stamp)
        if stamp <= 0.0:
            stamp = self.get_clock().now().nanoseconds * 1e-9

        if self._prune():
            self._schedule_costmap_clear()
        x = float(msg.pose.position.x)
        y = float(msg.pose.position.y)
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
        if self._prune():
            self._schedule_costmap_clear()
        elif self._pending_clear_client_indices:
            self._request_costmap_clear()
        self._clear_futures = [future for future in self._clear_futures if not future.done()]
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

    def _prune(self) -> bool:
        now = self.get_clock().now().nanoseconds * 1e-9
        ttl = float(self.get_parameter("ttl_sec").value)
        if ttl <= 0.0:
            return False
        before = len(self.obstacles)
        self.obstacles = [obs for obs in self.obstacles if now - obs.stamp_sec <= ttl]
        return len(self.obstacles) != before

    def _schedule_costmap_clear(self) -> None:
        if not bool(self.get_parameter("clear_costmaps_on_expiry").value):
            return
        self._pending_clear_client_indices.update(range(len(self._clear_clients)))
        self._request_costmap_clear()

    def _request_costmap_clear(self) -> None:
        if not self._pending_clear_client_indices:
            return

        now = self.get_clock().now().nanoseconds * 1e-9
        cooldown = max(
            0.0,
            float(self.get_parameter("clear_costmap_cooldown_sec").value),
        )
        if now - self._last_clear_request_sec < cooldown:
            return

        requested = False
        for index in list(self._pending_clear_client_indices):
            client = self._clear_clients[index]
            if client.service_is_ready():
                self._clear_futures.append(client.call_async(ClearEntireCostmap.Request()))
                self._pending_clear_client_indices.discard(index)
                requested = True

        if requested:
            self._last_clear_request_sec = now
            self.get_logger().info("clearing Nav2 costmaps after semantic obstacle expiry")
        if not self._pending_clear_client_indices:
            self._warned_clear_services_unavailable = False
        elif not self._warned_clear_services_unavailable:
            self._warned_clear_services_unavailable = True
            self.get_logger().warn(
                "semantic obstacle expired, but Nav2 clear-costmap services are unavailable"
            )

    def _nearest_obstacle(self, x: float, y: float) -> TimedObstacle | None:
        association_radius = max(0.0, float(self.get_parameter("association_radius_m").value))
        best: TimedObstacle | None = None
        best_dist = association_radius
        for obstacle in self.obstacles:
            dist = math.hypot(x - obstacle.x, y - obstacle.y)
            if dist <= best_dist:
                best = obstacle
                best_dist = dist
        return best

    @staticmethod
    def _clamp(value: float, low: float, high: float) -> float:
        return max(low, min(high, value))

    @staticmethod
    # 물체 중심을 반지름만큼 점 구름으로 펼쳐 Nav2가 실제 크기의 장애물로 보게 한다.
    def _disk_points(
        cx: float,
        cy: float,
        z: float,
        radius: float,
        spacing: float,
    ) -> list[tuple[float, float, float]]:
        radius = max(0.0, radius)
        spacing = max(spacing, 0.005)
        cells = int(math.ceil(radius / spacing))
        points: list[tuple[float, float, float]] = []
        for iy in range(-cells, cells + 1):
            for ix in range(-cells, cells + 1):
                x = cx + ix * spacing
                y = cy + iy * spacing
                if math.hypot(x - cx, y - cy) <= radius:
                    points.append((x, y, z))

        # Include the exact circumference.  A grid whose spacing does not divide
        # the radius otherwise represents 5 cm as only about 4-4.5 cm.
        if radius > 0.0:
            samples = max(16, int(math.ceil(2.0 * math.pi * radius / spacing)))
            for index in range(samples):
                angle = 2.0 * math.pi * index / samples
                points.append(
                    (
                        cx + radius * math.cos(angle),
                        cy + radius * math.sin(angle),
                        z,
                    )
                )
        elif not points:
            points.append((cx, cy, z))
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

    @staticmethod
    def _stamp_to_sec(stamp) -> float:
        return float(stamp.sec) + float(stamp.nanosec) * 1e-9


def main() -> None:
    rclpy.init()
    node = SemanticObstacleCloudNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
