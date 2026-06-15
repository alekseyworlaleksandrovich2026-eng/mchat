# MChat Workflow Orchestrator — Complete Guide

> This document covers the workflow orchestration design, node types, field linking syntax, skill I/O, execution engine, and best practices.

---

## Table of Contents

1. [Architecture Overview](#1-Architecture Overview)
2. [Node Types & Configuration](#2-Node Types & Configuration)
3. [Field Linking Syntax](#3-Field Linking Syntax)
4. [Skill Input & Output](#4-skill-输入与输出)
5. [Execution Engine](#5-Execution Engine)
6. [Conditional Branching](#6-Conditional Branching)
7. [Loop Node (Batch)](#7-循环节点batch)
8. [Approval Node](#8-Approval Node)
9. [Merge Node](#9-Merge Node)
10. [Node Groups](#10-Node Groups)
11. [Template System](#11-Template System)
12. [API Reference](#12-api-参考)
13. [Best Practices](#13-Best Practices)

---

## 1. Architecture Overview

```
┌─ Frontend (React + ReactFlow)─────────────────────────────────┐
│                                                            │
│  WorkflowGraphPage (Standalone full-screen page)                           │
│    ├─ WorkflowSidebar    Left panel: node tree + presets                │
│    ├─ ReactFlow 画布     Drag-and-drop + double-click search + context menu      │
│    ├─ WorkflowNodeSearch Double-click node search popup                 │
│    ├─ Right panel: properties       Node config + PayloadMapper            │
│    └─ Overlays               Template gallery / run history / results      │
│                                                            │
├─ Backend (FastAPI + SQLAlchemy)──────────────────────────────┤
│                                                            │
│  workflow_service.py                                       │
│    └─ _execute_graph_workflow()                            │
│         ├─ Topological sort → layer-by-layer concurrent execution                          │
│         ├─ _render_template()  Render ${} template variables            │
│         ├─ _resolve_path()     Dot-path resolution (incl. list index)│
│         └─ execute_skill()     Invoke skill executor            │
│                                                            │
│  skill/executor.py → workspace/skill_runner.py             │
│    └─ Python tool / CLI adapter / container execution                     │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### Key Files

| 文件 | Responsibility |
|------|------|
| `src/backend/app/services/workflow_service.py` | Execution Engine（拓扑Sort、模板渲染、节点分发） |
| `src/backend/app/skill/executor.py` | Skill execution entry (Python tool / Webhook) |
| `src/backend/app/workspace/skill_runner.py` | Local / in-container script execution |
| `src/backend/app/schemas/workflow.py` | Data models (Graph / Node / Edge) |
| `src/backend/app/data/workflow_templates.py` | Built-in template definitions |
| `src/frontend/src/components/workflow/WorkflowGraphEditor.tsx` | Graph editor main component |
| `src/frontend/src/components/workflow/PayloadMapper.tsx` | Skill parameter mapping UI |

---

## 2. Node Types & Configuration

### 2.1 Node Types Overview

| Type | Color | Icon | Purpose | Executes? |
|------|------|------|------|-------------|
| `start` | 🟢 #22c55e | ▶ CirclePlay | Defines input fields, receives user input | ✅ |
| `skill` | 🔵 #3b82f6 | 🔧 Wrench | Executes a skill | ✅ |
| `condition` | 🟡 #f59e0b | ⊕ Split | Conditional Branching | ✅ |
| `merge` | 🟣 #6366f1 | ⋈ GitMerge | Aggregates multiple upstream results | ✅ |
| `batch` | 🔵 #06b6d4 | 🔁 Repeat | Iterates a list, runs sub-workflow per item | ✅ |
| `approval` | 🔴 #ef4444 | 🛡 ShieldCheck | Human approval pause | ✅ |
| `end` | 🟣 #a855f7 | ■ Square | Aggregates final output | ✅ |
| `group` | ⬜ #64748b | ▢ Box | Visual grouping (not executed) | ❌ |

### 2.2 Node config Fields

#### start 节点

```jsonc
{
  "type": "start",
  "config": {
    "input_fields": [
      {
        "key": "keyword",          // Field key, referenced downstream via ${input.keyword} 引Use
        "label": "Keyword",          // Form display label
        "placeholder": "Enter search keyword",
        "required": true,           // Required validation at runtime
        "type": "text"              // text | multiline | number | file
      },
      {
        "key": "industry",
        "label": "Industry",
        "required": false,
        "type": "text"
      }
    ]
  }
}
```

#### skill 节点

```jsonc
{
  "type": "skill",
  "config": {
    "skill_id": "uuid-xxx",        // Skill ID (preferred)
    "skill_name": "patent-search", // Or use name (fallback)
    "workflow_role": "search",     // 分类：search/analyze/visualize/export/other
    "payload_template": {           // Parameters passed to skill (supports ${} 模板）
      "command": "search",
      "query": "${input.keyword}",
      "industry": "${input.industry}"
    },
    "retry_count": 0,              // Retry count on failure
    "timeout_seconds": 0           // Timeout seconds (0 = unlimited)
  }
}
```

#### condition 节点

```jsonc
{
  "type": "condition",
  "config": {
    "left": "input.keyword",       // Left value path (resolved via _resolve_path)
    "op": "==",                    // Operator (see table below)
    "right": "AI"                  // Right value (also supports ${} template variables）
  }
}
```

**Supported Operators：**

| op | Description | Type |
|----|------|------|
| `==` | Equal to | 任意 |
| `!=` | 不Equal to | 任意 |
| `>` | Greater than | 数字 |
| `<` | Less than | 数字 |
| `>=` | Greater thanEqual to | 数字 |
| `<=` | Less thanEqual to | 数字 |
| `contains` | Contains substring | 字符串 |
| `not_contains` | 不Contains substring | 字符串 |
| `startswith` | Prefix match | 字符串 |
| `endswith` | Suffix match | 字符串 |

> **Note**：`left` 和 `right` Both support `${}` template variables。`left` resolved via path（如 `input.keyword`），`right` rendered via template（如 `${nodes.x.result.field}` or static value）。

#### merge 节点

```jsonc
{
  "type": "merge",
  "config": {
    "merge_mode": "sections"   // Currently the only supported mode
  }
}
```

Aggregates all upstream node results into a `sections` dict, indexed by node name。

#### batch 节点

```jsonc
{
  "type": "batch",
  "config": {
    "list_path": "nodes.search.result.patent_ids",  // List data source
    "max_concurrent": 3                              // Max concurrency
  }
}
```

batch 节点的子节点通过 `parentId` 关联，在画布上放在 batch 容器内。子节点目前仅支持 `skill` Type。

#### approval 节点

No config. Pauses execution until human approval.

#### end 节点

No config. Auto-aggregates all executed node outputs.

#### group 节点

```jsonc
{
  "type": "group",
  "config": {
    "color": "#3b82f6",     // 组Color
    "collapsed": false,     // Collapsed
    "width": 280,           // Width
    "height": 160           // Height
  }
}
```

Pure visual container, not executed.

---

## 3. Field Linking Syntax

### 3.1 Variable Namespaces

Execution Engine维护一个 `outputs` context：

```python
outputs = {
    "input": { ... },          # start node user input
    "nodes": {                  # Per-node execution results
        "search": { "patent_ids": [...], "count": 42 },
        "merge": { "sections": { ... } },
    }
}
```

batch 循环中额外有：

```python
outputs = {
    ...,
    "item": { "line": "Patent标题" },  # Current iteration item
    "item_value": "Patent标题"          # Current item value
}
```

### 3.2 Variable Reference Syntax

| 语法 | Meaning | Example |
|------|------|------|
| `${input.KEY}` | Reference start node input | `${input.keyword}` |
| `${nodes.ID}` | Reference entire node result (dict) | `${nodes.search}` |
| `${nodes.ID.FIELD}` | Reference node result sub-field | `${nodes.search.patent_ids}` |
| `${nodes.ID.FIELD.0}` | Reference list item at index 0 | `${nodes.search.results.0.title}` |
| `${nodes.merge.sections}` | merge node aggregated result | `${nodes.merge.sections}` |
| `${item}` | batch Current iteration item（整段保留Type） | `${item}` |
| `${item.KEY}` | batch current item sub-field | `${item.line}` |
| `${item_value}` | batch current item scalar value | `${item_value}` |

### 3.3 Type Preservation Rules

Template rendering has two modes：

**Full match**（value is entirely a `${...}`）→ **Original type preserved**：

```jsonc
// payload_template:
{ "sections": "${nodes.merge.sections}" }
// Rendered result（sections is dict, passed as-is）：
{ "sections": { "search": {...}, "analyze": {...} } }
```

**Partial replacement**（value contains embedded `${...}`）→ **All converted to string**：

```jsonc
// payload_template:
{ "title": "Report：${input.keyword}（${input.industry}）" }
// Rendered result：
{ "title": "Report：AI（半导体）" }
```

> **Key difference**：To pass dict/list/number to a skill, the entire value must be just `"${...}"`，without mixing in other text。

### 3.4 Unsupported Syntax

| 不支持 | Description | 替代方案 |
|--------|------|---------|
| 数组索引 `[N]` | Use `.N` instead | `${nodes.x.list.0}` ✅ |
| Default value `${a:-b}` | — | Use condition 节点预处理 |
| Filter `${a|upper}` | — | Handle inside skill |
| Arithmetic | — | Calculate inside skill |
| Nested interpolation `${${var}}` | — | — |

---

## 4. Skill Input & Output

### 4.1 Skill 输入

Skills receive parameters via `payload_template` 接收参数。模板Rendered result，结果作为 `args` dict to the skill executor.

**payload_template Example：**

```jsonc
{
  "command": "search",
  "query": "${input.keyword}",
  "year_from": "${input.year_from}",
  "sort": "s"
}
```

Rendered result传给 Skill 的 `args`：

```python
args = {
    "command": "search",
    "query": "人工智能",
    "year_from": "2020",
    "sort": "s"
}
```

### 4.2 Skill 输入参数声明

Skill 可通过 `SKILL.md` Declare parameters (shown in PayloadMapper UI)：

```markdown
---
workflow_fields: [{"key":"query","label":"Search keyword","type":"string","required":true},{"key":"sort","label":"Sort","type":"select","options":["s","d","p"]}]
---
```

### 4.3 Skill 输出格式

Skill return values are normalized：

| Return type | Normalized result |
|---------|-----------|
| `dict` | Kept as-is |
| `str` / `int` / `float` / `bool` | `{"value": ...}` |
| `list` | Kept as-is |
| `None` | `{"ok": true}` |

典型 Skill Return：

```python
return {
    "patent_ids": ["CN123", "CN456"],
    "count": 2,
    "results": [{"title": "...", "patent_id": "CN123"}],
    # 可选：文件产出
    "files": [{"name": "report.xlsx", "path": "/tmp/report.xlsx"}],
    "charts": [{"name": "trend.png", "path": "/tmp/trend.png"}],
}
```

### 4.4 Skill ReturnField约定

| Field | Type | Description |
|------|------|------|
| `patent_ids` | `list[str]` | Patent ID list (patent search skills) |
| `results` | `list[dict]` | Detailed results list |
| `count` | `int` | Result count |
| `sections` | `dict` | 分段内容（merge 节点常Use） |
| `files` | `list[dict]` | File output (auto-renamed to `report_files`） |
| `charts` | `list[dict]` | Chart output (auto-copied as `report_charts`） |
| `stdout` | `str` | CLI mode stdout |
| `error` | `str` | Error message (engine treats as failure) |

---

## 5. Execution Engine

### 5.1 Topological Execution Flow

```
1. Parse graph → build incoming/outgoing adjacency
2. Initialize ready queue = [start 节点 + nodes with no incoming edges]
3. while ready:
     batch = ready 中未完成的节点
     results = asyncio.gather(execute batch concurrently)  ← each node gets independent DB session
     for each result:
       - success → add to done, write to outputs
       - paused  → record pause reason, continue processing siblings
       - failed  → add to done (marked failed), continue
     Update ready based on completed nodes (check deps satisfied)
     If paused → stop scheduling new nodes
4. Return (status, error, payload)
```

### 5.2 Concurrency Safety

- 每个并发执行的节点使Use独立的 `AsyncSession`（`async_session_factory()`）
- batch children also get independent sessions
- Avoids "This session is already handling a request" error

### 5.3 Retry & Timeout

Skill nodes support：

| Config | Description |
|------|------|
| `retry_count` | Retry count on failure (default 0) |
| `timeout_seconds` | Single execution timeout (0 = unlimited) |

---

## 6. Conditional Branching

### 6.1 How It Works

1. `condition` 节点evaluates `left op right`，producing `True` 或 `False`
2. Based on**出边的 condition Field**selects which branch to follow

### 6.2 Edge condition values

| edge.condition | Meaning |
|----------------|------|
| `"true"` | Taken when condition is True |
| `"false"` | Taken when condition is False |
| `"default"` 或空 | Always taken (fallback) |

### 6.3 Example

```
[condition: input.keyword == "AI"]
    ├──(condition="true")──→ [skill: AI Analysis]
    └──(condition="false")─→ [skill: 通UseAnalysis]
```

---

## 7. Loop Node (Batch)

### 7.1 How It Works

1. From `list_path` resolve list data
2. for each item in the list `item`，Creates独立执行context
3. by `max_concurrent` concurrent sub-workflow execution
4. sub-workflow skill nodes reference via `${item}` / `${item_value}` 引Use当前项

### 7.2 List Resolution Rules

| list_path Return值 | Processing |
|-----------------|---------|
| `list` | Iterate directly |
| JSON string (starting with `[` ) | Parse as list |
| Plain string | by换行分割为 `[{line: "xxx"}, ...]` |

### 7.3 子节点context

```python
local_outputs = {
    "input": ...,          # inherits parent input
    "nodes": ...,          # inherits parent node results snapshot
    "item": item,          # Current iteration item
    "item_value": ...,     # Current item value（dict+line 键取 line 值）
}
```

---

## 8. Approval Node

When execution reaches `approval` node：

1. Creates `SkillWorkflowApproval` record（status=pending）
2. Workflow pauses（status=paused）
3. Use户通过 API 审批 → resumes execution

### Approval API

| Endpoint | Description |
|------|------|
| `GET /workflows/approvals/pending` | List pending approvals |
| `POST /workflows/approvals/{id}/approve` | Approve |
| `POST /workflows/approvals/{id}/reject` | Reject |
| `POST /workflows/runs/{id}/resume` | Resume paused run |

---

## 9. Merge Node

Aggregates results from multiple upstream branches。

### Output Structure (sections mode)

```python
{
    "sections": {
        "Search": {"node_id": "search", "result": {...}},
        "Analysis": {"node_id": "analyze", "result": {...}},
        "Chart": {"node_id": "chart", "result": {...}},
    },
    "merged": True
}
```

Downstream nodes reference via `${nodes.merge.sections}` 引Use整个聚合结果。

---

## 10. Node Groups

Visual grouping container, not executed.

| Operation | Method |
|------|------|
| Creates | Select ≥2 nodes → `Cmd/Ctrl+G` or right-click → Group Selected |
| Rename | Double-click title |
| Change color | Click color dot |
| Collapse | Click chevron (hides children) |
| Delete | Delete组 → 子节点自动解除归属（不被Delete） |

---

## 11. Template System

### Built-in Templates

| ID | Name | Description |
|----|------|------|
| `patent_report_multidim` | Multi-dimensional patent analysis report | search→analyze→chart→export |
| `batch_url_fetch` | Batch URL fetch | batch loop + skill |
| `web_fetch` | Web page fetch | single-skill workflow |
| `notify_ping_test` | Notification test | notification pipeline test |

### Template Structure

```jsonc
{
  "id": "xxx",
  "name": "模板名",
  "description": "Description",
  "category": "patent",      // patent | notification | general
  "locale": "zh",            // zh | en
  "graph_json": { "version": 1, "nodes": [...], "edges": [...] }
}
```

---

## 12. API Reference

### 工作流 CRUD

| Method | Path | Description |
|------|------|------|
| GET | `/workflows` | List all |
| GET | `/workflows/wf/{id}` | Get single |
| POST | `/workflows` | Creates |
| PATCH | `/workflows/{id}` | Update (incl. graph_json) |
| DELETE | `/workflows/{id}` | Delete |

### 运行

| Method | Path | Description |
|------|------|------|
| POST | `/workflows/{id}/run-once` | Trigger run |
| GET | `/workflows/runs/list` | Run list |
| GET | `/workflows/runs/{id}` | Run detail |
| POST | `/workflows/runs/{id}/resume` | Resume paused |
| DELETE | `/workflows/runs/{id}` | Delete运行 |

### 模板

| Method | Path | Description |
|------|------|------|
| GET | `/workflows/templates` | Template list |
| POST | `/workflows/from-template/{id}` | From模板Creates |
| POST | `/workflows/{id}/save-as-template` | Save as template |

---

## 13. Best Practices

### 13.1 Naming Conventions

- 节点名Use中文短词（Search、Analysis、Chart、Export），for easy `${nodes.Search.result}` 引Use
- 或Use英文 ID 并在 name 中标注

### 13.2 error处理

- Set for critical skills `retry_count: 1-2`
- Set for long-running skills `timeout_seconds`
- Use condition 节点检查上游结果是否为空，避免下游报错

### 13.3 Performance

- batch `max_concurrent` recommended 3-5（too high triggers external API rate limits）
- Merge Node放扇出分支汇聚点
- Consider pagination for large datasets

### 13.4 Debugging Tips

- Insert condition nodes between skills to check intermediate values
- Use JSON 标签页直接查看/编辑 graph 结构
- Run history → Results panel to inspect each node output
- Double-click canvas for quick node search
