from __future__ import annotations

import os
from pathlib import Path

from PIL import Image


def adjust_jpeg_or_webp_quality(output_path: str, source_path: str, target_size_kb: int, quality: int,
                               step: int, min_quality: int, max_quality: int, format_name: str) -> tuple[int, int]:
    path = Path(output_path)
    if not path.exists():
        return quality, 0

    target_bytes = max(1, int(target_size_kb * 1024))
    file_size = path.stat().st_size
    current_quality = int(max(min_quality, min(max_quality, quality)))
    best_quality = current_quality
    attempts = 0
    max_attempts = 12

    while attempts < max_attempts:
        if file_size <= target_bytes:
            current_quality = min(max_quality, current_quality + step)
            best_quality = current_quality
        else:
            current_quality = max(min_quality, current_quality - step)
            best_quality = current_quality

        if current_quality == best_quality and attempts > 0:
            break

        img = Image.open(source_path)
        img = img.convert("RGB") if img.mode in {"RGBA", "LA", "P"} else img
        temp_path = str(path.with_suffix(path.suffix + ".tmp_quality"))
        img.save(temp_path, format=format_name.upper(), quality=current_quality, optimize=True)
        img.close()
        file_size = os.path.getsize(temp_path)
        os.remove(temp_path)
        attempts += 1

        if file_size <= target_bytes and current_quality >= max_quality:
            return current_quality, file_size
        if file_size > target_bytes and current_quality <= min_quality:
            return current_quality, file_size

    return best_quality, file_size
