# patent-report

MChat Workflow 报表导出：从 merge 节点 `sections` 生成图表 PNG，并导出 Excel / Word / PowerPoint。

## 子命令

| command | 输出 |
|---------|------|
| `chart` | 各维度横向柱状图 PNG |
| `excel` | 多 Sheet 工作簿 |
| `word` | `.docx` |
| `ppt` | `.pptx` |
| `all` | 上述全部 |

## MChat 集成

在 mchat `src/backend/.env`：

```env
EXTRA_SKILLS_DIRS=/path/to/patent-skills
PATENT_WORKFLOW_REPORT_SKILL=patent-report
```

然后：`make patent-skills-reload`（在 mchat 仓库内）。

## 依赖

- `matplotlib`, `openpyxl`, `python-docx`, `python-pptx`（mchat `requirements-lite.txt` 已声明）

无需 9235 API Token。
