from robot_nav_stack.exact_frame_sync import ExactFrameSynchronizer


def test_detection_waits_for_same_frame_classification() -> None:
    sync = ExactFrameSynchronizer[str, str](max_pending_frames=4)

    assert sync.add_left((10, 20), "cube", received_sec=1.0) is None
    assert sync.add_right((10, 19), "previous-apple", received_sec=1.1) is None
    assert sync.pending_left == 1

    assert sync.add_right((10, 20), "current-apple", received_sec=1.2) == (
        "cube",
        "current-apple",
    )
    assert sync.pending_left == 0


def test_classification_may_arrive_before_adapter_detection_callback() -> None:
    sync = ExactFrameSynchronizer[str, str](max_pending_frames=4)

    assert sync.add_right((30, 40), "apple", received_sec=2.0) is None
    assert sync.add_left((30, 40), "cube", received_sec=2.1) == ("cube", "apple")


def test_unclassified_cube_expires_without_a_fallback_match() -> None:
    sync = ExactFrameSynchronizer[str, str](max_pending_frames=4)
    sync.add_left((50, 60), "cube", received_sec=3.0)

    expired_cubes, expired_classifications = sync.expire(
        now_sec=4.1,
        max_age_sec=1.0,
    )

    assert expired_cubes == ["cube"]
    assert expired_classifications == []
    assert sync.pending_left == 0
