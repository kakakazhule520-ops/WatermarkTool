from __future__ import annotations

from pathlib import Path
from typing import Tuple

from PIL import Image, ImageOps


def load_watermark(path: str):
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"水印文件不存在：{path}")
    with Image.open(p) as img:
        img = ImageOps.exif_transpose(img)
        if img.mode not in {"RGBA", "LA", "P"}:
            img = img.convert("RGBA")
        return img.copy()


def compute_watermark_size(base_width: int, base_height: int, watermark: Image.Image, ratio: float) -> Tuple[int, int]:
    ratio = max(0.01, min(1.0, float(ratio)))
    target_width = max(1, int(base_width * ratio))
    original_w, original_h = watermark.size
    if original_w <= 0 or original_h <= 0:
        return 1, 1
    scale = target_width / original_w
    new_w = max(1, int(original_w * scale))
    new_h = max(1, int(original_h * scale))
    if new_h > base_height:
        scale = base_height / original_h
        new_h = max(1, int(original_h * scale))
        new_w = max(1, int(original_w * scale))
    return new_w, new_h


def compute_position(base_width: int, base_height: int, watermark_w: int, watermark_h: int,
                    horizontal_alignment: str, vertical_alignment: str,
                    offset_x: int, offset_y: int) -> Tuple[int, int]:
    h = horizontal_alignment.lower()
    v = vertical_alignment.lower()

    if h == "left":
        x = 0 + offset_x
    elif h == "center":
        x = (base_width - watermark_w) // 2 + offset_x
    else:
        x = base_width - watermark_w - offset_x

    if v == "top":
        y = 0 + offset_y
    elif v == "center":
        y = (base_height - watermark_h) // 2 + offset_y
    else:
        y = base_height - watermark_h - offset_y

    x = max(0, min(x, max(0, base_width - watermark_w)))
    y = max(0, min(y, max(0, base_height - watermark_h)))
    return x, y
