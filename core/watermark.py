from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, Tuple

from PIL import Image, ImageOps, UnidentifiedImageError


SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}


def ensure_directory(path: str) -> bool:
    try:
        Path(path).mkdir(parents=True, exist_ok=True)
        return True
    except Exception:
        return False


def validate_source_dir(path: str) -> Tuple[bool, str]:
    if not path:
        return False, "源目录为空。"
    p = Path(path)
    if not p.exists():
        return False, f"源目录不存在：{path}"
    if not p.is_dir():
        return False, f"不是有效目录：{path}"
    if not os.access(p, os.R_OK):
        return False, f"源目录无读取权限：{path}"
    return True, ""


def check_file_access(path: str) -> Tuple[bool, str]:
    p = Path(path)
    if not p.exists():
        return False, f"文件不存在：{path}"
    if not p.is_file():
        return False, f"不是文件：{path}"
    if not os.access(p, os.R_OK):
        return False, f"文件无读取权限：{path}"
    return True, ""


def scan_image_files(source_dir: str) -> list[str]:
    p = Path(source_dir)
    files: list[str] = []
    if not p.exists():
        return files
    for item in sorted(p.iterdir(), key=lambda x: x.name.lower()):
        if item.is_file() and item.suffix.lower() in SUPPORTED_EXTENSIONS:
            files.append(str(item))
    return files


def build_output_path(source_file: str, output_dir: str, output_format: str) -> str:
    src = Path(source_file)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    mapped = {
        "keep": src.suffix.lower(),
        "jpg": ".jpg",
        "jpeg": ".jpg",
        "png": ".png",
        "webp": ".webp",
    }
    target_ext = mapped.get(output_format.lower(), src.suffix.lower())
    if target_ext == ".jpg" and src.suffix.lower() in {".jpeg", ".jpg"}:
        target_ext = ".jpg"

    stem = src.stem
    if src.parent.resolve() == out_dir.resolve() and src.name == f"{stem}{target_ext}":
        stem = f"{stem}_wm_copy"

    target_name = f"{stem}{target_ext}"
    candidate = out_dir / target_name
    counter = 1
    while candidate.exists() and not candidate.samefile(src):
        candidate = out_dir / f"{stem}_{counter}{target_ext}"
        counter += 1
    return str(candidate)


def is_valid_image(path: str) -> bool:
    try:
        with Image.open(path) as img:
            img.verify()
        return True
    except (UnidentifiedImageError, OSError, ValueError):
        return False


def safe_write_image(image: Image.Image, destination: str, output_format: str, quality: int = 95) -> None:
    destination_path = Path(destination)
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    temp_fd, temp_path = tempfile.mkstemp(prefix="wm_", suffix=".tmp", dir=str(destination_path.parent))
    os.close(temp_fd)
    try:
        fmt = output_format.upper()
        if output_format.lower() == "png":
            image.save(temp_path, format="PNG")
        elif output_format.lower() in {"jpg", "jpeg"}:
            image.save(temp_path, format="JPEG", quality=max(1, min(100, quality)), optimize=True)
        elif output_format.lower() == "webp":
            image.save(temp_path, format="WEBP", quality=max(1, min(100, quality)))
        else:
            image.save(temp_path, format=image.format or "PNG")
        os.replace(temp_path, destination_path)
    except Exception:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise


def atomic_copy_to_temp(source_path: str, temp_dir: str) -> str:
    src = Path(source_path)
    temp = Path(temp_dir)
    temp.mkdir(parents=True, exist_ok=True)
    destination = temp / (src.name + ".tmp")
    shutil.copy2(src, destination)
    return str(destination)


def save_json_config(path: str, data: dict) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        import json
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_json_config(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        return {}
    try:
        with open(p, "r", encoding="utf-8") as f:
            import json
            return json.load(f)
    except Exception:
        return {}
