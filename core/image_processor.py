import json
from pathlib import Path
from typing import Any, Dict, Tuple


def load_rule_file(path: str) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"规则文件不存在：{path}")
    try:
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        raise ValueError(f"规则文件 JSON 格式错误：{exc.msg}") from exc
    if not isinstance(data, dict):
        raise ValueError("规则文件必须是一个 JSON 对象。")
    return data


def merge_rule_config(base_config: Dict[str, Any], rule_data: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(base_config)
    if not isinstance(rule_data, dict):
        return merged
    for key, value in rule_data.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = merge_rule_config(merged[key], value)
        else:
            merged[key] = value
    return merged


def validate_rule_config(rule_data: Dict[str, Any]) -> Tuple[bool, str]:
    if not isinstance(rule_data, dict):
        return False, "规则文件必须是一组键值对。"
    for key, value in rule_data.items():
        if key in {"watermark_width_ratio", "opacity"} and isinstance(value, (int, float)):
            if not (0 <= float(value) <= 1):
                return False, f"{key} 必须在 0~1 之间。"
    return True, ""
