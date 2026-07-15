import math
from collections import deque

from robot_nav_stack.core import Pose2D
from robot_nav_stack.time_alignment import (
    TimedPose2D,
    interpolate_pose,
    scan_duration_sec,
    transform_ray_to_reference,
)


def test_interpolate_pose_works_with_deque_and_wraps_yaw() -> None:
    samples = deque(
        [
            TimedPose2D(10.0, Pose2D(0.0, 0.0, math.radians(179.0))),
            TimedPose2D(12.0, Pose2D(2.0, 4.0, math.radians(-179.0))),
        ]
    )

    pose = interpolate_pose(samples, 11.0, max_extrapolation_sec=0.0)

    assert pose is not None
    assert math.isclose(pose.x, 1.0)
    assert math.isclose(pose.y, 2.0)
    assert math.isclose(abs(pose.theta), math.pi, abs_tol=1e-9)


def test_interpolate_pose_rejects_stale_extrapolation() -> None:
    samples = [TimedPose2D(10.0, Pose2D(1.0, 2.0, 0.3))]

    assert interpolate_pose(samples, 10.04, 0.05) == samples[0].pose
    assert interpolate_pose(samples, 10.06, 0.05) is None


def test_interpolate_pose_linearly_extrapolates_within_limit() -> None:
    samples = [
        TimedPose2D(10.0, Pose2D(0.0, 0.0, 0.0)),
        TimedPose2D(11.0, Pose2D(1.0, 2.0, 0.5)),
    ]

    pose = interpolate_pose(samples, 11.05, 0.05)

    assert pose is not None
    assert math.isclose(pose.x, 1.05, abs_tol=1e-9)
    assert math.isclose(pose.y, 2.10, abs_tol=1e-9)
    assert math.isclose(pose.theta, 0.525, abs_tol=1e-9)
    assert interpolate_pose(samples, 11.06, 0.05) is None


def test_scan_duration_prefers_per_ray_increment() -> None:
    assert math.isclose(scan_duration_sec(5, 0.01, 0.20), 0.04)
    assert math.isclose(scan_duration_sec(5, 0.0, 0.20), 0.20)
    assert scan_duration_sec(1, 0.01, 0.0) == 0.0


def test_deskew_translation_expresses_ray_in_midscan_base_frame() -> None:
    origin_x, origin_y, dir_x, dir_y = transform_ray_to_reference(
        origin_x=0.0,
        origin_y=0.0,
        dir_x=1.0,
        dir_y=0.0,
        odom_pose_at_ray=Pose2D(0.0, 0.0, 0.0),
        odom_pose_at_reference=Pose2D(1.0, 0.0, 0.0),
    )

    assert math.isclose(origin_x, -1.0, abs_tol=1e-9)
    assert math.isclose(origin_y, 0.0, abs_tol=1e-9)
    assert math.isclose(dir_x, 1.0, abs_tol=1e-9)
    assert math.isclose(dir_y, 0.0, abs_tol=1e-9)


def test_deskew_rotation_rotates_ray_into_reference_base_frame() -> None:
    origin_x, origin_y, dir_x, dir_y = transform_ray_to_reference(
        origin_x=0.0,
        origin_y=0.0,
        dir_x=1.0,
        dir_y=0.0,
        odom_pose_at_ray=Pose2D(0.0, 0.0, 0.0),
        odom_pose_at_reference=Pose2D(0.0, 0.0, math.pi / 2.0),
    )

    assert math.isclose(origin_x, 0.0, abs_tol=1e-9)
    assert math.isclose(origin_y, 0.0, abs_tol=1e-9)
    assert math.isclose(dir_x, 0.0, abs_tol=1e-9)
    assert math.isclose(dir_y, -1.0, abs_tol=1e-9)
