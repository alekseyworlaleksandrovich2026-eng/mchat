import json
import csv
import io
from typing import List, Dict, Any

def run(args: str) -> str:
    """
    将JSON数组或CSV字符串转换为Markdown表格。
    参数: args - 用户输入的原始字符串。
    返回: Markdown表格字符串。
    """
    text = args.strip()
    if not text:
        return "请提供JSON或CSV数据。"

    # 尝试解析为JSON
    try:
        data = json.loads(text)
        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
            return _json_to_table(data)
        else:
            return "错误：JSON必须是对象数组。"
    except json.JSONDecodeError:
        pass

    # 尝试解析为CSV
    try:
        reader = csv.DictReader(io.StringIO(text))
        rows = list(reader)
        if rows:
            return _dicts_to_table(rows)
        else:
            return "错误：CSV数据为空或格式无效。"
    except Exception:
        return "错误：无法解析输入。请提供有效的JSON数组或CSV文本。"

def _json_to_table(data: List[Dict[str, Any]]) -> str:
    return _dicts_to_table(data)

def _dicts_to_table(rows: List[Dict[str, Any]]) -> str:
    if not rows:
        return "无数据。"
    headers = list(rows[0].keys())
    # 构建Markdown表格
    header_line = "|" + "|".join(headers) + "|"
    separator = "|" + "|".join(["---"] * len(headers)) + "|"
    body_lines = []
    for row in rows:
        values = [str(row.get(h, "")) for h in headers]
        body_lines.append("|" + "|".join(values) + "|")
    return header_line + "\n" + separator + "\n" + "\n".join(body_lines)