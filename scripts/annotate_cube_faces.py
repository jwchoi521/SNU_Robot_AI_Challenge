from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.synthesize_cube_fruit_dataset import (  # noqa: E402
    CubeBox,
    _collect_cubes,
    _crop_cube,
    _cube_annotation_key,
    _dataset_root_from_data_yaml,
    _normalize_annotation_image_key,
    _read_rgb,
    order_quad_points,
)


@dataclass
class AnnotationRecord:
    source_image: str
    image_path: str
    split: str
    cube_index: int
    bbox_xyxy: list[int]
    faces: list[np.ndarray]


class FaceAnnotationStore:
    def __init__(self, output_path: Path, data_yaml: Path, dataset_root: Path) -> None:
        self.output_path = output_path
        self.data_yaml = data_yaml
        self.dataset_root = dataset_root
        self.records: dict[tuple[str, int], AnnotationRecord] = {}
        if output_path.exists():
            self._load()

    def _load(self) -> None:
        payload = json.loads(self.output_path.read_text(encoding="utf-8"))
        if payload.get("coordinate_system") != "crop_xy":
            raise ValueError("face annotation coordinate_system must be crop_xy")

        for raw_face in payload.get("faces", []):
            source_image = str(raw_face["source_image"])
            cube_index = int(raw_face["cube_index"])
            key = (_normalize_annotation_image_key(source_image), cube_index)
            record = self.records.get(key)
            if record is None:
                record = AnnotationRecord(
                    source_image=source_image,
                    image_path=str(raw_face.get("image_path", "")),
                    split=str(raw_face.get("split", "")),
                    cube_index=cube_index,
                    bbox_xyxy=[int(value) for value in raw_face.get("bbox_xyxy", [])],
                    faces=[],
                )
                self.records[key] = record
            record.faces.append(
                order_quad_points(np.asarray(raw_face["quad_crop_xy"], dtype=np.float32))
            )

    def faces_for_cube(self, cube: CubeBox) -> list[np.ndarray]:
        key = _cube_annotation_key(cube, self.dataset_root)
        record = self.records.get(key)
        return [face.copy() for face in record.faces] if record else []

    def set_faces_for_cube(self, cube: CubeBox, faces: list[np.ndarray]) -> None:
        key = _cube_annotation_key(cube, self.dataset_root)
        if not faces:
            self.records.pop(key, None)
            return

        self.records[key] = AnnotationRecord(
            source_image=_source_image_for_cube(cube, self.dataset_root),
            image_path=str(cube.image_path.resolve()),
            split=cube.split,
            cube_index=cube.index,
            bbox_xyxy=[int(value) for value in cube.bbox_xyxy],
            faces=[order_quad_points(face) for face in faces],
        )

    def save(self) -> None:
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        faces: list[dict[str, object]] = []
        for record in sorted(
            self.records.values(),
            key=lambda item: (item.split, item.source_image, item.cube_index),
        ):
            for face_index, quad in enumerate(record.faces):
                faces.append(
                    {
                        "source_image": record.source_image,
                        "image_path": record.image_path,
                        "split": record.split,
                        "cube_index": record.cube_index,
                        "face_index": face_index,
                        "bbox_xyxy": record.bbox_xyxy,
                        "quad_crop_xy": [
                            [round(float(x_value), 2), round(float(y_value), 2)]
                            for x_value, y_value in quad
                        ],
                    }
                )

        payload = {
            "version": 1,
            "coordinate_system": "crop_xy",
            "data_yaml": str(self.data_yaml),
            "faces": faces,
        }
        self.output_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )


class AnnotationUi:
    def __init__(self, display_scale: float) -> None:
        self.display_scale = display_scale
        self.image_rgb: np.ndarray | None = None
        self.current_points: list[np.ndarray] = []
        self.faces: list[np.ndarray] = []
        self.status = ""

    def set_image(
        self,
        image_rgb: np.ndarray,
        faces: list[np.ndarray],
        status: str,
    ) -> None:
        self.image_rgb = image_rgb
        self.faces = [face.copy() for face in faces]
        self.current_points = []
        self.status = status

    def on_mouse(self, event: int, x_value: int, y_value: int, _flags: int, _param: object) -> None:
        import cv2

        if self.image_rgb is None:
            return

        if event == cv2.EVENT_LBUTTONDOWN:
            point = np.array(
                [x_value / self.display_scale, y_value / self.display_scale],
                dtype=np.float32,
            )
            height, width = self.image_rgb.shape[:2]
            point[0] = np.clip(point[0], 0, width - 1)
            point[1] = np.clip(point[1], 0, height - 1)
            self.current_points.append(point)
            if len(self.current_points) == 4:
                self.faces.append(order_quad_points(np.array(self.current_points)))
                self.current_points = []
        elif event == cv2.EVENT_RBUTTONDOWN:
            self.undo()

    def undo(self) -> None:
        if self.current_points:
            self.current_points.pop()
        elif self.faces:
            self.faces.pop()

    def reset(self) -> None:
        self.current_points = []
        self.faces = []

    def render(self) -> np.ndarray:
        import cv2

        if self.image_rgb is None:
            raise RuntimeError("no image set")

        scaled = cv2.resize(
            self.image_rgb,
            None,
            fx=self.display_scale,
            fy=self.display_scale,
            interpolation=cv2.INTER_NEAREST,
        )
        canvas = cv2.cvtColor(scaled, cv2.COLOR_RGB2BGR)
        face_colors = [
            (0, 255, 0),
            (255, 0, 255),
            (0, 255, 255),
            (255, 128, 0),
            (128, 255, 0),
        ]

        for face_index, face in enumerate(self.faces):
            points = np.round(face * self.display_scale).astype(np.int32)
            color = face_colors[face_index % len(face_colors)]
            cv2.polylines(canvas, [points.reshape(-1, 1, 2)], True, color, 2)
            cv2.putText(
                canvas,
                f"face {face_index}",
                tuple(points[0]),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                color,
                1,
                cv2.LINE_AA,
            )

        for point_index, point in enumerate(self.current_points):
            draw_point = tuple(np.round(point * self.display_scale).astype(int))
            cv2.circle(canvas, draw_point, 4, (0, 0, 255), -1)
            cv2.putText(
                canvas,
                str(point_index),
                (draw_point[0] + 4, draw_point[1] - 4),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                (0, 0, 255),
                1,
                cv2.LINE_AA,
            )

        lines = [
            self.status,
            "L-click: point | 4 points: add face | Right/Backspace: undo",
            "n/Enter: save next | k: keep skip | r: reset | q: save quit | Esc: quit",
        ]
        y_value = 16
        for line in lines:
            cv2.putText(
                canvas,
                line,
                (6, y_value),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.42,
                (255, 255, 255),
                2,
                cv2.LINE_AA,
            )
            cv2.putText(
                canvas,
                line,
                (6, y_value),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.42,
                (0, 0, 0),
                1,
                cv2.LINE_AA,
            )
            y_value += 16
        return canvas


def _source_image_for_cube(cube: CubeBox, dataset_root: Path) -> str:
    try:
        return cube.image_path.resolve().relative_to(dataset_root).as_posix()
    except ValueError:
        return cube.image_path.resolve().as_posix()


def _iter_requested_cubes(
    data_yaml: Path,
    splits: list[str],
) -> list[CubeBox]:
    cubes_by_split = _collect_cubes(data_yaml)
    cubes: list[CubeBox] = []
    for split in splits:
        cubes.extend(cubes_by_split.get(split, []))
    return cubes


def run_annotation(args: argparse.Namespace) -> int:
    import cv2

    data_yaml = args.data.resolve()
    dataset_root = _dataset_root_from_data_yaml(data_yaml)
    store = FaceAnnotationStore(args.output.resolve(), data_yaml, dataset_root)
    cubes = _iter_requested_cubes(data_yaml, args.splits)
    if args.skip_annotated:
        cubes = [cube for cube in cubes if not store.faces_for_cube(cube)]
    if args.max_cubes is not None:
        cubes = cubes[: args.max_cubes]

    print("Controls:")
    print("  Left click: add a face corner")
    print("  Every 4 clicks automatically adds one visible face")
    print("  Right click or Backspace: undo")
    print("  n or Enter: save current cube and move next")
    print("  k: keep existing annotation unchanged and move next")
    print("  r: reset current cube faces")
    print("  q: save current cube and quit")
    print("  Esc: quit without saving current cube")
    print()

    ui = AnnotationUi(display_scale=args.display_scale)
    cv2.namedWindow(args.window_name, cv2.WINDOW_NORMAL)
    cv2.setMouseCallback(args.window_name, ui.on_mouse)

    for cube_position, cube in enumerate(cubes, start=1):
        image_rgb = _read_rgb(cube.image_path)
        cube_crop = _crop_cube(image_rgb, cube.bbox_xyxy)
        existing_faces = store.faces_for_cube(cube)
        status = (
            f"{cube_position}/{len(cubes)} {cube.split} "
            f"{cube.image_path.name} cube {cube.index} faces={len(existing_faces)}"
        )
        ui.set_image(cube_crop, existing_faces, status)

        while True:
            cv2.imshow(args.window_name, ui.render())
            key = cv2.waitKey(20) & 0xFF
            if key in (255,):
                continue
            if key in (8, 127):
                ui.undo()
            elif key in (ord("r"), ord("R")):
                ui.reset()
            elif key in (ord("k"), ord("K")):
                break
            elif key in (ord("n"), ord("N"), 13, 10, 32):
                store.set_faces_for_cube(cube, ui.faces)
                store.save()
                break
            elif key in (ord("q"), ord("Q")):
                store.set_faces_for_cube(cube, ui.faces)
                store.save()
                cv2.destroyAllWindows()
                return 0
            elif key == 27:
                store.save()
                cv2.destroyAllWindows()
                return 0

    store.save()
    cv2.destroyAllWindows()
    print(f"Saved face annotations to {args.output}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Manually annotate visible cube face quadrilaterals for synthetic "
            "fruit-sticker generation."
        )
    )
    parser.add_argument("--data", type=Path, default=Path("dataset/data_shapes.yaml"))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("dataset/cube_face_annotations.json"),
    )
    parser.add_argument(
        "--splits",
        nargs="+",
        choices=("train", "val", "test"),
        default=["train", "val", "test"],
    )
    parser.add_argument("--display-scale", type=float, default=3.0)
    parser.add_argument("--max-cubes", type=int, default=None)
    parser.add_argument("--skip-annotated", action="store_true")
    parser.add_argument("--window-name", default="Cube face annotator")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    return run_annotation(args)


if __name__ == "__main__":
    raise SystemExit(main())
