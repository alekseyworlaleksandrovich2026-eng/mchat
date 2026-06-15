"""Generate chart PNGs from normalized sections."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from charts_fonts import apply_font_to_figure, configure_matplotlib_cjk, get_cjk_font_properties
from io_utils import file_artifact, sanitize_filename
from text_utils import clean_chart_label

_YEAR_LABEL = re.compile(r"^\d{4}$")


def _chart_rows(section: dict[str, Any], *, limit: int = 15) -> list[tuple[str, float]]:
    rows: list[tuple[str, float]] = []
    for row in section.get("rows") or []:
        label = clean_chart_label(str(row.get("label") or ""))
        value = row.get("value")
        if not label or not isinstance(value, (int, float)):
            continue
        rows.append((label, float(value)))
    rows.sort(key=lambda item: item[1], reverse=True)
    return rows[:limit]


def _is_year_series(labels: list[str]) -> bool:
    if not labels:
        return False
    return all(_YEAR_LABEL.match(lbl.strip()) for lbl in labels)


def generate_charts(
    sections: list[dict[str, Any]],
    *,
    out_dir: Path,
    key_prefix: str,
    title: str,
) -> list[dict[str, Any]]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    configure_matplotlib_cjk(plt)
    cjk_font = get_cjk_font_properties()

    charts: list[dict[str, Any]] = []
    report_title = clean_chart_label(title)

    for section in sections:
        rows = _chart_rows(section)
        if not rows:
            continue

        labels = [lbl[:40] for lbl, _ in rows]
        values = [value for _, value in rows]
        section_title = clean_chart_label(str(section.get("title") or "图表"))
        year_series = _is_year_series(labels)

        if year_series:
            labels_sorted = sorted(labels, key=lambda x: int(x) if x.isdigit() else x)
            value_by_label = dict(zip(labels, values))
            labels = labels_sorted
            values = [value_by_label[lbl] for lbl in labels]
            fig, ax = plt.subplots(figsize=(10, max(3.5, 0.45 * len(labels) + 2)))
            ax.bar(labels, values, color="#3b82f6")
            ax.set_ylabel("数量（件）", fontproperties=cjk_font)
            ax.set_xlabel("年份", fontproperties=cjk_font)
            if cjk_font:
                for label in ax.get_xticklabels():
                    label.set_fontproperties(cjk_font)
                    label.set_rotation(45)
                    label.set_ha("right")
                for label in ax.get_yticklabels():
                    label.set_fontproperties(cjk_font)
        else:
            fig_h = max(3.0, min(10.0, 0.35 * len(labels) + 1.5))
            fig, ax = plt.subplots(figsize=(10, fig_h))
            y_pos = range(len(labels))
            ax.barh(list(y_pos), values, color="#3b82f6")
            ax.set_yticks(list(y_pos))
            if cjk_font:
                ax.set_yticklabels(labels, fontproperties=cjk_font)
            else:
                ax.set_yticklabels(labels)
            ax.invert_yaxis()
            ax.set_xlabel("数量（件）", fontproperties=cjk_font)

        chart_heading = f"{report_title} · {section_title}"
        if cjk_font:
            ax.set_title(chart_heading, fontproperties=cjk_font)
        else:
            ax.set_title(chart_heading)

        apply_font_to_figure(fig, cjk_font)
        fig.tight_layout()

        fname = sanitize_filename(section_title or "chart", default="chart") + ".png"
        path = out_dir / fname
        fig.savefig(path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        key = f"{key_prefix}/{fname}"
        charts.append(
            {
                "name": section_title or fname,
                **file_artifact(path, key, fmt="png"),
            }
        )
    return charts
