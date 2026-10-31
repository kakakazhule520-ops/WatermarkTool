from pathlib import Path

from PIL import Image

from core.image_processor import process_one_image


def test_jpg_watermark(tmp_path):
    src = tmp_path / "source.jpg"
    watermark = tmp_path / "watermark.png"
    Image.new("RGB", (200, 200), "white").save(src, "JPEG")
    Image.new("RGBA", (100, 50), (255, 0, 0, 180)).save(watermark, "PNG")
    output = tmp_path / "out" / "result.jpg"
    ok, msg, path = process_one_image(str(src), str(output), str(watermark), {
        "watermark_width_ratio": 0.5,
        "opacity": 0.7,
        "horizontal_alignment": "right",
        "vertical_alignment": "bottom",
        "offset_x": 5,
        "offset_y": 5,
        "output_format": "keep",
        "fixed_quality": 85,
    })
    assert ok is True
    assert output.exists()


def test_png_transparency(tmp_path):
    src = tmp_path / "source.png"
    watermark = tmp_path / "watermark.png"
    Image.new("RGBA", (200, 200), (0, 0, 0, 255)).save(src, "PNG")
    Image.new("RGBA", (80, 80), (255, 255, 255, 128)).save(watermark, "PNG")
    out = tmp_path / "out" / "result.png"
    ok, _, _ = process_one_image(str(src), str(out), str(watermark), {
        "watermark_width_ratio": 0.4,
        "opacity": 0.5,
        "horizontal_alignment": "center",
        "vertical_alignment": "center",
        "offset_x": 0,
        "offset_y": 0,
        "output_format": "png",
    })
    assert ok is True
    assert out.exists()
