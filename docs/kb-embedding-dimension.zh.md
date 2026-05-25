# 知识库向量维度与 Milvus 不一致

错误示例：

`Embedding dimension 1536 does not match Milvus collection dimension 768`

## 原因

- 全局 `EMBEDDING_DIMENSION`（或 Milvus 集合）为 **768**（如 Ollama `nomic-embed-text`）
- 知识库记录 `embedding_dimension` 为 **1536**（OpenAI 默认值），新建门户知识库现已自动使用全局维度

## 处理已有知识库

**方式 A（推荐）**：删除该知识库后在门户重新创建并上传（新库会使用 768）。

**方式 B**：改库维度并清空向量后重传（MySQL）：

```sql
UPDATE knowledge_bases SET embedding_dimension = 768 WHERE id = '<kb_id>';
DELETE FROM documents WHERE knowledge_base_id = '<kb_id>';
```

然后在门户重新上传文件。若 Milvus 中仍有旧向量，需在 Milvus 侧删除对应 collection/partition 或整库重建。

## 环境对齐（重要）

**推荐在管理后台配置**（知识库页 → **系统默认 Embedding**），写入数据库，服务启动时加载；**不必**在 `.env` 写 `EMBEDDING_*`。

Milvus 集合维度 = 系统默认里的 **向量维度**。提供商/模型产出的向量维度必须与之一致。

| 场景 | 提供商 | 模型示例 | 维度 |
|------|--------|----------|------|
| K8s + 本地 Ollama 网关 | ollama | nomic-embed-text | 768 |
| OpenAI 云端 | openai | text-embedding-3-small | 1536 |

修改系统默认维度并保存后，服务会尝试按新维度重建 Milvus 集合；已有向量需对各知识库执行「全量重嵌入」。

单库 RAG 设置里可覆盖 Embedding；留空则使用系统默认。上传时仍会**对齐**到当前 Milvus 维度，避免 1536/768 混用。

`.env` 中的 `EMBEDDING_*` 仅在**从未在后台保存过**时作为兜底默认值。

## Milvus 地址（非本机）

生产环境一般使用 **K8s 内 Milvus**，无需在本机或 Cloud 服务器上安装 Milvus。

1. 管理后台 → **知识库** → **Milvus 向量库**：填写 K8s 服务地址与端口，启用并**保存**。
2. 配置写入数据库 `settings` 表；服务**启动时**从 DB 加载并连接，`.env` 里的 `MILVUS_HOST` / `MILVUS_ENABLED` 仅为未保存前的默认值。
3. 保存后可用「测试连接」验证；`/api/health` 的 `milvus` 字段为 `connected` / `disconnected` / `disabled`（以 DB 是否启用为准）。
