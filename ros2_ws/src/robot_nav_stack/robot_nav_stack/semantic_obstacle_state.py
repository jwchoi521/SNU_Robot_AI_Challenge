from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class TimedObstacle:
    x: float
    y: float
    z: float
    stamp_sec: float
    hits: int = 1


def remove_obstacles_near(
    obstacles: list[TimedObstacle],
    x: float,
    y: float,
    radius_m: float,
) -> tuple[list[TimedObstacle], int]:
    """Remove cached obstacles that overlap a newly confirmed target pose."""

    radius = max(0.0, float(radius_m))
    kept = [
        obstacle
        for obstacle in obstacles
        if math.hypot(obstacle.x - x, obstacle.y - y) > radius
    ]
    return kept, len(obstacles) - len(kept)
