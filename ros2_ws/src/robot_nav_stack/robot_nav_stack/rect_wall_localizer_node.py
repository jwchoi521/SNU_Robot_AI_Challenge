from __future__ import annotations

import json
import math
from dataclasses import dataclass

import rclpy
from geometry_msgs.msg import PoseStamped, TransformStamped
from nav_msgs.msg import Odometry
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from std_msgs.msg import String
from tf2_ros import TransformBroadcaster

from .core import Pose2D, quaternion_from_yaw, wrap_angle, yaw_from_quaternion


@dataclass(frozen=True)
class LocalizerResult:
    pose: Pose2D
    wall_score: float
    prior_score: float
    total_score: float


class RectWallLocalizerNode(Node):
    """Estimate robot pose inside a rectangular arena from LiDAR wall returns.

    The wall-only scan matching objective is symmetric in a square arena. This
    node therefore generates symmetry-equivalent candidate poses and breaks the
    tie with a motion prior from the previous pose, optional odometry, and the
    configured initial pose.
    """

    def __init__(self) -> None:
        super().__init__("rect_wall_localizer_node")
        self.declare_parameter("scan_topic", "/scan")
        self.declare_parameter("odom_topic", "/odom")
        self.declare_parameter("pose_topic", "/robot_pose_map")
        self.declare_parameter("status_topic", "/rect_wall_localizer/status")
        self.declare_parameter("map_frame", "map")
        self.declare_parameter("base_frame", "base_link")
        self.declare_parameter("arena_width_m", 4.0)
        self.declare_parameter("arena_height_m", 4.0)
        self.declare_parameter("arena_origin", "center")
        self.declare_parameter("initial_x_m", 1.8)
        self.declare_parameter("initial_y_m", -1.8)
        self.declare_parameter("initial_yaw_deg", 90.0)
        self.declare_parameter("lidar_x_m", 0.0)
        self.declare_parameter("lidar_y_m", 0.0)
        self.declare_parameter("lidar_yaw_deg", 0.0)
        self.declare_parameter("use_odom_prior", True)
        self.declare_parameter("publish_tf", False)
        self.declare_parameter("max_points", 720)
        self.declare_parameter("min_points", 80)
        self.declare_parameter("trim_fraction", 0.65)
        self.declare_parameter("wall_distance_clamp_m", 0.50)
        self.declare_parameter("outside_penalty_m", 0.35)
        self.declare_parameter("opt_iterations", 5)
        self.declare_parameter("initial_step_xy_m", 0.08)
        self.declare_parameter("initial_step_yaw_deg", 4.0)
        self.declare_parameter("use_global_seed_search_on_first_scan", False)
        self.declare_parameter("global_seed_step_m", 0.75)
        self.declare_parameter("global_seed_yaw_step_deg", 90.0)
        self.declare_parameter("prior_xy_weight", 0.20)
        self.declare_parameter("prior_yaw_weight", 0.08)
        self.declare_parameter("symmetry_wall_score_ratio", 1.20)

        self.map_frame = str(self.get_parameter("map_frame").value)
        self.base_frame = str(self.get_parameter("base_frame").value)
        self.arena_w = float(self.get_parameter("arena_width_m").value)
        self.arena_h = float(self.get_parameter("arena_height_m").value)
        self.arena_origin = str(self.get_parameter("arena_origin").value).lower()
        self.min_x, self.max_x, self.min_y, self.max_y = self._arena_bounds()
        self.last_pose: Pose2D | None = None
        self.last_odom_pose: Pose2D | None = None
        self.current_odom_pose: Pose2D | None = None

        scan_topic = str(self.get_parameter("scan_topic").value)
        odom_topic = str(self.get_parameter("odom_topic").value)
        pose_topic = str(self.get_parameter("pose_topic").value)
        status_topic = str(self.get_parameter("status_topic").value)

        self.scan_sub = self.create_subscription(LaserScan, scan_topic, self.on_scan, 10)
        self.odom_sub = self.create_subscription(Odometry, odom_topic, self.on_odom, 30)
        self.pose_pub = self.create_publisher(PoseStamped, pose_topic, 10)
        self.status_pub = self.create_publisher(String, status_topic, 10)
        self.tf_broadcaster = TransformBroadcaster(self)

    def on_odom(self, msg: Odometry) -> None:
        q = msg.pose.pose.orientation
        self.current_odom_pose = Pose2D(
            x=float(msg.pose.pose.position.x),
            y=float(msg.pose.pose.position.y),
            theta=yaw_from_quaternion(q.x, q.y, q.z, q.w),
        )

    def on_scan(self, msg: LaserScan) -> None:
        points = self._scan_to_base_points(msg)
        if len(points) < int(self.get_parameter("min_points").value):
            self._publish_status(
                {
                    "ok": False,
                    "reason": "not_enough_scan_points",
                    "points": len(points),
                }
            )
            return

        has_pose_prior = self.last_pose is not None
        prior = self._predict_prior_pose()
        seeds = self._symmetry_seeds(prior)
        results = [
            self._optimize_seed(seed, prior, points, use_prior=has_pose_prior)
            for seed in seeds
        ]
        results.sort(key=lambda item: item.total_score)
        best = results[0]

        wall_sorted = sorted(results, key=lambda item: item.wall_score)
        wall_ratio = wall_sorted[1].wall_score / max(wall_sorted[0].wall_score, 1e-9) if len(wall_sorted) > 1 else 999.0
        symmetry_resolved_by_prior = wall_ratio <= float(self.get_parameter("symmetry_wall_score_ratio").value)
        ambiguous = symmetry_resolved_by_prior and best is not wall_sorted[0]

        self.last_pose = best.pose
        self.last_odom_pose = self.current_odom_pose
        self._publish_pose(best.pose, msg.header.stamp)
        if bool(self.get_parameter("publish_tf").value):
            self._publish_tf(best.pose, msg.header.stamp)
        self._publish_status(
            {
                "ok": True,
                "points": len(points),
                "x": best.pose.x,
                "y": best.pose.y,
                "yaw_deg": math.degrees(best.pose.theta),
                "arena_origin": self.arena_origin,
                "arena_bounds": {
                    "min_x": self.min_x,
                    "max_x": self.max_x,
                    "min_y": self.min_y,
                    "max_y": self.max_y,
                },
                "global_seed_search_on_first_scan": bool(
                    self.get_parameter("use_global_seed_search_on_first_scan").value
                ),
                "pose_prior_active": has_pose_prior,
                "wall_score": best.wall_score,
                "prior_score": best.prior_score,
                "total_score": best.total_score,
                "wall_score_ratio_best_two": wall_ratio,
                "symmetry_resolved_by_prior": symmetry_resolved_by_prior,
                "ambiguous_without_prior": ambiguous,
                "candidate_count": len(results),
            }
        )

    def _scan_to_base_points(self, msg: LaserScan) -> list[tuple[float, float]]:
        lidar_x = float(self.get_parameter("lidar_x_m").value)
        lidar_y = float(self.get_parameter("lidar_y_m").value)
        lidar_yaw = math.radians(float(self.get_parameter("lidar_yaw_deg").value))
        c_l = math.cos(lidar_yaw)
        s_l = math.sin(lidar_yaw)
        raw_points: list[tuple[float, float]] = []
        angle = float(msg.angle_min)
        for r in msg.ranges:
            rr = float(r)
            if math.isfinite(rr) and msg.range_min <= rr <= msg.range_max:
                lx = rr * math.cos(angle)
                ly = rr * math.sin(angle)
                bx = lidar_x + c_l * lx - s_l * ly
                by = lidar_y + s_l * lx + c_l * ly
                raw_points.append((bx, by))
            angle += float(msg.angle_increment)

        max_points = max(1, int(self.get_parameter("max_points").value))
        if len(raw_points) <= max_points:
            return raw_points
        stride = max(1, int(math.ceil(len(raw_points) / max_points)))
        return raw_points[::stride]

    def _predict_prior_pose(self) -> Pose2D:
        if (
            bool(self.get_parameter("use_odom_prior").value)
            and self.last_pose is not None
            and self.last_odom_pose is not None
            and self.current_odom_pose is not None
        ):
            dx_odom = self.current_odom_pose.x - self.last_odom_pose.x
            dy_odom = self.current_odom_pose.y - self.last_odom_pose.y
            c_o = math.cos(-self.last_odom_pose.theta)
            s_o = math.sin(-self.last_odom_pose.theta)
            dx_local = c_o * dx_odom - s_o * dy_odom
            dy_local = s_o * dx_odom + c_o * dy_odom
            dtheta = wrap_angle(self.current_odom_pose.theta - self.last_odom_pose.theta)
            c_m = math.cos(self.last_pose.theta)
            s_m = math.sin(self.last_pose.theta)
            return Pose2D(
                x=self.last_pose.x + c_m * dx_local - s_m * dy_local,
                y=self.last_pose.y + s_m * dx_local + c_m * dy_local,
                theta=wrap_angle(self.last_pose.theta + dtheta),
            )

        if self.last_pose is not None:
            return self.last_pose

        return Pose2D(
            x=float(self.get_parameter("initial_x_m").value),
            y=float(self.get_parameter("initial_y_m").value),
            theta=math.radians(float(self.get_parameter("initial_yaw_deg").value)),
        )

    def _symmetry_seeds(self, pose: Pose2D) -> list[Pose2D]:
        if self.last_pose is None:
            if bool(self.get_parameter("use_global_seed_search_on_first_scan").value):
                seeds = self._global_first_scan_seeds([], pose)
                if seeds:
                    return seeds
            return [self._clip_pose_to_arena(pose)]

        min_x = self.min_x
        max_x = self.max_x
        min_y = self.min_y
        max_y = self.max_y
        center_x = 0.5 * (min_x + max_x)
        center_y = 0.5 * (min_y + max_y)
        span_x = max_x - min_x
        span_y = max_y - min_y
        seeds = [
            pose,
            Pose2D(min_x + max_x - pose.x, min_y + max_y - pose.y, wrap_angle(pose.theta + math.pi)),
            Pose2D(min_x + max_x - pose.x, pose.y, wrap_angle(math.pi - pose.theta)),
            Pose2D(pose.x, min_y + max_y - pose.y, wrap_angle(-pose.theta)),
        ]

        if abs(span_x - span_y) <= 0.05:
            rel_x = pose.x - center_x
            rel_y = pose.y - center_y
            seeds.extend(
                [
                    Pose2D(center_x - rel_y, center_y + rel_x, wrap_angle(pose.theta + math.pi / 2.0)),
                    Pose2D(center_x + rel_y, center_y - rel_x, wrap_angle(pose.theta - math.pi / 2.0)),
                    Pose2D(center_x + rel_y, center_y + rel_x, wrap_angle(math.pi / 2.0 - pose.theta)),
                    Pose2D(center_x - rel_y, center_y - rel_x, wrap_angle(-math.pi / 2.0 - pose.theta)),
                ]
            )

        unique: list[Pose2D] = []
        for seed in seeds:
            clipped = Pose2D(
                x=min(max(seed.x, min_x + 0.02), max_x - 0.02),
                y=min(max(seed.y, min_y + 0.02), max_y - 0.02),
                theta=wrap_angle(seed.theta),
            )
            if not any(
                math.hypot(clipped.x - old.x, clipped.y - old.y) < 1e-4
                and abs(wrap_angle(clipped.theta - old.theta)) < 1e-4
                for old in unique
            ):
                unique.append(clipped)
        unique.extend(self._global_first_scan_seeds(unique, pose))
        return unique

    def _clip_pose_to_arena(self, pose: Pose2D) -> Pose2D:
        return Pose2D(
            x=min(max(pose.x, self.min_x + 0.02), self.max_x - 0.02),
            y=min(max(pose.y, self.min_y + 0.02), self.max_y - 0.02),
            theta=wrap_angle(pose.theta),
        )

    def _global_first_scan_seeds(self, existing: list[Pose2D], prior: Pose2D) -> list[Pose2D]:
        if self.last_pose is not None:
            return []
        if not bool(self.get_parameter("use_global_seed_search_on_first_scan").value):
            return []

        step = max(0.10, float(self.get_parameter("global_seed_step_m").value))
        yaw_step = math.radians(
            max(5.0, float(self.get_parameter("global_seed_yaw_step_deg").value))
        )
        yaw_count = max(1, int(math.ceil((2.0 * math.pi) / yaw_step)))
        margin = 0.02

        x_values = self._seed_axis_values(self.min_x + margin, self.max_x - margin, step)
        y_values = self._seed_axis_values(self.min_y + margin, self.max_y - margin, step)
        seeds: list[Pose2D] = []
        for x in x_values:
            for y in y_values:
                for yaw_idx in range(yaw_count):
                    seed = Pose2D(
                        x=x,
                        y=y,
                        theta=wrap_angle(prior.theta + yaw_idx * yaw_step),
                    )
                    if self._seed_exists(seed, existing) or self._seed_exists(seed, seeds):
                        continue
                    seeds.append(seed)
        return seeds

    @staticmethod
    def _seed_axis_values(low: float, high: float, step: float) -> list[float]:
        if high <= low:
            return [0.5 * (low + high)]
        values = [low]
        current = low
        while current + step < high:
            current += step
            values.append(current)
        if abs(values[-1] - high) > 1e-6:
            values.append(high)
        center = 0.5 * (low + high)
        if all(abs(value - center) > 1e-6 for value in values):
            values.append(center)
            values.sort()
        return values

    @staticmethod
    def _seed_exists(seed: Pose2D, seeds: list[Pose2D]) -> bool:
        return any(
            math.hypot(seed.x - old.x, seed.y - old.y) < 1e-4
            and abs(wrap_angle(seed.theta - old.theta)) < 1e-4
            for old in seeds
        )

    def _optimize_seed(
        self,
        seed: Pose2D,
        prior: Pose2D,
        points: list[tuple[float, float]],
        *,
        use_prior: bool,
    ) -> LocalizerResult:
        pose = seed
        score = self._wall_score(pose, points)
        step_xy = float(self.get_parameter("initial_step_xy_m").value)
        step_yaw = math.radians(float(self.get_parameter("initial_step_yaw_deg").value))
        iterations = int(self.get_parameter("opt_iterations").value)

        for _ in range(iterations):
            improved = True
            while improved:
                improved = False
                candidates = [
                    Pose2D(pose.x + step_xy, pose.y, pose.theta),
                    Pose2D(pose.x - step_xy, pose.y, pose.theta),
                    Pose2D(pose.x, pose.y + step_xy, pose.theta),
                    Pose2D(pose.x, pose.y - step_xy, pose.theta),
                    Pose2D(pose.x, pose.y, wrap_angle(pose.theta + step_yaw)),
                    Pose2D(pose.x, pose.y, wrap_angle(pose.theta - step_yaw)),
                ]
                for candidate in candidates:
                    if not (
                        self.min_x <= candidate.x <= self.max_x
                        and self.min_y <= candidate.y <= self.max_y
                    ):
                        continue
                    candidate_score = self._wall_score(candidate, points)
                    if candidate_score + 1e-12 < score:
                        pose = candidate
                        score = candidate_score
                        improved = True
            step_xy *= 0.5
            step_yaw *= 0.5

        prior_score = self._prior_score(pose, prior) if use_prior else 0.0
        return LocalizerResult(
            pose=pose,
            wall_score=score,
            prior_score=prior_score,
            total_score=score + prior_score,
        )

    def _wall_score(self, pose: Pose2D, points: list[tuple[float, float]]) -> float:
        c = math.cos(pose.theta)
        s = math.sin(pose.theta)
        clamp = max(0.05, float(self.get_parameter("wall_distance_clamp_m").value))
        outside_penalty = max(0.0, float(self.get_parameter("outside_penalty_m").value))
        distances: list[float] = []
        for px, py in points:
            mx = pose.x + c * px - s * py
            my = pose.y + s * px + c * py
            outside = max(0.0, self.min_x - mx, mx - self.max_x, self.min_y - my, my - self.max_y)
            wall_dist = min(abs(mx - self.min_x), abs(self.max_x - mx), abs(my - self.min_y), abs(self.max_y - my))
            d = min(clamp, wall_dist + outside_penalty * outside)
            distances.append(d * d)

        if not distances:
            return float("inf")
        distances.sort()
        keep = max(1, int(len(distances) * float(self.get_parameter("trim_fraction").value)))
        return sum(distances[:keep]) / keep

    def _arena_bounds(self) -> tuple[float, float, float, float]:
        if self.arena_origin in ("center", "centre", "middle"):
            return (
                -0.5 * self.arena_w,
                0.5 * self.arena_w,
                -0.5 * self.arena_h,
                0.5 * self.arena_h,
            )
        if self.arena_origin in ("corner", "bottom_left", "lower_left"):
            return (0.0, self.arena_w, 0.0, self.arena_h)
        raise ValueError(
            "arena_origin must be 'center' or 'corner', "
            f"got {self.arena_origin!r}"
        )

    def _prior_score(self, pose: Pose2D, prior: Pose2D) -> float:
        dx = pose.x - prior.x
        dy = pose.y - prior.y
        dtheta = wrap_angle(pose.theta - prior.theta)
        xy_weight = float(self.get_parameter("prior_xy_weight").value)
        yaw_weight = float(self.get_parameter("prior_yaw_weight").value)
        return xy_weight * (dx * dx + dy * dy) + yaw_weight * (dtheta * dtheta)

    def _publish_pose(self, pose: Pose2D, stamp) -> None:
        msg = PoseStamped()
        msg.header.stamp = stamp
        msg.header.frame_id = self.map_frame
        msg.pose.position.x = pose.x
        msg.pose.position.y = pose.y
        msg.pose.position.z = 0.0
        qx, qy, qz, qw = quaternion_from_yaw(pose.theta)
        msg.pose.orientation.x = qx
        msg.pose.orientation.y = qy
        msg.pose.orientation.z = qz
        msg.pose.orientation.w = qw
        self.pose_pub.publish(msg)

    def _publish_tf(self, pose: Pose2D, stamp) -> None:
        tf = TransformStamped()
        tf.header.stamp = stamp
        tf.header.frame_id = self.map_frame
        tf.child_frame_id = self.base_frame
        tf.transform.translation.x = pose.x
        tf.transform.translation.y = pose.y
        tf.transform.translation.z = 0.0
        qx, qy, qz, qw = quaternion_from_yaw(pose.theta)
        tf.transform.rotation.x = qx
        tf.transform.rotation.y = qy
        tf.transform.rotation.z = qz
        tf.transform.rotation.w = qw
        self.tf_broadcaster.sendTransform(tf)

    def _publish_status(self, payload: dict) -> None:
        msg = String()
        msg.data = json.dumps(payload)
        self.status_pub.publish(msg)


def main() -> None:
    rclpy.init()
    node = RectWallLocalizerNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
