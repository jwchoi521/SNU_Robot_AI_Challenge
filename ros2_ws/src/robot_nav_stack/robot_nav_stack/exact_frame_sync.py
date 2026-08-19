from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar


FrameKey = tuple[int, int]
LeftT = TypeVar("LeftT")
RightT = TypeVar("RightT")


@dataclass
class _TimedValue(Generic[LeftT]):
    value: LeftT
    received_sec: float


class ExactFrameSynchronizer(Generic[LeftT, RightT]):
    """Pair two asynchronous streams only when their frame stamps match."""

    def __init__(self, max_pending_frames: int = 10) -> None:
        self.max_pending_frames = max(1, int(max_pending_frames))
        self._left: dict[FrameKey, _TimedValue[LeftT]] = {}
        self._right: dict[FrameKey, _TimedValue[RightT]] = {}

    @property
    def pending_left(self) -> int:
        return len(self._left)

    @property
    def pending_right(self) -> int:
        return len(self._right)

    def add_left(
        self,
        key: FrameKey,
        value: LeftT,
        received_sec: float,
    ) -> tuple[LeftT, RightT] | None:
        right = self._right.pop(key, None)
        if right is not None:
            return value, right.value

        self._left[key] = _TimedValue(value=value, received_sec=received_sec)
        self._trim_oldest(self._left)
        return None

    def add_right(
        self,
        key: FrameKey,
        value: RightT,
        received_sec: float,
    ) -> tuple[LeftT, RightT] | None:
        left = self._left.pop(key, None)
        if left is not None:
            return left.value, value

        self._right[key] = _TimedValue(value=value, received_sec=received_sec)
        self._trim_oldest(self._right)
        return None

    def expire(
        self,
        now_sec: float,
        max_age_sec: float,
    ) -> tuple[list[LeftT], list[RightT]]:
        if max_age_sec <= 0.0:
            return [], []

        expired_left = self._expire_stream(self._left, now_sec, max_age_sec)
        expired_right = self._expire_stream(self._right, now_sec, max_age_sec)
        return expired_left, expired_right

    def _trim_oldest(self, stream: dict[FrameKey, _TimedValue]) -> None:
        while len(stream) > self.max_pending_frames:
            oldest_key = min(stream, key=lambda key: stream[key].received_sec)
            stream.pop(oldest_key)

    @staticmethod
    def _expire_stream(
        stream: dict[FrameKey, _TimedValue[LeftT]],
        now_sec: float,
        max_age_sec: float,
    ) -> list[LeftT]:
        expired_keys = [
            key
            for key, item in stream.items()
            if now_sec - item.received_sec > max_age_sec
        ]
        return [stream.pop(key).value for key in expired_keys]
