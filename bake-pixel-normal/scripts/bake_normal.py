#!/usr/bin/env python3
"""从 diffuse PNG 烘焙像素法线贴图，颜色量化到法线球调色板最近色。"""
from __future__ import annotations

import argparse
import math
from pathlib import Path

from PIL import Image

_SKILL_DIR = Path(__file__).resolve().parent.parent
SPHERE_PRESETS: dict[str, Path] = {
    "4": _SKILL_DIR / "normal_sphere_4.png",
    "8": _SKILL_DIR / "normal_sphere.png",
}
DEFAULT_LUT = "4"


def resolve_sphere_path(lut: str, sphere: Path | None) -> Path:
    if sphere is not None:
        return sphere
    if lut not in SPHERE_PRESETS:
        raise ValueError(f"未知法线球预设: {lut}，可选 {', '.join(SPHERE_PRESETS)}")
    return SPHERE_PRESETS[lut]


def load_palette_from_sphere(path: Path) -> list[tuple[int, int, int, int]]:
    sphere = Image.open(path).convert("RGBA")
    palette = sorted(set(sphere.getdata()))
    if not palette:
        raise ValueError(f"调色板为空: {path}")
    return palette


def pick_flat_colors() -> tuple[tuple[int, int, int, int], tuple[int, int, int, int]]:
    return (128, 128, 255, 255), (128, 128, 255, 0)


def dist_to_transparent(px, w: int, h: int, x: int, y: int, dx: int, dy: int, limit: int) -> int:
    for step in range(1, limit + 1):
        nx, ny = x + dx * step, y + dy * step
        if nx < 0 or nx >= w or ny < 0 or ny >= h:
            return limit + 1
        if px[nx, ny][3] == 0:
            return step
    return limit + 1


def nearest_palette(rgb: tuple[int, int, int], palette: list[tuple[int, int, int, int]]) -> tuple[int, int, int, int]:
    best = palette[0]
    best_d = 1 << 30
    for c in palette:
        d = (c[0] - rgb[0]) ** 2 + (c[1] - rgb[1]) ** 2 + (c[2] - rgb[2]) ** 2
        if d < best_d:
            best_d = d
            best = c
    return best


def quantize_normal(
    nx: float,
    ny: float,
    nz: float,
    palette: list[tuple[int, int, int, int]],
    flat_threshold: float,
    flat_opaque: tuple[int, int, int, int],
) -> tuple[int, int, int, int]:
    if abs(nx) < flat_threshold and abs(ny) < flat_threshold:
        return flat_opaque
    rgb = (
        int((nx * 0.5 + 0.5) * 255),
        int((ny * 0.5 + 0.5) * 255),
        int((nz * 0.5 + 0.5) * 255),
    )
    return nearest_palette(rgb, palette)


def bake(
    diffuse_path: Path,
    output_path: Path,
    sphere_path: Path,
    max_dist: int,
    strength: float,
    flat_threshold: float,
) -> None:
    palette = load_palette_from_sphere(sphere_path)
    flat_opaque, flat_transparent = pick_flat_colors()

    img = Image.open(diffuse_path).convert("RGBA")
    w, h = img.size
    px = img.load()

    normal = Image.new("RGBA", (w, h), flat_transparent)
    npx = normal.load()

    for y in range(h):
        for x in range(w):
            if px[x, y][3] == 0:
                continue
            up = dist_to_transparent(px, w, h, x, y, 0, -1, max_dist)
            down = dist_to_transparent(px, w, h, x, y, 0, 1, max_dist)
            left = dist_to_transparent(px, w, h, x, y, -1, 0, max_dist)
            right = dist_to_transparent(px, w, h, x, y, 1, 0, max_dist)
            tx = (left - right) / max_dist * strength
            ty = (down - up) / max_dist * strength
            length = math.sqrt(tx * tx + ty * ty + 1.0)
            nx, ny, nz = tx / length, ty / length, 1.0 / length
            npx[x, y] = quantize_normal(nx, ny, nz, palette, flat_threshold, flat_opaque)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    normal.save(output_path)
    print(
        f"baked {w}x{h} -> {output_path} "
        f"(palette={len(palette)} from {sphere_path.name}, max_dist={max_dist}, "
        f"strength={strength}, flat={flat_threshold})"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="烘焙像素法线贴图")
    parser.add_argument("diffuse", type=Path, help="diffuse PNG 路径")
    parser.add_argument("-o", "--output", type=Path, required=True, help="输出法线 PNG 路径")
    parser.add_argument(
        "--lut",
        choices=sorted(SPHERE_PRESETS),
        default=DEFAULT_LUT,
        help="内置法线球：4=normal_sphere_4（少梯度），8=normal_sphere（细腻）",
    )
    parser.add_argument(
        "--sphere",
        type=Path,
        default=None,
        help="自定义法线球路径；指定后覆盖 --lut",
    )
    parser.add_argument("-d", "--max-dist", type=int, default=16, help="边界距离探测半径（像素）")
    parser.add_argument("--strength", type=float, default=2.5, help="坡度强度倍率")
    parser.add_argument("--flat", type=float, default=0.25, help="低于此坡度视为平面 (128,128,255)")
    args = parser.parse_args()
    sphere_path = resolve_sphere_path(args.lut, args.sphere)
    bake(args.diffuse, args.output, sphere_path, args.max_dist, args.strength, args.flat)


if __name__ == "__main__":
    main()
