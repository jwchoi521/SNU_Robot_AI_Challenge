# Agent Notes

This repository is a YOLO object detection project for a robot AI challenge.

## Project Rules

- Keep the detection class mapping fixed to exactly 8 classes:
  `cube_any`, `octahedron`, `dodecahedron`, `icosahedron`, `apple_sticker`, `orange_sticker`, `banana_sticker`, `pineapple_sticker`.
- A lone `cube_any` must become `unknown_cube` and must not be pickable.
- A fruit target is valid only when a `cube_any` detection is connected to a fruit sticker detection.
- `target_confirmed` must come from repeated multi-frame observation, not a single frame.
- Camera output must include object kind and `bearing_deg`.
- Keep LiDAR integration bearing-based so distance matching can be added without changing camera post-processing contracts.

## Development

- Use `argparse` for all executable scripts.
- Keep robot decision rules in `src/postprocess.py` and cover changes with pytest.
- Prefer small, deterministic tests that do not require a camera, GPU, or YOLO weights.
- Do not commit generated model weights, TensorRT engines, datasets, runs, logs, or local virtual environments.

## Checks

Run these before handing off changes:

```powershell
ruff check .
pytest
```
