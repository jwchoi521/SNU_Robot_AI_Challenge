from robot_nav_stack.object_role import classify_object_role


def _role(
    object_type: str,
    fruit_kind: str = "",
    target_shape: str = "",
    target_fruit: str = "",
    detection_confidence: float = 1.0,
    target_min_confidence: float = 0.0,
) -> str:
    return classify_object_role(
        object_type=object_type,
        fruit_kind=fruit_kind,
        target_shape=target_shape,
        target_fruit=target_fruit,
        detection_confidence=detection_confidence,
        target_min_confidence=target_min_confidence,
    )


def test_apple_target_is_never_an_obstacle() -> None:
    assert _role("cube_any", "apple", target_fruit="apple") == "target"


def test_non_target_fruit_and_shapes_are_obstacles() -> None:
    assert _role("cube_any", "orange", target_fruit="apple") == "obstacle"
    assert _role("octahedron", target_fruit="apple") == "obstacle"


def test_shape_and_fruit_targets_are_combined_with_or() -> None:
    assert _role("octahedron", target_shape="octahedron", target_fruit="apple") == "target"
    assert _role("cube_any", "apple", target_shape="octahedron", target_fruit="apple") == "target"
    assert _role("dodecahedron", target_shape="octahedron", target_fruit="apple") == "obstacle"


def test_cube_any_shape_target_accepts_plain_cube_but_not_other_fruit() -> None:
    assert _role("cube_any", "none", target_shape="cube_any", target_fruit="apple") == "target"
    assert _role("cube_any", "orange", target_shape="cube_any", target_fruit="apple") == "obstacle"


def test_missing_target_configuration_is_not_assigned_to_both_roles() -> None:
    assert _role("cube_any", "apple") == "unfiltered"


def test_target_min_confidence_demotes_weak_target_to_obstacle() -> None:
    assert (
        _role(
            "octahedron",
            target_shape="octahedron",
            detection_confidence=0.75,
            target_min_confidence=0.9,
        )
        == "obstacle"
    )
    assert (
        _role(
            "octahedron",
            target_shape="octahedron",
            detection_confidence=0.95,
            target_min_confidence=0.9,
        )
        == "target"
    )


def test_target_min_confidence_applies_to_fruit_targets() -> None:
    assert (
        _role(
            "cube_any",
            "orange",
            target_fruit="orange",
            detection_confidence=0.7,
            target_min_confidence=0.9,
        )
        == "obstacle"
    )
    assert (
        _role(
            "cube_any",
            "orange",
            target_fruit="orange",
            detection_confidence=0.92,
            target_min_confidence=0.9,
        )
        == "target"
    )
