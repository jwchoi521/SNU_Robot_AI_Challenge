from math import isclose, pi

from robot_nav_stack.core import Pose2D
from robot_nav_stack.storage_dropoff import (
    StorageBounds,
    StorageEntryDirection,
    choose_storage_plan,
    footprint_fully_contained,
    heading_matches_entry,
    make_storage_plan,
    should_force_storage_dropoff,
    storage_forward_target_duration,
)


BOUNDS = StorageBounds(min_x=-2.0, max_x=-1.4, min_y=-2.0, max_y=-1.4)
HALF_LENGTH = 0.16
HALF_WIDTH = 0.165


def test_storage_bounds_contains_only_points_inside_rectangle() -> None:
    assert BOUNDS.contains_point(-1.8, -1.8)
    assert BOUNDS.contains_point(-2.0, -1.4)
    assert not BOUNDS.contains_point(-1.39, -1.8)
    assert not BOUNDS.contains_point(-1.8, -1.39)


def test_negative_x_plan_enters_from_right_and_faces_negative_x() -> None:
    plan = make_storage_plan(
        BOUNDS,
        StorageEntryDirection.NEGATIVE_X,
        HALF_LENGTH,
        HALF_WIDTH,
        approach_clearance_m=0.05,
    )

    assert plan.approach_pose.x > BOUNDS.max_x
    assert isclose(plan.approach_pose.x, -1.19, abs_tol=1.0e-12)
    assert plan.approach_pose.y == -1.4
    assert isclose(plan.inside_pose.x, -1.7, abs_tol=1.0e-12)
    assert isclose(plan.inside_pose.y, -1.7, abs_tol=1.0e-12)
    assert plan.inside_pose.theta == 0.0
    assert plan.exit_direction == "positive_x"


def test_negative_y_plan_enters_from_top_and_faces_negative_y() -> None:
    plan = make_storage_plan(
        BOUNDS,
        StorageEntryDirection.NEGATIVE_Y,
        HALF_LENGTH,
        HALF_WIDTH,
        approach_clearance_m=0.05,
    )

    assert plan.approach_pose.y > BOUNDS.max_y
    assert plan.approach_pose.x == -1.4
    assert isclose(plan.approach_pose.y, -1.19, abs_tol=1.0e-12)
    assert isclose(plan.inside_pose.x, -1.7, abs_tol=1.0e-12)
    assert isclose(plan.inside_pose.y, -1.7, abs_tol=1.0e-12)
    assert plan.inside_pose.theta == 0.0
    assert plan.exit_direction == "positive_y"


def test_auto_entry_chooses_nearest_legal_approach() -> None:
    from_right = choose_storage_plan(
        Pose2D(-1.0, -1.8, 0.0),
        BOUNDS,
        HALF_LENGTH,
        HALF_WIDTH,
        approach_clearance_m=0.05,
    )
    from_top = choose_storage_plan(
        Pose2D(-1.8, -1.0, 0.0),
        BOUNDS,
        HALF_LENGTH,
        HALF_WIDTH,
        approach_clearance_m=0.05,
    )

    assert from_right.entry_direction == StorageEntryDirection.NEGATIVE_X
    assert from_top.entry_direction == StorageEntryDirection.NEGATIVE_Y


def test_full_rectangular_footprint_must_be_inside_storage_bounds() -> None:
    centered = Pose2D(-1.8, -1.8, pi)
    too_far_right = Pose2D(-1.55, -1.7, pi)
    diagonal = Pose2D(-1.6, -1.7, 0.25 * pi)

    assert footprint_fully_contained(centered, BOUNDS, HALF_LENGTH, HALF_WIDTH)
    assert not footprint_fully_contained(
        too_far_right,
        BOUNDS,
        HALF_LENGTH,
        HALF_WIDTH,
    )
    assert not footprint_fully_contained(
        diagonal,
        BOUNDS,
        HALF_LENGTH,
        HALF_WIDTH,
    )


def test_heading_must_match_selected_entry_before_unloading() -> None:
    plan = make_storage_plan(
        BOUNDS,
        StorageEntryDirection.NEGATIVE_X,
        HALF_LENGTH,
        HALF_WIDTH,
        approach_clearance_m=0.05,
    )

    assert heading_matches_entry(Pose2D(-1.8, -1.8, 0.05), plan, 0.1)
    assert not heading_matches_entry(Pose2D(-1.8, -1.8, -0.5 * pi), plan, 0.1)


def test_mission_deadline_forces_one_shot_dropoff_with_cargo() -> None:
    assert not should_force_storage_dropoff(
        mission_started_sec=100.0,
        now_sec=249.99,
        timeout_sec=150.0,
        captured_object_count=1,
        already_triggered=False,
    )
    assert should_force_storage_dropoff(
        mission_started_sec=100.0,
        now_sec=250.0,
        timeout_sec=150.0,
        captured_object_count=1,
        already_triggered=False,
    )
    assert not should_force_storage_dropoff(
        mission_started_sec=100.0,
        now_sec=250.0,
        timeout_sec=150.0,
        captured_object_count=0,
        already_triggered=False,
    )
    assert not should_force_storage_dropoff(
        mission_started_sec=100.0,
        now_sec=300.0,
        timeout_sec=150.0,
        captured_object_count=1,
        already_triggered=True,
    )


def test_storage_forward_duration_adds_configured_drive_time() -> None:
    assert storage_forward_target_duration(2.5, 0.5) == 3.0
    assert storage_forward_target_duration(2.5, -1.0) == 2.5
