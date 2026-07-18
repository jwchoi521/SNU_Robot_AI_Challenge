from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import cos, hypot, pi, sin

from .core import Pose2D, angle_diff


class StorageEntryDirection(str, Enum):
    NEGATIVE_X = "negative_x"
    NEGATIVE_Y = "negative_y"


@dataclass(frozen=True)
class StorageBounds:
    min_x: float
    max_x: float
    min_y: float
    max_y: float

    @property
    def center_x(self) -> float:
        return 0.5 * (self.min_x + self.max_x)

    @property
    def center_y(self) -> float:
        return 0.5 * (self.min_y + self.max_y)

    def contains_point(self, x: float, y: float) -> bool:
        return (
            self.min_x <= float(x) <= self.max_x
            and self.min_y <= float(y) <= self.max_y
        )

    def validate(self) -> None:
        if self.min_x >= self.max_x or self.min_y >= self.max_y:
            raise ValueError(f"invalid storage bounds: {self}")


@dataclass(frozen=True)
class StoragePlan:
    entry_direction: StorageEntryDirection
    approach_pose: Pose2D
    inside_pose: Pose2D

    @property
    def exit_direction(self) -> str:
        if self.entry_direction == StorageEntryDirection.NEGATIVE_X:
            return "positive_x"
        return "positive_y"


def make_storage_plan(
    bounds: StorageBounds,
    entry_direction: StorageEntryDirection,
    robot_half_length_m: float,
    robot_half_width_m: float,
    approach_clearance_m: float,
) -> StoragePlan:
    bounds.validate()
    _validate_robot_size(robot_half_length_m, robot_half_width_m)
    clearance = max(0.0, float(approach_clearance_m))

    if entry_direction == StorageEntryDirection.NEGATIVE_X:
        heading = pi
        approach = Pose2D(
            x=bounds.max_x + robot_half_length_m + clearance,
            y=bounds.center_y,
            theta=heading,
        )
    elif entry_direction == StorageEntryDirection.NEGATIVE_Y:
        heading = -0.5 * pi
        approach = Pose2D(
            x=bounds.center_x,
            y=bounds.max_y + robot_half_length_m + clearance,
            theta=heading,
        )
    else:
        raise ValueError(f"unsupported storage entry direction: {entry_direction!r}")

    inside = Pose2D(
        x=bounds.center_x,
        y=bounds.center_y,
        theta=heading,
    )
    if not footprint_fully_contained(
        inside,
        bounds,
        robot_half_length_m,
        robot_half_width_m,
    ):
        raise ValueError(
            "storage zone is too small for the configured robot footprint "
            f"when entering {entry_direction.value}"
        )
    return StoragePlan(entry_direction, approach, inside)


def choose_storage_plan(
    robot_pose: Pose2D,
    bounds: StorageBounds,
    robot_half_length_m: float,
    robot_half_width_m: float,
    approach_clearance_m: float,
    entry_mode: str = "auto",
) -> StoragePlan:
    normalized_mode = entry_mode.strip().lower().replace("-", "_")
    aliases = {
        "negative_x": StorageEntryDirection.NEGATIVE_X,
        "minus_x": StorageEntryDirection.NEGATIVE_X,
        "x": StorageEntryDirection.NEGATIVE_X,
        "negative_y": StorageEntryDirection.NEGATIVE_Y,
        "minus_y": StorageEntryDirection.NEGATIVE_Y,
        "y": StorageEntryDirection.NEGATIVE_Y,
    }
    if normalized_mode != "auto":
        try:
            direction = aliases[normalized_mode]
        except KeyError as exc:
            raise ValueError(
                "storage entry mode must be auto, negative_x, or negative_y; "
                f"got {entry_mode!r}"
            ) from exc
        return make_storage_plan(
            bounds,
            direction,
            robot_half_length_m,
            robot_half_width_m,
            approach_clearance_m,
        )

    candidates = [
        make_storage_plan(
            bounds,
            direction,
            robot_half_length_m,
            robot_half_width_m,
            approach_clearance_m,
        )
        for direction in (
            StorageEntryDirection.NEGATIVE_X,
            StorageEntryDirection.NEGATIVE_Y,
        )
    ]
    return min(
        candidates,
        key=lambda plan: hypot(
            plan.approach_pose.x - robot_pose.x,
            plan.approach_pose.y - robot_pose.y,
        ),
    )


def footprint_fully_contained(
    robot_pose: Pose2D,
    bounds: StorageBounds,
    robot_half_length_m: float,
    robot_half_width_m: float,
    containment_margin_m: float = 0.0,
) -> bool:
    bounds.validate()
    _validate_robot_size(robot_half_length_m, robot_half_width_m)
    margin = max(0.0, float(containment_margin_m))
    min_x = bounds.min_x + margin
    max_x = bounds.max_x - margin
    min_y = bounds.min_y + margin
    max_y = bounds.max_y - margin
    if min_x > max_x or min_y > max_y:
        return False

    return all(
        min_x <= corner_x <= max_x and min_y <= corner_y <= max_y
        for corner_x, corner_y in footprint_world_corners(
            robot_pose,
            robot_half_length_m,
            robot_half_width_m,
        )
    )


def footprint_world_corners(
    robot_pose: Pose2D,
    robot_half_length_m: float,
    robot_half_width_m: float,
) -> tuple[tuple[float, float], ...]:
    _validate_robot_size(robot_half_length_m, robot_half_width_m)
    c = cos(robot_pose.theta)
    s = sin(robot_pose.theta)
    local_corners = (
        (robot_half_length_m, robot_half_width_m),
        (robot_half_length_m, -robot_half_width_m),
        (-robot_half_length_m, -robot_half_width_m),
        (-robot_half_length_m, robot_half_width_m),
    )
    return tuple(
        (
            robot_pose.x + c * local_x - s * local_y,
            robot_pose.y + s * local_x + c * local_y,
        )
        for local_x, local_y in local_corners
    )


def heading_matches_entry(
    robot_pose: Pose2D,
    plan: StoragePlan,
    tolerance_rad: float,
) -> bool:
    return abs(angle_diff(robot_pose.theta, plan.inside_pose.theta)) <= max(
        0.0,
        float(tolerance_rad),
    )


def _validate_robot_size(half_length_m: float, half_width_m: float) -> None:
    if half_length_m <= 0.0 or half_width_m <= 0.0:
        raise ValueError(
            "robot footprint half-length and half-width must both be positive"
        )
