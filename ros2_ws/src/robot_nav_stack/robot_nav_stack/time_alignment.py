from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

from .core import Pose2D, wrap_angle


@dataclass(frozen=True)
class TimedPose2D:
    stamp_sec: float
    pose: Pose2D


def interpolate_pose(
    samples: Sequence[TimedPose2D],
    stamp_sec: float,
    max_extrapolation_sec: float,
) -> Pose2D | None:
    """Interpolate a pose at ``stamp_sec`` without silently using stale motion."""

    if not samples:
        return None

    limit = max(0.0, max_extrapolation_sec)
    first = samples[0]
    last = samples[-1]
    epsilon = 1.0e-9
    if len(samples) == 1:
        return first.pose if abs(stamp_sec - first.stamp_sec) <= limit + epsilon else None
    if stamp_sec <= first.stamp_sec:
        if first.stamp_sec - stamp_sec > limit + epsilon:
            return None
        return _interpolate_pair(first, samples[1], stamp_sec)
    if stamp_sec >= last.stamp_sec:
        if stamp_sec - last.stamp_sec > limit + epsilon:
            return None
        return _interpolate_pair(samples[-2], last, stamp_sec)

    iterator = iter(samples)
    before = next(iterator)
    for after in iterator:
        if before.stamp_sec <= stamp_sec <= after.stamp_sec:
            return _interpolate_pair(before, after, stamp_sec)
        before = after
    return None


def _interpolate_pair(
    before: TimedPose2D,
    after: TimedPose2D,
    stamp_sec: float,
) -> Pose2D:
    dt = after.stamp_sec - before.stamp_sec
    if dt <= 0.0:
        return after.pose
    alpha = (stamp_sec - before.stamp_sec) / dt
    theta_delta = wrap_angle(after.pose.theta - before.pose.theta)
    return Pose2D(
        x=before.pose.x + alpha * (after.pose.x - before.pose.x),
        y=before.pose.y + alpha * (after.pose.y - before.pose.y),
        theta=wrap_angle(before.pose.theta + alpha * theta_delta),
    )


def scan_duration_sec(range_count: int, time_increment: float, scan_time: float) -> float:
    """Return the acquisition span represented by a LaserScan message."""

    if range_count > 1 and math.isfinite(time_increment) and time_increment > 0.0:
        return (range_count - 1) * time_increment
    if math.isfinite(scan_time) and scan_time > 0.0:
        return scan_time
    return 0.0


def transform_ray_to_reference(
    origin_x: float,
    origin_y: float,
    dir_x: float,
    dir_y: float,
    odom_pose_at_ray: Pose2D,
    odom_pose_at_reference: Pose2D,
) -> tuple[float, float, float, float]:
    """Express a ray captured at one base pose in a reference base frame."""

    c_ray = math.cos(odom_pose_at_ray.theta)
    s_ray = math.sin(odom_pose_at_ray.theta)
    origin_odom_x = odom_pose_at_ray.x + c_ray * origin_x - s_ray * origin_y
    origin_odom_y = odom_pose_at_ray.y + s_ray * origin_x + c_ray * origin_y

    dx = origin_odom_x - odom_pose_at_reference.x
    dy = origin_odom_y - odom_pose_at_reference.y
    c_ref = math.cos(odom_pose_at_reference.theta)
    s_ref = math.sin(odom_pose_at_reference.theta)
    origin_ref_x = c_ref * dx + s_ref * dy
    origin_ref_y = -s_ref * dx + c_ref * dy

    yaw_delta = wrap_angle(odom_pose_at_ray.theta - odom_pose_at_reference.theta)
    c_delta = math.cos(yaw_delta)
    s_delta = math.sin(yaw_delta)
    dir_ref_x = c_delta * dir_x - s_delta * dir_y
    dir_ref_y = s_delta * dir_x + c_delta * dir_y
    return origin_ref_x, origin_ref_y, dir_ref_x, dir_ref_y
