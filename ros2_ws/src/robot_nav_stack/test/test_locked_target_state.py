import pytest

from robot_nav_stack.core import Pose2D
from robot_nav_stack.locked_target_state import LockedTargetState


def test_locked_target_protects_nearby_map_observations() -> None:
    state = LockedTargetState()

    changed = state.update_json(
        '{"target_locked":true,"target":{"x":1.0,"y":2.0,"theta":0.5}}'
    )

    assert changed
    assert state.active
    assert state.pose == Pose2D(x=1.0, y=2.0, theta=0.5)
    assert state.protects(Pose2D(x=1.2, y=2.0), 0.25)
    assert not state.protects(Pose2D(x=1.3, y=2.0), 0.25)


def test_unlocked_status_clears_protection() -> None:
    state = LockedTargetState(Pose2D(x=1.0, y=2.0))

    changed = state.update_json('{"target_locked":false}')

    assert changed
    assert not state.active
    assert not state.protects(Pose2D(x=1.0, y=2.0), 0.25)


@pytest.mark.parametrize(
    "data",
    [
        "[]",
        '{"target_locked":true}',
        '{"target_locked":true,"target":{"x":"bad","y":2.0}}',
    ],
)
def test_invalid_locked_status_is_rejected(data: str) -> None:
    state = LockedTargetState()

    with pytest.raises(ValueError):
        state.update_json(data)
