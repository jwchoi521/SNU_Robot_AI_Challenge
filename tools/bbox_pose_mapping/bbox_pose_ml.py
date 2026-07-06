"""
Two-stage bbox pose model with a homography base.

Stage 1:
    Estimate a homography from image ground-contact pixels to robot-frame
    ground coordinates.

Stage 2:
    Use object bbox features to learn the x/y residual left by the homography.

Ground CSV columns, preferred:
    anchor_x, anchor_y, x_robot, y_robot

Ground CSV columns, also accepted:
    anchor_x, anchor_y, distance, angle

Object CSV columns, preferred:
    bbox_cx, bbox_cy, bbox_w, bbox_h, object_type, x_robot, y_robot

Object CSV columns, also accepted:
    bbox_cx, bbox_cy, bbox_w, bbox_h, object_type, distance, angle

You may also use bbox corner columns instead of center/size:
    x1, y1, x2, y2, object_type, ...

Examples:
    python bbox_pose_ml.py train --ground-data ground.csv --object-data objects.csv --model bbox_pose_model.joblib
    python bbox_pose_ml.py predict --model bbox_pose_model.joblib --bbox-cx 322 --bbox-cy 241 --bbox-w 80 --bbox-h 150 --object-type bottle

Install dependencies:
    pip install pandas scikit-learn joblib numpy
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Literal

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


AngleUnit = Literal["deg", "rad"]

XY_TARGET_COLUMNS = ["x_robot", "y_robot"]
POLAR_TARGET_COLUMNS = ["distance", "angle"]
GROUND_FEATURE_COLUMNS = ["anchor_x", "anchor_y"]
OBJECT_REQUIRED_COLUMNS = ["bbox_cx", "bbox_cy", "bbox_w", "bbox_h", "object_type"]
RESIDUAL_TARGET_COLUMNS = ["x_residual", "y_residual"]
RESIDUAL_NUMERIC_FEATURES = [
    "bbox_cx",
    "bbox_cy",
    "bbox_w",
    "bbox_h",
    "anchor_x",
    "anchor_y",
    "bbox_bottom_y",
    "bbox_top_y",
    "bbox_area",
    "aspect_ratio",
    "inv_w",
    "inv_h",
    "inv_sqrt_area",
    "base_x",
    "base_y",
    "base_distance",
    "base_angle",
]
RESIDUAL_CATEGORICAL_FEATURES = ["object_type"]
RESIDUAL_FEATURE_COLUMNS = RESIDUAL_NUMERIC_FEATURES + RESIDUAL_CATEGORICAL_FEATURES


def require_columns(df: pd.DataFrame, columns: list[str], label: str) -> None:
    missing = sorted(set(columns) - set(df.columns))
    if missing:
        raise ValueError(f"{label} is missing required columns: {missing}")


def normalize_angle_unit(unit: str) -> AngleUnit:
    if unit in {"deg", "degree", "degrees"}:
        return "deg"
    if unit in {"rad", "radian", "radians"}:
        return "rad"
    raise ValueError("--angle-unit must be 'deg' or 'rad'")


def angle_to_rad(angle: pd.Series | float, unit: AngleUnit):
    if unit == "deg":
        return np.deg2rad(angle)
    return angle


def angle_from_rad(angle_rad, unit: AngleUnit):
    if unit == "deg":
        return np.rad2deg(angle_rad)
    return angle_rad


def add_xy_targets(df: pd.DataFrame, label: str, angle_unit: AngleUnit) -> pd.DataFrame:
    df = df.copy()
    if set(XY_TARGET_COLUMNS).issubset(df.columns):
        return df

    require_columns(df, POLAR_TARGET_COLUMNS, label)
    angle_rad = angle_to_rad(df["angle"], angle_unit)
    df["x_robot"] = df["distance"] * np.cos(angle_rad)
    df["y_robot"] = df["distance"] * np.sin(angle_rad)
    return df


def add_polar_columns(df: pd.DataFrame, x_col: str, y_col: str, prefix: str, angle_unit: AngleUnit) -> pd.DataFrame:
    df = df.copy()
    x = df[x_col]
    y = df[y_col]
    df[f"{prefix}_distance"] = np.sqrt(x * x + y * y)
    df[f"{prefix}_angle"] = angle_from_rad(np.arctan2(y, x), angle_unit)
    return df


def wrap_angle_error(predicted, actual, unit: AngleUnit):
    if unit == "deg":
        return (predicted - actual + 180.0) % 360.0 - 180.0
    return (predicted - actual + math.pi) % (2.0 * math.pi) - math.pi


def load_ground_dataset(csv_path: Path, angle_unit: AngleUnit) -> pd.DataFrame:
    df = pd.read_csv(csv_path)

    coordinate_aliases = [
        ("anchor_x", "anchor_y"),
        ("point_x", "point_y"),
        ("pixel_x", "pixel_y"),
        ("u", "v"),
    ]
    for x_col, y_col in coordinate_aliases:
        if x_col in df.columns and y_col in df.columns:
            df = df.rename(columns={x_col: "anchor_x", y_col: "anchor_y"})
            break

    require_columns(df, GROUND_FEATURE_COLUMNS, "ground dataset")
    df = add_xy_targets(df, "ground dataset", angle_unit)
    return df.dropna(subset=GROUND_FEATURE_COLUMNS + XY_TARGET_COLUMNS).copy()


def load_object_dataset(csv_path: Path, angle_unit: AngleUnit) -> pd.DataFrame:
    df = pd.read_csv(csv_path)

    center_size_columns = ["bbox_cx", "bbox_cy", "bbox_w", "bbox_h"]
    corner_columns = ["x1", "y1", "x2", "y2"]
    if not set(center_size_columns).issubset(df.columns):
        if set(corner_columns).issubset(df.columns):
            df = df.copy()
            df["bbox_cx"] = (df["x1"] + df["x2"]) / 2.0
            df["bbox_cy"] = (df["y1"] + df["y2"]) / 2.0
            df["bbox_w"] = df["x2"] - df["x1"]
            df["bbox_h"] = df["y2"] - df["y1"]
        else:
            require_columns(df, center_size_columns, "object dataset")

    require_columns(df, OBJECT_REQUIRED_COLUMNS, "object dataset")
    df = add_xy_targets(df, "object dataset", angle_unit)
    df = df.dropna(subset=OBJECT_REQUIRED_COLUMNS + XY_TARGET_COLUMNS).copy()
    df["object_type"] = df["object_type"].astype(str)
    return df


def add_bbox_features(df: pd.DataFrame, anchor_alpha: float) -> pd.DataFrame:
    df = df.copy()
    eps = 1e-6
    safe_w = df["bbox_w"].clip(lower=eps)
    safe_h = df["bbox_h"].clip(lower=eps)
    area = (safe_w * safe_h).clip(lower=eps)

    df["anchor_x"] = df["bbox_cx"]
    df["anchor_y"] = df["bbox_cy"] + anchor_alpha * df["bbox_h"]
    df["bbox_bottom_y"] = df["bbox_cy"] + 0.5 * df["bbox_h"]
    df["bbox_top_y"] = df["bbox_cy"] - 0.5 * df["bbox_h"]
    df["bbox_area"] = df["bbox_w"] * df["bbox_h"]
    df["aspect_ratio"] = safe_w / safe_h
    df["inv_w"] = 1.0 / safe_w
    df["inv_h"] = 1.0 / safe_h
    df["inv_sqrt_area"] = 1.0 / area.pow(0.5)
    return df


def normalize_points(points: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    centroid = points.mean(axis=0)
    centered = points - centroid
    mean_dist = np.sqrt((centered * centered).sum(axis=1)).mean()
    if mean_dist < 1e-12:
        raise ValueError("Cannot estimate homography from collapsed points.")

    scale = math.sqrt(2.0) / mean_dist
    transform = np.array(
        [
            [scale, 0.0, -scale * centroid[0]],
            [0.0, scale, -scale * centroid[1]],
            [0.0, 0.0, 1.0],
        ]
    )
    hom = np.column_stack([points, np.ones(len(points))])
    normalized = (transform @ hom.T).T[:, :2]
    return normalized, transform


def estimate_homography(src_points: np.ndarray, dst_points: np.ndarray) -> np.ndarray:
    if len(src_points) < 4:
        raise ValueError("Homography needs at least 4 ground points.")

    src_norm, src_transform = normalize_points(src_points)
    dst_norm, dst_transform = normalize_points(dst_points)

    rows = []
    for (u, v), (x, y) in zip(src_norm, dst_norm):
        rows.append([-u, -v, -1.0, 0.0, 0.0, 0.0, u * x, v * x, x])
        rows.append([0.0, 0.0, 0.0, -u, -v, -1.0, u * y, v * y, y])

    _, _, vh = np.linalg.svd(np.asarray(rows))
    homography_norm = vh[-1].reshape(3, 3)
    homography = np.linalg.inv(dst_transform) @ homography_norm @ src_transform

    if abs(homography[2, 2]) > 1e-12:
        homography = homography / homography[2, 2]
    else:
        homography = homography / np.linalg.norm(homography)

    return homography


def apply_homography(homography: np.ndarray, points: np.ndarray) -> np.ndarray:
    hom = np.column_stack([points, np.ones(len(points))])
    mapped = (homography @ hom.T).T
    denom = mapped[:, 2]
    if np.any(np.abs(denom) < 1e-12):
        raise ValueError("Homography produced points near infinity.")
    return mapped[:, :2] / denom[:, None]


def build_residual_model(
    n_estimators: int,
    max_depth: int | None,
    min_samples_leaf: int,
) -> Pipeline:
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), RESIDUAL_NUMERIC_FEATURES),
            (
                "cat",
                OneHotEncoder(handle_unknown="ignore"),
                RESIDUAL_CATEGORICAL_FEATURES,
            ),
        ]
    )

    regressor = RandomForestRegressor(
        n_estimators=n_estimators,
        max_depth=max_depth,
        min_samples_leaf=min_samples_leaf,
        random_state=42,
        n_jobs=-1,
    )

    return Pipeline(
        steps=[
            ("preprocess", preprocessor),
            ("model", regressor),
        ]
    )


def add_base_predictions(df: pd.DataFrame, homography: np.ndarray, angle_unit: AngleUnit) -> pd.DataFrame:
    df = df.copy()
    base_xy = apply_homography(homography, df[GROUND_FEATURE_COLUMNS].to_numpy(dtype=float))
    df["base_x"] = base_xy[:, 0]
    df["base_y"] = base_xy[:, 1]
    df = add_polar_columns(df, "base_x", "base_y", "base", angle_unit)
    return df


def make_xy_predictions(df: pd.DataFrame, residual_predictions: np.ndarray) -> pd.DataFrame:
    result = df.copy()
    result["pred_x"] = result["base_x"] + residual_predictions[:, 0]
    result["pred_y"] = result["base_y"] + residual_predictions[:, 1]
    return result


def metric_block(df: pd.DataFrame, prefix: str, angle_unit: AngleUnit) -> dict[str, float | int | None]:
    x_pred = df[f"{prefix}_x"]
    y_pred = df[f"{prefix}_y"]
    dist_pred = df[f"{prefix}_distance"]
    angle_pred = df[f"{prefix}_angle"]
    angle_error = wrap_angle_error(angle_pred, df["angle"], angle_unit)

    xy_sq_error = (x_pred - df["x_robot"]) ** 2 + (y_pred - df["y_robot"]) ** 2
    metrics: dict[str, float | int | None] = {
        f"{prefix}_x_mae": float(mean_absolute_error(df["x_robot"], x_pred)),
        f"{prefix}_y_mae": float(mean_absolute_error(df["y_robot"], y_pred)),
        f"{prefix}_xy_rmse": float(math.sqrt(float(xy_sq_error.mean()))),
        f"{prefix}_distance_mae": float(mean_absolute_error(df["distance"], dist_pred)),
        f"{prefix}_angle_mae": float(np.abs(angle_error).mean()),
        f"{prefix}_angle_rmse": float(math.sqrt(float((angle_error * angle_error).mean()))),
        f"{prefix}_rows": int(len(df)),
    }
    if len(df) >= 2:
        metrics[f"{prefix}_x_r2"] = float(r2_score(df["x_robot"], x_pred))
        metrics[f"{prefix}_y_r2"] = float(r2_score(df["y_robot"], y_pred))
    else:
        metrics[f"{prefix}_x_r2"] = None
        metrics[f"{prefix}_y_r2"] = None
    return metrics


def ensure_polar_targets(df: pd.DataFrame, angle_unit: AngleUnit) -> pd.DataFrame:
    df = df.copy()
    if not set(POLAR_TARGET_COLUMNS).issubset(df.columns):
        df = add_polar_columns(df, "x_robot", "y_robot", "target", angle_unit)
        df["distance"] = df["target_distance"]
        df["angle"] = df["target_angle"]
        df = df.drop(columns=["target_distance", "target_angle"])
    return df


def train(
    ground_data_path: Path,
    object_data_path: Path,
    model_path: Path,
    test_size: float,
    anchor_alpha: float,
    angle_unit_arg: str,
    residual_trees: int,
    residual_max_depth: int | None,
    residual_min_samples_leaf: int,
) -> None:
    angle_unit = normalize_angle_unit(angle_unit_arg)
    ground_df = load_ground_dataset(ground_data_path, angle_unit)
    object_df = load_object_dataset(object_data_path, angle_unit)
    object_df = ensure_polar_targets(add_bbox_features(object_df, anchor_alpha), angle_unit)

    homography = estimate_homography(
        ground_df[GROUND_FEATURE_COLUMNS].to_numpy(dtype=float),
        ground_df[XY_TARGET_COLUMNS].to_numpy(dtype=float),
    )

    object_df = add_base_predictions(object_df, homography, angle_unit)
    residual_targets = pd.DataFrame(
        {
            "x_residual": object_df["x_robot"] - object_df["base_x"],
            "y_residual": object_df["y_robot"] - object_df["base_y"],
        },
        index=object_df.index,
    )

    if not 0.0 <= test_size < 1.0:
        raise ValueError("--test-size must be >= 0.0 and < 1.0")

    if test_size > 0.0 and len(object_df) >= 2:
        train_idx, test_idx = train_test_split(
            object_df.index,
            test_size=test_size,
            random_state=42,
            shuffle=True,
        )
    else:
        train_idx = object_df.index
        test_idx = object_df.index

    residual_model = build_residual_model(
        residual_trees,
        residual_max_depth,
        residual_min_samples_leaf,
    )
    residual_model.fit(
        object_df.loc[train_idx, RESIDUAL_FEATURE_COLUMNS],
        residual_targets.loc[train_idx, RESIDUAL_TARGET_COLUMNS],
    )

    eval_df = object_df.loc[test_idx].copy()
    residual_predictions = residual_model.predict(eval_df[RESIDUAL_FEATURE_COLUMNS])
    eval_df = make_xy_predictions(eval_df, residual_predictions)
    eval_df = add_polar_columns(eval_df, "pred_x", "pred_y", "pred", angle_unit)

    metrics = {
        "ground_rows": int(len(ground_df)),
        "object_train_rows": int(len(train_idx)),
        "object_test_rows": int(len(test_idx)),
        "anchor_alpha": float(anchor_alpha),
        "angle_unit": angle_unit,
        "residual_trees": int(residual_trees),
        "residual_max_depth": residual_max_depth,
        "residual_min_samples_leaf": int(residual_min_samples_leaf),
        **metric_block(eval_df.rename(columns={"base_x": "base_x", "base_y": "base_y"}), "base", angle_unit),
        **metric_block(eval_df, "pred", angle_unit),
    }

    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "kind": "homography_residual_v1",
            "homography": homography,
            "residual_model": residual_model,
            "anchor_alpha": anchor_alpha,
            "angle_unit": angle_unit,
            "base_feature_columns": GROUND_FEATURE_COLUMNS,
            "residual_feature_columns": RESIDUAL_FEATURE_COLUMNS,
            "target_columns": XY_TARGET_COLUMNS,
            "metrics": metrics,
        },
        model_path,
    )

    print(json.dumps(metrics, indent=2))
    print(f"Saved model: {model_path}")


def predict(
    model_path: Path,
    bbox_cx: float,
    bbox_cy: float,
    bbox_w: float,
    bbox_h: float,
    object_type: str,
) -> None:
    payload = joblib.load(model_path)
    if payload.get("kind") != "homography_residual_v1":
        raise ValueError("Unsupported model file. Train a new homography_residual_v1 model first.")

    angle_unit: AngleUnit = payload["angle_unit"]
    sample = pd.DataFrame(
        [
            {
                "bbox_cx": bbox_cx,
                "bbox_cy": bbox_cy,
                "bbox_w": bbox_w,
                "bbox_h": bbox_h,
                "object_type": object_type,
            }
        ]
    )
    sample = add_bbox_features(sample, payload["anchor_alpha"])
    sample = add_base_predictions(sample, payload["homography"], angle_unit)

    x_residual, y_residual = payload["residual_model"].predict(
        sample[RESIDUAL_FEATURE_COLUMNS]
    )[0]
    pred_x = float(sample.loc[0, "base_x"] + x_residual)
    pred_y = float(sample.loc[0, "base_y"] + y_residual)
    distance = math.sqrt(pred_x * pred_x + pred_y * pred_y)
    angle = float(angle_from_rad(math.atan2(pred_y, pred_x), angle_unit))

    result = {
        "x_robot": pred_x,
        "y_robot": pred_y,
        "distance": distance,
        "angle": angle,
        "base_x": float(sample.loc[0, "base_x"]),
        "base_y": float(sample.loc[0, "base_y"]),
        "base_distance": float(sample.loc[0, "base_distance"]),
        "base_angle": float(sample.loc[0, "base_angle"]),
        "x_residual": float(x_residual),
        "y_residual": float(y_residual),
        "anchor_x": float(sample.loc[0, "anchor_x"]),
        "anchor_y": float(sample.loc[0, "anchor_y"]),
        "angle_unit": angle_unit,
    }
    print(json.dumps(result, indent=2))


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Homography base + bbox residual pose model"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    train_parser = subparsers.add_parser("train")
    train_parser.add_argument("--ground-data", required=True, type=Path)
    train_parser.add_argument("--object-data", required=True, type=Path)
    train_parser.add_argument("--model", required=True, type=Path)
    train_parser.add_argument("--test-size", default=0.2, type=float)
    train_parser.add_argument(
        "--anchor-alpha",
        default=0.5,
        type=float,
        help="anchor_y = bbox_cy + anchor_alpha * bbox_h. 0.5 means bbox bottom.",
    )
    train_parser.add_argument(
        "--angle-unit",
        default="deg",
        choices=["deg", "rad"],
        help="Unit used when CSV contains distance/angle instead of x_robot/y_robot.",
    )
    train_parser.add_argument("--residual-trees", default=100, type=int)
    train_parser.add_argument("--residual-max-depth", default=3, type=int)
    train_parser.add_argument("--residual-min-samples-leaf", default=2, type=int)

    predict_parser = subparsers.add_parser("predict")
    predict_parser.add_argument("--model", required=True, type=Path)
    predict_parser.add_argument("--bbox-cx", required=True, type=float)
    predict_parser.add_argument("--bbox-cy", required=True, type=float)
    predict_parser.add_argument("--bbox-w", required=True, type=float)
    predict_parser.add_argument("--bbox-h", required=True, type=float)
    predict_parser.add_argument("--object-type", required=True)

    return parser


def main() -> None:
    args = make_parser().parse_args()

    if args.command == "train":
        train(
            args.ground_data,
            args.object_data,
            args.model,
            args.test_size,
            args.anchor_alpha,
            args.angle_unit,
            args.residual_trees,
            args.residual_max_depth,
            args.residual_min_samples_leaf,
        )
    elif args.command == "predict":
        predict(
            args.model,
            args.bbox_cx,
            args.bbox_cy,
            args.bbox_w,
            args.bbox_h,
            args.object_type,
        )


if __name__ == "__main__":
    main()
