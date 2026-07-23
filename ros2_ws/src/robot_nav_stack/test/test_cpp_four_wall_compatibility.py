from __future__ import annotations

import re
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_SRC = PACKAGE_ROOT.parent
PYTHON_NODE = PACKAGE_ROOT / "robot_nav_stack" / "four_wall_localizer_node.py"
CPP_NODE = (
    WORKSPACE_SRC
    / "robot_nav_stack_cpp"
    / "src"
    / "four_wall_localizer_node.cpp"
)
LAUNCH_FILE = PACKAGE_ROOT / "launch" / "robot_nav_stack.launch.py"


def _parameter_names(source: str, pattern: str) -> set[str]:
    return set(re.findall(pattern, source))


def test_cpp_localizer_declares_every_python_parameter() -> None:
    python_source = PYTHON_NODE.read_text(encoding="utf-8")
    cpp_source = CPP_NODE.read_text(encoding="utf-8")

    python_parameters = _parameter_names(
        python_source, r'declare_parameter\("([^"]+)"'
    )
    cpp_parameters = _parameter_names(
        cpp_source, r'declare_parameter<[^>]+>\("([^"]+)"'
    )

    assert cpp_parameters == python_parameters


def test_cpp_localizer_preserves_status_contract() -> None:
    cpp_source = CPP_NODE.read_text(encoding="utf-8")
    expected_fields = {
        "ok",
        "reason",
        "scan_reference_stamp",
        "odom_samples",
        "required_by",
        "base_frame",
        "lidar_frame",
        "rays",
        "motion_dropped_rays",
        "used_rays",
        "x",
        "y",
        "yaw_deg",
        "imu_yaw_deg",
        "imu_yaw_prior_used",
        "scan_start_stamp",
        "scan_duration_sec",
        "odom_aligned_to_scan",
        "lidar_deskew_enabled",
        "lidar_deskew_applied",
        "deskewed_rays",
        "lidar_extrinsics_source",
        "arena_origin",
        "tf_mode",
        "transform_tolerance_sec",
        "arena_bounds",
        "global_seed_search_on_first_scan",
        "symmetry_seeds_enabled",
        "pose_prior_active",
        "range_score",
        "prior_score",
        "total_score",
        "wall_counts",
        "visible_walls",
        "range_score_ratio_best_two",
        "symmetry_resolved_by_prior",
        "ambiguous_without_prior",
        "candidate_count",
    }

    for field in expected_fields:
        assert f'\\"{field}\\"' in cpp_source


def test_launch_defaults_to_cpp_with_python_fallback() -> None:
    launch_source = LAUNCH_FILE.read_text(encoding="utf-8-sig")

    assert '"four_wall_localizer_package"' in launch_source
    assert 'default_value="robot_nav_stack_cpp"' in launch_source
    assert 'package=LaunchConfiguration("four_wall_localizer_package")' in launch_source
