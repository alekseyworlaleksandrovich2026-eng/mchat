"""Rule-based executive summary and interpretation for patent workflow reports."""

from __future__ import annotations

from typing import Any


def _numeric_rows(section: dict[str, Any]) -> list[tuple[str, float]]:
    out: list[tuple[str, float]] = []
    for row in section.get("rows") or []:
        label = str(row.get("label") or "").strip()
        value = row.get("value")
        if not label or not isinstance(value, (int, float)):
            continue
        out.append((label, float(value)))
    out.sort(key=lambda x: x[1], reverse=True)
    return out


def build_report_narrative(
    sections: list[dict[str, Any]],
    *,
    title: str = "专利分析报告",
) -> dict[str, str]:
    data_sections: list[tuple[str, list[tuple[str, float]]]] = []
    for section in sections:
        rows = _numeric_rows(section)
        if rows:
            name = str(section.get("title") or "分析维度").strip()
            data_sections.append((name, rows))

    if not data_sections:
        text = str(sections[0].get("text") if sections else "").strip()
        if text:
            preview = text[:400] + ("…" if len(text) > 400 else "")
            return {
                "summary": f"《{title}》已汇总 {len(sections)} 个分析模块，主要结论见各章节文本。",
                "interpretation": preview or "当前结果以描述性文本为主，建议结合检索明细进一步研判。",
            }
        return {
            "summary": f"《{title}》暂无可量化的统计维度，请确认上游 merge/分析节点已输出表格或统计行。",
            "interpretation": "建议检查工作流中检索、分析节点是否执行成功，并确认 payload 含 applicants/status 等字段。",
        }

    total_points = sum(len(rows) for _, rows in data_sections)
    summary_parts = [
        f"《{title}》共覆盖 {len(data_sections)} 个可量化维度、{total_points} 条统计项。",
    ]

    insight_parts: list[str] = []
    for name, rows in data_sections[:6]:
        top = rows[0]
        total = sum(v for _, v in rows)
        share = (top[1] / total * 100) if total > 0 else 0.0
        summary_parts.append(
            f"「{name}」居首为 {top[0]}（{top[1]:,.0f}），"
            f"合计 {total:,.0f}，Top1 占比约 {share:.1f}%。"
        )
        if share >= 40:
            insight_parts.append(
                f"「{name}」呈现明显头部集中（{top[0]} 约占 {share:.0f}%），"
                "需重点关注其专利布局与潜在侵权/无效风险。"
            )
        elif len(rows) >= 5 and rows[4][1] > 0:
            insight_parts.append(
                f"「{name}」竞争主体较多（前五合计覆盖主要份额），"
                "适合结合同族与法律状态做分层监控。"
            )
        else:
            insight_parts.append(
                f"「{name}」分布相对分散，可优先跟踪 Top3："
                + "、".join(lbl for lbl, _ in rows[:3])
                + "。"
            )

    if len(data_sections) > 1:
        insight_parts.append(
            "多维度联合看：建议将申请人/状态/年份等交叉比对，识别高增长主体与失效专利池。"
        )

    return {
        "summary": "\n".join(summary_parts),
        "interpretation": "\n".join(insight_parts[:8]),
    }
