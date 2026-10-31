from __future__ import annotations

import os
from pathlib import Path

from PIL import Image


def adjust_jpeg_or_webp_quality(
    output_path: str,
    source_path: str,
    target_size_kb: int,
    quality: int,
    step: int,
    min_quality: int,
    max_quality: int,
    format_name: str,
) -> tuple[int, int]:
    target_bytes = max(1, int(target_size_kb * 1024))
    current_quality = max(min_quality, min(max_quality, int(quality)))
    output = Path(output_path)
    file_size = output.stat().st_size if output.exists() else 0
    last_quality = current_quality

    for _ in range(12):
        if output.exists():
            file_size = output.stat().st_size
            if file_size > target_bytes:
                current_quality = max(min_quality, current_quality - step)
            elif file_size < target_bytes:
                current_quality = min(max_quality, current_quality + step)
        else:
            current_quality = max(min_quality, min(max_quality, current_quality))

        try:
            with Image.open(source_path) as img:
                rgb = img.convert("RGB") if img.mode in {"RGBA", "LA", "P"} else img
                temp_path = output.with_suffix(output.suffix + ".quality_tmp")
                rgb.save(temp_path, format=format_name.upper(), quality=current_quality, optimize=True)
                file_size = os.path.getsize(temp_path)
                temp_path.unlink(missing_ok=True)
        except Exception:
            break

        last_quality = current_quality
        if abs(file_size - target_bytes) <= max(512, target_size_kb):
            break
        if file_size > target_bytes and current_quality <= min_quality:
            break
        if file_size < target_bytes and current_quality >= max_quality:
            break

    return last_quality, file_size
