#!/usr/bin/env python3
"""Image-bbox to LiDAR-frame object localization for the U-shape robot.

Pipeline:
  1. Print ArUco markers and place them at measured LiDAR-frame coordinates.
  2. Estimate an image->LiDAR ground-plane homography from the markers.
  3. Map each bbox bottom-center point through the homography.
  4. Optionally add a residual-learning correction trained from real samples.

LiDAR frame convention used by this file:
  x_lidar_m: forward from robot/LiDAR origin, meters
  y_lidar_m: left from robot/LiDAR origin, meters
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence

try:
    import numpy as np
except ImportError:  # pragma: no cover - dependency checked at runtime.
    np = None  # type: ignore[assignment]


DEFAULT_ARUCO_DICTIONARY = "DICT_4X4_50"
DEFAULT_MARKER_IDS = (10, 11, 12, 13, 14, 15)
DEFAULT_FEATURE_COLUMNS = (
    "x_center_norm",
    "y_center_norm",
    "width_norm",
    "height_norm",
    "bottom_x_norm",
    "bottom_y_norm",
    "bbox_area_norm",
    "bbox_aspect",
    "x_homography_m",
    "y_homography_m",
)


def require_numpy() -> Any:
    if np is None:
        raise SystemExit("numpy is required. Install with: python3 -m pip install numpy")
    return np


def require_cv2() -> Any:
    try:
        import cv2
    except ImportError as exc:
        raise SystemExit(
            "OpenCV is required. On Jetson try: sudo apt install python3-opencv. "
            "If cv2.aruco is missing, install opencv-contrib-python."
        ) from exc
    if not hasattr(cv2, "aruco"):
        raise SystemExit(
            "cv2.aruco is missing. Install an OpenCV build with contrib modules, "
            "for example: python3 -m pip install opencv-contrib-python"
        )
    return cv2


def parse_id_list(text: str) -> list[int]:
    ids = [int(part.strip()) for part in text.split(",") if part.strip()]
    if not ids:
        raise argparse.ArgumentTypeError("at least one marker id is required")
    return ids


def parse_float(row: dict[str, str], names: Sequence[str], default: float | None = None) -> float:
    for name in names:
        value = row.get(name)
        if value not in (None, ""):
            return float(value)
    if default is not None:
        return default
    raise KeyError(f"missing required column; expected one of {', '.join(names)}")


def parse_int(row: dict[str, str], names: Sequence[str], default: int | None = None) -> int:
    for name in names:
        value = row.get(name)
        if value not in (None, ""):
            return int(float(value))
    if default is not None:
        return default
    raise KeyError(f"missing required column; expected one of {', '.join(names)}")


@dataclass(frozen=True)
class BBox:
    """Axis-aligned detection box stored in pixel coordinates."""

    x1: float
    y1: float
    x2: float
    y2: float
    image_width: int
    image_height: int

    @classmethod
    def from_cxcywh(
        cls,
        x_center: float,
        y_center: float,
        width: float,
        height: float,
        image_width: int,
        image_height: int,
        normalized: bool,
    ) -> "BBox":
        if normalized:
            x_center *= image_width
            width *= image_width
            y_center *= image_height
            height *= image_height
        return cls(
            x1=x_center - width / 2.0,
            y1=y_center - height / 2.0,
            x2=x_center + width / 2.0,
            y2=y_center + height / 2.0,
            image_width=image_width,
            image_height=image_height,
        )

    @classmethod
    def from_xyxy(
        cls,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        image_width: int,
        image_height: int,
    ) -> "BBox":
        return cls(x1=x1, y1=y1, x2=x2, y2=y2, image_width=image_width, image_height=image_height)

    @property
    def x_center_px(self) -> float:
        return (self.x1 + self.x2) / 2.0

    @property
    def y_center_px(self) -> float:
        return (self.y1 + self.y2) / 2.0

    @property
    def width_px(self) -> float:
        return max(0.0, self.x2 - self.x1)

    @property
    def height_px(self) -> float:
        return max(0.0, self.y2 - self.y1)

    @property
    def bottom_center_px(self) -> tuple[float, float]:
        # Bottom center approximates the floor contact point of the object.
        return self.x_center_px, self.y2

    def feature_dict(self, x_homography_m: float, y_homography_m: float) -> dict[str, float]:
        w = max(float(self.image_width), 1.0)
        h = max(float(self.image_height), 1.0)
        width_norm = self.width_px / w
        height_norm = self.height_px / h
        return {
            "x_center_norm": self.x_center_px / w,
            "y_center_norm": self.y_center_px / h,
            "width_norm": width_norm,
            "height_norm": height_norm,
            "bottom_x_norm": self.bottom_center_px[0] / w,
            "bottom_y_norm": self.bottom_center_px[1] / h,
            "bbox_area_norm": width_norm * height_norm,
            "bbox_aspect": self.width_px / max(self.height_px, 1.0),
            "x_homography_m": x_homography_m,
            "y_homography_m": y_homography_m,
        }


@dataclass(frozen=True)
class MarkerLayoutEntry:
    marker_id: int
    x_lidar_m: float
    y_lidar_m: float
    marker_size_m: float | None = None
    yaw_deg: float | None = None

    def lidar_corners(self) -> list[tuple[float, float]]:
        if self.marker_size_m is None or self.yaw_deg is None:
            raise ValueError("corner mode requires marker_size_m and yaw_deg for every marker")

        half = self.marker_size_m / 2.0
        local_corners = [(-half, -half), (half, -half), (half, half), (-half, half)]
        yaw = math.radians(self.yaw_deg)
        cos_yaw = math.cos(yaw)
        sin_yaw = math.sin(yaw)
        return [
            (
                self.x_lidar_m + cos_yaw * x - sin_yaw * y,
                self.y_lidar_m + sin_yaw * x + cos_yaw * y,
            )
            for x, y in local_corners
        ]


@dataclass
class HomographyModel:
    matrix: list[list[float]]
    image_width: int | None = None
    image_height: int | None = None
    dictionary: str = DEFAULT_ARUCO_DICTIONARY
    point_mode: str = "center"
    marker_layout_path: str | None = None
    reprojection_rmse_m: float | None = None
    inlier_count: int | None = None
    point_count: int | None = None
    created_utc: str | None = None

    def image_to_lidar(self, u_px: float, v_px: float) -> tuple[float, float]:
        h = self.matrix
        denom = h[2][0] * u_px + h[2][1] * v_px + h[2][2]
        if abs(denom) < 1e-12:
            raise ZeroDivisionError("homography produced a near-zero homogeneous denominator")
        x = (h[0][0] * u_px + h[0][1] * v_px + h[0][2]) / denom
        y = (h[1][0] * u_px + h[1][1] * v_px + h[1][2]) / denom
        return float(x), float(y)

    def save(self, path: Path) -> None:
        payload = {
            "schema_version": 1,
            "type": "image_to_lidar_homography",
            "matrix": self.matrix,
            "image_width": self.image_width,
            "image_height": self.image_height,
            "dictionary": self.dictionary,
            "point_mode": self.point_mode,
            "marker_layout_path": self.marker_layout_path,
            "reprojection_rmse_m": self.reprojection_rmse_m,
            "inlier_count": self.inlier_count,
            "point_count": self.point_count,
            "created_utc": self.created_utc or utc_now(),
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> "HomographyModel":
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("type") != "image_to_lidar_homography":
            raise ValueError(f"{path} is not an image_to_lidar_homography calibration")
        return cls(
            matrix=payload["matrix"],
            image_width=payload.get("image_width"),
            image_height=payload.get("image_height"),
            dictionary=payload.get("dictionary", DEFAULT_ARUCO_DICTIONARY),
            point_mode=payload.get("point_mode", "center"),
            marker_layout_path=payload.get("marker_layout_path"),
            reprojection_rmse_m=payload.get("reprojection_rmse_m"),
            inlier_count=payload.get("inlier_count"),
            point_count=payload.get("point_count"),
            created_utc=payload.get("created_utc"),
        )


class ResidualCorrector:
    """Load a trained residual model and predict dx, dy in meters."""

    def __init__(self, model_path: Path) -> None:
        try:
            import joblib
        except ImportError as exc:
            raise SystemExit("joblib is required for residual inference: python3 -m pip install joblib") from exc

        payload = joblib.load(model_path)
        if isinstance(payload, dict):
            self.estimator = payload.get("estimator") or payload.get("pipeline")
            self.feature_columns = tuple(payload.get("feature_columns", DEFAULT_FEATURE_COLUMNS))
            self.metadata = payload.get("metadata", {})
        else:
            self.estimator = payload
            self.feature_columns = DEFAULT_FEATURE_COLUMNS
            self.metadata = {}

        if self.estimator is None:
            raise ValueError(f"residual model {model_path} does not contain an estimator")

    def predict_delta(self, bbox: BBox, x_homography_m: float, y_homography_m: float) -> tuple[float, float]:
        features = bbox.feature_dict(x_homography_m, y_homography_m)
        vector = [[features[name] for name in self.feature_columns]]
        prediction = self.estimator.predict(vector)[0]
        return float(prediction[0]), float(prediction[1])


class ObjectLidarEstimator:
    def __init__(self, homography: HomographyModel, residual: ResidualCorrector | None = None) -> None:
        self.homography = homography
        self.residual = residual

    def estimate_bbox(self, bbox: BBox) -> dict[str, float | str]:
        bottom_u, bottom_v = bbox.bottom_center_px
        x_h, y_h = self.homography.image_to_lidar(bottom_u, bottom_v)
        dx = 0.0
        dy = 0.0
        source = "homography"
        if self.residual is not None:
            dx, dy = self.residual.predict_delta(bbox, x_h, y_h)
            source = "homography_residual"

        return {
            "bbox_bottom_center_x_px": bottom_u,
            "bbox_bottom_center_y_px": bottom_v,
            "x_lidar_homography_m": x_h,
            "y_lidar_homography_m": y_h,
            "x_lidar_residual_dx_m": dx,
            "y_lidar_residual_dy_m": dy,
            "x_lidar_m": x_h + dx,
            "y_lidar_m": y_h + dy,
            "position_source": source,
        }


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_marker_layout(path: Path) -> dict[int, MarkerLayoutEntry]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        entries: dict[int, MarkerLayoutEntry] = {}
        for row in reader:
            marker_id = parse_int(row, ("marker_id", "id", "aruco_id"))
            size_value = row.get("marker_size_m") or row.get("size_m")
            yaw_value = row.get("yaw_deg")
            entries[marker_id] = MarkerLayoutEntry(
                marker_id=marker_id,
                x_lidar_m=parse_float(row, ("x_lidar_m", "x_m", "x")),
                y_lidar_m=parse_float(row, ("y_lidar_m", "y_m", "y")),
                marker_size_m=float(size_value) if size_value not in (None, "") else None,
                yaw_deg=float(yaw_value) if yaw_value not in (None, "") else None,
            )
    if not entries:
        raise ValueError(f"marker layout is empty: {path}")
    return entries


def aruco_dictionary(cv2: Any, dictionary_name: str) -> Any:
    if not hasattr(cv2.aruco, dictionary_name):
        raise ValueError(f"unknown ArUco dictionary: {dictionary_name}")
    return cv2.aruco.getPredefinedDictionary(getattr(cv2.aruco, dictionary_name))


def detect_aruco_markers(image: Any, dictionary_name: str) -> tuple[list[Any], list[int]]:
    cv2 = require_cv2()
    dictionary = aruco_dictionary(cv2, dictionary_name)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image

    if hasattr(cv2.aruco, "ArucoDetector"):
        parameters = cv2.aruco.DetectorParameters()
        detector = cv2.aruco.ArucoDetector(dictionary, parameters)
        corners, ids, _rejected = detector.detectMarkers(gray)
    else:  # OpenCV 4.6 and older.
        parameters = cv2.aruco.DetectorParameters_create()
        corners, ids, _rejected = cv2.aruco.detectMarkers(gray, dictionary, parameters=parameters)

    if ids is None:
        return [], []
    return corners, [int(value[0]) for value in ids]


def build_homography_points(
    marker_corners: Sequence[Any],
    marker_ids: Sequence[int],
    layout: dict[int, MarkerLayoutEntry],
    point_mode: str,
) -> tuple[list[tuple[float, float]], list[tuple[float, float]], list[int]]:
    src_image: list[tuple[float, float]] = []
    dst_lidar: list[tuple[float, float]] = []
    used_ids: list[int] = []

    for corners, marker_id in zip(marker_corners, marker_ids):
        if marker_id not in layout:
            continue
        image_corners = corners.reshape(4, 2)
        entry = layout[marker_id]
        used_ids.append(marker_id)

        if point_mode == "center":
            center = image_corners.mean(axis=0)
            src_image.append((float(center[0]), float(center[1])))
            dst_lidar.append((entry.x_lidar_m, entry.y_lidar_m))
        elif point_mode == "corners":
            for image_point, lidar_point in zip(image_corners, entry.lidar_corners()):
                src_image.append((float(image_point[0]), float(image_point[1])))
                dst_lidar.append(lidar_point)
        else:
            raise ValueError("point_mode must be center or corners")

    return src_image, dst_lidar, used_ids


def compute_rmse_m(homography: HomographyModel, src_image: Sequence[tuple[float, float]], dst_lidar: Sequence[tuple[float, float]]) -> float:
    squared_errors = []
    for (u, v), (x_true, y_true) in zip(src_image, dst_lidar):
        x_pred, y_pred = homography.image_to_lidar(u, v)
        squared_errors.append((x_pred - x_true) ** 2 + (y_pred - y_true) ** 2)
    return math.sqrt(sum(squared_errors) / max(len(squared_errors), 1))


def calibrate_homography(args: argparse.Namespace) -> int:
    np_mod = require_numpy()
    cv2 = require_cv2()
    layout = read_marker_layout(args.layout)
    image = cv2.imread(str(args.image))
    if image is None:
        raise SystemExit(f"could not read calibration image: {args.image}")

    corners, ids = detect_aruco_markers(image, args.dictionary)
    src_image, dst_lidar, used_ids = build_homography_points(corners, ids, layout, args.point_mode)
    if len(src_image) < 4:
        raise SystemExit(
            f"need at least 4 calibration points, got {len(src_image)}. "
            "Use more visible markers or switch point mode."
        )

    h_matrix, inlier_mask = cv2.findHomography(
        np_mod.asarray(src_image, dtype=np_mod.float64),
        np_mod.asarray(dst_lidar, dtype=np_mod.float64),
        method=cv2.RANSAC,
        ransacReprojThreshold=args.ransac_threshold_m,
    )
    if h_matrix is None:
        raise SystemExit("cv2.findHomography failed; check marker layout and measurements")

    model = HomographyModel(
        matrix=[[float(value) for value in row] for row in h_matrix.tolist()],
        image_width=int(image.shape[1]),
        image_height=int(image.shape[0]),
        dictionary=args.dictionary,
        point_mode=args.point_mode,
        marker_layout_path=str(args.layout),
        inlier_count=int(inlier_mask.sum()) if inlier_mask is not None else None,
        point_count=len(src_image),
        created_utc=utc_now(),
    )
    model.reprojection_rmse_m = compute_rmse_m(model, src_image, dst_lidar)
    model.save(args.output)

    print(
        json.dumps(
            {
                "output": str(args.output),
                "used_marker_ids": sorted(set(used_ids)),
                "point_count": len(src_image),
                "inlier_count": model.inlier_count,
                "reprojection_rmse_m": model.reprojection_rmse_m,
            },
            ensure_ascii=True,
        )
    )

    if args.preview:
        draw_calibration_preview(image, corners, ids, model, src_image, dst_lidar, args.preview)
    return 0


def draw_calibration_preview(
    image: Any,
    corners: Sequence[Any],
    ids: Sequence[int],
    model: HomographyModel,
    src_image: Sequence[tuple[float, float]],
    dst_lidar: Sequence[tuple[float, float]],
    output_path: Path,
) -> None:
    cv2 = require_cv2()
    preview = image.copy()
    if corners:
        ids_array = require_numpy().asarray([[marker_id] for marker_id in ids], dtype="int32")
        cv2.aruco.drawDetectedMarkers(preview, corners, ids_array)
    for (u, v), (x_true, y_true) in zip(src_image, dst_lidar):
        x_pred, y_pred = model.image_to_lidar(u, v)
        error_cm = math.hypot(x_pred - x_true, y_pred - y_true) * 100.0
        cv2.circle(preview, (int(round(u)), int(round(v))), 5, (0, 220, 255), -1)
        cv2.putText(
            preview,
            f"{x_true:.2f},{y_true:.2f} e={error_cm:.1f}cm",
            (int(round(u)) + 8, int(round(v)) - 8),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (0, 220, 255),
            1,
            cv2.LINE_AA,
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output_path), preview)


def recommended_layout(ids: Sequence[int], marker_size_m: float) -> list[dict[str, float | int]]:
    base_positions = [
        (0.40, -0.45),
        (0.40, 0.45),
        (0.80, -0.55),
        (0.80, 0.55),
        (1.20, -0.65),
        (1.20, 0.65),
        (1.60, -0.70),
        (1.60, 0.70),
    ]
    rows = []
    for index, marker_id in enumerate(ids):
        if index < len(base_positions):
            x_lidar_m, y_lidar_m = base_positions[index]
        else:
            x_lidar_m = 0.40 + 0.40 * (index // 2)
            y_lidar_m = -0.75 if index % 2 == 0 else 0.75
        rows.append(
            {
                "marker_id": marker_id,
                "x_lidar_m": x_lidar_m,
                "y_lidar_m": y_lidar_m,
                "marker_size_m": marker_size_m,
                "yaw_deg": 0.0,
            }
        )
    return rows


def generate_markers(args: argparse.Namespace) -> int:
    np_mod = require_numpy()
    cv2 = require_cv2()
    dictionary = aruco_dictionary(cv2, args.dictionary)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    marker_size_m = args.marker_size_mm / 1000.0
    manifest = {
        "dictionary": args.dictionary,
        "marker_ids": args.ids,
        "marker_size_mm": args.marker_size_mm,
        "image_pixels": args.image_pixels,
        "generated_utc": utc_now(),
        "files": [],
    }

    marker_pixels = args.image_pixels
    margin_px = int(round(marker_pixels * args.margin_ratio))
    for marker_id in args.ids:
        marker = np_mod.zeros((marker_pixels, marker_pixels), dtype=np_mod.uint8)
        if hasattr(cv2.aruco, "generateImageMarker"):
            generated = cv2.aruco.generateImageMarker(dictionary, marker_id, marker_pixels, marker, args.border_bits)
        else:
            generated = cv2.aruco.drawMarker(dictionary, marker_id, marker_pixels, marker, args.border_bits)
        if generated is not None:
            marker = generated

        canvas = np_mod.full(
            (marker_pixels + 2 * margin_px, marker_pixels + 2 * margin_px),
            255,
            dtype=np_mod.uint8,
        )
        canvas[margin_px : margin_px + marker_pixels, margin_px : margin_px + marker_pixels] = marker
        filename = f"aruco_{args.dictionary}_{marker_id:03d}_{args.marker_size_mm:.0f}mm.png"
        output_path = args.output_dir / filename
        cv2.imwrite(str(output_path), canvas)
        manifest["files"].append(str(output_path))

    layout_path = args.output_dir / "recommended_marker_layout.csv"
    write_layout_csv(layout_path, recommended_layout(args.ids, marker_size_m))
    manifest["layout_template"] = str(layout_path)
    (args.output_dir / "print_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"output_dir": str(args.output_dir), "layout_template": str(layout_path)}, ensure_ascii=True))
    return 0


def write_layout_csv(path: Path, rows: Sequence[dict[str, float | int]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = ["marker_id", "x_lidar_m", "y_lidar_m", "marker_size_m", "yaw_deg"]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def bbox_from_row(
    row: dict[str, str],
    bbox_format: str,
    default_image_width: int | None,
    default_image_height: int | None,
) -> BBox:
    image_width = parse_int(row, ("image_width", "img_width", "width_px"), default_image_width)
    image_height = parse_int(row, ("image_height", "img_height", "height_px"), default_image_height)

    if bbox_format == "auto":
        if row.get("bbox_xyxy"):
            values = json.loads(row["bbox_xyxy"])
            return BBox.from_xyxy(float(values[0]), float(values[1]), float(values[2]), float(values[3]), image_width, image_height)
        if all(row.get(name) not in (None, "") for name in ("x1", "y1", "x2", "y2")):
            bbox_format = "xyxy"
        elif all(row.get(name) not in (None, "") for name in ("xmin", "ymin", "xmax", "ymax")):
            return BBox.from_xyxy(
                parse_float(row, ("xmin",)),
                parse_float(row, ("ymin",)),
                parse_float(row, ("xmax",)),
                parse_float(row, ("ymax",)),
                image_width,
                image_height,
            )
        elif all(row.get(name) not in (None, "") for name in ("x_center", "y_center", "width", "height")):
            cx = parse_float(row, ("x_center",))
            cy = parse_float(row, ("y_center",))
            bw = parse_float(row, ("width",))
            bh = parse_float(row, ("height",))
            normalized = max(abs(cx), abs(cy), abs(bw), abs(bh)) <= 1.5
            return BBox.from_cxcywh(cx, cy, bw, bh, image_width, image_height, normalized=normalized)
        else:
            raise KeyError("could not infer bbox columns")

    if bbox_format == "yolo":
        return BBox.from_cxcywh(
            parse_float(row, ("x_center", "cx")),
            parse_float(row, ("y_center", "cy")),
            parse_float(row, ("width", "w")),
            parse_float(row, ("height", "h")),
            image_width,
            image_height,
            normalized=True,
        )
    if bbox_format == "cxcywh_pixel":
        return BBox.from_cxcywh(
            parse_float(row, ("x_center", "cx")),
            parse_float(row, ("y_center", "cy")),
            parse_float(row, ("width", "w")),
            parse_float(row, ("height", "h")),
            image_width,
            image_height,
            normalized=False,
        )
    if bbox_format == "xyxy":
        return BBox.from_xyxy(
            parse_float(row, ("x1", "xmin")),
            parse_float(row, ("y1", "ymin")),
            parse_float(row, ("x2", "xmax")),
            parse_float(row, ("y2", "ymax")),
            image_width,
            image_height,
        )
    if bbox_format == "xywh":
        x = parse_float(row, ("x", "xmin"))
        y = parse_float(row, ("y", "ymin"))
        width = parse_float(row, ("width", "w"))
        height = parse_float(row, ("height", "h"))
        return BBox.from_xyxy(x, y, x + width, y + height, image_width, image_height)
    raise ValueError(f"unsupported bbox format: {bbox_format}")


def load_estimator(args: argparse.Namespace) -> ObjectLidarEstimator:
    homography = HomographyModel.load(args.calibration)
    residual = ResidualCorrector(args.residual_model) if args.residual_model else None
    return ObjectLidarEstimator(homography, residual)


def estimate_csv(args: argparse.Namespace) -> int:
    estimator = load_estimator(args)
    with args.input.open("r", newline="", encoding="utf-8") as in_handle:
        reader = csv.DictReader(in_handle)
        rows = []
        output_fieldnames = list(reader.fieldnames or [])
        extra_fields = [
            "bbox_bottom_center_x_px",
            "bbox_bottom_center_y_px",
            "x_lidar_homography_m",
            "y_lidar_homography_m",
            "x_lidar_residual_dx_m",
            "y_lidar_residual_dy_m",
            "x_lidar_m",
            "y_lidar_m",
            "position_source",
        ]
        for field in extra_fields:
            if field not in output_fieldnames:
                output_fieldnames.append(field)

        for row in reader:
            bbox = bbox_from_row(row, args.bbox_format, args.image_width, args.image_height)
            estimate = estimator.estimate_bbox(bbox)
            for key, value in estimate.items():
                row[key] = f"{value:.6f}" if isinstance(value, float) else str(value)
            rows.append(row)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as out_handle:
        writer = csv.DictWriter(out_handle, fieldnames=output_fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps({"output": str(args.output), "rows": len(rows)}, ensure_ascii=True))
    return 0


def bbox_from_xyxy_payload(payload: dict[str, Any], image_width: int, image_height: int) -> BBox | None:
    values = payload.get("bbox_xyxy")
    if values is None:
        return None
    return BBox.from_xyxy(float(values[0]), float(values[1]), float(values[2]), float(values[3]), image_width, image_height)


def add_lidar_estimates_to_payload(payload: dict[str, Any], estimator: ObjectLidarEstimator, image_width: int, image_height: int) -> dict[str, Any]:
    for key in ("targets", "detections"):
        items = payload.get(key)
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            bbox = bbox_from_xyxy_payload(item, image_width, image_height)
            if bbox is None:
                continue
            estimate = estimator.estimate_bbox(bbox)
            item["lidar_position_m"] = {
                "x": round(float(estimate["x_lidar_m"]), 4),
                "y": round(float(estimate["y_lidar_m"]), 4),
                "source": estimate["position_source"],
                "x_homography": round(float(estimate["x_lidar_homography_m"]), 4),
                "y_homography": round(float(estimate["y_lidar_homography_m"]), 4),
                "dx_residual": round(float(estimate["x_lidar_residual_dx_m"]), 4),
                "dy_residual": round(float(estimate["y_lidar_residual_dy_m"]), 4),
            }
    return payload


def live_yolo_jsonl(args: argparse.Namespace) -> int:
    estimator = load_estimator(args)
    input_handle = sys.stdin if str(args.input) == "-" else args.input.open("r", encoding="utf-8")
    output_handle = sys.stdout if str(args.output) == "-" else args.output.open("w", encoding="utf-8")
    try:
        for raw_line in input_handle:
            line = raw_line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                print(raw_line.rstrip("\n"), file=output_handle, flush=True)
                continue
            payload = add_lidar_estimates_to_payload(payload, estimator, args.image_width, args.image_height)
            print(json.dumps(payload, ensure_ascii=True), file=output_handle, flush=True)
    finally:
        if input_handle is not sys.stdin:
            input_handle.close()
        if output_handle is not sys.stdout:
            output_handle.close()
    return 0


def add_shared_estimator_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--calibration", type=Path, required=True, help="homography JSON from calibrate-homography")
    parser.add_argument("--residual-model", type=Path, default=None, help="optional residual model .joblib from train_residual_model.py")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ArUco homography + residual object localization in LiDAR frame.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    marker_parser = subparsers.add_parser("generate-markers", help="Generate printable ArUco marker PNG files.")
    marker_parser.add_argument("--output-dir", type=Path, default=Path("u_shape_robot_slam/generated_markers"))
    marker_parser.add_argument("--dictionary", default=DEFAULT_ARUCO_DICTIONARY)
    marker_parser.add_argument("--ids", type=parse_id_list, default=list(DEFAULT_MARKER_IDS), help="comma-separated marker ids")
    marker_parser.add_argument("--marker-size-mm", type=float, default=80.0, help="physical black marker square size")
    marker_parser.add_argument("--image-pixels", type=int, default=1200)
    marker_parser.add_argument("--border-bits", type=int, default=1)
    marker_parser.add_argument("--margin-ratio", type=float, default=0.18, help="white print margin around marker image")
    marker_parser.set_defaults(func=generate_markers)

    calibration_parser = subparsers.add_parser("calibrate-homography", help="Estimate image->LiDAR homography from ArUco markers.")
    calibration_parser.add_argument("--image", type=Path, required=True, help="calibration image containing floor markers")
    calibration_parser.add_argument("--layout", type=Path, required=True, help="CSV with marker_id,x_lidar_m,y_lidar_m")
    calibration_parser.add_argument("--output", type=Path, required=True, help="output homography JSON")
    calibration_parser.add_argument("--dictionary", default=DEFAULT_ARUCO_DICTIONARY)
    calibration_parser.add_argument("--point-mode", choices=("center", "corners"), default="center")
    calibration_parser.add_argument("--ransac-threshold-m", type=float, default=0.035)
    calibration_parser.add_argument("--preview", type=Path, default=None, help="optional annotated calibration image")
    calibration_parser.set_defaults(func=calibrate_homography)

    estimate_parser = subparsers.add_parser("estimate-csv", help="Append LiDAR coordinates to a detection CSV.")
    add_shared_estimator_args(estimate_parser)
    estimate_parser.add_argument("--input", type=Path, required=True)
    estimate_parser.add_argument("--output", type=Path, required=True)
    estimate_parser.add_argument("--bbox-format", choices=("auto", "yolo", "cxcywh_pixel", "xyxy", "xywh"), default="auto")
    estimate_parser.add_argument("--image-width", type=int, default=None, help="fallback if CSV has no image_width column")
    estimate_parser.add_argument("--image-height", type=int, default=None, help="fallback if CSV has no image_height column")
    estimate_parser.set_defaults(func=estimate_csv)

    jsonl_parser = subparsers.add_parser("live-yolo-jsonl", help="Read YOLO JSONL and add lidar_position_m to each bbox.")
    add_shared_estimator_args(jsonl_parser)
    jsonl_parser.add_argument("--input", type=Path, default=Path("-"), help="JSONL input path or - for stdin")
    jsonl_parser.add_argument("--output", type=Path, default=Path("-"), help="JSONL output path or - for stdout")
    jsonl_parser.add_argument("--image-width", type=int, required=True)
    jsonl_parser.add_argument("--image-height", type=int, required=True)
    jsonl_parser.set_defaults(func=live_yolo_jsonl)

    return parser


def clean_jupyter_argv(argv: Sequence[str]) -> tuple[list[str], bool]:
    """Remove Colab/Jupyter's injected kernel JSON argument when present."""

    cleaned: list[str] = []
    removed_kernel_arg = False
    for arg in argv:
        normalized = arg.replace("\\", "/")
        if normalized.endswith(".json") and "/runtime/kernel-" in normalized:
            removed_kernel_arg = True
            continue
        cleaned.append(arg)
    return cleaned, removed_kernel_arg


def main(argv: Sequence[str] | None = None) -> int:
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    cleaned_argv, removed_kernel_arg = clean_jupyter_argv(raw_argv)
    parser = build_parser()
    if removed_kernel_arg and not cleaned_argv:
        print(
            "Colab/Jupyter kernel argument was ignored, but no command was supplied.\n"
            "Use a shell cell like: !python u_shape_robot_slam/object_lidar_localizer.py generate-markers ...",
            file=sys.stderr,
        )
        parser.print_help(sys.stderr)
        return 2

    args = parser.parse_args(cleaned_argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
