from __future__ import annotations

import math
from dataclasses import dataclass


def wrap_angle(theta: float) -> float:
    return (theta + math.pi) % (2.0 * math.pi) - math.pi


def angle_diff(target: float, current: float) -> float:
    return wrap_angle(target - current)


@dataclass(frozen=True)
class Pose2D:
    x: float
    y: float
    theta: float = 0.0


@dataclass(frozen=True)
class BBox:
    cx: float
    cy: float
    w: float
    h: float


@dataclass(frozen=True)
class Detection:
    stamp: float
    bbox: BBox
    object_type: str
    confidence: float = 1.0
    class_id: int = -1
    fruit_kind: str = ""
    fruit_confidence: float = 0.0


def transform_point(parent_pose_child: Pose2D, point_child: Pose2D) -> Pose2D:
    """Transform a 2D point from child frame into parent frame."""

    c = math.cos(parent_pose_child.theta)
    s = math.sin(parent_pose_child.theta)
    x = parent_pose_child.x + c * point_child.x - s * point_child.y
    y = parent_pose_child.y + s * point_child.x + c * point_child.y
    return Pose2D(x=x, y=y, theta=wrap_angle(parent_pose_child.theta + point_child.theta))


def yaw_from_quaternion(x: float, y: float, z: float, w: float) -> float:
    """Extract yaw from quaternion."""

    siny_cosp = 2.0 * (w * z + x * y)
    cosy_cosp = 1.0 - 2.0 * (y * y + z * z)
    return math.atan2(siny_cosp, cosy_cosp)


def quaternion_from_yaw(yaw: float) -> tuple[float, float, float, float]:
    half = yaw * 0.5
    return (0.0, 0.0, math.sin(half), math.cos(half))
