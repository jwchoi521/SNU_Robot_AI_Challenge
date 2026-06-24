from __future__ import annotations

import struct
from dataclasses import dataclass
from math import atan2, hypot, isfinite, pi

import rclpy
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Path
from rclpy.node import Node
from rclpy.time import Time
from sensor_msgs.msg import PointCloud2, PointField
from std_msgs.msg import String


@dataclass(frozen=True)
class PathMetrics:
    status: str
    pose_count: int
    obstacle_count: int
    path_length_m: float
    straight_distance_m: float
    detour_ratio: float
    rotation_rad: float
    min_clearance_m: float
    estimated_time_sec: float
    goal_error_m: float | None
    notes: tuple[str, ...]


class PathFeedbackMonitor(Node):
    """Evaluate the latest Nav2 plan against semantic obstacle memory."""

    def __init__(self) -> None:
        super().__init__("path_feedback_monitor")

        self.declare_parameter("path_topic", "/plan")
        self.declare_parameter("obstacle_cloud_topic", "/semantic_obstacles")
        self.declare_parameter("goal_topic", "/mission/nav_goal")
        self.declare_parameter("feedback_topic", "/navigation/path_feedback")
        self.declare_parameter("publish_rate_hz", 2.0)
        self.declare_parameter("path_timeout_sec", 3.0)
        self.declare_parameter("obstacle_timeout_sec", 5.0)
        self.declare_parameter("goal_timeout_sec", 10.0)
        self.declare_parameter("blocked_clearance_m", 0.22)
        self.declare_parameter("caution_clearance_m", 0.45)
        self.declare_parameter("goal_tolerance_m", 0.25)
        self.declare_parameter("detour_ratio_warn", 1.60)
        self.declare_parameter("desired_linear_speed_mps", 0.20)
        self.declare_parameter("max_angular_speed_radps", 0.80)
        self.declare_parameter("obstacle_slowdown_weight", 0.80)
        self.declare_parameter("clearance_sample_step_m", 0.05)
        self.declare_parameter("max_path_samples", 2000)
        self.declare_parameter("max_obstacle_points", 1000)

        self._path_topic = str(self.get_parameter("path_topic").value)
        self._obstacle_cloud_topic = str(
            self.get_parameter("obstacle_cloud_topic").value
        )
        self._goal_topic = str(self.get_parameter("goal_topic").value)
        self._path_timeout_sec = float(self.get_parameter("path_timeout_sec").value)
        self._obstacle_timeout_sec = float(
            self.get_parameter("obstacle_timeout_sec").value
        )
        self._goal_timeout_sec = float(self.get_parameter("goal_timeout_sec").value)
        self._blocked_clearance_m = float(
            self.get_parameter("blocked_clearance_m").value
        )
        self._caution_clearance_m = float(
            self.get_parameter("caution_clearance_m").value
        )
        self._goal_tolerance_m = float(self.get_parameter("goal_tolerance_m").value)
        self._detour_ratio_warn = float(self.get_parameter("detour_ratio_warn").value)
        self._desired_linear_speed_mps = float(
            self.get_parameter("desired_linear_speed_mps").value
        )
        self._max_angular_speed_radps = float(
            self.get_parameter("max_angular_speed_radps").value
        )
        self._obstacle_slowdown_weight = float(
            self.get_parameter("obstacle_slowdown_weight").value
        )
        self._clearance_sample_step_m = float(
            self.get_parameter("clearance_sample_step_m").value
        )
        self._max_path_samples = int(self.get_parameter("max_path_samples").value)
        self._max_obstacle_points = int(self.get_parameter("max_obstacle_points").value)

        self._latest_path: Path | None = None
        self._latest_path_time: Time | None = None
        self._latest_path_frame = ""
        self._obstacles: list[tuple[float, float]] = []
        self._latest_obstacle_time: Time | None = None
        self._latest_obstacle_frame = ""
        self._latest_goal: PoseStamped | None = None
        self._latest_goal_time: Time | None = None
        self._last_status = ""

        self._feedback_publisher = self.create_publisher(
            String,
            str(self.get_parameter("feedback_topic").value),
            10,
        )
        self._path_subscription = self.create_subscription(
            Path,
            self._path_topic,
            self._on_path,
            10,
        )
        self._obstacle_subscription = self.create_subscription(
            PointCloud2,
            self._obstacle_cloud_topic,
            self._on_obstacle_cloud,
            10,
        )
        self._goal_subscription = self.create_subscription(
            PoseStamped,
            self._goal_topic,
            self._on_goal,
            10,
        )

        publish_rate_hz = float(self.get_parameter("publish_rate_hz").value)
        self._timer = self.create_timer(
            1.0 / max(0.1, publish_rate_hz),
            self._publish_feedback,
        )
        self.get_logger().info(
            "Path feedback monitor is evaluating Nav2 plans for fastest safe arrival"
        )

    def _on_path(self, msg: Path) -> None:
        self._latest_path = msg
        self._latest_path_time = self.get_clock().now()
        self._latest_path_frame = _path_frame(msg)

    def _on_obstacle_cloud(self, msg: PointCloud2) -> None:
        points = _read_cloud_xy(msg)
        if len(points) > self._max_obstacle_points:
            points = points[: self._max_obstacle_points]
        self._obstacles = points
        self._latest_obstacle_time = self.get_clock().now()
        self._latest_obstacle_frame = msg.header.frame_id

    def _on_goal(self, msg: PoseStamped) -> None:
        self._latest_goal = msg
        self._latest_goal_time = self.get_clock().now()

    def _publish_feedback(self) -> None:
        metrics = self._evaluate()
        msg = String()
        msg.data = _format_feedback(metrics)
        self._feedback_publisher.publish(msg)

        if metrics.status != self._last_status:
            self._last_status = metrics.status
            if metrics.status in ("BLOCKED", "CAUTION", "GOAL_MISMATCH", "STALE_PATH"):
                self.get_logger().warn(msg.data)
            else:
                self.get_logger().info(msg.data)

    def _evaluate(self) -> PathMetrics:
        if self._latest_path is None or self._latest_path_time is None:
            return _empty_metrics("WAITING", "path_not_received")

        path_age = self._age_sec(self._latest_path_time)
        if path_age is not None and path_age > self._path_timeout_sec:
            return _empty_metrics(
                "STALE_PATH",
                f"path_age={path_age:.2f}s",
                f"path_topic={self._path_topic}",
            )

        points = _path_points(self._latest_path)
        if len(points) < 2:
            return _empty_metrics("WAITING", "path_has_too_few_poses")

        path_length = _path_length(points)
        straight_distance = hypot(points[-1][0] - points[0][0], points[-1][1] - points[0][1])
        detour_ratio = path_length / straight_distance if straight_distance > 0.01 else 1.0
        rotation = _path_rotation(points)
        sampled_points = _sample_path(
            points,
            max(0.01, self._clearance_sample_step_m),
            max(2, self._max_path_samples),
        )
        min_clearance = _min_clearance(sampled_points, self._obstacles)
        goal_error = self._goal_error(points[-1])
        estimated_time = self._estimate_time(path_length, rotation, min_clearance)

        status = "OK"
        notes: list[str] = []
        obstacle_age = self._age_sec(self._latest_obstacle_time)
        goal_age = self._age_sec(self._latest_goal_time)

        if obstacle_age is None:
            notes.append("semantic_obstacles_not_received")
        elif obstacle_age > self._obstacle_timeout_sec:
            notes.append(f"semantic_obstacles_stale={obstacle_age:.2f}s")

        if self._latest_path_frame and self._latest_obstacle_frame:
            if self._latest_path_frame != self._latest_obstacle_frame:
                status = _worse_status(status, "CAUTION")
                notes.append(
                    f"frame_mismatch:path={self._latest_path_frame},obstacles={self._latest_obstacle_frame}"
                )

        if min_clearance < self._blocked_clearance_m:
            status = _worse_status(status, "BLOCKED")
            notes.append("path_crosses_semantic_obstacle_zone")
        elif min_clearance < self._caution_clearance_m:
            status = _worse_status(status, "CAUTION")
            notes.append("path_close_to_semantic_obstacle")

        if detour_ratio >= self._detour_ratio_warn:
            status = _worse_status(status, "SLOW")
            notes.append("detour_ratio_high")

        if goal_error is not None and goal_error > self._goal_tolerance_m:
            status = _worse_status(status, "GOAL_MISMATCH")
            notes.append("path_endpoint_far_from_mission_goal")
        elif goal_age is None:
            notes.append("mission_goal_not_received")
        elif goal_age > self._goal_timeout_sec:
            notes.append(f"mission_goal_stale={goal_age:.2f}s")

        return PathMetrics(
            status=status,
            pose_count=len(points),
            obstacle_count=len(self._obstacles),
            path_length_m=path_length,
            straight_distance_m=straight_distance,
            detour_ratio=detour_ratio,
            rotation_rad=rotation,
            min_clearance_m=min_clearance,
            estimated_time_sec=estimated_time,
            goal_error_m=goal_error,
            notes=tuple(notes),
        )

    def _age_sec(self, stamp: Time | None) -> float | None:
        if stamp is None:
            return None
        return (self.get_clock().now() - stamp).nanoseconds * 1.0e-9

    def _goal_error(self, path_end: tuple[float, float]) -> float | None:
        if self._latest_goal is None:
            return None
        goal_age = self._age_sec(self._latest_goal_time)
        if goal_age is not None and goal_age > self._goal_timeout_sec:
            return None
        goal = self._latest_goal.pose.position
        return hypot(goal.x - path_end[0], goal.y - path_end[1])

    def _estimate_time(
        self,
        path_length_m: float,
        rotation_rad: float,
        min_clearance_m: float,
    ) -> float:
        linear_speed = max(0.01, self._desired_linear_speed_mps)
        angular_speed = max(0.01, self._max_angular_speed_radps)
        drive_time = path_length_m / linear_speed
        turn_time = rotation_rad / angular_speed
        slowdown_time = 0.0

        if isfinite(min_clearance_m) and min_clearance_m < self._caution_clearance_m:
            closeness = (
                self._caution_clearance_m - max(0.0, min_clearance_m)
            ) / max(0.01, self._caution_clearance_m)
            slowdown_time = drive_time * self._obstacle_slowdown_weight * closeness

        return drive_time + turn_time + slowdown_time


def _empty_metrics(status: str, *notes: str) -> PathMetrics:
    return PathMetrics(
        status=status,
        pose_count=0,
        obstacle_count=0,
        path_length_m=0.0,
        straight_distance_m=0.0,
        detour_ratio=1.0,
        rotation_rad=0.0,
        min_clearance_m=float("inf"),
        estimated_time_sec=0.0,
        goal_error_m=None,
        notes=tuple(notes),
    )


def _format_feedback(metrics: PathMetrics) -> str:
    clearance = (
        "inf" if not isfinite(metrics.min_clearance_m) else f"{metrics.min_clearance_m:.2f}"
    )
    goal_error = (
        "n/a" if metrics.goal_error_m is None else f"{metrics.goal_error_m:.2f}"
    )
    fields = [
        f"status={metrics.status}",
        f"eta={metrics.estimated_time_sec:.2f}s",
        f"path_length={metrics.path_length_m:.2f}m",
        f"straight={metrics.straight_distance_m:.2f}m",
        f"detour={metrics.detour_ratio:.2f}",
        f"rotation={metrics.rotation_rad:.2f}rad",
        f"min_clearance={clearance}m",
        f"goal_error={goal_error}m",
        f"poses={metrics.pose_count}",
        f"obstacles={metrics.obstacle_count}",
    ]
    if metrics.notes:
        fields.append("notes=" + ",".join(metrics.notes))
    return " ".join(fields)


def _path_frame(path: Path) -> str:
    if path.header.frame_id:
        return path.header.frame_id
    for pose in path.poses:
        if pose.header.frame_id:
            return pose.header.frame_id
    return ""


def _path_points(path: Path) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
    for pose in path.poses:
        x = float(pose.pose.position.x)
        y = float(pose.pose.position.y)
        if isfinite(x) and isfinite(y):
            points.append((x, y))
    return points


def _path_length(points: list[tuple[float, float]]) -> float:
    return sum(
        hypot(curr[0] - prev[0], curr[1] - prev[1])
        for prev, curr in zip(points, points[1:])
    )


def _path_rotation(points: list[tuple[float, float]]) -> float:
    headings: list[float] = []
    for prev, curr in zip(points, points[1:]):
        dx = curr[0] - prev[0]
        dy = curr[1] - prev[1]
        if hypot(dx, dy) > 0.01:
            headings.append(atan2(dy, dx))
    return sum(
        abs(_angle_delta(curr, prev)) for prev, curr in zip(headings, headings[1:])
    )


def _angle_delta(curr: float, prev: float) -> float:
    delta = curr - prev
    while delta > pi:
        delta -= 2.0 * pi
    while delta < -pi:
        delta += 2.0 * pi
    return delta


def _sample_path(
    points: list[tuple[float, float]],
    sample_step_m: float,
    max_samples: int,
) -> list[tuple[float, float]]:
    samples: list[tuple[float, float]] = [points[0]]
    for prev, curr in zip(points, points[1:]):
        segment_length = hypot(curr[0] - prev[0], curr[1] - prev[1])
        step_count = max(1, int(segment_length / sample_step_m))
        for step in range(1, step_count + 1):
            ratio = step / step_count
            samples.append(
                (
                    prev[0] + (curr[0] - prev[0]) * ratio,
                    prev[1] + (curr[1] - prev[1]) * ratio,
                )
            )
            if len(samples) >= max_samples:
                return samples
    return samples


def _min_clearance(
    path_points: list[tuple[float, float]],
    obstacles: list[tuple[float, float]],
) -> float:
    if not path_points or not obstacles:
        return float("inf")
    best = float("inf")
    for path_x, path_y in path_points:
        for obstacle_x, obstacle_y in obstacles:
            distance = hypot(path_x - obstacle_x, path_y - obstacle_y)
            if distance < best:
                best = distance
    return best


def _read_cloud_xy(msg: PointCloud2) -> list[tuple[float, float]]:
    fields = {field.name: field for field in msg.fields}
    x_field = fields.get("x")
    y_field = fields.get("y")
    if x_field is None or y_field is None:
        return []

    x_fmt = _field_format(x_field)
    y_fmt = _field_format(y_field)
    if x_fmt is None or y_fmt is None:
        return []

    endian = ">" if msg.is_bigendian else "<"
    data = bytes(msg.data)
    points: list[tuple[float, float]] = []
    for row in range(msg.height):
        row_offset = row * msg.row_step
        for col in range(msg.width):
            base = row_offset + col * msg.point_step
            x = struct.unpack_from(endian + x_fmt, data, base + x_field.offset)[0]
            y = struct.unpack_from(endian + y_fmt, data, base + y_field.offset)[0]
            if isfinite(x) and isfinite(y):
                points.append((float(x), float(y)))
    return points


def _field_format(field: PointField) -> str | None:
    if field.datatype == PointField.FLOAT32:
        return "f"
    if field.datatype == PointField.FLOAT64:
        return "d"
    return None


def _worse_status(current: str, candidate: str) -> str:
    severity = {
        "OK": 0,
        "SLOW": 1,
        "CAUTION": 2,
        "GOAL_MISMATCH": 3,
        "STALE_PATH": 4,
        "BLOCKED": 5,
        "WAITING": 6,
    }
    return candidate if severity[candidate] > severity[current] else current


def main() -> None:
    rclpy.init()
    node = PathFeedbackMonitor()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
