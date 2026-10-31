from pathlib import Path

from PIL import Image

from core.compression import adjust_jpeg_or_webp_quality


def test_adjust_jpeg_quality(tmp_path):
    src = tmp_path / "source.jpg"
    Image.new("RGB", (200, 200), "blue").save(src, "JPEG", quality=85)
    output = tmp_path / "result.jpg"
    output.write_bytes(src.read_bytes())
    q, size = adjust_jpeg_or_webp_quality(str(output), str(src), 50, 85, 5, 30, 95, "JPEG")
    assert q >= 30
    assert size >= 0
