---
name: patent-report
description: 专利工作流报表导出 — 从 merge 汇总结果生成图表 PNG，并导出 Excel / Word / PowerPoint。
type: tool
workflow_role: export
parameters: {"type":"object","properties":{"command":{"type":"string","enum":["chart","excel","word","ppt","all"],"description":"chart=PNG 图表；excel/word/ppt=单格式；all=图表+三种 Office 文件"},"sections":{"type":"object","description":"工作流 merge 节点输出的 sections（${nodes.merge.sections}）"},"title":{"type":"string","description":"报告标题"},"filename":{"type":"string","description":"输出文件名（不含扩展名）"},"charts":{"type":"array","description":"上游 chart 节点输出的 charts（export 节点可选 ${nodes.chart.charts}）"}},"required":["command"]}
---

# Patent Report Export

将工作流 **merge** 节点汇总的各维度分析结果，转为可视化图表与 Office 报告。

## 子命令

| command | 输出 |
|---------|------|
| `chart` | 每个有数值行的 section 生成横向柱状图 PNG |
| `excel` | 多 Sheet 工作簿（Summary + 各维度） |
| `word` | `.docx` 报告（含表格，可嵌入上游图表） |
| `ppt` | `.pptx` 演示稿（每 section 一页） |
| `all` | 上述全部（推荐作为工作流最终导出节点） |

## 工作流用法

1. **图表节点**（visualize）：`command=chart`，`sections=${nodes.merge.sections}`
2. **导出节点**（export）：`command=all`，`sections=${nodes.merge.sections}`，`charts=${nodes.chart.charts}`

文件写入 `MCHAT_UPLOAD_DIR/workflow_reports/`，返回 `files[].url` 签名下载链接。

## 输入格式

`sections` 支持 merge 结构：

```json
{
  "申请人分析": { "node_id": "...", "result": { "message": "| 排名 | 申请人 | 数量 |\n..." } }
}
```

也支持带 `rows` / `data` 的结构化结果。
