"""Normalize workflow merge sections into report-ready structures."""

from __future__ import annotations

import re
from typing import Any


def _coerce_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (int, float, bool)):
        return str(value)
    return ""


_ANALYSIS_LINE = re.compile(
    r"^\s*\d+\.\s*(.+?):\s*([\d,]+)\s*件?\s*$",
    re.MULTILINE,
)


def _parse_number(raw: str) -> float | None:
    text = (raw or "").strip().replace(",", "")
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _split_table_row(line: str) -> list[str]:
    inner = line.strip().strip("|")
    return [cell.strip() for cell in inner.split("|")]


def _is_separator_row(cells: list[str]) -> bool:
    if not cells:
        return True
    return all(re.fullmatch(r":?-{2,}:?", c.replace(" ", "")) for c in cells if c)


def parse_markdown_table(text: str) -> list[dict[str, Any]]:
    """Extract label/value rows from a markdown pipe table."""
    lines = [ln for ln in text.splitlines() if ln.strip().startswith("|")]
    if len(lines) < 2:
        return []

    header = _split_table_row(lines[0])
    rows: list[dict[str, Any]] = []
    data_lines = lines[1:]
    if data_lines and _is_separator_row(_split_table_row(data_lines[0])):
        data_lines = data_lines[1:]

    for line in data_lines:
        cells = _split_table_row(line)
        if not cells or _is_separator_row(cells):
            continue
        label = ""
        value: float | None = None
        if len(cells) >= 3:
            label = cells[1] or cells[0]
            value = _parse_number(cells[-1])
        elif len(cells) == 2:
            label = cells[0]
            value = _parse_number(cells[1])
        elif len(cells) == 1:
            label = cells[0]
        if label:
            rows.append({"label": label, "value": value})
    return rows


def parse_analysis_lines(text: str) -> list[dict[str, Any]]:
    """Parse patent-search analysis output: ``1. 华为: 120件``."""
    rows: list[dict[str, Any]] = []
    for match in _ANALYSIS_LINE.finditer(text or ""):
        label = (match.group(1) or "").strip()
        value = _parse_number(match.group(2))
        if label:
            rows.append({"label": label, "value": value})
    return rows


def _extract_result_body(result: Any) -> tuple[str, list[dict[str, Any]]]:
    if result is None:
        return "", []
    if isinstance(result, str):
        text = result.strip()
        return text, parse_markdown_table(text)
    if not isinstance(result, dict):
        return _coerce_text(result), []

    text_parts: list[str] = []
    for key in ("message", "text", "content", "summary", "output", "value"):
        part = _coerce_text(result.get(key))
        if part:
            text_parts.append(part)

    rows: list[dict[str, Any]] = []
    for key in ("rows", "data", "items", "series"):
        raw = result.get(key)
        if isinstance(raw, list):
            for item in raw:
                if isinstance(item, dict):
                    label = _coerce_text(
                        item.get("label")
                        or item.get("name")
                        or item.get("applicant")
                        or item.get("dimension")
                        or item.get("key")
                    )
                    value = item.get("value")
                    if value is None:
                        value = item.get("count") or item.get("total") or item.get("num")
                    num = value if isinstance(value, (int, float)) else _parse_number(str(value or ""))
                    if label:
                        rows.append({"label": label, "value": num})
                elif isinstance(item, (list, tuple)) and len(item) >= 2:
                    rows.append(
                        {
                            "label": _coerce_text(item[0]),
                            "value": _parse_number(str(item[1])),
                        }
                    )

    text = "\n\n".join(text_parts)
    if not rows and text:
        rows = parse_markdown_table(text)
    if not rows and text:
        rows = parse_analysis_lines(text)
    return text, rows


def normalize_sections(sections_raw: Any) -> list[dict[str, Any]]:
    """Return [{title, text, rows}] from workflow merge payload or list."""
    sections: list[dict[str, Any]] = []

    if isinstance(sections_raw, list):
        for idx, item in enumerate(sections_raw):
            if isinstance(item, dict):
                title = _coerce_text(item.get("title") or item.get("name")) or f"Section {idx + 1}"
                text, rows = _extract_result_body(item.get("result") or item)
                sections.append({"title": title, "text": text, "rows": rows})
        return sections

    if not isinstance(sections_raw, dict):
        if sections_raw:
            text = _coerce_text(sections_raw)
            sections.append({"title": "Report", "text": text, "rows": parse_markdown_table(text)})
        return sections

    for title, payload in sections_raw.items():
        title_str = _coerce_text(title) or "Section"
        if isinstance(payload, dict) and "result" in payload:
            text, rows = _extract_result_body(payload.get("result"))
        else:
            text, rows = _extract_result_body(payload)
        sections.append({"title": title_str, "text": text, "rows": rows})
    return sections
