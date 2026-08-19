from __future__ import annotations

import math
import re
import struct
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_SRC = PACKAGE_ROOT.parent
PYTHON_NODE = PACKAGE_ROOT / "robot_nav_stack" / "object_localizer_node.py"
CPP_NODE = WORKSPACE_SRC / "robot_nav_stack_cpp" / "src" / "object_localizer_node.cpp"
PORTABLE_MODEL = PACKAGE_ROOT / "models" / "bbox_pose_anchor033.cppbin"
LAUNCH_FILE = PACKAGE_ROOT / "launch" / "robot_nav_stack.launch.py"


def _parameter_names(source: str, pattern: str) -> set[str]:
    return set(re.findall(pattern, source))


def test_cpp_localizer_declares_every_python_parameter() -> None:
    python_source = PYTHON_NODE.read_text(encoding="utf-8")
    cpp_source = CPP_NODE.read_text(encoding="utf-8")

    python_parameters = _parameter_names(
        python_source, r'declare_parameter\(\s*"([^"]+)"'
    )
    cpp_parameters = _parameter_names(
        cpp_source, r'declare_parameter<[^>]+>\("([^"]+)"'
    )

    assert cpp_parameters == python_parameters


def test_launch_defaults_both_localizers_to_cpp_with_python_fallback() -> None:
    launch_source = LAUNCH_FILE.read_text(encoding="utf-8-sig")

    assert '"object_localizer_package"' in launch_source
    assert 'default_value="robot_nav_stack_cpp"' in launch_source
    assert (
        launch_source.count(
            'package=LaunchConfiguration("object_localizer_package")'
        )
        == 2
    )


def _read_portable_model(path: Path):
    stream = path.open("rb")

    def read(fmt: str):
        record = struct.Struct("<" + fmt)
        data = stream.read(record.size)
        assert len(data) == record.size
        return record.unpack(data)

    def read_string() -> str:
        (size,) = read("I")
        return stream.read(size).decode("utf-8")

    magic, version = read("8sI")
    (anchor_alpha,) = read("d")
    homography = read("9d")
    (numeric_count,) = read("I")
    numeric = [(read_string(), *read("dd")) for _ in range(numeric_count)]
    (category_count,) = read("I")
    categories = [read_string() for _ in range(category_count)]
    feature_count, output_count, tree_count = read("III")
    trees = []
    for _ in range(tree_count):
        (node_count,) = read("I")
        trees.append([read("iiiddd") for _ in range(node_count)])
    assert stream.read(1) == b""
    stream.close()
    return {
        "magic": magic,
        "version": version,
        "anchor_alpha": anchor_alpha,
        "homography": homography,
        "numeric": numeric,
        "categories": categories,
        "feature_count": feature_count,
        "output_count": output_count,
        "trees": trees,
    }


def _predict(model, cx: float, cy: float, width: float, height: float, object_type: str):
    alpha = model["anchor_alpha"]
    h = model["homography"]
    anchor_x = cx
    anchor_y = cy + alpha * height
    denominator = h[6] * anchor_x + h[7] * anchor_y + h[8]
    base_x = (h[0] * anchor_x + h[1] * anchor_y + h[2]) / denominator
    base_y = (h[3] * anchor_x + h[4] * anchor_y + h[5]) / denominator
    safe_width = max(width, 1.0e-6)
    safe_height = max(height, 1.0e-6)
    area = max(safe_width * safe_height, 1.0e-6)
    raw = {
        "bbox_cx": cx,
        "bbox_cy": cy,
        "bbox_w": width,
        "bbox_h": height,
        "anchor_x": anchor_x,
        "anchor_y": anchor_y,
        "bbox_bottom_y": cy + 0.5 * height,
        "bbox_top_y": cy - 0.5 * height,
        "bbox_area": width * height,
        "aspect_ratio": safe_width / safe_height,
        "inv_w": 1.0 / safe_width,
        "inv_h": 1.0 / safe_height,
        "inv_sqrt_area": 1.0 / math.sqrt(area),
        "base_x": base_x,
        "base_y": base_y,
        "base_distance": math.hypot(base_x, base_y),
        "base_angle": math.degrees(math.atan2(base_y, base_x)),
    }
    features = [
        (raw[name] - mean) / scale for name, mean, scale in model["numeric"]
    ]
    features.extend(float(object_type == value) for value in model["categories"])

    residual_x = 0.0
    residual_y = 0.0
    for tree in model["trees"]:
        node_index = 0
        while tree[node_index][2] >= 0:
            left, right, feature, threshold, _, _ = tree[node_index]
            node_index = left if features[feature] <= threshold else right
        residual_x += tree[node_index][4]
        residual_y += tree[node_index][5]
    return (
        base_x + residual_x / len(model["trees"]),
        base_y + residual_y / len(model["trees"]),
    )


def test_portable_model_structure_and_predictions_match_sklearn_reference() -> None:
    model = _read_portable_model(PORTABLE_MODEL)
    assert model["magic"] == b"BNRFV1\0\0"
    assert model["version"] == 1
    assert len(model["numeric"]) == 17
    assert model["categories"] == [
        "cube_any",
        "dodecahedron",
        "icosahedron",
        "octahedron",
    ]
    assert model["feature_count"] == 21
    assert model["output_count"] == 2
    assert len(model["trees"]) == 400
    assert sum(len(tree) for tree in model["trees"]) == 39942

    cases = [
        ((640, 300, 100, 90, "cube_any"), (0.6155226278504429, -0.0008722261767970824)),
        ((156, 97, 43, 38, "octahedron"), (1.9539254122447558, 1.3899924815165847)),
        ((748, 85, 29, 28, "dodecahedron"), (2.359233960166696, -0.4004511453743163)),
        ((516, 83, 33, 34, "icosahedron"), (2.357710446813977, 0.4097078314779634)),
        ((300, 250, 50, 50, "unknown"), (0.7498605215806967, 0.33349593307549846)),
        ((1223, 148, 93, 61, "cube_any"), (1.223462779511652, -1.0266697309453052)),
    ]
    for inputs, expected in cases:
        predicted = _predict(model, *inputs)
        assert math.isclose(predicted[0], expected[0], rel_tol=0.0, abs_tol=1.0e-14)
        assert math.isclose(predicted[1], expected[1], rel_tol=0.0, abs_tol=1.0e-14)
