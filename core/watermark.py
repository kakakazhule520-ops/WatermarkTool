from __future__ import annotations

import json
import os
from pathlib import Path
from typing import List, Tuple

from PIL import Image, UnidentifiedImageError

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}


__all__ = [
    "SUPPORTED_EXTENSIONS",
    "ensure_directory",
    "validate_source_dir",
    "check_file_access",
    "scan_image_files",
    "build_output_path",
    "is_valid_image",
    "save_json_config",
    "load_json_config",
    "atomic_write_image",
]


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


def scan_image_files(source_dir: str) -> List[str]:
    p = Path(source_dir)
    if not p.exists() or not p.is_dir():
        return []
    files: List[str] = []
    for item in sorted(p.iterdir(), key=lambda x: x.name.lower()):
        if item.is_file() and item.suffix.lower() in SUPPORTED_EXTENSIONS:
            files.append(str(item))
    return files


def build_output_path(source_file: str, output_dir: str, output_format: str) -> str:
    src = Path(source_file)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    fmt = (output_format or "keep").lower()
    ext_map = {"keep": src.suffix.lower(), "jpg": ".jpg", "jpeg": ".jpg", "png": ".png", "webp": ".webp"}
    target_ext = ext_map.get(fmt, src.suffix.lower())
    stem = src.stem
    candidate = out_dir / f"{stem}{target_ext}"
    index = 1
    while candidate.exists() and str(candidate.resolve()) != str(src.resolve()):
        candidate = out_dir / f"{stem}_{index}{target_ext}"
        index += 1
    return str(candidate)


def is_valid_image(path: str) -> bool:
    try:
        with Image.open(path) as img:
            img.verify()
        return True
    except (UnidentifiedImageError, OSError, ValueError):
        return False


def save_json_config(path: str, data: dict) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_json_config(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        return {}
    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def atomic_write_image(image: Image.Image, destination: str) -> None:
    dst = Path(destination)
    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp = dst.with_suffix(dst.suffix + ".tmp")
    if tmp.exists():
        tmp.unlink()
    image.save(tmp)
    os.replace(tmp, dst)
