from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

from .yaw_response_model import model_to_json_dict


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Train a nonparametric yaw response model from calibration CSV files."
    )
    parser.add_argument("csv", nargs="+", help="CSV file(s) from yaw_calibration_collector")
    parser.add_argument("-o", "--output", required=True, help="output model JSON path")
    parser.add_argument("--min-count", type=int, default=8)
    parser.add_argument("--max-imu-age-sec", type=float, default=0.25)
    parser.add_argument("--min-abs-yaw-cmd", type=float, default=0.05)
    parser.add_argument("--candidate-step-rad-s", type=float, default=0.05)
    parser.add_argument("--max-abs-yaw-cmd-rad-s", type=float, default=4.0)
    parser.add_argument("--v-scale", type=float, default=0.05)
    parser.add_argument("--yaw-scale", type=float, default=0.35)
    args = parser.parse_args()

    grouped: dict[tuple[float, float], list[dict[str, float]]] = defaultdict(list)
    total_rows = 0
    used_rows = 0
    for csv_path in args.csv:
        with Path(csv_path).expanduser().open("r", newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                total_rows += 1
                parsed = _parse_row(row, args)
                if parsed is None:
                    continue
                key = (round(parsed["linear_x"], 4), round(parsed["yaw_cmd"], 4))
                grouped[key].append(parsed)
                used_rows += 1

    samples: list[dict[str, Any]] = []
    for (linear_x, yaw_cmd), rows in sorted(grouped.items()):
        if len(rows) < args.min_count:
            continue
        imu_values = [row["imu_wz"] for row in rows]
        joint_fl = _median_optional(row.get("joint_fl_rad_s") for row in rows)
        joint_fr = _median_optional(row.get("joint_fr_rad_s") for row in rows)
        joint_rl = _median_optional(row.get("joint_rl_rad_s") for row in rows)
        joint_rr = _median_optional(row.get("joint_rr_rad_s") for row in rows)
        actual_median = statistics.median(imu_values)
        actual_mean = statistics.fmean(imu_values)
        actual_std = statistics.pstdev(imu_values) if len(imu_values) > 1 else 0.0
        samples.append(
            {
                "linear_x": linear_x,
                "yaw_cmd": yaw_cmd,
                "actual_wz_median": actual_median,
                "actual_wz_mean": actual_mean,
                "actual_wz_std": actual_std,
                "count": len(rows),
                "joint_fl_rad_s_median": joint_fl,
                "joint_fr_rad_s_median": joint_fr,
                "joint_rl_rad_s_median": joint_rl,
                "joint_rr_rad_s_median": joint_rr,
            }
        )

    if not samples:
        raise SystemExit(
            "No usable calibration samples. Check enable_motion, /imu, and CSV valid_sample rows."
        )

    output = model_to_json_dict(
        samples,
        source_files=[str(Path(path).expanduser()) for path in args.csv],
        v_scale=args.v_scale,
        yaw_scale=args.yaw_scale,
        candidate_step_rad_s=args.candidate_step_rad_s,
        max_abs_yaw_cmd_rad_s=args.max_abs_yaw_cmd_rad_s,
    )
    output["training"] = {
        "total_rows": total_rows,
        "used_rows": used_rows,
        "sample_count": len(samples),
        "min_count": args.min_count,
        "max_imu_age_sec": args.max_imu_age_sec,
    }

    output_path = Path(args.output).expanduser()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2, sort_keys=True), encoding="utf-8")

    print(f"Wrote {output_path}")
    print(f"rows: total={total_rows} used={used_rows} grouped_samples={len(samples)}")
    print("largest observed responses:")
    for sample in sorted(samples, key=lambda item: abs(item["actual_wz_median"]), reverse=True)[:8]:
        print(
            f"  v={sample['linear_x']:+.3f} yaw_cmd={sample['yaw_cmd']:+.3f} "
            f"actual_wz={sample['actual_wz_median']:+.3f} n={sample['count']}"
        )


def _parse_row(row: dict[str, str], args: argparse.Namespace) -> dict[str, float] | None:
    if str(row.get("valid_sample", "")).strip() not in ("1", "true", "True"):
        return None
    linear_x = _float_or_none(row.get("linear_x"))
    yaw_cmd = _float_or_none(row.get("yaw_cmd"))
    imu_wz = _float_or_none(row.get("imu_wz"))
    imu_age = _float_or_none(row.get("imu_age_sec"))
    if linear_x is None or yaw_cmd is None or imu_wz is None:
        return None
    if imu_age is not None and imu_age > args.max_imu_age_sec:
        return None
    if abs(yaw_cmd) < args.min_abs_yaw_cmd:
        return None
    return {
        "linear_x": linear_x,
        "yaw_cmd": yaw_cmd,
        "imu_wz": imu_wz,
        "joint_fl_rad_s": _float_or_nan(row.get("joint_fl_rad_s")),
        "joint_fr_rad_s": _float_or_nan(row.get("joint_fr_rad_s")),
        "joint_rl_rad_s": _float_or_nan(row.get("joint_rl_rad_s")),
        "joint_rr_rad_s": _float_or_nan(row.get("joint_rr_rad_s")),
    }


def _float_or_none(value: str | None) -> float | None:
    try:
        result = float(value) if value not in (None, "") else math.nan
    except ValueError:
        return None
    return result if math.isfinite(result) else None


def _float_or_nan(value: str | None) -> float:
    parsed = _float_or_none(value)
    return parsed if parsed is not None else math.nan


def _median_optional(values) -> float | None:
    finite = [float(value) for value in values if math.isfinite(float(value))]
    if not finite:
        return None
    return statistics.median(finite)


if __name__ == "__main__":
    main()

