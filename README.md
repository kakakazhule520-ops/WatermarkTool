from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Tuple

from PIL import Image, ImageDraw, ImageFont, ImageOps

from core.naming import generate_output_name


def _convert_to_output_mode(image: Image.Image, output_format: str, source_ext: str) -> Image.Image:
    fmt = (output_format or "keep").lower()
    if fmt == "keep":
        fmt = source_ext.lower().lstrip(".")
    if fmt in {"jpg", "jpeg"}:
        if image.mode in {"RGBA", "LA", "P"}:
            bg = Image.new("RGB", image.size, (255, 255, 255))
            image = image.convert("RGBA")
            bg.paste(image, (0, 0), image)
            return bg
        return image.convert("RGB")
    if fmt == "png":
        return image.convert("RGBA") if image.mode != "RGBA" else image
    if fmt == "webp":
        return image.convert("RGBA") if image.mode in {"RGBA", "LA", "P"} else image.convert("RGB")
    return image


def _apply_text_overlay(base: Image.Image, settings: Dict[str, Any]) -> Image.Image:
    if not settings.get("add_text_enabled"):
        return base
    text = settings.get("text_content", "")
    if not text:
        return base

    size = int(settings.get("text_size", 28))
    try:
        font = ImageFont.truetype("arial.ttf", size)
    except Exception:
        try:
            font = ImageFont.truetype("msyh.ttc", size)
        except Exception:
            font = None

    rgba = base.convert("RGBA")
    temp = Image.new("RGBA", rgba.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(temp)
    x = int(settings.get("text_offset_x", 10))
    y = int(settings.get("text_offset_y", 10))
    color = settings.get("text_color", "#FFFFFF")
    opacity = float(settings.get("text_opacity", 1.0))
    if color.startswith("#"):
        color = color.lstrip("#")
        if len(color) == 6:
            color = tuple(int(color[i:i + 2], 16) for i in (0, 2, 4))
    if font is None:
        d.text((x, y), text, fill=(255, 255, 255, int(255 * opacity)))
    else:
        d.text((x, y), text, font=font, fill=(255, 255, 255, int(255 * opacity)))
    return Image.alpha_composite(rgba, temp)


def _apply_number_overlay(base: Image.Image, settings: Dict[str, Any], index: int = 1) -> Image.Image:
    if not settings.get("add_number_enabled"):
        return base
    digits = max(1, int(settings.get("number_digits", 3)))
    prefix = settings.get("number_prefix", "")
    suffix = settings.get("number_suffix", "")
    value = str(int(settings.get("start_index", 1)) + max(0, index - 1)).zfill(digits)
    text = f"{prefix}{value}{suffix}"
    rgba = base.convert("RGBA")
    temp = Image.new("RGBA", rgba.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(temp)
    try:
        font = ImageFont.truetype("arial.ttf", 30)
    except Exception:
        try:
            font = ImageFont.truetype("msyh.ttc", 30)
        except Exception:
            font = None
    if font is None:
        d.text((10, 10), text, fill=(255, 255, 255, 200))
    else:
        d.text((10, 10), text, fill=(255, 255, 255, 200), font=font)
    return Image.alpha_composite(rgba, temp)


def process_one_image(source_path: str, output_path: str, watermark_path: str, settings: Dict[str, Any],
                     index: int = 1, use_name_rule: bool = True) -> Tuple[bool, str, str]:
    if not source_path or not watermark_path:
        return False, "源图片或水印图片路径为空。", output_path
    if not os.path.exists(source_path):
        return False, f"源图片不存在：{source_path}", output_path

    try:
        with Image.open(source_path) as source_img:
            source_img = ImageOps.exif_transpose(source_img)
            if source_img.mode not in {"RGB", "RGBA", "L", "LA", "P"}:
                source_img = source_img.convert("RGBA")

            if source_img.mode in {"L", "P"}:
                source_img = source_img.convert("RGBA")

            with Image.open(watermark_path) as watermark_img:
                watermark = ImageOps.exif_transpose(watermark_img)
                if watermark.mode not in {"RGBA", "LA", "P"}:
                    watermark = watermark.convert("RGBA")
                else:
                    watermark = watermark.convert("RGBA")

                ratio = float(settings.get("watermark_width_ratio", 0.6))
                target_w = max(1, int(source_img.width * ratio))
                scale = target_w / max(1, watermark.width)
                target_h = max(1, int(watermark.height * scale))
                if target_h > source_img.height:
                    scale = source_img.height / max(1, watermark.height)
                    target_h = max(1, int(watermark.height * scale))
                    target_w = max(1, int(watermark.width * scale))

                watermark = watermark.resize((target_w, target_h), Image.Resampling.LANCZOS)
                alpha = watermark.getchannel("A")
                opacity = float(settings.get("opacity", 0.7))
                watermark = watermark.copy()
                watermark.putalpha(Image.eval(alpha, lambda p: int((p / 255.0) * opacity * 255)))

                x, y = (0, 0)
                from core.watermark import compute_position
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

                source_ext = Path(source_path).suffix.lower()
                output_format = settings.get("output_format", "keep")
                result = _convert_to_output_mode(result, output_format, source_ext)

                final_path = Path(output_path)
                final_path.parent.mkdir(parents=True, exist_ok=True)
                temp_path = final_path.with_suffix(final_path.suffix + ".tmp")
                if temp_path.exists():
                    temp_path.unlink()

                fmt = (output_format or "keep").lower()
                if fmt == "keep":
                    fmt = source_ext.lstrip(".")
                if fmt in {"jpg", "jpeg"}:
                    result.save(temp_path, format="JPEG", quality=max(1, min(100, int(settings.get("fixed_quality", 85)))), optimize=True)
                elif fmt == "png":
                    result.save(temp_path, format="PNG")
                elif fmt == "webp":
                    result.save(temp_path, format="WEBP", quality=max(1, min(100, int(settings.get("fixed_quality", 85)))))
                else:
                    result.save(temp_path)

                os.replace(temp_path, final_path)
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
    name = generate_output_name(base_name, settings, index=index)
    if not name or name == base_name:
        name = source.stem + source.suffix

    output_format = (settings.get("output_format", "keep") or "keep").lower()
    ext_map = {"keep": source.suffix.lower(), "jpg": ".jpg", "png": ".png", "webp": ".webp"}
    target_ext = ext_map.get(output_format, source.suffix.lower())
    if output_format == "keep":
        return str(out_dir / name)
    return str(out_dir / (Path(name).stem + target_ext))
