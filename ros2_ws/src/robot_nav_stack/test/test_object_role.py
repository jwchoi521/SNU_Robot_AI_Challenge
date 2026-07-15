from robot_nav_stack.object_role import classify_object_role


def _role(
    object_type: str,
    fruit_kind: str = "",
    target_shape: str = "",
    target_fruit: str = "",
) -> str:
    return classify_object_role(
        object_type=object_type,
        fruit_kind=fruit_kind,
        target_shape=target_shape,
        target_fruit=target_fruit,
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
