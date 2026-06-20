from __future__ import annotations

import pytest

from src.postprocess import (
    Detection,
    LidarBearingSample,
    NearestBearingDistanceMatcher,
    TargetConfirmationTracker,
    bearing_from_bbox,
    postprocess_detections,
)


def test_cube_without_connected_sticker_is_unknown_and_not_pickable() -> None:
    targets = postprocess_detections(
        [Detection(class_id=0, confidence=0.91, bbox_xyxy=(270, 100, 370, 220))],
        image_width=640,
        horizontal_fov_deg=60.0,
    )

    assert len(targets) == 1
    assert targets[0].object_kind == "unknown_cube"
    assert targets[0].pick_allowed is False
    assert targets[0].target_confirmed is False
    assert targets[0].bearing_deg == pytest.approx(0.0)


def test_connected_fruit_sticker_and_cube_become_set2_fruit() -> None:
    targets = postprocess_detections(
        [
            Detection(class_id=0, confidence=0.90, bbox_xyxy=(200, 100, 320, 240)),
            Detection(class_id=4, confidence=0.86, bbox_xyxy=(236, 142, 282, 192)),
        ],
        image_width=640,
        horizontal_fov_deg=60.0,
    )

    assert len(targets) == 1
    assert targets[0].object_kind == "set2_fruit"
    assert targets[0].fruit_kind == "apple"
    assert targets[0].pick_allowed is True
    assert targets[0].confidence == pytest.approx(0.86)


def test_disconnected_sticker_does_not_create_fruit_target() -> None:
    targets = postprocess_detections(
        [
            Detection(class_id=0, confidence=0.90, bbox_xyxy=(100, 100, 200, 200)),
            Detection(class_id=5, confidence=0.86, bbox_xyxy=(420, 120, 460, 160)),
        ],
        image_width=640,
    )

    assert len(targets) == 1
    assert targets[0].object_kind == "unknown_cube"
    assert targets[0].fruit_kind is None
    assert targets[0].pick_allowed is False


def test_target_confirmed_only_after_repeated_frames() -> None:
    tracker = TargetConfirmationTracker(confirm_frames=3, max_center_shift_px=20)
    frames = [
        postprocess_detections(
            [
                Detection(class_id=0, confidence=0.90, bbox_xyxy=(200, 100, 320, 240)),
                Detection(class_id=6, confidence=0.86, bbox_xyxy=(236, 142, 282, 192)),
            ],
            image_width=640,
        )
        for _ in range(3)
    ]

    first = tracker.update(frames[0])
    second = tracker.update(frames[1])
    third = tracker.update(frames[2])

    assert first[0].target_confirmed is False
    assert second[0].target_confirmed is False
    assert third[0].target_confirmed is True


def test_bearing_and_lidar_distance_are_bearing_based() -> None:
    assert bearing_from_bbox((0, 0, 100, 100), 200, 90.0) == pytest.approx(-22.5)

    matcher = NearestBearingDistanceMatcher(
        [
            LidarBearingSample(bearing_deg=-23.0, distance_m=1.2),
            LidarBearingSample(bearing_deg=10.0, distance_m=3.0),
        ],
        max_delta_deg=2.0,
    )
    targets = postprocess_detections(
        [Detection(class_id=1, confidence=0.95, bbox_xyxy=(0, 0, 100, 100))],
        image_width=200,
        horizontal_fov_deg=90.0,
        lidar_matcher=matcher,
    )

    assert targets[0].object_kind == "octahedron"
    assert targets[0].distance_m == pytest.approx(1.2)
