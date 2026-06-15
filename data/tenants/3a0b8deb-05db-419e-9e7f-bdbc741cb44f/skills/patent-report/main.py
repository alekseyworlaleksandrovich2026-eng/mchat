"""Patent workflow report export — charts, Excel, Word, PowerPoint."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

_SKILL_DIR = Path(__file__).resolve().parent
if str(_SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(_SKILL_DIR))

from charts import generate_charts
from excel_export import export_excel
from io_utils import report_output_dir, sanitize_filename
from narrative import build_report_narrative
from ppt_export import export_ppt
from sections import normalize_sections
from word_export import export_word

_COMMANDS = frozenset({"chart", "excel", "word", "ppt", "all"})


def _fail(message: str) -> dict[str, Any]:
    return {"ok": False, "message": message}


def _resolve_title(title: str | None, filename: str | None) -> str:
    if title and str(title).strip():
        return str(title).strip()
    if filename and str(filename).strip():
        return str(filename).strip()
    return "Patent Analysis Report"


def _resolve_filename(filename: str | None, title: str) -> str:
    if filename and str(filename).strip():
        return sanitize_filename(str(filename).strip())
    return sanitize_filename(title)


def _format_links(files: list[dict[str, Any]]) -> str:
    lines = []
    for item in files:
        url = item.get("url") or ""
        name = item.get("filename") or item.get("format") or "file"
        if url:
            lines.append(f"- [{name}]({url})")
    return "\n".join(lines)


def run(
    command: str = "chart",
    sections: Any = None,
    title: str | None = None,
    filename: str | None = None,
    charts: Any = None,
    **kwargs: Any,
) -> dict[str, Any]:
    cmd = (command or "chart").strip().lower()
    if cmd not in _COMMANDS:
        return _fail(f"未知 command: {command!r}，可选: {', '.join(sorted(_COMMANDS))}")

    normalized = normalize_sections(sections)
    if not normalized:
        return _fail("sections 为空，请先连接 merge 节点或传入分析结果。")

    report_title = _resolve_title(title, filename)
    base_name = _resolve_filename(filename, report_title)
    out_dir, key_prefix = report_output_dir(base_name)
    narrative = build_report_narrative(normalized, title=report_title)

    existing_charts: list[dict[str, Any]] = []
    if isinstance(charts, list):
        existing_charts = [c for c in charts if isinstance(c, dict)]
    elif isinstance(charts, dict):
        existing_charts = [charts]

    generated_charts: list[dict[str, Any]] = []
    files: list[dict[str, Any]] = []

    if cmd in ("chart", "all"):
        generated_charts = generate_charts(
            normalized,
            out_dir=out_dir,
            key_prefix=key_prefix,
            title=report_title,
        )
        if cmd == "chart":
            files.extend(generated_charts)

    chart_assets = existing_charts or generated_charts

    narrative_kwargs = {
        "summary": narrative.get("summary") or "",
        "interpretation": narrative.get("interpretation") or "",
    }

    if cmd in ("excel", "all"):
        files.append(
            export_excel(
                normalized,
                out_dir=out_dir,
                key_prefix=key_prefix,
                title=report_title,
                filename=base_name,
                **narrative_kwargs,
            )
        )
    if cmd in ("word", "all"):
        files.append(
            export_word(
                normalized,
                out_dir=out_dir,
                key_prefix=key_prefix,
                title=report_title,
                filename=base_name,
                charts=chart_assets,
                **narrative_kwargs,
            )
        )
    if cmd in ("ppt", "all"):
        files.append(
            export_ppt(
                normalized,
                out_dir=out_dir,
                key_prefix=key_prefix,
                title=report_title,
                filename=base_name,
                charts=chart_assets,
                **narrative_kwargs,
            )
        )

    if not files:
        return _fail("未生成任何文件（可能各 section 缺少可绘制的数值行）。")

    links = _format_links(files)
    narrative_block = ""
    if narrative_kwargs["summary"]:
        narrative_block += f"\n\n### 总结\n{narrative_kwargs['summary']}"
    if narrative_kwargs["interpretation"]:
        narrative_block += f"\n\n### 解读\n{narrative_kwargs['interpretation']}"
    message = f"已生成 {len(files)} 个文件（{cmd}）。{narrative_block}\n{links}".strip()
    return {
        "ok": True,
        "command": cmd,
        "title": report_title,
        "sections_count": len(normalized),
        "summary": narrative_kwargs["summary"],
        "interpretation": narrative_kwargs["interpretation"],
        "charts": generated_charts or existing_charts,
        "files": files,
        "message": message,
    }
