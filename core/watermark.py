from __future__ import annotations

import json
import os
from pathlib import Path
from typing import List, Tuple
from PIL import Image, UnidentifiedImageError


def ensure_directory(path: str) -> bool:
    try:
        p = Path(path)
        p.mkdir(parents=True, exist_ok=True)
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
    try:
        if not os.access(p, os.R_OK):
            return False, f"源目录无读取权限：{path}"
    except Exception:
        return False, f"无法访问源目录：{path}"
    return True, ""


def check_file_access(path: str) -> Tuple[bool, str]:
    p = Path(path)
    if not p.exists():
        return False, f"文件不存在：{path}"
    if not p.is_file():
        return False, f"不是文件：{path}"
    try:
        if not os.access(p, os.R_OK):
            return False, f"文件无读取权限：{path}"
    except Exception:
        return False, f"无法访问文件：{path}"
    return True, ""


def scan_image_files(source_dir: str) -> List[str]:
    p = Path(source_dir)
    allowed_exts = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}
    files: List[str] = []
    if not p.exists():
        return files
    for item in sorted(p.iterdir(), key=lambda x: x.name.lower()):
        if item.is_file() and item.suffix.lower() in allowed_exts:
            files.append(str(item))
    return files


def build_output_path(source_file: str, output_dir: str, output_format: str) -> str:
    src = Path(source_file)
    out = Path(output_dir)
    if not out.exists():
        out.mkdir(parents=True, exist_ok=True)

    ext_map = {
        "keep": src.suffix.lower(),
        "jpg": ".jpg",
        "jpeg": ".jpg",
        "png": ".png",
        "webp": ".webp",
    }

    fmt = output_format.lower()
    target_ext = ext_map.get(fmt, src.suffix.lower())
    if target_ext == ".jpg" and src.suffix.lower() in {".jpeg", ".jpg"}:
        target_ext = ".jpg"
    target_name = src.stem + target_ext
    return str(out / target_name)


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
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_json_config(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        return {}
    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}
