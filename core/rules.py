import ast
from datetime import datetime
from typing import Any, Dict


_ALLOWED_NAMES = {
    "filename": None,
    "index": None,
    "date": None,
    "time": None,
    "extension": None,
    "width": None,
    "height": None,
    "str": str,
    "int": int,
    "float": float,
    "len": len,
    "lower": str.lower,
    "upper": str.upper,
    "replace": str.replace,
    "startswith": str.startswith,
    "endswith": str.endswith,
    "format": format,
}


def render_template(template: str, values: Dict[str, Any]) -> str:
    result = template
    for key, value in values.items():
        result = result.replace("{" + key + "}", str(value))
    return result


def generate_output_name(source_name: str, config: Dict[str, Any], index: int = 1, current_datetime=None) -> str:
    if config.get("use_advanced_script"):
        return evaluate_safe_script(
            config.get("advanced_script", "return filename + '_' + str(index)"),
            {
                "filename": source_name.rsplit(".", 1)[0] if "." in source_name else source_name,
                "index": index,
                "date": (current_datetime or datetime.now()).strftime("%Y%m%d"),
                "time": (current_datetime or datetime.now()).strftime("%H%M%S"),
                "extension": source_name.rsplit(".", 1)[1].lower() if "." in source_name else "",
                "width": config.get("width", 0),
                "height": config.get("height", 0),
            },
        )

    if config.get("use_template"):
        template = config.get("template_text", "{filename}_{index}{extension}")
        values = {
            "filename": source_name.rsplit(".", 1)[0] if "." in source_name else source_name,
            "index": index,
            "date": (current_datetime or datetime.now()).strftime("%Y%m%d"),
            "time": (current_datetime or datetime.now()).strftime("%H%M%S"),
            "extension": source_name.rsplit(".", 1)[1].lower() if "." in source_name else "",
        }
        return render_template(template, values)

    if config.get("add_number_enabled"):
        digits = max(1, int(config.get("number_digits", 3)))
        prefix = config.get("number_prefix", "")
        suffix = config.get("number_suffix", "")
        number = str(int(config.get("start_index", 1)) + max(0, index - 1)).zfill(digits)
        stem = source_name.rsplit(".", 1)[0] if "." in source_name else source_name
        ext = source_name.rsplit(".", 1)[1].lower() if "." in source_name else ""
        result = f"{stem}{prefix}{number}{suffix}"
        if ext:
            return f"{result}.{ext}"
        return result

    if config.get("add_text_enabled"):
        text = config.get("text_content", "")
        stem = source_name.rsplit(".", 1)[0] if "." in source_name else source_name
        ext = source_name.rsplit(".", 1)[1].lower() if "." in source_name else ""
        result = f"{stem}_{text}"
        if ext:
            return f"{result}.{ext}"
        return result

    return source_name


def evaluate_safe_script(script: str, env: Dict[str, Any]) -> str:
    if not script or not isinstance(script, str):
        raise ValueError("高级脚本为空或格式错误。")
    if "__" in script:
        raise ValueError("脚本包含禁止的双下划线字段。")
    blocked = ["import ", "open(", "os.", "subprocess", "exec(", "eval(", "__import__"]
    if any(token in script for token in blocked):
        raise ValueError("高级脚本包含不允许的操作。")

    try:
        tree = ast.parse(script, mode="eval")
    except SyntaxError as exc:
        raise ValueError(f"脚本语法错误：{exc.msg}") from exc

    allowed = (
        ast.Expression, ast.BinOp, ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod, ast.Pow,
        ast.UnaryOp, ast.USub, ast.UAdd, ast.Call, ast.Attribute, ast.Name, ast.Load,
        ast.Constant, ast.Tuple, ast.List, ast.Dict, ast.Subscript, ast.Compare, ast.Gt,
        ast.GtE, ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.And, ast.Or, ast.BoolOp,
        ast.IfExp, ast.JoinedStr, ast.FormattedValue, ast.Str, ast.keyword, ast.Call
    )
    for node in ast.walk(tree):
        if not isinstance(node, allowed):
            raise ValueError(f"脚本包含不允许的语法节点：{type(node).__name__}")

    safe_env = {**_ALLOWED_NAMES, **env}
    try:
        result = eval(compile(tree, "<safe_script>", "eval"), {"__builtins__": {}}, safe_env)
        return str(result)
    except Exception as exc:
        raise ValueError(f"高级脚本执行失败：{exc}") from exc
