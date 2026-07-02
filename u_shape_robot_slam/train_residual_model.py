#!/usr/bin/env python3
"""Train residual correction for bbox-to-LiDAR homography estimates.

The model learns:
  residual_dx_m = x_lidar_gt_m - x_lidar_homography_m
  residual_dy_m = y_lidar_gt_m - y_lidar_homography_m

Inputs are all bbox parameters plus the raw homography estimate. The trained
model is saved as a joblib file and can be loaded by object_lidar_localizer.py.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any

try:
    import numpy as np
except ImportError as exc:  # pragma: no cover - dependency checked at runtime.
    raise SystemExit("numpy is required. Install with: python3 -m pip install numpy") from exc

from object_lidar_localizer import (
    DEFAULT_FEATURE_COLUMNS,
    HomographyModel,
    bbox_from_row,
    parse_float,
    utc_now,
)


def require_joblib() -> Any:
    try:
        import joblib
    except ImportError as exc:  # pragma: no cover - dependency checked at runtime.
        raise SystemExit("joblib is required. Install with: python3 -m pip install joblib") from exc
    return joblib


def require_sklearn() -> dict[str, Any]:
    try:
        from sklearn.ensemble import ExtraTreesRegressor, RandomForestRegressor
        from sklearn.linear_model import Ridge
        from sklearn.model_selection import train_test_split
        from sklearn.pipeline import make_pipeline
        from sklearn.preprocessing import PolynomialFeatures, StandardScaler
    except ImportError as exc:  # pragma: no cover - dependency checked at runtime.
        raise SystemExit("scikit-learn is required. Install with: python3 -m pip install scikit-learn") from exc

    return {
        "ExtraTreesRegressor": ExtraTreesRegressor,
        "RandomForestRegressor": RandomForestRegressor,
        "Ridge": Ridge,
        "train_test_split": train_test_split,
        "make_pipeline": make_pipeline,
        "PolynomialFeatures": PolynomialFeatures,
        "StandardScaler": StandardScaler,
    }


def build_estimator(args: argparse.Namespace) -> Any:
    sklearn = require_sklearn()
    if args.model == "random_forest":
        return sklearn["RandomForestRegressor"](
            n_estimators=args.n_estimators,
            min_samples_leaf=args.min_samples_leaf,
            max_depth=args.max_depth or None,
            random_state=args.seed,
            n_jobs=-1,
        )
    if args.model == "extra_trees":
        return sklearn["ExtraTreesRegressor"](
            n_estimators=args.n_estimators,
            min_samples_leaf=args.min_samples_leaf,
            max_depth=args.max_depth or None,
            random_state=args.seed,
            n_jobs=-1,
        )
    if args.model == "poly_ridge":
        return sklearn["make_pipeline"](
            sklearn["PolynomialFeatures"](degree=args.poly_degree, include_bias=False),
            sklearn["StandardScaler"](),
            sklearn["Ridge"](alpha=args.ridge_alpha, random_state=args.seed),
        )
    raise ValueError(f"unsupported model: {args.model}")


def rmse_cm(pred_xy_m: np.ndarray, true_xy_m: np.ndarray) -> float:
    errors_m = np.linalg.norm(pred_xy_m - true_xy_m, axis=1)
    return float(math.sqrt(np.mean(errors_m**2)) * 100.0)


def mae_cm(pred_xy_m: np.ndarray, true_xy_m: np.ndarray) -> float:
    errors_m = np.linalg.norm(pred_xy_m - true_xy_m, axis=1)
    return float(np.mean(np.abs(errors_m)) * 100.0)


def load_training_data(args: argparse.Namespace) -> dict[str, Any]:
    homography = HomographyModel.load(args.calibration)
    feature_rows: list[list[float]] = []
    residual_rows: list[list[float]] = []
    homography_xy_rows: list[list[float]] = []
    gt_xy_rows: list[list[float]] = []
    source_rows: list[dict[str, str]] = []

    with args.data.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            bbox = bbox_from_row(row, args.bbox_format, args.image_width, args.image_height)
            if row.get("x_lidar_homography_m") not in (None, "") and row.get("y_lidar_homography_m") not in (None, ""):
                x_h = parse_float(row, ("x_lidar_homography_m",))
                y_h = parse_float(row, ("y_lidar_homography_m",))
            else:
                bottom_u, bottom_v = bbox.bottom_center_px
                x_h, y_h = homography.image_to_lidar(bottom_u, bottom_v)

            x_gt = parse_float(row, ("x_lidar_gt_m", "x_gt_m", "x_lidar_true_m"))
            y_gt = parse_float(row, ("y_lidar_gt_m", "y_gt_m", "y_lidar_true_m"))
            features = bbox.feature_dict(x_h, y_h)
            feature_rows.append([features[name] for name in DEFAULT_FEATURE_COLUMNS])
            residual_rows.append([x_gt - x_h, y_gt - y_h])
            homography_xy_rows.append([x_h, y_h])
            gt_xy_rows.append([x_gt, y_gt])
            source_rows.append(row)

    if len(feature_rows) < 8:
        raise SystemExit("at least 8 residual samples are required; 100+ is strongly recommended")

    return {
        "features": np.asarray(feature_rows, dtype=np.float64),
        "residuals": np.asarray(residual_rows, dtype=np.float64),
        "homography_xy": np.asarray(homography_xy_rows, dtype=np.float64),
        "gt_xy": np.asarray(gt_xy_rows, dtype=np.float64),
        "source_rows": source_rows,
        "homography": homography,
    }


def split_indices(sample_count: int, test_size: float, seed: int) -> tuple[np.ndarray, np.ndarray]:
    train_test_split = require_sklearn()["train_test_split"]
    indices = np.arange(sample_count)
    if sample_count < 20:
        # Keep a small validation slice while still leaving enough data to fit.
        test_count = max(2, sample_count // 5)
        train_idx, test_idx = train_test_split(indices, test_size=test_count, random_state=seed)
    else:
        train_idx, test_idx = train_test_split(indices, test_size=test_size, random_state=seed)
    return np.asarray(train_idx), np.asarray(test_idx)


def evaluate(estimator: Any, data: dict[str, Any], indices: np.ndarray) -> dict[str, float]:
    x = data["features"][indices]
    gt_xy = data["gt_xy"][indices]
    homography_xy = data["homography_xy"][indices]
    pred_residual = estimator.predict(x)
    corrected_xy = homography_xy + pred_residual
    base_rmse = rmse_cm(homography_xy, gt_xy)
    corrected_rmse = rmse_cm(corrected_xy, gt_xy)
    base_mae = mae_cm(homography_xy, gt_xy)
    corrected_mae = mae_cm(corrected_xy, gt_xy)
    improvement = 0.0 if base_rmse <= 1e-9 else (base_rmse - corrected_rmse) / base_rmse * 100.0
    return {
        "samples": int(len(indices)),
        "homography_rmse_cm": round(base_rmse, 3),
        "corrected_rmse_cm": round(corrected_rmse, 3),
        "homography_mae_cm": round(base_mae, 3),
        "corrected_mae_cm": round(corrected_mae, 3),
        "rmse_improvement_percent": round(improvement, 2),
    }


def write_predictions_csv(path: Path, estimator: Any, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pred_residual = estimator.predict(data["features"])
    corrected_xy = data["homography_xy"] + pred_residual
    fieldnames = list(data["source_rows"][0].keys())
    extra_fields = [
        "x_lidar_homography_m",
        "y_lidar_homography_m",
        "x_residual_true_m",
        "y_residual_true_m",
        "x_residual_pred_m",
        "y_residual_pred_m",
        "x_lidar_corrected_m",
        "y_lidar_corrected_m",
        "error_homography_cm",
        "error_corrected_cm",
    ]
    for field in extra_fields:
        if field not in fieldnames:
            fieldnames.append(field)

    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for index, source_row in enumerate(data["source_rows"]):
            row = dict(source_row)
            homography_xy = data["homography_xy"][index]
            gt_xy = data["gt_xy"][index]
            true_residual = data["residuals"][index]
            pred = pred_residual[index]
            corrected = corrected_xy[index]
            row.update(
                {
                    "x_lidar_homography_m": f"{homography_xy[0]:.6f}",
                    "y_lidar_homography_m": f"{homography_xy[1]:.6f}",
                    "x_residual_true_m": f"{true_residual[0]:.6f}",
                    "y_residual_true_m": f"{true_residual[1]:.6f}",
                    "x_residual_pred_m": f"{pred[0]:.6f}",
                    "y_residual_pred_m": f"{pred[1]:.6f}",
                    "x_lidar_corrected_m": f"{corrected[0]:.6f}",
                    "y_lidar_corrected_m": f"{corrected[1]:.6f}",
                    "error_homography_cm": f"{np.linalg.norm(homography_xy - gt_xy) * 100.0:.3f}",
                    "error_corrected_cm": f"{np.linalg.norm(corrected - gt_xy) * 100.0:.3f}",
                }
            )
            writer.writerow(row)


def train(args: argparse.Namespace) -> int:
    joblib = require_joblib()
    data = load_training_data(args)
    train_idx, test_idx = split_indices(len(data["features"]), args.test_size, args.seed)
    estimator = build_estimator(args)
    estimator.fit(data["features"][train_idx], data["residuals"][train_idx])

    metrics = {
        "created_utc": utc_now(),
        "model": args.model,
        "feature_columns": list(DEFAULT_FEATURE_COLUMNS),
        "train": evaluate(estimator, data, train_idx),
        "test": evaluate(estimator, data, test_idx),
        "data_path": str(args.data),
        "calibration_path": str(args.calibration),
    }

    payload = {
        "schema_version": 1,
        "type": "bbox_homography_residual_model",
        "estimator": estimator,
        "feature_columns": list(DEFAULT_FEATURE_COLUMNS),
        "metadata": metrics,
    }
    args.output_model.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(payload, args.output_model)

    if args.metrics_json:
        args.metrics_json.parent.mkdir(parents=True, exist_ok=True)
        args.metrics_json.write_text(json.dumps(metrics, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    if args.predictions_csv:
        write_predictions_csv(args.predictions_csv, estimator, data)

    print(json.dumps({"output_model": str(args.output_model), "metrics": metrics}, ensure_ascii=True))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Train bbox residual correction for LiDAR-frame localization.")
    parser.add_argument("--data", type=Path, required=True, help="CSV with bbox columns and x_lidar_gt_m,y_lidar_gt_m")
    parser.add_argument("--calibration", type=Path, required=True, help="homography JSON")
    parser.add_argument("--output-model", type=Path, required=True, help="output .joblib model")
    parser.add_argument("--metrics-json", type=Path, default=None)
    parser.add_argument("--predictions-csv", type=Path, default=None)
    parser.add_argument("--bbox-format", choices=("auto", "yolo", "cxcywh_pixel", "xyxy", "xywh"), default="auto")
    parser.add_argument("--image-width", type=int, default=None, help="fallback if CSV has no image_width")
    parser.add_argument("--image-height", type=int, default=None, help="fallback if CSV has no image_height")
    parser.add_argument("--model", choices=("random_forest", "extra_trees", "poly_ridge"), default="random_forest")
    parser.add_argument("--n-estimators", type=int, default=500)
    parser.add_argument("--min-samples-leaf", type=int, default=2)
    parser.add_argument("--max-depth", type=int, default=0, help="0 means unlimited tree depth")
    parser.add_argument("--poly-degree", type=int, default=2)
    parser.add_argument("--ridge-alpha", type=float, default=1.0)
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    return parser


def main() -> int:
    return train(build_parser().parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
