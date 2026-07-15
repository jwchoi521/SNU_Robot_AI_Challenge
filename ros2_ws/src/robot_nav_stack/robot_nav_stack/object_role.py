from __future__ import annotations


def classify_object_role(
    object_type: str,
    fruit_kind: str,
    target_shape: str,
    target_fruit: str,
    no_fruit_class: str = "none",
) -> str:
    """Return one exclusive navigation role for a detected object."""

    object_type = _clean(object_type)
    fruit_kind = _clean(fruit_kind)
    target_shape = _clean(target_shape)
    target_fruit = _clean(target_fruit)
    no_fruit_class = _clean(no_fruit_class)

    if not target_shape and not target_fruit:
        return "unfiltered"

    is_cube = object_type == "cube_any"
    has_no_fruit = not fruit_kind or fruit_kind == no_fruit_class

    # cube_any as a shape target means a plain cube. A cube carrying another
    # fruit remains an obstacle unless that fruit is the configured target.
    if target_shape == "cube_any":
        shape_matches = is_cube and has_no_fruit
    else:
        shape_matches = bool(target_shape) and object_type == target_shape

    if target_fruit == no_fruit_class:
        fruit_matches = is_cube and has_no_fruit
    else:
        fruit_matches = (
            bool(target_fruit)
            and is_cube
            and not has_no_fruit
            and fruit_kind == target_fruit
        )

    return "target" if shape_matches or fruit_matches else "obstacle"


def _clean(value: str) -> str:
    return value.strip().lower()
