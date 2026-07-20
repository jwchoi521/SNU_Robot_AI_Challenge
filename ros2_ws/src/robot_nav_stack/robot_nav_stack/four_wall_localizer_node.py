from __future__ import annotations

import json
import math
from collections import deque
from dataclasses import dataclass

import rclpy
from geometry_msgs.msg import PoseStamped, TransformStamped
from nav_msgs.msg import Odometry
from rclpy.duration import Duration
from rclpy.node import Node
from rclpy.time import Time
from sensor_msgs.msg import Imu, LaserScan
from std_msgs.msg import String
from tf2_ros import Buffer, TransformBroadcaster, TransformException, TransformListener

from .core import Pose2D, quaternion_from_yaw, wrap_angle, yaw_from_quaternion
from .time_alignment import (
    TimedPose2D,
    interpolate_pose,
    scan_duration_sec,
    transform_ray_to_reference,
)


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
        self.declare_parameter("use_lidar_tf_extrinsics", False)
        self.declare_parameter("lidar_tf_timeout_sec", 0.05)
        self.declare_parameter("enable_lidar_deskew", True)
        self.declare_parameter("motion_history_sec", 3.0)
        self.declare_parameter("motion_max_extrapolation_sec", 0.05)
        self.declare_parameter("use_odom_prior", True)
        self.declare_parameter("use_imu_yaw_prior", True)
        self.declare_parameter("max_imu_age_sec", 0.5)
        self.declare_parameter("publish_tf", False)
        self.declare_parameter("tf_mode", "map_to_base")
        self.declare_parameter("transform_tolerance_sec", 0.2)
        self.declare_parameter("publish_lidar_tf", True)
        self.declare_parameter("max_rays", 60)
        self.declare_parameter("min_rays", 40)
        self.declare_parameter("trim_fraction", 0.70)
        self.declare_parameter("range_residual_clamp_m", 0.25)
        self.declare_parameter("min_visible_walls", 2)
        self.declare_parameter("min_rays_per_wall", 10)
        self.declare_parameter("missing_wall_penalty", 0.05)
        self.declare_parameter("opt_iterations", 1)
        self.declare_parameter("initial_step_xy_m", 0.10)
        self.declare_parameter("initial_step_yaw_deg", 5.0)
        self.declare_parameter("use_global_seed_search_on_first_scan", False)
        self.declare_parameter("use_symmetry_seeds", False)
        self.declare_parameter("global_seed_step_m", 0.75)
        self.declare_parameter("global_seed_yaw_step_deg", 90.0)
        self.declare_parameter("prior_xy_weight", 0.003)
        self.declare_parameter("prior_yaw_weight", 0.003)
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
        self.odom_history: deque[TimedPose2D] = deque()
        self.last_imu_yaw: float | None = None
        self.current_imu_yaw: float | None = None
        self.current_imu_time_sec: float | None = None
        self.imu_history: deque[TimedPose2D] = deque()
        self._imu_prior_used = False
        self._warned_missing_odom_for_tf = False
        self._warned_bad_odom_stamp = False
        self._warned_bad_imu_stamp = False
        self._warned_missing_lidar_tf = False

        scan_topic = str(self.get_parameter("scan_topic").value)
        odom_topic = str(self.get_parameter("odom_topic").value)
        imu_topic = str(self.get_parameter("imu_topic").value)
        pose_topic = str(self.get_parameter("pose_topic").value)
        status_topic = str(self.get_parameter("status_topic").value)

        self.scan_sub = self.create_subscription(LaserScan, scan_topic, self.on_scan, 1)
        self.odom_sub = self.create_subscription(Odometry, odom_topic, self.on_odom, 30)
        self.imu_sub = self.create_subscription(Imu, imu_topic, self.on_imu, 30)
        self.pose_pub = self.create_publisher(PoseStamped, pose_topic, 10)
        self.status_pub = self.create_publisher(String, status_topic, 10)
        self.tf_broadcaster = TransformBroadcaster(self)
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self, spin_thread=True)

    def on_odom(self, msg: Odometry) -> None:
        q = msg.pose.pose.orientation
        pose = Pose2D(
            x=float(msg.pose.pose.position.x),
            y=float(msg.pose.pose.position.y),
            theta=yaw_from_quaternion(q.x, q.y, q.z, q.w),
        )
        self.current_odom_pose = pose
        stamp_sec = self._message_stamp_sec(msg.header.stamp, "odometry")
        if stamp_sec is not None:
            self._append_motion_sample(self.odom_history, TimedPose2D(stamp_sec, pose))

    def on_imu(self, msg: Imu) -> None:
        q = msg.orientation
        yaw = yaw_from_quaternion(q.x, q.y, q.z, q.w)
        self.current_imu_yaw = yaw
        stamp_sec = self._message_stamp_sec(msg.header.stamp, "IMU")
        if stamp_sec is not None:
            self.current_imu_time_sec = stamp_sec
            self._append_motion_sample(
                self.imu_history,
                TimedPose2D(stamp_sec, Pose2D(x=0.0, y=0.0, theta=yaw)),
            )

    def _message_stamp_sec(self, stamp, source: str) -> float | None:
        stamp_sec = self._stamp_to_seconds(stamp)
        if stamp_sec > 0.0:
            return stamp_sec
        warned_attr = "_warned_bad_odom_stamp" if source == "odometry" else "_warned_bad_imu_stamp"
        if not getattr(self, warned_attr):
            self.get_logger().warn(f"ignoring {source} sample with a zero timestamp")
            setattr(self, warned_attr, True)
        return None

    def _append_motion_sample(
        self,
        history: deque[TimedPose2D],
        sample: TimedPose2D,
    ) -> None:
        if history and sample.stamp_sec < history[-1].stamp_sec - 1.0e-6:
            return
        if history and abs(sample.stamp_sec - history[-1].stamp_sec) <= 1.0e-9:
            history[-1] = sample
        else:
            history.append(sample)
        history_sec = max(0.5, float(self.get_parameter("motion_history_sec").value))
        cutoff = sample.stamp_sec - history_sec
        while len(history) > 1 and history[1].stamp_sec < cutoff:
            history.popleft()

    def on_scan(self, msg: LaserScan) -> None:
        scan_start_sec = self._stamp_to_seconds(msg.header.stamp)
        if scan_start_sec <= 0.0:
            self._publish_status({"ok": False, "reason": "zero_scan_timestamp"})
            return

        scan_span_sec = scan_duration_sec(
            len(msg.ranges),
            float(msg.time_increment),
            float(msg.scan_time),
        )
        reference_sec = scan_start_sec + 0.5 * scan_span_sec
        reference_stamp = Time(
            nanoseconds=int(round(reference_sec * 1.0e9))
        ).to_msg()
        max_extrapolation = max(
            0.0,
            float(self.get_parameter("motion_max_extrapolation_sec").value),
        )
        odom_pose_at_reference = interpolate_pose(
            self.odom_history,
            reference_sec,
            max_extrapolation,
        )
        tf_mode = str(self.get_parameter("tf_mode").value).lower()
        deskew_requested = bool(self.get_parameter("enable_lidar_deskew").value)
        odom_reference_required = (
            tf_mode in ("map_to_odom", "map_odom") or deskew_requested
        )
        if odom_reference_required and odom_pose_at_reference is None:
            required_by = []
            if tf_mode in ("map_to_odom", "map_odom"):
                required_by.append("map_to_odom")
            if deskew_requested:
                required_by.append("lidar_deskew")
            self._publish_status(
                {
                    "ok": False,
                    "reason": "missing_odom_at_scan_reference",
                    "scan_reference_stamp": reference_sec,
                    "odom_samples": len(self.odom_history),
                    "required_by": required_by,
                }
            )
            return

        lidar_extrinsics = self._resolve_lidar_extrinsics(msg)
        if lidar_extrinsics is None:
            self._publish_status(
                {
                    "ok": False,
                    "reason": "missing_lidar_extrinsics_tf",
                    "base_frame": self.base_frame,
                    "lidar_frame": msg.header.frame_id,
                }
            )
            return

        rays, deskewed_rays, motion_dropped_rays = self._scan_to_base_rays(
            msg,
            scan_start_sec=scan_start_sec,
            reference_sec=reference_sec,
            odom_pose_at_reference=odom_pose_at_reference,
            lidar_extrinsics=lidar_extrinsics,
        )
        if len(rays) < int(self.get_parameter("min_rays").value):
            self._publish_status(
                {
                    "ok": False,
                    "reason": "not_enough_lidar_rays",
                    "rays": len(rays),
                    "motion_dropped_rays": motion_dropped_rays,
                }
            )
            return

        self._imu_prior_used = False
        imu_yaw_at_reference = self._imu_yaw_at(reference_sec)
        has_pose_prior = self.last_pose is not None
        prior = self._predict_prior_pose(odom_pose_at_reference, imu_yaw_at_reference)
        seeds = self._symmetry_seeds(prior)
        results = [
            self._optimize_seed(seed, prior, rays, use_prior=has_pose_prior)
            for seed in seeds
        ]
        if not results:
            self._publish_status({"ok": False, "reason": "no_localization_candidates"})
            return
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
        self.last_odom_pose = odom_pose_at_reference
        if imu_yaw_at_reference is not None:
            self.last_imu_yaw = imu_yaw_at_reference
        self._publish_pose(best.pose, reference_stamp)
        if bool(self.get_parameter("publish_tf").value):
            self._publish_tf(best.pose, reference_stamp, odom_pose_at_reference)

        self._publish_status(
            {
                "ok": True,
                "rays": len(rays),
                "used_rays": best.range_score.used_rays,
                "x": best.pose.x,
                "y": best.pose.y,
                "yaw_deg": math.degrees(best.pose.theta),
                "imu_yaw_deg": (
                    math.degrees(imu_yaw_at_reference)
                    if imu_yaw_at_reference is not None
                    else None
                ),
                "imu_yaw_prior_used": self._imu_prior_used,
                "scan_start_stamp": scan_start_sec,
                "scan_reference_stamp": reference_sec,
                "scan_duration_sec": scan_span_sec,
                "odom_aligned_to_scan": odom_pose_at_reference is not None,
                "lidar_deskew_enabled": deskew_requested,
                "lidar_deskew_applied": deskewed_rays > 0,
                "deskewed_rays": deskewed_rays,
                "motion_dropped_rays": motion_dropped_rays,
                "lidar_extrinsics_source": (
                    "tf"
                    if bool(self.get_parameter("use_lidar_tf_extrinsics").value)
                    else "parameters"
                ),
                "arena_origin": self.arena_origin,
                "tf_mode": str(self.get_parameter("tf_mode").value),
                "transform_tolerance_sec": float(
                    self.get_parameter("transform_tolerance_sec").value
                ),
                "arena_bounds": {
                    "min_x": self.min_x,
                    "max_x": self.max_x,
                    "min_y": self.min_y,
                    "max_y": self.max_y,
                },
                "global_seed_search_on_first_scan": bool(
                    self.get_parameter("use_global_seed_search_on_first_scan").value
                ),
                "symmetry_seeds_enabled": bool(
                    self.get_parameter("use_symmetry_seeds").value
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

    def _resolve_lidar_extrinsics(self, msg: LaserScan) -> tuple[float, float, float] | None:
        if not bool(self.get_parameter("use_lidar_tf_extrinsics").value):
            return (
                float(self.get_parameter("lidar_x_m").value),
                float(self.get_parameter("lidar_y_m").value),
                math.radians(float(self.get_parameter("lidar_yaw_deg").value)),
            )

        lidar_frame = msg.header.frame_id or str(self.get_parameter("lidar_frame").value)
        if lidar_frame == self.base_frame:
            return (0.0, 0.0, 0.0)
        timeout = max(0.0, float(self.get_parameter("lidar_tf_timeout_sec").value))
        try:
            transform = self.tf_buffer.lookup_transform(
                self.base_frame,
                lidar_frame,
                Time(),
                timeout=Duration(seconds=timeout),
            )
        except TransformException as exc:
            if not self._warned_missing_lidar_tf:
                self.get_logger().warn(
                    f"waiting for static {self.base_frame}->{lidar_frame} TF: {exc}"
                )
                self._warned_missing_lidar_tf = True
            return None

        self._warned_missing_lidar_tf = False
        translation = transform.transform.translation
        rotation = transform.transform.rotation
        return (
            float(translation.x),
            float(translation.y),
            yaw_from_quaternion(rotation.x, rotation.y, rotation.z, rotation.w),
        )

    def _scan_to_base_rays(
        self,
        msg: LaserScan,
        *,
        scan_start_sec: float,
        reference_sec: float,
        odom_pose_at_reference: Pose2D | None,
        lidar_extrinsics: tuple[float, float, float],
    ) -> tuple[list[ScanRay], int, int]:
        lidar_x, lidar_y, lidar_yaw = lidar_extrinsics
        valid: list[tuple[int, float, float]] = []
        angle = float(msg.angle_min)
        for index, observed in enumerate(msg.ranges):
            rr = float(observed)
            if math.isfinite(rr) and msg.range_min <= rr <= msg.range_max:
                valid.append((index, angle, rr))
            angle += float(msg.angle_increment)

        max_rays = max(1, int(self.get_parameter("max_rays").value))
        if len(valid) > max_rays:
            stride = max(1, int(math.ceil(len(valid) / max_rays)))
            valid = valid[::stride]

        max_extrapolation = max(
            0.0,
            float(self.get_parameter("motion_max_extrapolation_sec").value),
        )
        deskew = (
            bool(self.get_parameter("enable_lidar_deskew").value)
            and odom_pose_at_reference is not None
            and len(msg.ranges) > 1
            and reference_sec > scan_start_sec
        )
        ray_dt = float(msg.time_increment)
        if not math.isfinite(ray_dt) or ray_dt <= 0.0:
            ray_dt = (2.0 * (reference_sec - scan_start_sec)) / max(
                1, len(msg.ranges) - 1
            )

        rays: list[ScanRay] = []
        deskewed_rays = 0
        motion_dropped_rays = 0
        for index, angle, observed_range in valid:
            ray_yaw = lidar_yaw + angle
            origin_x = lidar_x
            origin_y = lidar_y
            dir_x = math.cos(ray_yaw)
            dir_y = math.sin(ray_yaw)
            if deskew:
                odom_pose_at_ray = interpolate_pose(
                    self.odom_history,
                    scan_start_sec + index * ray_dt,
                    max_extrapolation,
                )
                if odom_pose_at_ray is None:
                    motion_dropped_rays += 1
                    continue
                origin_x, origin_y, dir_x, dir_y = transform_ray_to_reference(
                    origin_x,
                    origin_y,
                    dir_x,
                    dir_y,
                    odom_pose_at_ray,
                    odom_pose_at_reference,
                )
                deskewed_rays += 1
            rays.append(
                ScanRay(
                    origin_x=origin_x,
                    origin_y=origin_y,
                    dir_x=dir_x,
                    dir_y=dir_y,
                    observed_range=observed_range,
                )
            )
        return rays, deskewed_rays, motion_dropped_rays

    def _predict_prior_pose(
        self,
        odom_pose_at_reference: Pose2D | None,
        imu_yaw_at_reference: float | None,
    ) -> Pose2D:
        imu_delta = self._imu_yaw_delta_since_last_scan(imu_yaw_at_reference)
        if (
            bool(self.get_parameter("use_odom_prior").value)
            and self.last_pose is not None
            and self.last_odom_pose is not None
            and odom_pose_at_reference is not None
        ):
            dx_odom = odom_pose_at_reference.x - self.last_odom_pose.x
            dy_odom = odom_pose_at_reference.y - self.last_odom_pose.y
            c_o = math.cos(-self.last_odom_pose.theta)
            s_o = math.sin(-self.last_odom_pose.theta)
            dx_local = c_o * dx_odom - s_o * dy_odom
            dy_local = s_o * dx_odom + c_o * dy_odom
            dtheta = wrap_angle(odom_pose_at_reference.theta - self.last_odom_pose.theta)
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

    def _imu_yaw_delta_since_last_scan(
        self, imu_yaw_at_reference: float | None
    ) -> float | None:
        if imu_yaw_at_reference is None or self.last_imu_yaw is None:
            return None
        self._imu_prior_used = True
        return wrap_angle(imu_yaw_at_reference - self.last_imu_yaw)

    def _imu_yaw_at(self, stamp_sec: float) -> float | None:
        if not bool(self.get_parameter("use_imu_yaw_prior").value):
            return None
        max_age = max(0.0, float(self.get_parameter("max_imu_age_sec").value))
        sample = interpolate_pose(self.imu_history, stamp_sec, max_age)
        return sample.theta if sample is not None else None

    @staticmethod
    def _stamp_to_seconds(stamp) -> float:
        return float(stamp.sec) + float(stamp.nanosec) * 1.0e-9

    def _symmetry_seeds(self, pose: Pose2D) -> list[Pose2D]:
        if self.last_pose is None:
            if bool(self.get_parameter("use_global_seed_search_on_first_scan").value):
                seeds = self._global_first_scan_seeds([], pose)
                if seeds:
                    return seeds
            return [self._clip_pose_to_arena(pose)]

        if not bool(self.get_parameter("use_symmetry_seeds").value):
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

    def _publish_tf(
        self, pose: Pose2D, stamp, odom_pose_at_stamp: Pose2D | None
    ) -> None:
        tf_stamp = self._tf_publish_stamp(stamp)
        tf_mode = str(self.get_parameter("tf_mode").value).lower()
        if tf_mode in ("map_to_odom", "map_odom"):
            self._publish_map_to_odom_tf(pose, tf_stamp, odom_pose_at_stamp)
            return
        if tf_mode not in ("map_to_base", "map_base", "direct"):
            self.get_logger().warn(
                f"unknown tf_mode {tf_mode!r}; falling back to map_to_base"
            )

        tf = TransformStamped()
        tf.header.stamp = tf_stamp
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
        lidar_tf.header.stamp = tf_stamp
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

    def _publish_map_to_odom_tf(
        self, map_pose_base: Pose2D, stamp, odom_pose_at_stamp: Pose2D | None
    ) -> None:
        if odom_pose_at_stamp is None:
            if not self._warned_missing_odom_for_tf:
                self.get_logger().warn(
                    "tf_mode=map_to_odom needs odometry interpolated at the TF stamp; "
                    "skipping map -> odom"
                )
                self._warned_missing_odom_for_tf = True
            return

        self._warned_missing_odom_for_tf = False
        odom_pose_base = odom_pose_at_stamp
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

    def _tf_publish_stamp(self, stamp):
        tolerance_sec = max(
            0.0,
            float(self.get_parameter("transform_tolerance_sec").value),
        )
        if tolerance_sec <= 0.0:
            return stamp
        stamp_sec = self._stamp_to_seconds(stamp) + tolerance_sec
        return Time(nanoseconds=int(round(stamp_sec * 1.0e9))).to_msg()

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
