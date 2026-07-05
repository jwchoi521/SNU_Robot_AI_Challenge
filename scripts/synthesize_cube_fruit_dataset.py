from __future__ import annotations

import argparse
import csv
import json
import random
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import yaml


FRUIT_CLASSES = ("apple", "orange", "banana", "pineapple")
NO_FRUIT_CLASS = "none"
CUBE_CLASS_ID = 0
IMAGE_SUFFIXES = {".bmp", ".jpg", ".jpeg", ".png", ".webp"}
SPLITS = ("train", "val", "test")


@dataclass(frozen=True)
class CubeBox:
    image_path: Path
    split: str
    index: int
    bbox_xyxy: tuple[int, int, int, int]


@dataclass(frozen=True)
class EdgeSegment:
    start: tuple[float, float]
    end: tuple[float, float]
    source: str


@dataclass(frozen=True)
class ManualFace:
    source_image: str
    cube_index: int
    face_index: int
    quad_crop_xy: np.ndarray


def _normalize_names(raw_names: Any) -> dict[int, str]:
    if isinstance(raw_names, list):
        return {idx: str(name) for idx, name in enumerate(raw_names)}
    if isinstance(raw_names, dict):
        return {int(idx): str(name) for idx, name in raw_names.items()}
    raise TypeError("data.yaml names must be a list or mapping")


def _resolve_dataset_root(data_yaml: Path, config: dict[str, Any]) -> Path:
    raw_path = Path(str(config.get("path", data_yaml.parent)))
    if raw_path.is_absolute():
        return raw_path

    candidates = (
        data_yaml.parent / raw_path,
        data_yaml.parent.parent / raw_path,
        Path.cwd() / raw_path,
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    return candidates[0].resolve()


def _label_dir_for(image_dir: Path) -> Path:
    parts = list(image_dir.parts)
    if "images" in parts:
        parts[parts.index("images")] = "labels"
        return Path(*parts)
    return image_dir.parent.parent / "labels" / image_dir.name


def _iter_images(image_dir: Path) -> list[Path]:
    return sorted(
        path
        for path in image_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
    )


def _decoded_image_to_rgb_on_white(decoded_image: np.ndarray) -> np.ndarray:
    if decoded_image.ndim == 2:
        return np.repeat(decoded_image[..., None], 3, axis=2)

    channels = decoded_image.shape[2]
    if channels == 3:
        return decoded_image[..., ::-1].copy()
    if channels != 4:
        raise ValueError(f"unsupported image channel count: {channels}")

    bgr = decoded_image[..., :3].astype(np.float32)
    alpha = decoded_image[..., 3:4].astype(np.float32) / 255.0
    composited = bgr * alpha + 255.0 * (1.0 - alpha)
    return np.rint(np.clip(composited, 0, 255)).astype(np.uint8)[..., ::-1].copy()


def _read_rgb(path: Path) -> np.ndarray:
    import cv2

    buffer = np.fromfile(path, dtype=np.uint8)
    decoded_image = cv2.imdecode(buffer, cv2.IMREAD_UNCHANGED)
    if decoded_image is None:
        raise ValueError(f"image could not be read: {path}")
    return _decoded_image_to_rgb_on_white(decoded_image)


def _write_rgb(path: Path, image_rgb: np.ndarray) -> None:
    import cv2

    path.parent.mkdir(parents=True, exist_ok=True)
    image_bgr = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)
    ok, buffer = cv2.imencode(path.suffix, image_bgr)
    if not ok:
        raise ValueError(f"image could not be written: {path}")
    buffer.tofile(path)


def _yolo_box_to_xyxy(
    values: list[float],
    image_width: int,
    image_height: int,
) -> tuple[int, int, int, int]:
    x_center, y_center, width, height = values
    x1 = int(round((x_center - width / 2.0) * image_width))
    y1 = int(round((y_center - height / 2.0) * image_height))
    x2 = int(round((x_center + width / 2.0) * image_width))
    y2 = int(round((y_center + height / 2.0) * image_height))
    return (
        max(0, min(image_width, x1)),
        max(0, min(image_height, y1)),
        max(0, min(image_width, x2)),
        max(0, min(image_height, y2)),
    )


def _iter_cube_boxes(image_dir: Path, label_dir: Path, split: str) -> list[CubeBox]:
    records: list[CubeBox] = []
    for image_path in _iter_images(image_dir):
        relative = image_path.relative_to(image_dir)
        label_path = (label_dir / relative).with_suffix(".txt")
        if not label_path.exists():
            continue

        image_rgb = _read_rgb(image_path)
        image_height, image_width = image_rgb.shape[:2]
        cube_index = 0
        for raw_line in label_path.read_text().splitlines():
            line = raw_line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) != 5 or int(parts[0]) != CUBE_CLASS_ID:
                continue

            bbox = _yolo_box_to_xyxy(
                [float(value) for value in parts[1:]],
                image_width=image_width,
                image_height=image_height,
            )
            if bbox[2] > bbox[0] and bbox[3] > bbox[1]:
                records.append(
                    CubeBox(
                        image_path=image_path,
                        split=split,
                        index=cube_index,
                        bbox_xyxy=bbox,
                    )
                )
                cube_index += 1
    return records


def _collect_cubes(data_yaml: Path) -> dict[str, list[CubeBox]]:
    config = yaml.safe_load(data_yaml.read_text()) or {}
    names = _normalize_names(config.get("names"))
    if names.get(CUBE_CLASS_ID) != "cube_any":
        raise ValueError("class id 0 must be cube_any in shape data config")

    dataset_root = _resolve_dataset_root(data_yaml, config)
    records: dict[str, list[CubeBox]] = {}
    for split in SPLITS:
        split_value = config.get(split)
        if not split_value:
            records[split] = []
            continue
        image_dir = (dataset_root / str(split_value)).resolve()
        label_dir = _label_dir_for(image_dir)
        records[split] = _iter_cube_boxes(image_dir, label_dir, split)
    return records


def _dataset_root_from_data_yaml(data_yaml: Path) -> Path:
    config = yaml.safe_load(data_yaml.read_text()) or {}
    return _resolve_dataset_root(data_yaml, config)


def _normalize_annotation_image_key(value: str) -> str:
    return value.replace("\\", "/").lower()


def _cube_annotation_key(
    cube: CubeBox,
    dataset_root: Path,
) -> tuple[str, int]:
    try:
        image_key = cube.image_path.resolve().relative_to(dataset_root).as_posix()
    except ValueError:
        image_key = cube.image_path.resolve().as_posix()
    return (_normalize_annotation_image_key(image_key), cube.index)


def _load_face_annotations(
    annotation_path: Path,
) -> dict[tuple[str, int], list[ManualFace]]:
    payload = json.loads(annotation_path.read_text(encoding="utf-8"))
    if payload.get("coordinate_system") != "crop_xy":
        raise ValueError("face annotation coordinate_system must be crop_xy")

    faces_by_cube: dict[tuple[str, int], list[ManualFace]] = {}
    for raw_face in payload.get("faces", []):
        source_image = str(raw_face["source_image"])
        cube_index = int(raw_face["cube_index"])
        face_index = int(raw_face.get("face_index", 0))
        quad = np.asarray(raw_face["quad_crop_xy"], dtype=np.float32)
        if quad.shape != (4, 2):
            raise ValueError(
                f"annotation quad must have shape 4x2: {source_image} cube "
                f"{cube_index}"
            )

        face = ManualFace(
            source_image=source_image,
            cube_index=cube_index,
            face_index=face_index,
            quad_crop_xy=order_quad_points(quad),
        )
        key = (_normalize_annotation_image_key(source_image), cube_index)
        faces_by_cube.setdefault(key, []).append(face)

        image_path = raw_face.get("image_path")
        if image_path:
            absolute_key = (_normalize_annotation_image_key(str(image_path)), cube_index)
            faces_by_cube.setdefault(absolute_key, []).append(face)

    return faces_by_cube


def _collect_fruit_images(fruit_root: Path, split: str) -> dict[str, list[Path]]:
    images: dict[str, list[Path]] = {}
    for fruit in FRUIT_CLASSES:
        candidates: list[Path] = []
        split_dir = fruit_root / split / fruit
        if split_dir.exists():
            candidates.extend(_iter_images(split_dir))
        else:
            for class_dir in fruit_root.rglob(fruit):
                if class_dir.is_dir():
                    candidates.extend(_iter_images(class_dir))

        if not candidates:
            raise ValueError(f"no {fruit} images found under {fruit_root}")
        images[fruit] = sorted(set(candidates))
    return images


def _safe_clear_output(output_root: Path) -> None:
    output_root = output_root.resolve()
    if output_root.anchor == str(output_root):
        raise ValueError(f"refusing to clear filesystem root: {output_root}")
    if output_root.exists():
        shutil.rmtree(output_root)


def order_quad_points(points: np.ndarray) -> np.ndarray:
    points = np.asarray(points, dtype=np.float32).reshape(4, 2)
    if len({tuple(point) for point in points.tolist()}) != 4:
        raise ValueError("quad points must be four distinct points")

    center = points.mean(axis=0)
    angles = np.arctan2(points[:, 1] - center[1], points[:, 0] - center[0])
    ordered = points[np.argsort(angles)]

    # Image coordinates have y pointing down. The angle sort gives the polygon
    # in boundary order; rotate it so downstream perspective warps receive
    # top-left, top-right, bottom-right, bottom-left.
    top_left_index = int(np.argmin(ordered.sum(axis=1)))
    ordered = np.roll(ordered, -top_left_index, axis=0)

    if ordered[1, 0] < ordered[-1, 0]:
        ordered = np.array([ordered[0], ordered[-1], ordered[-2], ordered[1]])

    return ordered.astype(np.float32)


def _quad_aspect_ratio(quad: np.ndarray) -> float:
    top = float(np.linalg.norm(quad[1] - quad[0]))
    right = float(np.linalg.norm(quad[2] - quad[1]))
    bottom = float(np.linalg.norm(quad[2] - quad[3]))
    left = float(np.linalg.norm(quad[3] - quad[0]))
    width = max((top + bottom) / 2.0, 1.0)
    height = max((left + right) / 2.0, 1.0)
    return max(width / height, height / width)


def _quad_area(quad: np.ndarray) -> float:
    x_values = quad[:, 0]
    y_values = quad[:, 1]
    return float(
        0.5
        * abs(
            np.dot(x_values, np.roll(y_values, -1))
            - np.dot(y_values, np.roll(x_values, -1))
        )
    )


def _quad_bbox(quad: np.ndarray) -> tuple[float, float, float, float]:
    return (
        float(quad[:, 0].min()),
        float(quad[:, 1].min()),
        float(quad[:, 0].max()),
        float(quad[:, 1].max()),
    )


def _edge_angle_degrees(start: np.ndarray, end: np.ndarray) -> float:
    vector = end - start
    return float(np.degrees(np.arctan2(vector[1], vector[0])) % 180.0)


def _parallel_angle_delta_degrees(angle_a: float, angle_b: float) -> float:
    delta = abs(angle_a - angle_b) % 180.0
    return min(delta, 180.0 - delta)


def _opposite_edge_angle_deltas(quad: np.ndarray) -> tuple[float, float]:
    top_angle = _edge_angle_degrees(quad[0], quad[1])
    bottom_angle = _edge_angle_degrees(quad[3], quad[2])
    left_angle = _edge_angle_degrees(quad[0], quad[3])
    right_angle = _edge_angle_degrees(quad[1], quad[2])
    return (
        _parallel_angle_delta_degrees(top_angle, bottom_angle),
        _parallel_angle_delta_degrees(left_angle, right_angle),
    )


def _make_edge_segment(
    start: np.ndarray | tuple[float, float] | list[float],
    end: np.ndarray | tuple[float, float] | list[float],
    source: str,
) -> EdgeSegment | None:
    start_array = np.asarray(start, dtype=np.float32).reshape(2)
    end_array = np.asarray(end, dtype=np.float32).reshape(2)
    if float(np.linalg.norm(end_array - start_array)) < 1.0:
        return None
    return EdgeSegment(
        start=(float(start_array[0]), float(start_array[1])),
        end=(float(end_array[0]), float(end_array[1])),
        source=source,
    )


def _segment_points(segment: EdgeSegment) -> tuple[np.ndarray, np.ndarray]:
    return (
        np.array(segment.start, dtype=np.float32),
        np.array(segment.end, dtype=np.float32),
    )


def _segment_length(segment: EdgeSegment) -> float:
    start, end = _segment_points(segment)
    return float(np.linalg.norm(end - start))


def _segment_angle(segment: EdgeSegment) -> float:
    start, end = _segment_points(segment)
    return _edge_angle_degrees(start, end)


def _line_coefficients(segment: EdgeSegment) -> tuple[float, float, float] | None:
    start, end = _segment_points(segment)
    x1, y1 = start
    x2, y2 = end
    a = float(y1 - y2)
    b = float(x2 - x1)
    c = float(x1 * y2 - x2 * y1)
    norm = float(np.hypot(a, b))
    if norm <= 1e-6:
        return None
    a /= norm
    b /= norm
    c /= norm
    if a < 0 or (abs(a) < 1e-6 and b < 0):
        a = -a
        b = -b
        c = -c
    return a, b, c


def _line_intersection(
    line_a: tuple[float, float, float],
    line_b: tuple[float, float, float],
) -> np.ndarray | None:
    a1, b1, c1 = line_a
    a2, b2, c2 = line_b
    determinant = a1 * b2 - a2 * b1
    if abs(determinant) < 1e-6:
        return None
    x_value = (b1 * c2 - b2 * c1) / determinant
    y_value = (c1 * a2 - c2 * a1) / determinant
    return np.array([x_value, y_value], dtype=np.float32)


def _parallel_line_distance(
    segment_a: EdgeSegment,
    segment_b: EdgeSegment,
) -> float:
    line_a = _line_coefficients(segment_a)
    line_b = _line_coefficients(segment_b)
    if line_a is None or line_b is None:
        return 0.0
    return abs(line_a[2] - line_b[2])


def _build_cube_mask(cube_rgb: np.ndarray) -> np.ndarray:
    import cv2

    hsv = cv2.cvtColor(cube_rgb, cv2.COLOR_RGB2HSV)
    value = hsv[:, :, 2]
    saturation = hsv[:, :, 1]

    bright_threshold = max(35, int(np.percentile(value, 45)))
    saturation_threshold = min(210, int(np.percentile(saturation, 80)) + 50)
    cube_mask = (
        (value >= bright_threshold)
        & ((saturation <= saturation_threshold) | (value >= np.percentile(value, 80)))
    ).astype(np.uint8) * 255

    kernel = np.ones((3, 3), dtype=np.uint8)
    cube_mask = cv2.morphologyEx(cube_mask, cv2.MORPH_CLOSE, kernel, iterations=3)
    cube_mask = cv2.morphologyEx(cube_mask, cv2.MORPH_OPEN, kernel, iterations=1)
    return cube_mask


def _largest_contour(mask: np.ndarray) -> np.ndarray | None:
    import cv2

    contours, _hierarchy = cv2.findContours(
        mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE,
    )
    if not contours:
        return None
    return max(contours, key=cv2.contourArea)


def _outline_segments_from_mask(mask: np.ndarray) -> list[EdgeSegment]:
    import cv2

    contour = _largest_contour(mask)
    if contour is None:
        return []

    perimeter = cv2.arcLength(contour, True)
    if perimeter <= 0:
        return []

    segments: list[EdgeSegment] = []
    for epsilon_ratio in (0.01, 0.02, 0.035):
        approx = cv2.approxPolyDP(contour, epsilon_ratio * perimeter, True)
        points = approx.reshape(-1, 2)
        if len(points) < 4:
            continue
        for index, start in enumerate(points):
            end = points[(index + 1) % len(points)]
            segment = _make_edge_segment(start, end, "outline")
            if segment is not None:
                segments.append(segment)
    return segments


def _hough_segments_from_masked_edges(
    cube_rgb: np.ndarray,
    mask: np.ndarray,
) -> list[EdgeSegment]:
    import cv2

    height, width = cube_rgb.shape[:2]
    gray = cv2.cvtColor(cube_rgb, cv2.COLOR_RGB2GRAY)
    gray = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(gray)
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    median = float(np.median(blurred))
    low = int(max(0, 0.60 * median))
    high = int(min(255, 1.40 * median + 32))
    edges = cv2.Canny(blurred, low, high)
    edges = cv2.bitwise_and(edges, edges, mask=mask)

    lines = cv2.HoughLinesP(
        edges,
        rho=1,
        theta=np.pi / 180,
        threshold=max(14, min(width, height) // 9),
        minLineLength=max(12, min(width, height) // 5),
        maxLineGap=max(6, min(width, height) // 18),
    )
    if lines is None:
        return []

    segments: list[EdgeSegment] = []
    for x1, y1, x2, y2 in lines[:, 0, :]:
        segment = _make_edge_segment((x1, y1), (x2, y2), "hough")
        if segment is not None:
            segments.append(segment)
    return segments


def _quad_mask_ratio(mask: np.ndarray, quad: np.ndarray) -> float:
    try:
        import cv2
    except ModuleNotFoundError:
        height, width = mask.shape[:2]
        y_grid, x_grid = np.mgrid[:height, :width]
        x_points = x_grid.astype(np.float32) + 0.5
        y_points = y_grid.astype(np.float32) + 0.5
        inside = np.zeros((height, width), dtype=bool)
        points = np.asarray(quad, dtype=np.float32)
        x_values = points[:, 0]
        y_values = points[:, 1]
        previous = len(points) - 1
        for current in range(len(points)):
            yi = y_values[current]
            yj = y_values[previous]
            xi = x_values[current]
            xj = x_values[previous]
            crosses = (yi > y_points) != (yj > y_points)
            x_intersection = (xj - xi) * (y_points - yi) / (yj - yi + 1e-6) + xi
            inside ^= crosses & (x_points < x_intersection)
            previous = current
        quad_mask = inside.astype(np.uint8) * 255
    else:
        quad_mask = np.zeros(mask.shape[:2], dtype=np.uint8)
        cv2.fillConvexPoly(quad_mask, np.round(quad).astype(np.int32), 255)

    quad_pixels = int(np.count_nonzero(quad_mask))
    if quad_pixels == 0:
        return 0.0
    inside_pixels = int(np.count_nonzero((quad_mask > 0) & (mask > 0)))
    return inside_pixels / quad_pixels


def _candidate_quads_from_edge_segments(
    segments: list[EdgeSegment],
    mask: np.ndarray,
    width: int,
    height: int,
    min_area_ratio: float,
    max_aspect_ratio: float,
) -> list[np.ndarray]:
    if len(segments) < 4:
        return []

    candidates: list[np.ndarray] = []
    min_line_distance = max(8.0, min(width, height) * 0.16)
    max_line_distance = max(width, height) * 1.05
    max_parallel_delta = 16.0

    segment_count = len(segments)
    for first_a in range(segment_count - 1):
        for first_b in range(first_a + 1, segment_count):
            segment_a = segments[first_a]
            segment_b = segments[first_b]
            if (
                _parallel_angle_delta_degrees(
                    _segment_angle(segment_a),
                    _segment_angle(segment_b),
                )
                > max_parallel_delta
            ):
                continue
            distance_ab = _parallel_line_distance(segment_a, segment_b)
            if distance_ab < min_line_distance or distance_ab > max_line_distance:
                continue

            for second_a in range(segment_count - 1):
                if second_a in (first_a, first_b):
                    continue
                for second_b in range(second_a + 1, segment_count):
                    if second_b in (first_a, first_b):
                        continue

                    segment_c = segments[second_a]
                    segment_d = segments[second_b]
                    if (
                        _parallel_angle_delta_degrees(
                            _segment_angle(segment_c),
                            _segment_angle(segment_d),
                        )
                        > max_parallel_delta
                    ):
                        continue

                    family_delta = _parallel_angle_delta_degrees(
                        _segment_angle(segment_a),
                        _segment_angle(segment_c),
                    )
                    if family_delta < 35.0 or family_delta > 145.0:
                        continue

                    distance_cd = _parallel_line_distance(segment_c, segment_d)
                    if (
                        distance_cd < min_line_distance
                        or distance_cd > max_line_distance
                    ):
                        continue

                    lines = [
                        _line_coefficients(segment_a),
                        _line_coefficients(segment_b),
                        _line_coefficients(segment_c),
                        _line_coefficients(segment_d),
                    ]
                    if any(line is None for line in lines):
                        continue
                    line_a, line_b, line_c, line_d = lines
                    intersections = [
                        _line_intersection(line_a, line_c),
                        _line_intersection(line_b, line_c),
                        _line_intersection(line_b, line_d),
                        _line_intersection(line_a, line_d),
                    ]
                    if any(point is None for point in intersections):
                        continue

                    quad = order_quad_points(np.array(intersections, dtype=np.float32))
                    if not _is_face_like_quad(
                        quad,
                        width=width,
                        height=height,
                        min_area_ratio=min_area_ratio,
                        max_aspect_ratio=max_aspect_ratio,
                    ):
                        continue
                    if _quad_mask_ratio(mask, quad) < 0.82:
                        continue
                    candidates.append(quad)
    return candidates


def _estimate_face_quad_from_outline_edges(
    cube_rgb: np.ndarray,
    min_area_ratio: float,
    max_aspect_ratio: float,
) -> np.ndarray | None:
    height, width = cube_rgb.shape[:2]
    mask = _build_cube_mask(cube_rgb)
    contour = _largest_contour(mask)
    if contour is None:
        return None

    import cv2

    contour_area_ratio = float(cv2.contourArea(contour)) / max(float(width * height), 1.0)
    if contour_area_ratio < min_area_ratio:
        return None

    outline_segments = _outline_segments_from_mask(mask)
    hough_segments = sorted(
        _hough_segments_from_masked_edges(cube_rgb, mask),
        key=_segment_length,
        reverse=True,
    )[:16]
    segments = outline_segments + hough_segments
    segments = [
        segment
        for segment in segments
        if _segment_length(segment) >= max(8.0, min(width, height) * 0.12)
    ]
    segments = sorted(segments, key=_segment_length, reverse=True)[:28]

    candidates = _candidate_quads_from_edge_segments(
        segments=segments,
        mask=mask,
        width=width,
        height=height,
        min_area_ratio=min_area_ratio,
        max_aspect_ratio=max_aspect_ratio,
    )
    if not candidates:
        return None

    return max(
        candidates,
        key=lambda quad: _score_face_quad(quad, width, height)
        + 0.35 * _quad_mask_ratio(mask, quad)
        + 0.20 * (_quad_area(quad) / max(float(width * height), 1.0)),
    )


def _is_face_like_quad(
    quad: np.ndarray,
    width: int,
    height: int,
    min_area_ratio: float,
    max_aspect_ratio: float,
) -> bool:
    crop_area = float(width * height)
    if crop_area <= 0:
        return False

    quad = np.asarray(quad, dtype=np.float32)
    if not np.isfinite(quad).all():
        return False

    margin = 2.0
    if (
        quad[:, 0].min() < -margin
        or quad[:, 1].min() < -margin
        or quad[:, 0].max() > width + margin
        or quad[:, 1].max() > height + margin
    ):
        return False

    area_ratio = _quad_area(quad) / crop_area
    if area_ratio < min_area_ratio or area_ratio > 0.82:
        return False

    aspect_ratio = _quad_aspect_ratio(quad)
    if aspect_ratio > max_aspect_ratio:
        return False

    x1, y1, x2, y2 = _quad_bbox(quad)
    bbox_width_ratio = (x2 - x1) / max(float(width), 1.0)
    bbox_height_ratio = (y2 - y1) / max(float(height), 1.0)

    # A contour that nearly fills both crop dimensions is usually the whole cube
    # silhouette, not one visible face.
    if bbox_width_ratio > 0.93 and bbox_height_ratio > 0.93:
        return False

    # Very short top/bottom strips are usually the cube top edge or a shadow.
    if bbox_height_ratio < 0.32 or bbox_width_ratio < 0.32:
        return False

    horizontal_delta, vertical_delta = _opposite_edge_angle_deltas(quad)
    if horizontal_delta > 32.0 or vertical_delta > 38.0:
        return False

    return True


def _score_face_quad(quad: np.ndarray, width: int, height: int) -> float:
    crop_area = float(width * height)
    area_ratio = _quad_area(quad) / max(crop_area, 1.0)
    aspect_ratio = _quad_aspect_ratio(quad)
    center = np.array([width / 2.0, height / 2.0], dtype=np.float32)
    center_distance = float(np.linalg.norm(quad.mean(axis=0) - center))
    max_center_distance = float(np.hypot(width, height) / 2.0)
    center_penalty = center_distance / max(max_center_distance, 1.0)
    x1, y1, x2, y2 = _quad_bbox(quad)
    fill_width = (x2 - x1) / max(float(width), 1.0)
    fill_height = (y2 - y1) / max(float(height), 1.0)
    silhouette_penalty = max(0.0, fill_width - 0.86) + max(0.0, fill_height - 0.86)
    top_strip_penalty = max(0.0, 0.45 - fill_height)
    return (
        area_ratio
        - 0.25 * center_penalty
        - 0.18 * (aspect_ratio - 1.0)
        - 0.35 * silhouette_penalty
        - 0.40 * top_strip_penalty
    )


def _candidate_quads_from_mask(
    mask: np.ndarray,
    width: int,
    height: int,
    min_area_ratio: float,
    max_aspect_ratio: float,
) -> list[np.ndarray]:
    import cv2

    candidates: list[np.ndarray] = []
    contours, _hierarchy = cv2.findContours(
        mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE,
    )
    for contour in contours:
        perimeter = cv2.arcLength(contour, True)
        if perimeter <= 0:
            continue
        hull = cv2.convexHull(contour)
        for epsilon_ratio in (0.015, 0.025, 0.04, 0.065, 0.09):
            approx = cv2.approxPolyDP(hull, epsilon_ratio * perimeter, True)
            if len(approx) != 4 or not cv2.isContourConvex(approx):
                continue
            quad = order_quad_points(approx.reshape(4, 2))
            if _is_face_like_quad(
                quad,
                width=width,
                height=height,
                min_area_ratio=min_area_ratio,
                max_aspect_ratio=max_aspect_ratio,
            ):
                candidates.append(quad)
    return candidates


def _estimate_face_quad_from_color(
    cube_rgb: np.ndarray,
    min_area_ratio: float,
    max_aspect_ratio: float,
) -> np.ndarray | None:
    import cv2

    height, width = cube_rgb.shape[:2]
    cube_mask = _build_cube_mask(cube_rgb)

    if int(cube_mask.sum() / 255) < width * height * min_area_ratio:
        return None

    kernel = np.ones((3, 3), dtype=np.uint8)
    lab = cv2.cvtColor(cube_rgb, cv2.COLOR_RGB2LAB)
    pixels = lab[cube_mask > 0].reshape(-1, 3).astype(np.float32)
    if len(pixels) < 16:
        return None

    k = min(4, max(2, len(pixels) // 40))
    criteria = (
        cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER,
        30,
        0.5,
    )
    _compactness, labels, _centers = cv2.kmeans(
        pixels,
        k,
        None,
        criteria,
        3,
        cv2.KMEANS_PP_CENTERS,
    )

    cluster_map = np.full((height, width), -1, dtype=np.int16)
    cluster_map[cube_mask > 0] = labels.reshape(-1)

    candidates: list[np.ndarray] = []
    for cluster_id in range(k):
        mask = (cluster_map == cluster_id).astype(np.uint8) * 255
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
        candidates.extend(
            _candidate_quads_from_mask(
                mask,
                width=width,
                height=height,
                min_area_ratio=min_area_ratio,
                max_aspect_ratio=max_aspect_ratio,
            )
        )

    if not candidates:
        return None
    return max(candidates, key=lambda quad: _score_face_quad(quad, width, height))


def estimate_cube_face_quad(
    cube_rgb: np.ndarray,
    min_area_ratio: float = 0.12,
    max_aspect_ratio: float = 1.9,
) -> np.ndarray | None:
    import cv2

    height, width = cube_rgb.shape[:2]
    crop_area = float(width * height)
    if crop_area <= 0:
        return None

    outline_quad = _estimate_face_quad_from_outline_edges(
        cube_rgb,
        min_area_ratio=min_area_ratio,
        max_aspect_ratio=max_aspect_ratio,
    )
    if outline_quad is not None:
        return outline_quad

    color_quad = _estimate_face_quad_from_color(
        cube_rgb,
        min_area_ratio=min_area_ratio,
        max_aspect_ratio=max_aspect_ratio,
    )
    if color_quad is not None:
        return color_quad

    gray = cv2.cvtColor(cube_rgb, cv2.COLOR_RGB2GRAY)
    gray = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(gray)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    median = float(np.median(blurred))
    low = int(max(0, 0.66 * median))
    high = int(min(255, 1.33 * median + 24))
    edges = cv2.Canny(blurred, low, high)
    kernel = np.ones((3, 3), dtype=np.uint8)
    edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel, iterations=2)
    contours, _hierarchy = cv2.findContours(
        edges,
        cv2.RETR_LIST,
        cv2.CHAIN_APPROX_SIMPLE,
    )

    best_quad: np.ndarray | None = None
    best_score = -1.0

    for contour in contours:
        perimeter = cv2.arcLength(contour, True)
        if perimeter <= 0:
            continue
        hull = cv2.convexHull(contour)
        for epsilon_ratio in (0.015, 0.025, 0.04, 0.065, 0.09):
            approx = cv2.approxPolyDP(hull, epsilon_ratio * perimeter, True)
            if len(approx) != 4 or not cv2.isContourConvex(approx):
                continue
            quad = order_quad_points(approx.reshape(4, 2))
            if not _is_face_like_quad(
                quad,
                width=width,
                height=height,
                min_area_ratio=min_area_ratio,
                max_aspect_ratio=max_aspect_ratio,
            ):
                continue
            score = _score_face_quad(quad, width, height)
            if score > best_score:
                best_quad = quad
                best_score = score
    return best_quad


def _bilinear_quad_point(
    quad: np.ndarray,
    u_value: float,
    v_value: float,
) -> np.ndarray:
    top = quad[0] * (1.0 - u_value) + quad[1] * u_value
    bottom = quad[3] * (1.0 - u_value) + quad[2] * u_value
    return top * (1.0 - v_value) + bottom * v_value


def _scale_quad_about_center(
    quad: np.ndarray,
    scale: float,
    image_width: int | None = None,
    image_height: int | None = None,
) -> np.ndarray:
    if scale <= 0:
        raise ValueError("sticker fill scale must be greater than 0")

    scaled = np.asarray(quad, dtype=np.float32).copy()
    if scale != 1.0:
        center = scaled.mean(axis=0)
        scaled = center + (scaled - center) * scale

    if image_width is not None:
        scaled[:, 0] = np.clip(scaled[:, 0], 0, image_width - 1)
    if image_height is not None:
        scaled[:, 1] = np.clip(scaled[:, 1], 0, image_height - 1)
    return scaled.astype(np.float32)


def sample_sticker_quad(
    face_quad: np.ndarray,
    rng: random.Random,
    inset_min: float = 0.0,
    inset_max: float = 0.0,
    fill_scale: float = 1.0,
    image_width: int | None = None,
    image_height: int | None = None,
) -> np.ndarray:
    if inset_min < 0.0 or inset_max < inset_min or inset_max >= 0.5:
        raise ValueError("sticker inset must satisfy 0 <= min <= max < 0.5")

    if inset_min == 0.0 and inset_max == 0.0:
        return _scale_quad_about_center(
            face_quad,
            scale=fill_scale,
            image_width=image_width,
            image_height=image_height,
        )

    inset = rng.uniform(inset_min, inset_max)
    u0 = inset
    u1 = 1.0 - inset
    v0 = inset
    v1 = 1.0 - inset
    inset_quad = np.array(
        [
            _bilinear_quad_point(face_quad, u0, v0),
            _bilinear_quad_point(face_quad, u1, v0),
            _bilinear_quad_point(face_quad, u1, v1),
            _bilinear_quad_point(face_quad, u0, v1),
        ],
        dtype=np.float32,
    )
    return _scale_quad_about_center(
        inset_quad,
        scale=fill_scale,
        image_width=image_width,
        image_height=image_height,
    )


def random_face_quad(width: int, height: int, rng: random.Random) -> np.ndarray:
    x1 = width * rng.uniform(0.15, 0.28)
    x2 = width * rng.uniform(0.72, 0.88)
    y1 = height * rng.uniform(0.15, 0.30)
    y2 = height * rng.uniform(0.70, 0.88)
    jitter = min(width, height) * 0.08
    points = np.array(
        [
            [x1 + rng.uniform(-jitter, jitter), y1 + rng.uniform(-jitter, jitter)],
            [x2 + rng.uniform(-jitter, jitter), y1 + rng.uniform(-jitter, jitter)],
            [x2 + rng.uniform(-jitter, jitter), y2 + rng.uniform(-jitter, jitter)],
            [x1 + rng.uniform(-jitter, jitter), y2 + rng.uniform(-jitter, jitter)],
        ],
        dtype=np.float32,
    )
    return order_quad_points(points)


def _augment_sticker(sticker_rgb: np.ndarray, rng: random.Random) -> np.ndarray:
    import cv2

    brightness = rng.uniform(0.85, 1.15)
    contrast = rng.uniform(0.85, 1.15)
    adjusted = sticker_rgb.astype(np.float32) * contrast
    adjusted = (adjusted - 127.5) * brightness + 127.5
    adjusted = np.clip(adjusted, 0, 255).astype(np.uint8)
    if rng.random() < 0.25:
        adjusted = cv2.GaussianBlur(adjusted, (3, 3), 0)
    return adjusted


def _odd_kernel_size(value: float) -> int:
    kernel_size = max(3, int(round(value)))
    if kernel_size % 2 == 0:
        kernel_size += 1
    return kernel_size


def _random_shadow_mask(
    height: int,
    width: int,
    rng: random.Random,
    blur_ratio: float,
) -> np.ndarray:
    if height <= 0 or width <= 0:
        raise ValueError("shadow mask image dimensions must be positive")
    if blur_ratio < 0.0:
        raise ValueError("shadow blur ratio must be non-negative")

    try:
        import cv2
    except ModuleNotFoundError:
        cv2 = None  # type: ignore[assignment]

    if cv2 is not None and rng.random() < 0.5:
        mask = np.zeros((height, width), dtype=np.float32)
        center = (
            rng.randint(0, max(0, width - 1)),
            rng.randint(0, max(0, height - 1)),
        )
        axes = (
            max(1, int(width * rng.uniform(0.25, 0.80))),
            max(1, int(height * rng.uniform(0.18, 0.65))),
        )
        angle = rng.uniform(0.0, 180.0)
        cv2.ellipse(mask, center, axes, angle, 0.0, 360.0, 1.0, -1)
    else:
        y_values, x_values = np.mgrid[0:height, 0:width]
        angle = rng.uniform(0.0, np.pi)
        projection = x_values * np.cos(angle) + y_values * np.sin(angle)
        projection_min = float(projection.min())
        projection_max = float(projection.max())
        center = rng.uniform(projection_min, projection_max)
        band_width = max(1.0, min(height, width) * rng.uniform(0.20, 0.70))
        mask = 1.0 - np.abs(projection - center) / band_width
        mask = np.clip(mask, 0.0, 1.0).astype(np.float32)

    if cv2 is not None and blur_ratio > 0.0 and min(height, width) > 2:
        kernel_size = _odd_kernel_size(min(height, width) * blur_ratio)
        mask = cv2.GaussianBlur(mask, (kernel_size, kernel_size), 0)
    return np.clip(mask, 0.0, 1.0).astype(np.float32)


def apply_lighting_augmentation(
    image_rgb: np.ndarray,
    rng: random.Random,
    shadow_prob: float = 0.0,
    shadow_min_factor: float = 0.45,
    shadow_max_factor: float = 0.85,
    shadow_blur_ratio: float = 0.20,
    global_brightness_min: float = 1.0,
    global_brightness_max: float = 1.0,
    color_jitter: float = 0.0,
) -> np.ndarray:
    if not 0.0 <= shadow_prob <= 1.0:
        raise ValueError("shadow probability must be in 0..1")
    if not 0.0 < shadow_min_factor <= shadow_max_factor <= 1.0:
        raise ValueError("shadow factors must satisfy 0 < min <= max <= 1")
    if global_brightness_min <= 0.0:
        raise ValueError("global brightness minimum must be positive")
    if global_brightness_max < global_brightness_min:
        raise ValueError("global brightness max must be >= min")
    if global_brightness_max > 1.0:
        raise ValueError("global brightness max must be <= 1 for darkening only")

    adjusted = image_rgb.astype(np.float32)
    brightness = rng.uniform(global_brightness_min, global_brightness_max)
    adjusted *= brightness

    # Keep the original color balance. Fruit kind is color-sensitive, so this
    # augmentation only darkens uniformly and never adds colored lighting.
    _ = color_jitter

    if rng.random() < shadow_prob:
        height, width = image_rgb.shape[:2]
        shadow_factor = rng.uniform(shadow_min_factor, shadow_max_factor)
        mask = _random_shadow_mask(height, width, rng, shadow_blur_ratio)
        adjusted *= 1.0 - mask[..., None] * (1.0 - shadow_factor)

    return np.clip(adjusted, 0, 255).astype(np.uint8)


def _make_square_sticker(
    fruit_rgb: np.ndarray,
    size: int,
    rng: random.Random,
) -> np.ndarray:
    import cv2

    resized = cv2.resize(fruit_rgb, (size, size), interpolation=cv2.INTER_AREA)
    return _augment_sticker(resized, rng)


def paste_perspective_sticker(
    cube_rgb: np.ndarray,
    sticker_rgb: np.ndarray,
    quad: np.ndarray,
    alpha: float,
) -> np.ndarray:
    import cv2

    height, width = cube_rgb.shape[:2]
    src = np.float32(
        [
            [0, 0],
            [sticker_rgb.shape[1] - 1, 0],
            [sticker_rgb.shape[1] - 1, sticker_rgb.shape[0] - 1],
            [0, sticker_rgb.shape[0] - 1],
        ]
    )
    matrix = cv2.getPerspectiveTransform(src, np.float32(quad))
    warped = cv2.warpPerspective(sticker_rgb, matrix, (width, height))
    mask = np.full(sticker_rgb.shape[:2], 255, dtype=np.uint8)
    warped_mask = cv2.warpPerspective(mask, matrix, (width, height))
    warped_mask = cv2.GaussianBlur(warped_mask, (3, 3), 0)
    mask_float = (warped_mask.astype(np.float32) / 255.0)[..., None]
    blend = mask_float * alpha
    output = cube_rgb.astype(np.float32) * (1.0 - blend)
    output += warped.astype(np.float32) * blend
    return np.clip(output, 0, 255).astype(np.uint8)


def _crop_cube(image_rgb: np.ndarray, bbox: tuple[int, int, int, int]) -> np.ndarray:
    x1, y1, x2, y2 = bbox
    return image_rgb[y1:y2, x1:x2]


def _make_stem(cube: CubeBox, fruit: str, sample_index: int) -> str:
    return (
        f"{cube.split}_{cube.image_path.stem}_cube{cube.index:02d}_"
        f"{fruit}_{sample_index:03d}.jpg"
    )


def _write_metadata_header(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "split",
                "class_name",
                "output_path",
                "source_image",
                "fruit_source",
                "face_method",
            ]
        )


def _append_metadata(path: Path, row: list[str]) -> None:
    with path.open("a", newline="", encoding="utf-8") as handle:
        csv.writer(handle).writerow(row)


def _make_debug_face_stem(cube: CubeBox, face_method: str) -> str:
    safe_face_method = "".join(
        character if character.isalnum() or character in ("-", "_") else "_"
        for character in face_method
    )
    return (
        f"{cube.split}_{cube.image_path.stem}_cube{cube.index:02d}_"
        f"{safe_face_method}.jpg"
    )


def _split_sequence(
    items: list[Any],
    train_ratio: float,
    val_ratio: float,
    test_ratio: float,
    seed: int,
) -> dict[str, list[Any]]:
    total_ratio = train_ratio + val_ratio + test_ratio
    if total_ratio <= 0:
        raise ValueError("split ratios must sum to a positive value")

    shuffled = list(items)
    random.Random(seed).shuffle(shuffled)
    normalized_train = train_ratio / total_ratio
    normalized_val = val_ratio / total_ratio
    train_end = round(len(shuffled) * normalized_train)
    val_end = train_end + round(len(shuffled) * normalized_val)
    return {
        "train": shuffled[:train_end],
        "val": shuffled[train_end:val_end],
        "test": shuffled[val_end:],
    }


def _assign_cubes_to_output_splits(
    cubes_by_split: dict[str, list[CubeBox]],
    output_split_mode: str,
    train_ratio: float,
    val_ratio: float,
    test_ratio: float,
    seed: int,
) -> dict[str, list[CubeBox]]:
    if output_split_mode == "source":
        return {split: list(cubes_by_split.get(split, [])) for split in SPLITS}
    if output_split_mode != "random":
        raise ValueError(f"unknown output split mode: {output_split_mode}")

    all_cubes = [
        cube
        for split in SPLITS
        for cube in cubes_by_split.get(split, [])
    ]
    return _split_sequence(
        all_cubes,
        train_ratio=train_ratio,
        val_ratio=val_ratio,
        test_ratio=test_ratio,
        seed=seed,
    )


def _write_face_debug_overlay(
    output_path: Path,
    cube_rgb: np.ndarray,
    face_quad: np.ndarray,
    sticker_quad: np.ndarray,
    face_method: str,
) -> None:
    import cv2

    overlay_bgr = cv2.cvtColor(cube_rgb, cv2.COLOR_RGB2BGR)
    face_points = np.round(face_quad).astype(np.int32).reshape(-1, 1, 2)
    sticker_points = np.round(sticker_quad).astype(np.int32).reshape(-1, 1, 2)

    face_layer = overlay_bgr.copy()
    cv2.fillConvexPoly(face_layer, face_points, (0, 180, 0))
    overlay_bgr = cv2.addWeighted(face_layer, 0.22, overlay_bgr, 0.78, 0)

    cv2.polylines(overlay_bgr, [face_points], True, (0, 255, 0), 2)
    cv2.polylines(overlay_bgr, [sticker_points], True, (255, 0, 255), 2)
    for index, point in enumerate(face_points.reshape(-1, 2)):
        x_value, y_value = int(point[0]), int(point[1])
        cv2.circle(overlay_bgr, (x_value, y_value), 3, (0, 255, 255), -1)
        cv2.putText(
            overlay_bgr,
            str(index),
            (x_value + 3, y_value - 3),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.35,
            (0, 255, 255),
            1,
            cv2.LINE_AA,
        )

    cv2.putText(
        overlay_bgr,
        f"face={face_method} green, sticker=magenta",
        (4, max(12, min(overlay_bgr.shape[0] - 4, 14))),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.35,
        (255, 255, 255),
        1,
        cv2.LINE_AA,
    )
    output_rgb = cv2.cvtColor(overlay_bgr, cv2.COLOR_BGR2RGB)
    _write_rgb(output_path, output_rgb)


def _manual_face_quads(
    manual_faces: list[ManualFace],
) -> list[tuple[np.ndarray, str]]:
    return [
        (manual_face.quad_crop_xy, f"manual:{manual_face.face_index}")
        for manual_face in manual_faces
    ]


def _face_method_label(face_quads: list[tuple[np.ndarray, str]]) -> str:
    return "|".join(face_method for _face_quad, face_method in face_quads)


def _fruit_source_label(fruit_paths: list[Path]) -> str:
    return "|".join(str(path) for path in fruit_paths)


def _select_sticker_face_quads(
    face_quads: list[tuple[np.ndarray, str]],
    rng: random.Random,
    sticker_face_mode: str,
    max_sticker_faces: int,
) -> list[tuple[np.ndarray, str]]:
    if not face_quads:
        return []
    if max_sticker_faces < 0:
        raise ValueError("max sticker faces must be non-negative")

    face_limit = len(face_quads)
    if max_sticker_faces > 0:
        face_limit = min(face_limit, max_sticker_faces)

    if sticker_face_mode == "all":
        if face_limit == len(face_quads):
            return list(face_quads)
        selected_indices = sorted(rng.sample(range(len(face_quads)), face_limit))
        return [face_quads[index] for index in selected_indices]
    if sticker_face_mode == "one":
        return [rng.choice(face_quads)]
    if sticker_face_mode != "random":
        raise ValueError(f"unknown sticker face mode: {sticker_face_mode}")

    face_count = rng.randint(1, face_limit)
    selected_indices = sorted(rng.sample(range(len(face_quads)), face_count))
    return [face_quads[index] for index in selected_indices]


def synthesize_cube_fruit_dataset(
    data_yaml: Path,
    fruit_root: Path,
    output_root: Path,
    face_annotations: Path | None,
    manual_missing: str,
    output_split_mode: str,
    train_ratio: float,
    val_ratio: float,
    test_ratio: float,
    per_cube_per_fruit: int,
    none_per_cube: int,
    sticker_size: int,
    sticker_alpha: float,
    sticker_inset_min: float,
    sticker_inset_max: float,
    sticker_fill_scale: float,
    sticker_face_mode: str,
    max_sticker_faces: int,
    shadow_prob: float,
    shadow_min_factor: float,
    shadow_max_factor: float,
    shadow_blur_ratio: float,
    global_brightness_min: float,
    global_brightness_max: float,
    color_jitter: float,
    fallback: str,
    seed: int,
    clear: bool,
    debug_face_dir: Path | None,
    debug_max_per_split: int,
) -> dict[str, dict[str, int]]:
    rng = random.Random(seed)
    data_yaml = data_yaml.resolve()
    fruit_root = fruit_root.resolve()
    output_root = output_root.resolve()

    if clear:
        _safe_clear_output(output_root)
    metadata_path = output_root / "metadata.csv"
    _write_metadata_header(metadata_path)

    dataset_root = _dataset_root_from_data_yaml(data_yaml)
    faces_by_cube = (
        _load_face_annotations(face_annotations.resolve())
        if face_annotations is not None
        else None
    )
    cubes_by_split = _collect_cubes(data_yaml)
    output_cubes_by_split = _assign_cubes_to_output_splits(
        cubes_by_split,
        output_split_mode=output_split_mode,
        train_ratio=train_ratio,
        val_ratio=val_ratio,
        test_ratio=test_ratio,
        seed=seed,
    )
    counts = {
        split: {class_name: 0 for class_name in (*FRUIT_CLASSES, NO_FRUIT_CLASS)}
        for split in SPLITS
    }
    debug_counts = {split: 0 for split in SPLITS}
    fruits_by_output_split = {
        split: _collect_fruit_images(fruit_root, split) for split in SPLITS
    }

    for split, cubes in output_cubes_by_split.items():
        fruits_by_class = fruits_by_output_split[split]
        for cube in cubes:
            image_rgb = _read_rgb(cube.image_path)
            cube_crop = _crop_cube(image_rgb, cube.bbox_xyxy)
            if cube_crop.size == 0:
                continue

            manual_faces: list[ManualFace] = []
            if faces_by_cube is not None:
                manual_faces = faces_by_cube.get(
                    _cube_annotation_key(cube, dataset_root),
                    [],
                )
                if not manual_faces:
                    if manual_missing == "error":
                        raise ValueError(
                            "missing manual face annotation for "
                            f"{cube.image_path} cube {cube.index}"
                        )
                    if manual_missing == "skip":
                        continue

            face_quads: list[tuple[np.ndarray, str]] = []
            if manual_faces:
                face_quads = _manual_face_quads(manual_faces)
            else:
                face_quad = estimate_cube_face_quad(cube_crop)
                if face_quad is not None:
                    face_quads = [(face_quad, "auto")]

            if not face_quads:
                if fallback == "skip":
                    continue
                height, width = cube_crop.shape[:2]
                face_quad = random_face_quad(width, height, rng)
                face_quads = [(face_quad, "random_fallback")]

            face_quad = face_quads[0][0]
            face_method = _face_method_label(face_quads)

            if debug_face_dir is not None and (
                debug_max_per_split <= 0 or debug_counts[split] < debug_max_per_split
            ):
                height, width = cube_crop.shape[:2]
                debug_faces = manual_faces or [
                    ManualFace(
                        source_image=str(cube.image_path),
                        cube_index=cube.index,
                        face_index=0,
                        quad_crop_xy=face_quads[0][0],
                    )
                ]
                for debug_face in debug_faces:
                    if (
                        debug_max_per_split > 0
                        and debug_counts[split] >= debug_max_per_split
                    ):
                        break
                    debug_sticker_quad = sample_sticker_quad(
                        debug_face.quad_crop_xy,
                        random.Random(seed),
                        inset_min=sticker_inset_min,
                        inset_max=sticker_inset_max,
                        fill_scale=sticker_fill_scale,
                        image_width=width,
                        image_height=height,
                    )
                    debug_method = (
                        f"manual:{debug_face.face_index}"
                        if manual_faces
                        else face_method
                    )
                    debug_output_path = (
                        debug_face_dir
                        / split
                        / _make_debug_face_stem(cube, debug_method)
                    )
                    _write_face_debug_overlay(
                        debug_output_path,
                        cube_crop,
                        debug_face.quad_crop_xy,
                        debug_sticker_quad,
                        debug_method,
                    )
                    debug_counts[split] += 1

            for sample_index in range(none_per_cube):
                none_crop = apply_lighting_augmentation(
                    cube_crop,
                    rng,
                    shadow_prob=shadow_prob,
                    shadow_min_factor=shadow_min_factor,
                    shadow_max_factor=shadow_max_factor,
                    shadow_blur_ratio=shadow_blur_ratio,
                    global_brightness_min=global_brightness_min,
                    global_brightness_max=global_brightness_max,
                    color_jitter=color_jitter,
                )
                output_path = (
                    output_root
                    / split
                    / NO_FRUIT_CLASS
                    / _make_stem(cube, NO_FRUIT_CLASS, sample_index)
                )
                _write_rgb(output_path, none_crop)
                counts[split][NO_FRUIT_CLASS] += 1
                _append_metadata(
                    metadata_path,
                    [
                        split,
                        NO_FRUIT_CLASS,
                        str(output_path),
                        str(cube.image_path),
                        "",
                        face_method,
                    ],
                )

            for fruit in FRUIT_CLASSES:
                fruit_images = fruits_by_class[fruit]
                for sample_index in range(per_cube_per_fruit):
                    height, width = cube_crop.shape[:2]
                    synthetic = cube_crop.copy()
                    fruit_paths: list[Path] = []
                    sticker_face_quads = _select_sticker_face_quads(
                        face_quads,
                        rng,
                        sticker_face_mode=sticker_face_mode,
                        max_sticker_faces=max_sticker_faces,
                    )
                    for face_quad, _face_method in sticker_face_quads:
                        fruit_path = rng.choice(fruit_images)
                        fruit_paths.append(fruit_path)
                        fruit_image = _read_rgb(fruit_path)
                        sticker = _make_square_sticker(fruit_image, sticker_size, rng)
                        sticker_quad = sample_sticker_quad(
                            face_quad,
                            rng,
                            inset_min=sticker_inset_min,
                            inset_max=sticker_inset_max,
                            fill_scale=sticker_fill_scale,
                            image_width=width,
                            image_height=height,
                        )
                        synthetic = paste_perspective_sticker(
                            synthetic,
                            sticker,
                            sticker_quad,
                            alpha=sticker_alpha,
                        )
                    synthetic = apply_lighting_augmentation(
                        synthetic,
                        rng,
                        shadow_prob=shadow_prob,
                        shadow_min_factor=shadow_min_factor,
                        shadow_max_factor=shadow_max_factor,
                        shadow_blur_ratio=shadow_blur_ratio,
                        global_brightness_min=global_brightness_min,
                        global_brightness_max=global_brightness_max,
                        color_jitter=color_jitter,
                    )
                    synthetic_face_method = _face_method_label(sticker_face_quads)
                    output_path = (
                        output_root
                        / split
                        / fruit
                        / _make_stem(cube, fruit, sample_index)
                    )
                    _write_rgb(output_path, synthetic)
                    counts[split][fruit] += 1
                    _append_metadata(
                        metadata_path,
                        [
                            split,
                            fruit,
                            str(output_path),
                            str(cube.image_path),
                            _fruit_source_label(fruit_paths),
                            synthetic_face_method,
                        ],
                    )
    return counts


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Create synthetic cube-fruit classifier data by estimating cube "
            "face quadrilaterals and perspective-warping fruit images onto them."
        ),
    )
    parser.add_argument("--data", type=Path, default=Path("dataset/data_shapes.yaml"))
    parser.add_argument("--fruit-root", type=Path, default=Path("dataset/fruits360"))
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("dataset/cube_fruits_synthetic"),
    )
    parser.add_argument(
        "--face-annotations",
        type=Path,
        default=None,
        help=(
            "Manual cube-face annotation JSON created by "
            "scripts/annotate_cube_faces.py. When provided, synthetic fruit "
            "stickers use these manually selected faces first."
        ),
    )
    parser.add_argument(
        "--manual-missing",
        choices=("skip", "auto", "error"),
        default="skip",
        help=(
            "Behavior for cubes missing manual face annotations when "
            "--face-annotations is set."
        ),
    )
    parser.add_argument(
        "--output-split-mode",
        choices=("source", "random"),
        default="source",
        help=(
            "source keeps the original YOLO split for each cube; random "
            "reshuffles all available cubes into train/val/test using the "
            "ratio options below."
        ),
    )
    parser.add_argument("--train-ratio", type=float, default=0.7)
    parser.add_argument("--val-ratio", type=float, default=0.15)
    parser.add_argument("--test-ratio", type=float, default=0.15)
    parser.add_argument("--per-cube-per-fruit", type=int, default=1)
    parser.add_argument("--none-per-cube", type=int, default=1)
    parser.add_argument("--sticker-size", type=int, default=256)
    parser.add_argument("--sticker-alpha", type=float, default=0.95)
    parser.add_argument("--sticker-inset-min", type=float, default=0.0)
    parser.add_argument("--sticker-inset-max", type=float, default=0.0)
    parser.add_argument("--sticker-fill-scale", type=float, default=1.0)
    parser.add_argument(
        "--shadow-prob",
        type=float,
        default=0.0,
        help="Probability of adding a soft synthetic shadow to each cube crop.",
    )
    parser.add_argument(
        "--shadow-min-factor",
        type=float,
        default=0.45,
        help="Darkest possible multiplier inside a synthetic shadow.",
    )
    parser.add_argument(
        "--shadow-max-factor",
        type=float,
        default=0.85,
        help="Lightest possible multiplier inside a synthetic shadow.",
    )
    parser.add_argument(
        "--shadow-blur-ratio",
        type=float,
        default=0.20,
        help="Shadow edge blur as a fraction of the shorter crop side.",
    )
    parser.add_argument(
        "--global-brightness-min",
        type=float,
        default=1.0,
        help="Minimum global brightness multiplier for cube crops.",
    )
    parser.add_argument(
        "--global-brightness-max",
        type=float,
        default=1.0,
        help="Maximum global darkening multiplier for cube crops. Must be <= 1.0.",
    )
    parser.add_argument(
        "--color-jitter",
        type=float,
        default=0.0,
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--sticker-face-mode",
        choices=("random", "one", "all"),
        default="random",
        help=(
            "How many annotated faces receive a sticker in one synthetic image. "
            "random picks a non-empty subset, one picks one face, all uses every "
            "annotated face. All selected faces use the same fruit class."
        ),
    )
    parser.add_argument(
        "--max-sticker-faces",
        type=int,
        default=2,
        help=(
            "Maximum number of faces that receive stickers in one synthetic "
            "image. Use 0 to disable the cap."
        ),
    )
    parser.add_argument("--fallback", choices=("random", "skip"), default="skip")
    parser.add_argument(
        "--debug-face-overlays",
        action="store_true",
        help=(
            "Save cube crops with detected face quads drawn before synthesis. "
            "Green is the estimated face; magenta is the final sticker quad."
        ),
    )
    parser.add_argument(
        "--debug-face-dir",
        type=Path,
        default=None,
        help=(
            "Directory for debug face overlay images. Defaults to "
            "<output-root>/debug_faces when --debug-face-overlays is set."
        ),
    )
    parser.add_argument(
        "--debug-max-per-split",
        type=int,
        default=50,
        help="Maximum debug overlay images to save per split. Use 0 for all.",
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--clear", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    debug_face_dir = args.debug_face_dir
    if args.debug_face_overlays and debug_face_dir is None:
        debug_face_dir = args.output_root / "debug_faces"

    counts = synthesize_cube_fruit_dataset(
        data_yaml=args.data,
        fruit_root=args.fruit_root,
        output_root=args.output_root,
        face_annotations=args.face_annotations,
        manual_missing=args.manual_missing,
        output_split_mode=args.output_split_mode,
        train_ratio=args.train_ratio,
        val_ratio=args.val_ratio,
        test_ratio=args.test_ratio,
        per_cube_per_fruit=args.per_cube_per_fruit,
        none_per_cube=args.none_per_cube,
        sticker_size=args.sticker_size,
        sticker_alpha=args.sticker_alpha,
        sticker_inset_min=args.sticker_inset_min,
        sticker_inset_max=args.sticker_inset_max,
        sticker_fill_scale=args.sticker_fill_scale,
        sticker_face_mode=args.sticker_face_mode,
        max_sticker_faces=args.max_sticker_faces,
        shadow_prob=args.shadow_prob,
        shadow_min_factor=args.shadow_min_factor,
        shadow_max_factor=args.shadow_max_factor,
        shadow_blur_ratio=args.shadow_blur_ratio,
        global_brightness_min=args.global_brightness_min,
        global_brightness_max=args.global_brightness_max,
        color_jitter=args.color_jitter,
        fallback=args.fallback,
        seed=args.seed,
        clear=args.clear,
        debug_face_dir=debug_face_dir,
        debug_max_per_split=args.debug_max_per_split,
    )
    for split, split_counts in counts.items():
        total = sum(split_counts.values())
        details = " ".join(
            f"{class_name}={split_counts[class_name]}"
            for class_name in (*FRUIT_CLASSES, NO_FRUIT_CLASS)
        )
        print(f"{split}: total={total} {details}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
