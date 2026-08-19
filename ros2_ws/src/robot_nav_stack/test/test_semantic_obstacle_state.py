from robot_nav_stack.semantic_obstacle_state import (
    TimedObstacle,
    remove_obstacles_near,
)


def _obstacle(x: float, y: float) -> TimedObstacle:
    return TimedObstacle(x=x, y=y, z=0.05, stamp_sec=10.0)


def test_target_confirmation_removes_only_nearby_obstacles() -> None:
    obstacles = [_obstacle(1.0, 1.0), _obstacle(1.2, 1.0), _obstacle(2.0, 2.0)]

    kept, removed = remove_obstacles_near(obstacles, 1.0, 1.0, radius_m=0.25)

    assert removed == 2
    assert kept == [obstacles[2]]


def test_target_confirmation_does_not_remove_distant_obstacle() -> None:
    obstacles = [_obstacle(1.3, 1.0)]

    kept, removed = remove_obstacles_near(obstacles, 1.0, 1.0, radius_m=0.25)

    assert removed == 0
    assert kept == obstacles
