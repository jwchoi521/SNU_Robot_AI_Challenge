from __future__ import annotations

import math
from dataclasses import dataclass, field


_STAMP_EPSILON_SEC = 1e-6
_SCORE_EPSILON = 1e-9


@dataclass
class TrackEvidence:
    frame_count: int = 0
    class_scores: dict[str, float] = field(default_factory=dict)
    role_scores: dict[tuple[str, str], float] = field(default_factory=dict)
    representative_class: str = ""
    representative_role: str = "unfiltered"
    last_frame_stamp_sec: float | None = None
    last_frame_class: str = ""
    last_frame_role: str = "unfiltered"
    last_frame_confidence: float = -1.0

    def observe(
        self,
        stamp_sec: float,
        object_type: str,
        role: str,
        confidence: float,
    ) -> bool:
        """Record at most one, highest-confidence observation per track and frame."""
        object_type = object_type.strip()
        role = role.strip() or "unfiltered"
        confidence = self._clean_confidence(confidence)
        same_frame = (
            self.last_frame_stamp_sec is not None
            and abs(stamp_sec - self.last_frame_stamp_sec) <= _STAMP_EPSILON_SEC
        )

        if same_frame:
            if confidence <= self.last_frame_confidence:
                return False
            self._adjust_score(
                self.class_scores,
                self.last_frame_class,
                -self.last_frame_confidence,
            )
            self._adjust_score(
                self.role_scores,
                (self.last_frame_class, self.last_frame_role),
                -self.last_frame_confidence,
            )
        else:
            self.frame_count += 1

        self._adjust_score(self.class_scores, object_type, confidence)
        self._adjust_score(self.role_scores, (object_type, role), confidence)
        self.last_frame_stamp_sec = stamp_sec
        self.last_frame_class = object_type
        self.last_frame_role = role
        self.last_frame_confidence = confidence
        self._refresh_representative()
        return True

    @property
    def representative_class_score(self) -> float:
        return self.class_scores.get(self.representative_class, 0.0)

    def _refresh_representative(self) -> None:
        if not self.class_scores:
            self.representative_class = self.last_frame_class
            self.representative_role = self.last_frame_role
            return

        best_class_score = max(self.class_scores.values())
        current_class_score = self.class_scores.get(
            self.representative_class,
            float("-inf"),
        )
        if current_class_score < best_class_score - _SCORE_EPSILON:
            self.representative_class = max(
                self.class_scores,
                key=lambda name: (self.class_scores[name], name),
            )

        matching_roles = {
            role: score
            for (object_type, role), score in self.role_scores.items()
            if object_type == self.representative_class
        }
        if not matching_roles:
            self.representative_role = self.last_frame_role
            return

        best_role_score = max(matching_roles.values())
        current_role_score = matching_roles.get(
            self.representative_role,
            float("-inf"),
        )
        if current_role_score < best_role_score - _SCORE_EPSILON:
            self.representative_role = max(
                matching_roles,
                key=lambda name: (matching_roles[name], name),
            )

    @staticmethod
    def _clean_confidence(value: float) -> float:
        value = float(value)
        if not math.isfinite(value):
            return 0.0
        return max(0.0, min(1.0, value))

    @staticmethod
    def _adjust_score(scores: dict, key, delta: float) -> None:
        value = scores.get(key, 0.0) + delta
        if value <= _SCORE_EPSILON:
            scores.pop(key, None)
        else:
            scores[key] = value
