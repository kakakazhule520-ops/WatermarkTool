from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from PIL import Image, ImageDraw, ImageFilter, ImageOps

from core.compression import adjust_jpeg_or_webp_quality
from core.file_manager import build_output_path, is_valid_image
from core.naming import generate_output_name
from core.watermark import compute_position, compute_watermark_size, load_watermark


def _finalize_output_format(output_format: str, image: Image.Image) -> Image.Image:
    fmt = (output_format or "keep").lower()
    if fmt == "keep":
        return image
    if fmt == "jpg":
        if image.mode in {"RGBA", "LA", "P"}:
            bg = Image.new("RGB", image.size, (255, 255, 255))
            bg.paste(image.convert("RGB"), (0, 0))
            return bg
        return image.convert("RGB")
    if fmt == "png":
        if image.mode not in {"RGBA"}:
            return image.convert("RGBA")
        return image
    if fmt == "webp":
        if image.mode in {"RGBA", "LA", "P"}:
            return image.convert("RGBA")
        return image.convert("RGB")
    return image


def _apply_text_overlay(base: Image.Image, settings: Dict[str, Any]) -> Image.Image:
    if not settings.get("add_text_enabled"):
        return base
    text = settings.get("text_content", "")
    if not text:
        return base
    draw = ImageDraw.Draw(base)
    font_size = int(settings.get("text_size", 32))
    font = None
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except Exception:
        try:
            font = ImageFont.truetype("msyh.ttc", font_size)
        except Exception:
            font = None
    color = settings.get("text_color", "#FFFFFF")
    opacity = float(settings.get("text_opacity", 1.0))
    x_offset = int(settings.get("text_offset_x", 10))
    y_offset = int(settings.get("text_offset_y", 10))
    top_left = (x_offset, y_offset)
    if font is None:
        draw.text(top_left, text, fill=color)
    else:
        rgba = base.convert("RGBA")
        temp = Image.new("RGBA", rgba.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(temp)
        d.text(top_left, text, font=font, fill=(255, 255, 255, int(255 * opacity)))
        base = Image.alpha_composite(rgba, temp)
    return base


def _apply_number_overlay(base: Image.Image, settings: Dict[str, Any], index: int = 1) -> Image.Image:
    if not settings.get("add_number_enabled"):
        return base
    digits = max(1, int(settings.get("number_digits", 3)))
    num = str(int(settings.get("start_index", 1)) + max(0, index - 1)).zfill(digits)
    prefix = settings.get("number_prefix", "")
    suffix = settings.get("number_suffix", "")
    text = f"{prefix}{num}{suffix}"
    draw = ImageDraw.Draw(base)
    try:
        font = ImageFont.truetype("arial.ttf", 24)
    except Exception:
        try:
            font = ImageFont.truetype("msyh.ttc", 24)
        except Exception:
            font = None
    if font is None:
        draw.text((10, 10), text, fill=(255, 255, 255, 255))
    else:
        rgba = base.convert("RGBA")
        temp = Image.new("RGBA", rgba.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(temp)
        d.text((10, 10), text, font=font, fill=(255, 255, 255, 220))
        base = Image.alpha_composite(rgba, temp)
    return base


def process_one_image(source_path: str, output_path: str, watermark_path: str, settings: Dict[str, Any],
                     index: int = 1, use_name_rule: bool = True) -> Tuple[bool, str, str]:
    if not source_path or not watermark_path:
        return False, "源图片或水印图片路径为空。", output_path

    if not os.path.exists(source_path):
        return False, f"源图片不存在：{source_path}", output_path

    try:
        with Image.open(source_path) as source_img:
            source_img = ImageOps.exif_transpose(source_img)
            if source_img.mode not in {"RGBA", "RGB", "L", "P", "LA"}:
                source_img = source_img.convert("RGBA")

            watermark = load_watermark(watermark_path)
            if watermark.size[0] <= 0 or watermark.size[1] <= 0:
                raise ValueError("水印图片尺寸无效。")

            ratio = float(settings.get("watermark_width_ratio", 0.6))
            target_w, target_h = compute_watermark_size(source_img.width, source_img.height, watermark, ratio)
            watermark = watermark.resize((target_w, target_h), Image.Resampling.LANCZOS)

            opacity = float(settings.get("opacity", 0.7))
            if watermark.mode != "RGBA":
                watermark = watermark.convert("RGBA")
            alpha = watermark.getchannel("A")
            watermark.putalpha(Image.eval(alpha, lambda p: int((p / 255.0) * opacity * 255)))

            x, y = compute_position(
                source_img.width,
                source_img.height,
                target_w,
                target_h,
                settings.get("horizontal_alignment", "right"),
                settings.get("vertical_alignment", "bottom"),
                int(settings.get("offset_x", 5)),
                int(settings.get("offset_y", 5)),
            )

            result = source_img.convert("RGBA")
            result.paste(watermark, (x, y), watermark)

            if settings.get("add_text_enabled"):
                result = _apply_text_overlay(result, settings)
            if settings.get("add_number_enabled"):
                result = _apply_number_overlay(result, settings, index)

            target_format = settings.get("output_format", "keep")
            out_ext = Path(output_path).suffix.lower()
            if target_format.lower() == "keep":
                source_ext = Path(source_path).suffix.lower()
                if source_ext in {".jpg", ".jpeg"}:
                    result = result.convert("RGB")
                elif source_ext == ".png":
                    result = result if result.mode == "RGBA" else result.convert("RGBA")
                elif source_ext in {".webp"}:
                    result = result.convert("RGBA")
                elif source_ext in {".bmp", ".tif", ".tiff"}:
                    result = result.convert("RGB")
            else:
                result = _finalize_output_format(target_format, result)

            final_path = Path(output_path)
            final_path.parent.mkdir(parents=True, exist_ok=True)
            temp_path = final_path.with_suffix(final_path.suffix + ".tmp")
            if temp_path.exists():
                temp_path.unlink()

            if target_format.lower() == "png" or (target_format.lower() == "keep" and Path(source_path).suffix.lower() == ".png"):
                result.save(temp_path, format="PNG")
            elif target_format.lower() in {"jpg", "jpeg"} or (target_format.lower() == "keep" and Path(source_path).suffix.lower() in {".jpg", ".jpeg"}):
                result.save(temp_path, format="JPEG", quality=max(1, min(100, int(settings.get("fixed_quality", 85)))), optimize=True)
            elif target_format.lower() in {"webp"} or (target_format.lower() == "keep" and Path(source_path).suffix.lower() == ".webp"):
                result.save(temp_path, format="WEBP", quality=max(1, min(100, int(settings.get("fixed_quality", 85)))))
            else:
                result.save(temp_path)

            if not os.path.exists(temp_path):
                raise OSError("输出临时文件不存在。")

            os.replace(temp_path, final_path)
            if not os.path.exists(final_path):
                raise OSError("输出文件写入失败。")
            return True, "处理成功", str(final_path)
    except Exception as exc:
        return False, str(exc), output_path


def generate_output_file_path(source_path: str, settings: Dict[str, Any], index: int = 1) -> str:
    source = Path(source_path)
    if not settings.get("output_dir"):
        raise ValueError("输出目录为空。")
    out_dir = Path(settings["output_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)

    base_name = source.name
    rule_name = generate_output_name(base_name, settings, index=index)
    if not rule_name:
        rule_name = source.name

    output_format = (settings.get("output_format", "keep") or "keep").lower()
    ext_map = {"keep": source.suffix.lower(), "jpg": ".jpg", "png": ".png", "webp": ".webp"}
    target_ext = ext_map.get(output_format, source.suffix.lower())
    if output_format == "keep":
        candidate = out_dir / rule_name
    else:
        candidate = out_dir / (Path(rule_name).stem + target_ext)
    return str(candidate)
