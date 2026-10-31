from pathlib import Path

from core.file_manager import build_output_path, scan_image_files, validate_source_dir


def test_scan_valid_files(tmp_path):
    (tmp_path / "a.jpg").write_bytes(b"0")
    (tmp_path / "b.png").write_bytes(b"0")
    (tmp_path / "c.txt").write_bytes(b"0")
    files = scan_image_files(str(tmp_path))
    assert len(files) == 2


def test_build_output_path_avoids_source_overwrite(tmp_path):
    src = tmp_path / "sample.jpg"
    src.write_bytes(b"0")
    out = build_output_path(str(src), str(tmp_path), "keep")
    assert out != str(src)


def test_validate_source_dir(tmp_path):
    ok, msg = validate_source_dir(str(tmp_path))
    assert ok is True
    assert msg == ""
