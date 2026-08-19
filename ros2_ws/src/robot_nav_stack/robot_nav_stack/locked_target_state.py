from __future__ import annotations

import json
import math
from dataclasses import dataclass
from typing import Any

from .core import Pose2D


@dataclass
class LockedTargetState:
    """Mirror the navigator's locked target from its JSON status message."""

    pose: Pose2D | None = None

    @property
    def active(self) -> bool:
        return self.pose is not None

    def update_json(self, data: str) -> bool:
        payload = json.loads(data)
        if not isinstance(payload, dict):
            raise ValueError("target-lock status must be a JSON object")
        return self.update_payload(payload)

    def update_payload(self, payload: dict[str, Any]) -> bool:
        previous = self.pose
        if payload.get("target_locked") is not True:
            self.pose = None
            return self.pose != previous

        target = payload.get("target")
        if not isinstance(target, dict):
            raise ValueError("locked target status is missing target coordinates")

        try:
            x = float(target["x"])
            y = float(target["y"])
            theta = float(target.get("theta", 0.0))
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("locked target coordinates are invalid") from exc
        if not all(math.isfinite(value) for value in (x, y, theta)):
            raise ValueError("locked target coordinates must be finite")

        self.pose = Pose2D(x=x, y=y, theta=theta)
        return self.pose != previous

    def protects(self, pose: Pose2D, radius_m: float) -> bool:
        return self.protects_xy(pose.x, pose.y, radius_m)

    def protects_xy(self, x: float, y: float, radius_m: float) -> bool:
        return (
            self.pose is not None
            and math.hypot(x - self.pose.x, y - self.pose.y) <= max(0.0, radius_m)
        )
