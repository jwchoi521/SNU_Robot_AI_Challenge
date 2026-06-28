from pathlib import Path

from scripts.annotate_cube_faces import build_parser


def test_annotate_cube_faces_parser_defaults() -> None:
    args = build_parser().parse_args([])

    assert args.data == Path("dataset/data_shapes.yaml")
    assert args.output == Path("dataset/cube_face_annotations.json")
    assert args.splits == ["train", "val", "test"]
    assert args.display_scale == 3.0


def test_annotate_cube_faces_parser_custom_values() -> None:
    args = build_parser().parse_args(
        [
            "--data",
            "dataset/data_shapes.yaml",
            "--output",
            "dataset/faces.json",
            "--splits",
            "train",
            "val",
            "--display-scale",
            "4",
            "--max-cubes",
            "5",
            "--skip-annotated",
        ]
    )

    assert args.output == Path("dataset/faces.json")
    assert args.splits == ["train", "val"]
    assert args.display_scale == 4
    assert args.max_cubes == 5
    assert args.skip_annotated
