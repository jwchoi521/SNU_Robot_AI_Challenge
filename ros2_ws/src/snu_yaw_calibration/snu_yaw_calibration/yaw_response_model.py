from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class YawResponseSample:
    linear_x: float
    yaw_cmd: float
    actual_wz: float
    count: int = 1


class YawResponseModel:
    """Nonparametric yaw response model.

    The model predicts actual IMU yaw rate from the commanded linear speed and
    internal yaw command. It deliberately does not assume proportional response.
    """

    def __init__(
        self,
        samples: list[YawResponseSample],
        *,
        v_scale: float = 0.05,
        yaw_scale: float = 0.35,
        power: float = 2.0,
        candidate_step_rad_s: float = 0.05,
        max_abs_yaw_cmd_rad_s: float = 4.0,
    ) -> None:
        if not samples:
            raise ValueError("yaw response model needs at least one sample")
        self.samples = samples
        self.v_scale = max(float(v_scale), 1.0e-6)
        self.yaw_scale = max(float(yaw_scale), 1.0e-6)
        self.power = max(float(power), 0.5)
        self.candidate_step_rad_s = max(float(candidate_step_rad_s), 1.0e-3)
        self.max_abs_yaw_cmd_rad_s = max(float(max_abs_yaw_cmd_rad_s), 0.1)

    @classmethod
    def from_file(cls, path: str | Path) -> "YawResponseModel":
        data = json.loads(Path(path).expanduser().read_text(encoding="utf-8"))
        if data.get("model_type") != "local_idw_yaw_response_v1":
            raise ValueError(f"unsupported yaw response model type: {data.get('model_type')!r}")
        samples = [
            YawResponseSample(
                linear_x=float(item["linear_x"]),
                yaw_cmd=float(item["yaw_cmd"]),
                actual_wz=float(item["actual_wz_median"]),
                count=int(item.get("count", 1)),
            )
            for item in data.get("samples", [])
        ]
        params = data.get("prediction", {})
        return cls(
            samples,
            v_scale=float(params.get("v_scale", 0.05)),
            yaw_scale=float(params.get("yaw_scale", 0.35)),
            power=float(params.get("power", 2.0)),
            candidate_step_rad_s=float(params.get("candidate_step_rad_s", 0.05)),
            max_abs_yaw_cmd_rad_s=float(params.get("max_abs_yaw_cmd_rad_s", 4.0)),
        )

    def predict_actual_wz(self, linear_x: float, yaw_cmd: float) -> float:
        weighted_sum = 0.0
        weight_total = 0.0
        for sample in self.samples:
            dv = (linear_x - sample.linear_x) / self.v_scale
            dw = (yaw_cmd - sample.yaw_cmd) / self.yaw_scale
            distance = math.hypot(dv, dw)
            weight = max(sample.count, 1) / ((distance + 1.0e-6) ** self.power)
            weighted_sum += weight * sample.actual_wz
            weight_total += weight
        return weighted_sum / weight_total if weight_total > 0.0 else 0.0

    def choose_yaw_cmd(
        self,
        linear_x: float,
        target_wz: float,
        *,
        deadband_rad_s: float = 0.01,
        max_abs_yaw_cmd_rad_s: float | None = None,
    ) -> tuple[float, float, bool]:
        if abs(target_wz) <= deadband_rad_s:
            return 0.0, 0.0, True

        sign = 1.0 if target_wz > 0.0 else -1.0
        max_cmd = max_abs_yaw_cmd_rad_s or self.max_abs_yaw_cmd_rad_s
        max_cmd = max(abs(max_cmd), self.candidate_step_rad_s)

        best_cmd = sign * max_cmd
        best_pred = self.predict_actual_wz(linear_x, best_cmd)
        best_error = abs(target_wz - best_pred)

        steps = max(1, int(round(max_cmd / self.candidate_step_rad_s)))
        for index in range(steps + 1):
            magnitude = index * max_cmd / steps
            candidate = sign * magnitude
            predicted = self.predict_actual_wz(linear_x, candidate)
            error = abs(target_wz - predicted)
            if error < best_error - 1.0e-9:
                best_cmd = candidate
                best_pred = predicted
                best_error = error
            elif abs(error - best_error) <= 1.0e-9 and abs(candidate) < abs(best_cmd):
                best_cmd = candidate
                best_pred = predicted

        reachable = abs(target_wz - best_pred) <= max(0.05, abs(target_wz) * 0.20)
        return best_cmd, best_pred, reachable


def model_to_json_dict(
    samples: list[dict[str, Any]],
    *,
    source_files: list[str],
    v_scale: float,
    yaw_scale: float,
    candidate_step_rad_s: float,
    max_abs_yaw_cmd_rad_s: float,
) -> dict[str, Any]:
    return {
        "model_type": "local_idw_yaw_response_v1",
        "source_files": source_files,
        "prediction": {
            "v_scale": v_scale,
            "yaw_scale": yaw_scale,
            "power": 2.0,
            "candidate_step_rad_s": candidate_step_rad_s,
            "max_abs_yaw_cmd_rad_s": max_abs_yaw_cmd_rad_s,
        },
        "samples": samples,
    }

