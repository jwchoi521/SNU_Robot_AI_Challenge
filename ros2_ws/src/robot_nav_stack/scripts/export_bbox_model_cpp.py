#!/usr/bin/env python3
"""Export the sklearn bbox residual pipeline to the C++ portable forest format."""

from __future__ import annotations

import argparse
import math
import struct
from pathlib import Path


MAGIC = b"BNRFV1\0\0"
VERSION = 1


def _write_string(stream, value: str) -> None:
    encoded = value.encode("utf-8")
    stream.write(struct.pack("<I", len(encoded)))
    stream.write(encoded)


def export_model(model_path: Path, output_path: Path) -> None:
    import joblib

    payload = joblib.load(model_path)
    if payload.get("kind") != "homography_residual_v1":
        raise ValueError("Expected homography_residual_v1 model.")

    pipeline = payload["residual_model"]
    preprocess = pipeline.named_steps["preprocess"]
    scaler = preprocess.named_transformers_["num"]
    encoder = preprocess.named_transformers_["cat"]
    forest = pipeline.named_steps["model"]
    numeric_columns = list(preprocess.transformers_[0][2])
    categories = [str(value) for value in encoder.categories_[0]]

    if len(scaler.mean_) != len(numeric_columns):
        raise ValueError("numeric feature/scaler size mismatch")
    if int(forest.n_outputs_) != 2:
        raise ValueError("bbox residual model must have two outputs")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("wb") as stream:
        stream.write(struct.pack("<8sI", MAGIC, VERSION))
        stream.write(struct.pack("<d", float(payload["anchor_alpha"])))
        stream.write(struct.pack("<9d", *payload["homography"].reshape(-1).tolist()))

        stream.write(struct.pack("<I", len(numeric_columns)))
        for name, mean, scale in zip(numeric_columns, scaler.mean_, scaler.scale_):
            _write_string(stream, str(name))
            stream.write(struct.pack("<2d", float(mean), float(scale)))

        stream.write(struct.pack("<I", len(categories)))
        for category in categories:
            _write_string(stream, category)

        stream.write(struct.pack("<III", int(forest.n_features_in_), 2, len(forest.estimators_)))
        for estimator in forest.estimators_:
            tree = estimator.tree_
            stream.write(struct.pack("<I", int(tree.node_count)))
            for node in range(tree.node_count):
                stream.write(
                    struct.pack(
                        "<iiiddd",
                        int(tree.children_left[node]),
                        int(tree.children_right[node]),
                        int(tree.feature[node]),
                        float(tree.threshold[node]),
                        float(tree.value[node, 0, 0]),
                        float(tree.value[node, 1, 0]),
                    )
                )

    print(
        f"exported {len(forest.estimators_)} trees, "
        f"{sum(tree.tree_.node_count for tree in forest.estimators_)} nodes "
        f"to {output_path} ({output_path.stat().st_size} bytes)"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("model", type=Path, help="input homography_residual_v1 joblib")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="output file (default: replace input suffix with .cppbin)",
    )
    args = parser.parse_args()
    output = args.output or args.model.with_suffix(".cppbin")
    export_model(args.model, output)


if __name__ == "__main__":
    main()
