#!/usr/bin/env python3
"""Generate the centered 4 m x 4 m arena map with a 1 cm wall."""

from pathlib import Path


RESOLUTION_M = 0.01
FREE_SIZE_M = 4.0
WALL_CELLS = 1
FREE_CELLS = round(FREE_SIZE_M / RESOLUTION_M)
SIZE_CELLS = FREE_CELLS + 2 * WALL_CELLS


def generate_map(output_path: Path) -> None:
    pixels = bytearray(SIZE_CELLS * SIZE_CELLS)
    free_row = bytes([255]) * FREE_CELLS
    for row in range(WALL_CELLS, WALL_CELLS + FREE_CELLS):
        start = row * SIZE_CELLS + WALL_CELLS
        pixels[start : start + FREE_CELLS] = free_row

    header = f"P5\n{SIZE_CELLS} {SIZE_CELLS}\n255\n".encode("ascii")
    output_path.write_bytes(header + pixels)


if __name__ == "__main__":
    destination = Path(__file__).with_name("arena_4x4_center.pgm")
    generate_map(destination)
    print(
        f"wrote {destination} ({SIZE_CELLS}x{SIZE_CELLS}, "
        f"{RESOLUTION_M:.2f} m/cell)"
    )
