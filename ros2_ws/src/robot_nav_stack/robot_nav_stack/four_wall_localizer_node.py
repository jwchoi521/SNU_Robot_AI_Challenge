from __future__ import annotations

import json
import math
from dataclasses import dataclass

import rclpy
from geometry_msgs.msg import PoseStamped, TransformStamped
from nav_msgs.msg import Odometry
from rclpy.node import Node
from sensor_msgs.msg import Imu, LaserScan
from std_msgs.msg import String
from tf2_ros import TransformBroadcaster

from .core import Pose2D, quaternion_from_yaw, wrap_angle, yaw_from_quaternion


@dataclass(frozen=True)
class ScanRay:
    origin_x: float
    origin_y: float
    dir_x: float
    dir_y: float
    observed_range: float


@dataclass(frozen=True)
class RangeScore:
    score: float
    used_rays: int
    wall_counts: dict[str, int]
    visible_walls: int


@dataclass(frozen=True)
class LocalizerResult:
    pose: Pose2D
    range_score: RangeScore
    prior_score: float
    total_score: float


class FourWallLocalizerNode(Node):
    """Estimate robot pose by ray-casting LiDAR returns against four arena walls.

    This node assumes the LiDAR mainly sees the known rectangular arena walls.
    For each candidate robot pose, it predicts where every LiDAR ray should hit
    one of the four walls, then minimizes the robust range residual.

    A square arena is symmetric, so wall ranges alone can produce mirror/rotate
    pose candidates. The node evaluates those symmetry candidates and uses the
    previous pose plus optional odometry as the continuity prior.
    """

    def __init__(self) -> None:
        super().__init__("four_wall_localizer_node")
        self.declare_parameter("scan_topic", "/scan")
        self.declare_parameter("odom_topic", "/odom")
        self.declare_parameter("imu_topic", "/imu")
        self.declare_parameter("pose_topic", "/robot_pose_map")
        self.declare_parameter("status_topic", "/four_wall_localizer/status")
        self.declare_parameter("map_frame", "map")
        self.declare_parameter("odom_frame", "odom")
        self.declare_parameter("base_frame", "base_link")
        self.declare_parameter("lidar_frame", "lidar")
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
        self.declare_parameter("use_imu_yaw_prior", True)
        self.declare_parameter("max_imu_age_sec", 0.5)
        self.declare_parameter("publish_tf", False)
        self.declare_parameter("tf_mode", "map_to_base")
        self.declare_parameter("publish_lidar_tf", True)
        self.declare_parameter("max_rays", 720)
        self.declare_parameter("min_rays", 80)
        self.declare_parameter("trim_fraction", 0.70)
        self.declare_parameter("range_residual_clamp_m", 0.35)
        self.declare_parameter("min_visible_walls", 2)
        self.declare_parameter("min_rays_per_wall", 10)
        self.declare_parameter("missing_wall_penalty", 0.05)
        self.declare_parameter("opt_iterations", 6)
        self.declare_parameter("initial_step_xy_m", 0.10)
        self.declare_parameter("initial_step_yaw_deg", 5.0)
        self.declare_parameter("use_global_seed_search_on_first_scan", False)
        self.declare_parameter("global_seed_step_m", 0.75)
        self.declare_parameter("global_seed_yaw_step_deg", 90.0)
        self.declare_parameter("prior_xy_weight", 0.03)
        self.declare_parameter("prior_yaw_weight", 0.01)
        self.declare_parameter("symmetry_range_score_ratio", 1.20)

        self.map_frame = str(self.get_parameter("map_frame").value)
        self.odom_frame = str(self.get_parameter("odom_frame").value)
        self.base_frame = str(self.get_parameter("base_frame").value)
        self.arena_w = float(self.get_parameter("arena_width_m").value)
        self.arena_h = float(self.get_parameter("arena_height_m").value)
        self.arena_origin = str(self.get_parameter("arena_origin").value).lower()
        self.min_x, self.max_x, self.min_y, self.max_y = self._arena_bounds()
        self.last_pose: Pose2D | None = None
        self.last_odom_pose: Pose2D | None = None
        self.current_odom_pose: Pose2D | None = None
        self.last_imu_yaw: float | None = None
        self.current_imu_yaw: float | None = None
        self.current_imu_time_sec: float | None = None
        self._imu_prior_used = False
        self._warned_missing_odom_for_tf = False

        scan_topic = str(self.get_parameter("scan_topic").value)
        odom_topic = str(self.get_parameter("odom_topic").value)
        imu_topic = str(self.get_parameter("imu_topic").value)
        pose_topic = str(self.get_parameter("pose_topic").value)
        status_topic = str(self.get_parameter("status_topic").value)

        self.scan_sub = self.create_subscription(LaserScan, scan_topic, self.on_scan, 10)
        self.odom_sub = self.create_subscription(Odometry, odom_topic, self.on_odom, 30)
        self.imu_sub = self.create_subscription(Imu, imu_topic, self.on_imu, 30)
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

    def on_imu(self, msg: Imu) -> None:
        q = msg.orientation
        self.current_imu_yaw = yaw_from_quaternion(q.x, q.y, q.z, q.w)
        self.current_imu_time_sec = self.get_clock().now().nanoseconds * 1.0e-9

    def on_scan(self, msg: LaserScan) -> None:
        rays = self._scan_to_base_rays(msg)
        if len(rays) < int(self.get_parameter("min_rays").value):
            self._publish_status(
                {
                    "ok": False,
                    "reason": "not_enough_lidar_rays",
                    "rays": len(rays),
                }
            )
            return

        self._imu_prior_used = False
        has_pose_prior = self.last_pose is not None
        prior = self._predict_prior_pose()
        seeds = self._symmetry_seeds(prior)
        results = [
            self._optimize_seed(seed, prior, rays, use_prior=has_pose_prior)
            for seed in seeds
        ]
        results.sort(key=lambda item: item.total_score)
        best = results[0]

        wall_sorted = sorted(results, key=lambda item: item.range_score.score)
        score_ratio = (
            wall_sorted[1].range_score.score / max(wall_sorted[0].range_score.score, 1e-9)
            if len(wall_sorted) > 1
            else 999.0
        )
        symmetry_resolved_by_prior = score_ratio <= float(
            self.get_parameter("symmetry_range_score_ratio").value
        )
        ambiguous = symmetry_resolved_by_prior and best is not wall_sorted[0]

        self.last_pose = best.pose
        self.last_odom_pose = self.current_odom_pose
        if self.current_imu_yaw is not None:
            self.last_imu_yaw = self.current_imu_yaw
        self._publish_pose(best.pose, msg.header.stamp)
        if bool(self.get_parameter("publish_tf").value):
            self._publish_tf(best.pose, msg.header.stamp)

        self._publish_status(
            {
                "ok": True,
                "rays": len(rays),
                "used_rays": best.range_score.used_rays,
                "x": best.pose.x,
                "y": best.pose.y,
                "yaw_deg": math.degrees(best.pose.theta),
                "imu_yaw_deg": (
                    math.degrees(self.current_imu_yaw)
                    if self.current_imu_yaw is not None
                    else None
                ),
                "imu_yaw_prior_used": self._imu_prior_used,
                "arena_origin": self.arena_origin,
                "tf_mode": str(self.get_parameter("tf_mode").value),
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
                "range_score": best.range_score.score,
                "prior_score": best.prior_score,
                "total_score": best.total_score,
                "wall_counts": best.range_score.wall_counts,
                "visible_walls": best.range_score.visible_walls,
                "range_score_ratio_best_two": score_ratio,
                "symmetry_resolved_by_prior": symmetry_resolved_by_prior,
                "ambiguous_without_prior": ambiguous,
                "candidate_count": len(results),
            }
        )

    def _scan_to_base_rays(self, msg: LaserScan) -> list[ScanRay]:
        lidar_x = float(self.get_parameter("lidar_x_m").value)
        lidar_y = float(self.get_parameter("lidar_y_m").value)
        lidar_yaw = math.radians(float(self.get_parameter("lidar_yaw_deg").value))
        rays: list[ScanRay] = []

        angle = float(msg.angle_min)
        for observed in msg.ranges:
            rr = float(observed)
            if math.isfinite(rr) and msg.range_min <= rr <= msg.range_max:
                ray_yaw = lidar_yaw + angle
                rays.append(
                    ScanRay(
                        origin_x=lidar_x,
                        origin_y=lidar_y,
                        dir_x=math.cos(ray_yaw),
                        dir_y=math.sin(ray_yaw),
                        observed_range=rr,
                    )
                )
            angle += float(msg.angle_increment)

        max_rays = max(1, int(self.get_parameter("max_rays").value))
        if len(rays) <= max_rays:
            return rays
        stride = max(1, int(math.ceil(len(rays) / max_rays)))
        return rays[::stride]

    def _predict_prior_pose(self) -> Pose2D:
        imu_delta = self._imu_yaw_delta_since_last_scan()
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
            if imu_delta is not None:
                dtheta = imu_delta
            c_m = math.cos(self.last_pose.theta)
            s_m = math.sin(self.last_pose.theta)
            return Pose2D(
                x=self.last_pose.x + c_m * dx_local - s_m * dy_local,
                y=self.last_pose.y + s_m * dx_local + c_m * dy_local,
                theta=wrap_angle(self.last_pose.theta + dtheta),
            )

        if self.last_pose is not None:
            if imu_delta is not None:
                return Pose2D(
                    x=self.last_pose.x,
                    y=self.last_pose.y,
                    theta=wrap_angle(self.last_pose.theta + imu_delta),
                )
            return self.last_pose

        return Pose2D(
            x=float(self.get_parameter("initial_x_m").value),
            y=float(self.get_parameter("initial_y_m").value),
            theta=math.radians(float(self.get_parameter("initial_yaw_deg").value)),
        )

    def _imu_yaw_delta_since_last_scan(self) -> float | None:
        current = self._fresh_current_imu_yaw()
        if current is None or self.last_imu_yaw is None:
            return None
        self._imu_prior_used = True
        return wrap_angle(current - self.last_imu_yaw)

    def _fresh_current_imu_yaw(self) -> float | None:
        if not bool(self.get_parameter("use_imu_yaw_prior").value):
            return None
        if self.current_imu_yaw is None or self.current_imu_time_sec is None:
            return None
        now_sec = self.get_clock().now().nanoseconds * 1.0e-9
        max_age = max(0.0, float(self.get_parameter("max_imu_age_sec").value))
        if now_sec - self.current_imu_time_sec > max_age:
            return None
        return self.current_imu_yaw

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
        rays: list[ScanRay],
        *,
        use_prior: bool,
    ) -> LocalizerResult:
        pose = seed
        range_score = self._range_score(pose, rays)
        score = range_score.score
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
                    candidate_score = self._range_score(candidate, rays)
                    if candidate_score.score + 1e-12 < score:
                        pose = candidate
                        range_score = candidate_score
                        score = candidate_score.score
                        improved = True
            step_xy *= 0.5
            step_yaw *= 0.5

        prior_score = self._prior_score(pose, prior) if use_prior else 0.0
        return LocalizerResult(
            pose=pose,
            range_score=range_score,
            prior_score=prior_score,
            total_score=range_score.score + prior_score,
        )

    def _range_score(self, pose: Pose2D, rays: list[ScanRay]) -> RangeScore:
        c = math.cos(pose.theta)
        s = math.sin(pose.theta)
        clamp = max(0.05, float(self.get_parameter("range_residual_clamp_m").value))
        residuals: list[float] = []
        wall_counts = {"left": 0, "right": 0, "bottom": 0, "top": 0}

        for ray in rays:
            origin_x = pose.x + c * ray.origin_x - s * ray.origin_y
            origin_y = pose.y + s * ray.origin_x + c * ray.origin_y
            dir_x = c * ray.dir_x - s * ray.dir_y
            dir_y = s * ray.dir_x + c * ray.dir_y
            hit = self._first_wall_hit(origin_x, origin_y, dir_x, dir_y)
            if hit is None:
                continue

            expected_range, wall_name = hit
            residual = min(clamp, abs(ray.observed_range - expected_range))
            residuals.append(residual * residual)
            wall_counts[wall_name] += 1

        if not residuals:
            return RangeScore(
                score=float("inf"),
                used_rays=0,
                wall_counts=wall_counts,
                visible_walls=0,
            )

        residuals.sort()
        keep = max(1, int(len(residuals) * float(self.get_parameter("trim_fraction").value)))
        base_score = sum(residuals[:keep]) / keep
        min_rays_per_wall = int(self.get_parameter("min_rays_per_wall").value)
        visible_walls = sum(1 for count in wall_counts.values() if count >= min_rays_per_wall)
        missing = max(0, int(self.get_parameter("min_visible_walls").value) - visible_walls)
        score = base_score + missing * float(self.get_parameter("missing_wall_penalty").value)
        return RangeScore(
            score=score,
            used_rays=len(residuals),
            wall_counts=wall_counts,
            visible_walls=visible_walls,
        )

    def _first_wall_hit(
        self,
        origin_x: float,
        origin_y: float,
        dir_x: float,
        dir_y: float,
    ) -> tuple[float, str] | None:
        eps = 1e-9
        tolerance = 1e-6
        hits: list[tuple[float, str]] = []

        if abs(dir_x) > eps:
            t_left = (self.min_x - origin_x) / dir_x
            y_left = origin_y + t_left * dir_y
            if t_left > 0.0 and self.min_y - tolerance <= y_left <= self.max_y + tolerance:
                hits.append((t_left, "left"))

            t_right = (self.max_x - origin_x) / dir_x
            y_right = origin_y + t_right * dir_y
            if t_right > 0.0 and self.min_y - tolerance <= y_right <= self.max_y + tolerance:
                hits.append((t_right, "right"))

        if abs(dir_y) > eps:
            t_bottom = (self.min_y - origin_y) / dir_y
            x_bottom = origin_x + t_bottom * dir_x
            if t_bottom > 0.0 and self.min_x - tolerance <= x_bottom <= self.max_x + tolerance:
                hits.append((t_bottom, "bottom"))

            t_top = (self.max_y - origin_y) / dir_y
            x_top = origin_x + t_top * dir_x
            if t_top > 0.0 and self.min_x - tolerance <= x_top <= self.max_x + tolerance:
                hits.append((t_top, "top"))

        if not hits:
            return None
        return min(hits, key=lambda item: item[0])

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
        tf_mode = str(self.get_parameter("tf_mode").value).lower()
        if tf_mode in ("map_to_odom", "map_odom"):
            self._publish_map_to_odom_tf(pose, stamp)
            return
        if tf_mode not in ("map_to_base", "map_base", "direct"):
            self.get_logger().warn(
                f"unknown tf_mode {tf_mode!r}; falling back to map_to_base"
            )

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

        if not bool(self.get_parameter("publish_lidar_tf").value):
            return

        lidar_frame = str(self.get_parameter("lidar_frame").value)
        if lidar_frame == self.base_frame:
            return

        lidar_x = float(self.get_parameter("lidar_x_m").value)
        lidar_y = float(self.get_parameter("lidar_y_m").value)
        lidar_yaw = math.radians(float(self.get_parameter("lidar_yaw_deg").value))
        c = math.cos(pose.theta)
        s = math.sin(pose.theta)
        lidar_pose = Pose2D(
            x=pose.x + c * lidar_x - s * lidar_y,
            y=pose.y + s * lidar_x + c * lidar_y,
            theta=wrap_angle(pose.theta + lidar_yaw),
        )

        lidar_tf = TransformStamped()
        lidar_tf.header.stamp = stamp
        lidar_tf.header.frame_id = self.map_frame
        lidar_tf.child_frame_id = lidar_frame
        lidar_tf.transform.translation.x = lidar_pose.x
        lidar_tf.transform.translation.y = lidar_pose.y
        lidar_tf.transform.translation.z = 0.0
        qx, qy, qz, qw = quaternion_from_yaw(lidar_pose.theta)
        lidar_tf.transform.rotation.x = qx
        lidar_tf.transform.rotation.y = qy
        lidar_tf.transform.rotation.z = qz
        lidar_tf.transform.rotation.w = qw
        self.tf_broadcaster.sendTransform(lidar_tf)

    def _publish_map_to_odom_tf(self, map_pose_base: Pose2D, stamp) -> None:
        if self.current_odom_pose is None:
            if not self._warned_missing_odom_for_tf:
                self.get_logger().warn(
                    "tf_mode=map_to_odom needs odometry; "
                    "waiting before publishing map -> odom"
                )
                self._warned_missing_odom_for_tf = True
            return

        self._warned_missing_odom_for_tf = False
        odom_pose_base = self.current_odom_pose
        theta = wrap_angle(map_pose_base.theta - odom_pose_base.theta)
        c = math.cos(theta)
        s = math.sin(theta)
        tx = map_pose_base.x - (c * odom_pose_base.x - s * odom_pose_base.y)
        ty = map_pose_base.y - (s * odom_pose_base.x + c * odom_pose_base.y)

        tf = TransformStamped()
        tf.header.stamp = stamp
        tf.header.frame_id = self.map_frame
        tf.child_frame_id = self.odom_frame
        tf.transform.translation.x = tx
        tf.transform.translation.y = ty
        tf.transform.translation.z = 0.0
        qx, qy, qz, qw = quaternion_from_yaw(theta)
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
    node = FourWallLocalizerNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
