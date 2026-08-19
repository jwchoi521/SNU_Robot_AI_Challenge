from __future__ import annotations

import math
from pathlib import Path

from .core import BBox, Detection, Pose2D


class HomographyResidualBboxEstimator:
    """Loads the trained bbox_pose_ml.py model.

    The model predicts object position in the lidar frame:

    bbox -> anchor point -> homography base x/y -> RF residual x/y -> final x/y
    """

    def __init__(self, model_path: str | Path) -> None:
        model_path = Path(model_path)
        if not model_path.exists():
            raise FileNotFoundError(f"bbox residual model not found: {model_path}")

        try:
            import joblib
        except ImportError as exc:
            raise RuntimeError(
                "joblib is required to load the bbox residual model. "
                "Install the Jetson Python requirements before launching robot_nav_stack."
            ) from exc

        self.payload = joblib.load(model_path)
        if self.payload.get("kind") != "homography_residual_v1":
            raise ValueError("Expected homography_residual_v1 model.")

    @staticmethod
    def _features(row: dict[str, float | str], alpha: float) -> dict[str, float | str]:
        eps = 1e-6
        w = max(float(row["bbox_w"]), eps)
        h = max(float(row["bbox_h"]), eps)
        area = max(w * h, eps)

        row["anchor_x"] = float(row["bbox_cx"])
        row["anchor_y"] = float(row["bbox_cy"]) + alpha * float(row["bbox_h"])
        row["bbox_bottom_y"] = float(row["bbox_cy"]) + 0.5 * float(row["bbox_h"])
        row["bbox_top_y"] = float(row["bbox_cy"]) - 0.5 * float(row["bbox_h"])
        row["bbox_area"] = float(row["bbox_w"]) * float(row["bbox_h"])
        row["aspect_ratio"] = w / h
        row["inv_w"] = 1.0 / w
        row["inv_h"] = 1.0 / h
        row["inv_sqrt_area"] = 1.0 / math.sqrt(area)
        return row

    @staticmethod
    def _apply_homography(homography, x: float, y: float) -> tuple[float, float]:
        try:
            import numpy as np
        except ImportError as exc:
            raise RuntimeError("numpy is required for homography projection.") from exc

        mapped = homography @ np.array([x, y, 1.0], dtype=float)
        if abs(mapped[2]) < 1e-12:
            raise ValueError("Homography mapped point near infinity.")
        return (float(mapped[0] / mapped[2]), float(mapped[1] / mapped[2]))

    def predict_lidar_pose(self, detection: Detection) -> Pose2D:
        try:
            import pandas as pd
        except ImportError as exc:
            raise RuntimeError("pandas is required for bbox residual inference.") from exc

        bbox: BBox = detection.bbox
        row: dict[str, float | str] = {
            "bbox_cx": bbox.cx,
            "bbox_cy": bbox.cy,
            "bbox_w": bbox.w,
            "bbox_h": bbox.h,
            "object_type": detection.object_type,
        }
        row = self._features(row, self.payload["anchor_alpha"])
        base_x, base_y = self._apply_homography(
            self.payload["homography"],
            float(row["anchor_x"]),
            float(row["anchor_y"]),
        )
        row["base_x"] = base_x
        row["base_y"] = base_y
        row["base_distance"] = math.hypot(base_x, base_y)
        row["base_angle"] = math.degrees(math.atan2(base_y, base_x))

        sample = pd.DataFrame([row])
        x_residual, y_residual = self.payload["residual_model"].predict(
            sample[self.payload["residual_feature_columns"]]
        )[0]
        return Pose2D(x=base_x + float(x_residual), y=base_y + float(y_residual))
