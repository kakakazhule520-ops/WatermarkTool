from __future__ import annotations

import os
from pathlib import Path

from PIL import Image


def adjust_jpeg_or_webp_quality(output_path: str, source_path: str, target_size_kb: int,
                               quality: int, step: int, min_quality: int, max_quality: int,
                               format_name: str) -> tuple[int, int]:
    output = Path(output_path)
    if not output.exists():
        return max(min_quality, min(max_quality, quality)), 0

    target_size = max(1, int(target_size_kb * 1024))
    current_quality = max(min_quality, min(max_quality, int(quality)))
    best_quality = current_quality
    last_size = output.stat().st_size
    attempts = 0
    max_attempts = 12

    while attempts < max_attempts:
        if last_size > target_size:
            current_quality = max(min_quality, current_quality - step)
        elif last_size < target_size:
            current_quality = min(max_quality, current_quality + step)

        current_quality = max(min_quality, min(max_quality, int(current_quality)))
        best_quality = current_quality

        with Image.open(source_path) as img:
            rgb = img.convert("RGB") if img.mode in {"RGBA", "LA", "P"} else img
            temp_name = output.with_suffix(output.suffix + ".quality_tmp")
            rgb.save(temp_name, format=format_name.upper(), quality=current_quality, optimize=True)
            last_size = temp_name.stat().st_size
            temp_name.unlink(missing_ok=True)

        attempts += 1
        if abs(last_size - target_size) <= max(512, target_size // 20):
            break
        if current_quality <= min_quality and last_size > target_size:
            break
        if current_quality >= max_quality and last_size < target_size:
            break

    return best_quality, last_size
