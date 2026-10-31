from __future__ import annotations

from pathlib import Path
from typing import Dict, Tuple

from PIL import Image, ImageOps


def compute_watermark_size(image_width: int, image_height: int, ratio: float = 0.35,
                          max_width: int | None = None, max_height: int | None = None) -> Tuple[int, int]:
    """Compute watermark dimensions proportional to the source image."""
    if image_width <= 0 or image_height <= 0:
        return 1, 1
    target_w = max(1, int(image_width * max(0.05, min(1.0, ratio))))
    if max_width and target_w > max_width:
        target_w = max_width
    target_h = max(1, int(target_w * 0.5))
    if max_height and target_h > max_height:
        target_h = max_height
        target_w = max(1, int(target_h * 2))
    return target_w, target_h


def compute_position(image_w: int, image_h: int, watermark_w: int, watermark_h: int,
                     horizontal_alignment: str = "right", vertical_alignment: str = "bottom",
                     offset_x: int = 0, offset_y: int = 0) -> Tuple[int, int]:
    horizontal = (horizontal_alignment or "right").lower()
    vertical = (vertical_alignment or "bottom").lower()

    if horizontal == "left":
        x = offset_x
    elif horizontal == "center":
        x = max(0, (image_w - watermark_w) // 2 + offset_x)
    else:
        x = max(0, image_w - watermark_w - offset_x)

    if vertical == "top":
        y = offset_y
    elif vertical == "center":
        y = max(0, (image_h - watermark_h) // 2 + offset_y)
    else:
        y = max(0, image_h - watermark_h - offset_y)

    return x, y


def load_watermark(path: str, max_width: int | None = None, max_height: int | None = None,
                  opacity: float = 1.0) -> Image.Image:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Watermark not found: {path}")
    with Image.open(p) as img:
        img = ImageOps.exif_transpose(img).convert("RGBA")
        if max_width is not None or max_height is not None:
            factor = 1.0
            if max_width and img.width > max_width:
                factor = min(factor, max_width / img.width)
            if max_height and img.height > max_height:
                factor = min(factor, max_height / img.height)
            if factor < 1.0:
                img = img.resize((max(1, int(img.width * factor)), max(1, int(img.height * factor))), Image.Resampling.LANCZOS)

        alpha = img.getchannel("A")
        if opacity < 1.0:
            alpha = Image.eval(alpha, lambda x: int(x * opacity))
            img.putalpha(alpha)
        return img
