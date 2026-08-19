from __future__ import annotations

import math

from robot_nav_stack.core import Pose2D
from robot_nav_stack.target_lock import (
    TargetLock,
    closer_target_improvement_m,
    should_switch_to_closer_target,
)


def _select(
    target_lock: TargetLock,
    candidate: Pose2D | None,
    robot: Pose2D,
    lock_distance_m: float,
    stamp_sec: float = 1.0,
):
    return target_lock.select(
        candidate_pose=candidate,
        candidate_stamp_sec=stamp_sec if candidate is not None else None,
        robot_pose=robot,
        lock_distance_m=lock_distance_m,
    )


def test_target_is_locked_at_configured_distance() -> None:
    target_lock = TargetLock()
    robot = Pose2D(0.0, 0.0)
    original = Pose2D(0.30, 0.0)

    selection = _select(target_lock, original, robot, lock_distance_m=0.30)

    assert selection is not None
    assert selection.locked
    assert target_lock.active


def test_locked_target_ignores_a_closer_replacement() -> None:
    target_lock = TargetLock()
    original = Pose2D(0.30, 0.0)
    replacement = Pose2D(0.05, 0.0)
    _select(target_lock, original, Pose2D(0.0, 0.0), lock_distance_m=0.30)

    selection = _select(
        target_lock,
        replacement,
        Pose2D(0.10, 0.0),
        lock_distance_m=0.30,
        stamp_sec=2.0,
    )

    assert selection is not None
    assert selection.pose == original
    assert selection.stamp_sec == 1.0
    assert selection.locked


def test_lock_distance_is_configurable_and_zero_disables_locking() -> None:
    target_lock = TargetLock()
    target = Pose2D(0.30, 0.0)

    selection = _select(target_lock, target, Pose2D(0.0, 0.0), lock_distance_m=0.20)
    assert selection is not None
    assert not selection.locked
    assert not target_lock.active

    selection = _select(target_lock, target, Pose2D(0.0, 0.0), lock_distance_m=0.0)
    assert selection is not None
    assert not selection.locked
    assert not target_lock.active


def test_locked_target_survives_missing_detection_and_reclassification() -> None:
    target_lock = TargetLock()
    original = Pose2D(0.25, 0.0)
    _select(target_lock, original, Pose2D(0.0, 0.0), lock_distance_m=0.30)

    selection = _select(
        target_lock,
        None,
        Pose2D(0.10, 0.0),
        lock_distance_m=0.30,
    )

    assert selection is not None
    assert selection.pose == original
    assert target_lock.protects(Pose2D(0.27, 0.01), radius_m=0.05)

    target_lock.clear()
    assert not target_lock.active


def test_switches_only_when_candidate_is_sufficiently_closer() -> None:
    robot = Pose2D(0.0, 0.0)
    active = Pose2D(1.0, 0.0)

    assert not should_switch_to_closer_target(
        robot_pose=robot,
        active_target_pose=active,
        candidate_target_pose=Pose2D(0.89, 0.0),
        min_improvement_m=0.12,
    )
    assert should_switch_to_closer_target(
        robot_pose=robot,
        active_target_pose=active,
        candidate_target_pose=Pose2D(0.88, 0.0),
        min_improvement_m=0.12,
    )


def test_target_switch_improvement_uses_current_robot_pose() -> None:
    improvement = closer_target_improvement_m(
        robot_pose=Pose2D(0.5, 0.0),
        active_target_pose=Pose2D(1.5, 0.0),
        candidate_target_pose=Pose2D(0.2, 0.0),
    )

    assert math.isclose(improvement, 0.7)
