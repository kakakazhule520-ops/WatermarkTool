from core.naming import generate_output_name, render_template


def test_template_name():
    cfg = {"use_template": True, "template_text": "{filename}_{index}{extension}"}
    result = generate_output_name("avatar.png", cfg, index=3)
    assert "avatar_3.png" in result


def test_advanced_script_name():
    cfg = {"use_advanced_script": True, "advanced_script": "filename + '_' + str(index)"}
    result = generate_output_name("photo.jpg", cfg, index=7)
    assert "photo_7" in result
