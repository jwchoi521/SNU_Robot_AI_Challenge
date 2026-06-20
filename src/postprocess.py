from __future__ import annotations

from dataclasses import dataclass, replace
from math import hypot
from typing import Iterable, Protocol, Sequence, Tuple


CLASS_NAMES: tuple[str, ...] = (
    "cube_any",
    "octahedron",
    "dodecahedron",
    "icosahedron",
    "apple_sticker",
    "orange_sticker",
    "banana_sticker",
    "pineapple_sticker",
)

CUBE_CLASS_ID = 0
SHAPE_CLASS_IDS = frozenset({1, 2, 3})
FRUIT_STICKER_CLASS_IDS = {
    4: "apple",
    5: "orange",
    6: "banana",
    7: "pineapple",
}

Box = Tuple[float, float, float, float]


class InfraredDistanceProvider(Protocol):
    """Infrared sensor hook for target distance measurement."""

    def distance_for_target(self, bearing_deg: float, bbox_xyxy: Box) -> float | None:
        """Return a distance in meters for a camera target, if available."""


@dataclass(frozen=True)
class Detection:
    class_id: int
    confidence: float
    bbox_xyxy: Box

    @property
    def class_name(self) -> str:
        return class_name(self.class_id)


@dataclass(frozen=True)
class FrameTarget:
    object_kind: str
    bbox_xyxy: Box
    confidence: float
    bearing_deg: float
    pick_allowed: bool
    target_confirmed: bool = False
    fruit_kind: str | None = None
    distance_m: float | None = None
    cube_detection: Detection | None = None
    sticker_detection: Detection | None = None

    def as_dict(self) -> dict[str, object]:
        return {
            "object_kind": self.object_kind,
            "fruit_kind": self.fruit_kind,
            "bbox_xyxy": [round(value, 3) for value in self.bbox_xyxy],
            "confidence": round(self.confidence, 4),
            "bearing_deg": round(self.bearing_deg, 3),
            "distance_m": self.distance_m,
            "pick_allowed": self.pick_allowed,
            "target_confirmed": self.target_confirmed,
        }


@dataclass(frozen=True)
class InfraredBearingSample:
    bearing_deg: float
    distance_m: float


class NearestInfraredBearingMatcher:
    def __init__(
        self,
        samples: Iterable[InfraredBearingSample],
        max_delta_deg: float = 2.0,
    ) -> None:
        self.samples = tuple(samples)
        self.max_delta_deg = max_delta_deg

    def distance_for_target(self, bearing_deg: float, bbox_xyxy: Box) -> float | None:
        del bbox_xyxy
        best_sample: InfraredBearingSample | None = None
        best_delta = self.max_delta_deg
        for sample in self.samples:
            delta = abs(sample.bearing_deg - bearing_deg)
            if delta <= best_delta:
                best_sample = sample
                best_delta = delta
        return None if best_sample is None else best_sample.distance_m


@dataclass
class _Track:
    target: FrameTarget
    hits: int
    missed: int = 0


class TargetConfirmationTracker:
    def __init__(
        self,
        confirm_frames: int = 3,
        max_missed: int = 1,
        max_center_shift_px: float = 80.0,
    ) -> None:
        if confirm_frames < 1:
            raise ValueError("confirm_frames must be >= 1")
        self.confirm_frames = confirm_frames
        self.max_missed = max_missed
        self.max_center_shift_px = max_center_shift_px
        self._tracks: list[_Track] = []

    def update(self, targets: Sequence[FrameTarget]) -> list[FrameTarget]:
        matched_track_indexes: set[int] = set()
        output: list[FrameTarget] = []

        for target in targets:
            track_index = self._find_track(target, matched_track_indexes)
            if track_index is None:
                track = _Track(target=target, hits=1)
                self._tracks.append(track)
                track_index = len(self._tracks) - 1
            else:
                track = self._tracks[track_index]
                track.target = target
                track.hits += 1
                track.missed = 0

            matched_track_indexes.add(track_index)
            output.append(
                replace(
                    target,
                    target_confirmed=self._tracks[track_index].hits
                    >= self.confirm_frames,
                )
            )

        for index, track in enumerate(self._tracks):
            if index not in matched_track_indexes:
                track.missed += 1

        self._tracks = [
            track for track in self._tracks if track.missed <= self.max_missed
        ]
        return output

    def _find_track(
        self,
        target: FrameTarget,
        matched_track_indexes: set[int],
    ) -> int | None:
        best_index: int | None = None
        best_distance = self.max_center_shift_px
        target_center = box_center(target.bbox_xyxy)

        for index, track in enumerate(self._tracks):
            if index in matched_track_indexes:
                continue
            if not _same_target_type(track.target, target):
                continue
            distance = hypot(
                target_center[0] - box_center(track.target.bbox_xyxy)[0],
                target_center[1] - box_center(track.target.bbox_xyxy)[1],
            )
            if distance <= best_distance:
                best_index = index
                best_distance = distance
        return best_index


def class_name(class_id: int) -> str:
    if class_id < 0 or class_id >= len(CLASS_NAMES):
        raise ValueError(f"class_id must be 0..7, got {class_id}")
    return CLASS_NAMES[class_id]


def bearing_from_bbox(
    bbox_xyxy: Box,
    image_width: int,
    horizontal_fov_deg: float,
) -> float:
    if image_width <= 0:
        raise ValueError("image_width must be positive")
    center_x, _center_y = box_center(bbox_xyxy)
    return ((center_x / image_width) - 0.5) * horizontal_fov_deg


def box_center(box: Box) -> tuple[float, float]:
    x1, y1, x2, y2 = box
    return (x1 + x2) / 2.0, (y1 + y2) / 2.0


def box_area(box: Box) -> float:
    x1, y1, x2, y2 = box
    return max(0.0, x2 - x1) * max(0.0, y2 - y1)


def box_iou(first: Box, second: Box) -> float:
    left = max(first[0], second[0])
    top = max(first[1], second[1])
    right = min(first[2], second[2])
    bottom = min(first[3], second[3])
    intersection = box_area((left, top, right, bottom))
    if intersection <= 0.0:
        return 0.0
    union = box_area(first) + box_area(second) - intersection
    return 0.0 if union <= 0.0 else intersection / union


def postprocess_detections(
    detections: Sequence[Detection],
    image_width: int,
    horizontal_fov_deg: float = 69.4,
    infrared_provider: InfraredDistanceProvider | None = None,
) -> list[FrameTarget]:
    cubes = [detection for detection in detections if detection.class_id == CUBE_CLASS_ID]
    stickers = [
        detection
        for detection in detections
        if detection.class_id in FRUIT_STICKER_CLASS_IDS
    ]
    shapes = [detection for detection in detections if detection.class_id in SHAPE_CLASS_IDS]

    targets: list[FrameTarget] = []
    used_sticker_indexes: set[int] = set()

    for cube in sorted(cubes, key=lambda item: item.confidence, reverse=True):
        sticker_index = _best_connected_sticker(cube, stickers, used_sticker_indexes)
        if sticker_index is None:
            targets.append(
                _make_target(
                    object_kind="unknown_cube",
                    bbox_xyxy=cube.bbox_xyxy,
                    confidence=cube.confidence,
                    image_width=image_width,
                    horizontal_fov_deg=horizontal_fov_deg,
                    pick_allowed=False,
                    infrared_provider=infrared_provider,
                    cube_detection=cube,
                )
            )
            continue

        used_sticker_indexes.add(sticker_index)
        sticker = stickers[sticker_index]
        fruit_kind = FRUIT_STICKER_CLASS_IDS[sticker.class_id]
        union_box = _union_box(cube.bbox_xyxy, sticker.bbox_xyxy)
        targets.append(
            _make_target(
                object_kind="set2_fruit",
                fruit_kind=fruit_kind,
                bbox_xyxy=union_box,
                confidence=min(cube.confidence, sticker.confidence),
                image_width=image_width,
                horizontal_fov_deg=horizontal_fov_deg,
                pick_allowed=True,
                infrared_provider=infrared_provider,
                cube_detection=cube,
                sticker_detection=sticker,
            )
        )

    for shape in shapes:
        targets.append(
            _make_target(
                object_kind=shape.class_name,
                bbox_xyxy=shape.bbox_xyxy,
                confidence=shape.confidence,
                image_width=image_width,
                horizontal_fov_deg=horizontal_fov_deg,
                pick_allowed=True,
                infrared_provider=infrared_provider,
            )
        )

    return sorted(targets, key=lambda item: item.confidence, reverse=True)


def _make_target(
    object_kind: str,
    bbox_xyxy: Box,
    confidence: float,
    image_width: int,
    horizontal_fov_deg: float,
    pick_allowed: bool,
    infrared_provider: InfraredDistanceProvider | None,
    fruit_kind: str | None = None,
    cube_detection: Detection | None = None,
    sticker_detection: Detection | None = None,
) -> FrameTarget:
    bearing_deg = bearing_from_bbox(bbox_xyxy, image_width, horizontal_fov_deg)
    distance_m = (
        None
        if infrared_provider is None
        else infrared_provider.distance_for_target(bearing_deg, bbox_xyxy)
    )
    return FrameTarget(
        object_kind=object_kind,
        fruit_kind=fruit_kind,
        bbox_xyxy=bbox_xyxy,
        confidence=confidence,
        bearing_deg=bearing_deg,
        distance_m=distance_m,
        pick_allowed=pick_allowed,
        cube_detection=cube_detection,
        sticker_detection=sticker_detection,
    )


def _best_connected_sticker(
    cube: Detection,
    stickers: Sequence[Detection],
    used_sticker_indexes: set[int],
) -> int | None:
    best_index: int | None = None
    best_score = 0.0
    for index, sticker in enumerate(stickers):
        if index in used_sticker_indexes:
            continue
        score = _connection_score(cube.bbox_xyxy, sticker.bbox_xyxy)
        if score > best_score:
            best_index = index
            best_score = score
    return best_index


def _connection_score(cube_box: Box, sticker_box: Box) -> float:
    iou = box_iou(cube_box, sticker_box)
    center = box_center(sticker_box)
    expanded_cube = _expand_box(cube_box, ratio=0.18)

    if _point_inside(center, expanded_cube):
        return 2.0 + iou
    if iou > 0.0:
        return 1.0 + iou
    return 0.0


def _expand_box(box: Box, ratio: float) -> Box:
    x1, y1, x2, y2 = box
    width = x2 - x1
    height = y2 - y1
    return (
        x1 - width * ratio,
        y1 - height * ratio,
        x2 + width * ratio,
        y2 + height * ratio,
    )


def _point_inside(point: tuple[float, float], box: Box) -> bool:
    x, y = point
    return box[0] <= x <= box[2] and box[1] <= y <= box[3]


def _union_box(first: Box, second: Box) -> Box:
    return (
        min(first[0], second[0]),
        min(first[1], second[1]),
        max(first[2], second[2]),
        max(first[3], second[3]),
    )


def _same_target_type(first: FrameTarget, second: FrameTarget) -> bool:
    return (
        first.object_kind == second.object_kind
        and first.fruit_kind == second.fruit_kind
        and first.pick_allowed == second.pick_allowed
    )
