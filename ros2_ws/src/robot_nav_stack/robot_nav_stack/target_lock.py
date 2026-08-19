from __future__ import annotations

import math
from dataclasses import dataclass

from .core import Pose2D


@dataclass(frozen=True)
class TargetSelection:
    pose: Pose2D
    stamp_sec: float
    distance_m: float
    locked: bool


class TargetLock:
    """Latch a selected target pose once the robot is close enough."""

    def __init__(self) -> None:
        self._pose: Pose2D | None = None
        self._stamp_sec: float | None = None

    @property
    def active(self) -> bool:
        return self._pose is not None and self._stamp_sec is not None

    def select(
        self,
        *,
        candidate_pose: Pose2D | None,
        candidate_stamp_sec: float | None,
        robot_pose: Pose2D,
        lock_distance_m: float,
    ) -> TargetSelection | None:
        if self.active:
            assert self._pose is not None
            assert self._stamp_sec is not None
            return TargetSelection(
                pose=self._pose,
                stamp_sec=self._stamp_sec,
                distance_m=_distance(self._pose, robot_pose),
                locked=True,
            )

        if candidate_pose is None or candidate_stamp_sec is None:
            return None

        distance_m = _distance(candidate_pose, robot_pose)
        should_lock = lock_distance_m > 0.0 and distance_m <= lock_distance_m
        if should_lock:
            self._pose = candidate_pose
            self._stamp_sec = candidate_stamp_sec

        return TargetSelection(
            pose=candidate_pose,
            stamp_sec=candidate_stamp_sec,
            distance_m=distance_m,
            locked=should_lock,
        )

    def protects(self, pose: Pose2D, radius_m: float) -> bool:
        return (
            self.active
            and self._pose is not None
            and _distance(self._pose, pose) <= max(0.0, radius_m)
        )

    def clear(self) -> None:
        self._pose = None
        self._stamp_sec = None


def closer_target_improvement_m(
    *,
    robot_pose: Pose2D,
    active_target_pose: Pose2D,
    candidate_target_pose: Pose2D,
) -> float:
    """Return how much closer the candidate is than the active target."""

    return _distance(active_target_pose, robot_pose) - _distance(
        candidate_target_pose,
        robot_pose,
    )


def should_switch_to_closer_target(
    *,
    robot_pose: Pose2D,
    active_target_pose: Pose2D,
    candidate_target_pose: Pose2D,
    min_improvement_m: float,
) -> bool:
    """Return whether a distinct candidate is sufficiently closer to preempt."""

    if _distance(active_target_pose, candidate_target_pose) <= 1.0e-6:
        return False
    improvement_m = closer_target_improvement_m(
        robot_pose=robot_pose,
        active_target_pose=active_target_pose,
        candidate_target_pose=candidate_target_pose,
    )
    return improvement_m + 1.0e-9 >= max(0.0, min_improvement_m)


def _distance(first: Pose2D, second: Pose2D) -> float:
    return math.hypot(first.x - second.x, first.y - second.y)
