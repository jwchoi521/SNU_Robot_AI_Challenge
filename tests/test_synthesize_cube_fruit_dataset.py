from __future__ import annotations

import random
from pathlib import Path

import numpy as np

from scripts.synthesize_cube_fruit_dataset import (
    EdgeSegment,
    ManualFace,
    _assign_cubes_to_output_splits,
    _candidate_quads_from_edge_segments,
    _decoded_image_to_rgb_on_white,
    _face_method_label,
    _fruit_source_label,
    _is_face_like_quad,
    _manual_face_quads,
    _select_sticker_face_quads,
    build_parser,
    apply_lighting_augmentation,
    order_quad_points,
    random_face_quad,
    sample_sticker_quad,
)


def _quad_area(quad: np.ndarray) -> float:
    x_values = quad[:, 0]
    y_values = quad[:, 1]
    return float(
        0.5
        * abs(
            np.dot(x_values, np.roll(y_values, -1))
            - np.dot(y_values, np.roll(x_values, -1))
        )
    )


def test_order_quad_points_returns_clockwise_top_left_first() -> None:
    points = np.array(
        [
            [10.0, 30.0],
            [40.0, 10.0],
            [12.0, 8.0],
            [43.0, 35.0],
        ],
        dtype=np.float32,
    )

    ordered = order_quad_points(points)

    assert ordered.tolist() == [
        [12.0, 8.0],
        [40.0, 10.0],
        [43.0, 35.0],
        [10.0, 30.0],
    ]


def test_order_quad_points_handles_diamond_without_duplicate_points() -> None:
    points = np.array(
        [
            [50.0, 8.0],
            [88.0, 50.0],
            [50.0, 92.0],
            [12.0, 50.0],
        ],
        dtype=np.float32,
    )

    ordered = order_quad_points(points)

    assert ordered.shape == (4, 2)
    assert len({tuple(point) for point in ordered.tolist()}) == 4
    np.testing.assert_allclose(
        ordered,
        np.array(
            [
                [50.0, 8.0],
                [88.0, 50.0],
                [50.0, 92.0],
                [12.0, 50.0],
            ],
            dtype=np.float32,
        ),
    )


def test_sample_sticker_quad_covers_entire_face_by_default() -> None:
    rng = random.Random(7)
    face_quad = np.array(
        [
            [10.0, 10.0],
            [90.0, 20.0],
            [80.0, 90.0],
            [20.0, 80.0],
        ],
        dtype=np.float32,
    )

    sticker_quad = sample_sticker_quad(face_quad, rng)

    assert sticker_quad.shape == (4, 2)
    np.testing.assert_allclose(sticker_quad, face_quad)
    assert _quad_area(sticker_quad) == _quad_area(face_quad)


def test_sample_sticker_quad_can_use_explicit_inset() -> None:
    rng = random.Random(7)
    face_quad = np.array(
        [
            [10.0, 10.0],
            [90.0, 20.0],
            [80.0, 90.0],
            [20.0, 80.0],
        ],
        dtype=np.float32,
    )

    sticker_quad = sample_sticker_quad(
        face_quad,
        rng,
        inset_min=0.05,
        inset_max=0.05,
    )

    assert sticker_quad.shape == (4, 2)
    assert sticker_quad[:, 0].min() >= face_quad[:, 0].min()
    assert sticker_quad[:, 0].max() <= face_quad[:, 0].max()
    assert sticker_quad[:, 1].min() >= face_quad[:, 1].min()
    assert sticker_quad[:, 1].max() <= face_quad[:, 1].max()
    assert 0.7 < _quad_area(sticker_quad) / _quad_area(face_quad) < 1.0


def test_sample_sticker_quad_can_scale_to_cover_face_edges() -> None:
    rng = random.Random(7)
    face_quad = np.array(
        [
            [20.0, 20.0],
            [80.0, 20.0],
            [80.0, 80.0],
            [20.0, 80.0],
        ],
        dtype=np.float32,
    )

    sticker_quad = sample_sticker_quad(
        face_quad,
        rng,
        fill_scale=1.1,
        image_width=100,
        image_height=100,
    )

    assert sticker_quad.tolist() == [
        [17.0, 17.0],
        [83.0, 17.0],
        [83.0, 83.0],
        [17.0, 83.0],
    ]


def test_random_face_quad_uses_crop_bounds() -> None:
    quad = random_face_quad(width=120, height=80, rng=random.Random(11))

    assert quad.shape == (4, 2)
    assert quad[:, 0].min() >= 0
    assert quad[:, 0].max() <= 120
    assert quad[:, 1].min() >= 0
    assert quad[:, 1].max() <= 80


def test_decoded_transparent_image_is_composited_on_white() -> None:
    bgra = np.array(
        [
            [
                [0, 0, 0, 0],
                [0, 0, 255, 255],
                [255, 0, 0, 128],
            ]
        ],
        dtype=np.uint8,
    )

    rgb = _decoded_image_to_rgb_on_white(bgra)

    assert rgb.tolist() == [
        [
            [255, 255, 255],
            [255, 0, 0],
            [127, 127, 255],
        ]
    ]


def test_lighting_augmentation_is_noop_by_default() -> None:
    image = np.full((16, 18, 3), 120, dtype=np.uint8)

    augmented = apply_lighting_augmentation(image, random.Random(13))

    np.testing.assert_array_equal(augmented, image)


def test_lighting_augmentation_can_darken_with_shadow() -> None:
    image = np.full((48, 64, 3), 180, dtype=np.uint8)

    augmented = apply_lighting_augmentation(
        image,
        random.Random(13),
        shadow_prob=1.0,
        shadow_min_factor=0.5,
        shadow_max_factor=0.5,
        shadow_blur_ratio=0.1,
    )

    assert augmented.mean() < image.mean()
    assert augmented.min() >= 0
    assert augmented.max() <= image.max()


def test_lighting_augmentation_keeps_color_balance() -> None:
    image = np.array([[[100, 150, 200]]], dtype=np.uint8)

    augmented = apply_lighting_augmentation(
        image,
        random.Random(13),
        global_brightness_min=0.8,
        global_brightness_max=0.8,
        color_jitter=0.5,
    )

    assert augmented.tolist() == [[[80, 120, 160]]]


def test_face_like_quad_rejects_whole_cube_silhouette() -> None:
    silhouette = np.array(
        [
            [1.0, 1.0],
            [119.0, 2.0],
            [118.0, 78.0],
            [2.0, 79.0],
        ],
        dtype=np.float32,
    )
    face = np.array(
        [
            [18.0, 12.0],
            [102.0, 15.0],
            [98.0, 72.0],
            [22.0, 70.0],
        ],
        dtype=np.float32,
    )

    assert not _is_face_like_quad(
        silhouette,
        width=120,
        height=80,
        min_area_ratio=0.12,
        max_aspect_ratio=1.9,
    )
    assert _is_face_like_quad(
        face,
        width=120,
        height=80,
        min_area_ratio=0.12,
        max_aspect_ratio=1.9,
    )


def test_face_like_quad_rejects_diagonal_multi_face_strip() -> None:
    multi_face_strip = np.array(
        [
            [0.0, 27.0],
            [145.0, 121.0],
            [137.0, 145.0],
            [28.0, 173.0],
        ],
        dtype=np.float32,
    )

    assert not _is_face_like_quad(
        multi_face_strip,
        width=166,
        height=174,
        min_area_ratio=0.12,
        max_aspect_ratio=1.9,
    )


def test_candidate_quads_from_edge_segments_builds_face_from_line_pairs() -> None:
    mask = np.full((100, 100), 255, dtype=np.uint8)
    segments = [
        EdgeSegment((20.0, 20.0), (20.0, 80.0), "outline"),
        EdgeSegment((80.0, 20.0), (80.0, 80.0), "hough"),
        EdgeSegment((20.0, 20.0), (80.0, 20.0), "hough"),
        EdgeSegment((20.0, 80.0), (80.0, 80.0), "outline"),
    ]

    candidates = _candidate_quads_from_edge_segments(
        segments=segments,
        mask=mask,
        width=100,
        height=100,
        min_area_ratio=0.12,
        max_aspect_ratio=1.9,
    )

    assert candidates
    best = max(candidates, key=_quad_area)
    np.testing.assert_allclose(
        best,
        np.array(
            [
                [20.0, 20.0],
                [80.0, 20.0],
                [80.0, 80.0],
                [20.0, 80.0],
            ],
            dtype=np.float32,
        ),
    )


def test_assign_cubes_to_random_output_splits_rebalances_source_splits() -> None:
    cubes_by_split = {
        "train": [
            object(),
            object(),
            object(),
            object(),
            object(),
            object(),
            object(),
            object(),
        ],
        "val": [object()],
        "test": [object()],
    }

    output = _assign_cubes_to_output_splits(
        cubes_by_split,  # type: ignore[arg-type]
        output_split_mode="random",
        train_ratio=0.6,
        val_ratio=0.2,
        test_ratio=0.2,
        seed=7,
    )

    assert len(output["train"]) == 6
    assert len(output["val"]) == 2
    assert len(output["test"]) == 2


def test_manual_faces_can_be_selected_as_consistent_sticker_subset() -> None:
    face_zero = np.array(
        [
            [0.0, 0.0],
            [10.0, 0.0],
            [10.0, 10.0],
            [0.0, 10.0],
        ],
        dtype=np.float32,
    )
    face_one = np.array(
        [
            [12.0, 0.0],
            [22.0, 0.0],
            [22.0, 10.0],
            [12.0, 10.0],
        ],
        dtype=np.float32,
    )
    manual_faces = [
        ManualFace("images/train/a.jpg", 0, 0, face_zero),
        ManualFace("images/train/a.jpg", 0, 1, face_one),
    ]

    face_quads = _manual_face_quads(manual_faces)

    assert len(face_quads) == 2
    np.testing.assert_allclose(face_quads[0][0], face_zero)
    np.testing.assert_allclose(face_quads[1][0], face_one)
    assert _face_method_label(face_quads) == "manual:0|manual:1"

    selected = _select_sticker_face_quads(
        face_quads,
        random.Random(3),
        sticker_face_mode="random",
        max_sticker_faces=2,
    )

    assert 1 <= len(selected) <= len(face_quads)
    assert set(_face_method_label(selected).split("|")).issubset(
        {"manual:0", "manual:1"}
    )


def test_sticker_face_mode_all_selects_every_annotated_face() -> None:
    face_quads = [
        (np.zeros((4, 2), dtype=np.float32), "manual:0"),
        (np.ones((4, 2), dtype=np.float32), "manual:1"),
        (np.full((4, 2), 2.0, dtype=np.float32), "manual:2"),
    ]

    selected = _select_sticker_face_quads(
        face_quads,
        random.Random(5),
        sticker_face_mode="all",
        max_sticker_faces=0,
    )

    assert _face_method_label(selected) == "manual:0|manual:1|manual:2"
    for selected_item, original_item in zip(selected, face_quads):
        np.testing.assert_allclose(selected_item[0], original_item[0])


def test_max_sticker_faces_caps_selected_annotated_faces() -> None:
    face_quads = [
        (np.zeros((4, 2), dtype=np.float32), "manual:0"),
        (np.ones((4, 2), dtype=np.float32), "manual:1"),
        (np.full((4, 2), 2.0, dtype=np.float32), "manual:2"),
    ]

    selected = _select_sticker_face_quads(
        face_quads,
        random.Random(5),
        sticker_face_mode="all",
        max_sticker_faces=2,
    )

    assert len(selected) == 2
    assert set(_face_method_label(selected).split("|")).issubset(
        {"manual:0", "manual:1", "manual:2"}
    )


def test_fruit_source_label_records_per_face_sources() -> None:
    paths = [
        Path("dataset/fruits360/apple/a.jpg"),
        Path("dataset/fruits360/apple/b.jpg"),
    ]

    assert _fruit_source_label(
        paths
    ) == "|".join(str(path) for path in paths)


def test_debug_face_overlay_options_parse() -> None:
    args = build_parser().parse_args(
        [
            "--face-annotations",
            "dataset/cube_face_annotations.json",
            "--manual-missing",
            "error",
            "--output-split-mode",
            "random",
            "--train-ratio",
            "0.6",
            "--val-ratio",
            "0.2",
            "--test-ratio",
            "0.2",
            "--sticker-face-mode",
            "one",
            "--max-sticker-faces",
            "2",
            "--shadow-prob",
            "0.5",
            "--shadow-min-factor",
            "0.35",
            "--shadow-max-factor",
            "0.8",
            "--shadow-blur-ratio",
            "0.18",
            "--global-brightness-min",
            "0.7",
            "--global-brightness-max",
            "1.0",
            "--color-jitter",
            "0.08",
            "--debug-face-overlays",
            "--debug-max-per-split",
            "3",
        ]
    )

    assert args.face_annotations.as_posix() == "dataset/cube_face_annotations.json"
    assert args.manual_missing == "error"
    assert args.output_split_mode == "random"
    assert args.train_ratio == 0.6
    assert args.val_ratio == 0.2
    assert args.test_ratio == 0.2
    assert args.sticker_face_mode == "one"
    assert args.max_sticker_faces == 2
    assert args.shadow_prob == 0.5
    assert args.shadow_min_factor == 0.35
    assert args.shadow_max_factor == 0.8
    assert args.shadow_blur_ratio == 0.18
    assert args.global_brightness_min == 0.7
    assert args.global_brightness_max == 1.0
    assert args.color_jitter == 0.08
    assert args.debug_face_overlays
    assert args.debug_face_dir is None
    assert args.debug_max_per_split == 3
