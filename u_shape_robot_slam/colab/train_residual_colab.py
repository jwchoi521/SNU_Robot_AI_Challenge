"""Minimal Colab entrypoint for residual model training.

Usage in Colab after uploading the repository folder to Drive:

    %cd /content/drive/MyDrive/AI_robot_challenge
    !pip install -q -r u_shape_robot_slam/requirements.txt
    !python u_shape_robot_slam/train_residual_model.py \
      --data u_shape_robot_slam/data/residual_samples.csv \
      --calibration u_shape_robot_slam/calibration/homography_lidar.json \
      --output-model u_shape_robot_slam/models/residual_lidar_corrector.joblib \
      --metrics-json u_shape_robot_slam/models/residual_metrics.json \
      --predictions-csv u_shape_robot_slam/models/residual_predictions.csv
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
PROJECT_DIR = THIS_DIR.parent
sys.path.insert(0, str(PROJECT_DIR))

from train_residual_model import train  # noqa: E402


def main() -> int:
    default_root = Path("u_shape_robot_slam")
    args = argparse.Namespace(
        data=default_root / "data" / "residual_samples.csv",
        calibration=default_root / "calibration" / "homography_lidar.json",
        output_model=default_root / "models" / "residual_lidar_corrector.joblib",
        metrics_json=default_root / "models" / "residual_metrics.json",
        predictions_csv=default_root / "models" / "residual_predictions.csv",
        bbox_format="auto",
        image_width=None,
        image_height=None,
        model="random_forest",
        n_estimators=500,
        min_samples_leaf=2,
        max_depth=0,
        poly_degree=2,
        ridge_alpha=1.0,
        test_size=0.2,
        seed=42,
    )
    return train(args)


if __name__ == "__main__":
    raise SystemExit(main())
