# AI 智能客服平台使用手册

## 产品概述

AI 智能客服平台是一个基于大语言模型的多租户智能对话系统，支持知识库管理、技能插件和工作流编排。

## 核心功能

### 1. 知识库管理

知识库是 AI 客服的核心组件。您可以将产品文档、FAQ、技术手册等上传到知识库中，AI 将基于这些内容回答用户问题。

**支持的检索模式：**
- 向量检索：基于语义相似度匹配最相关的内容
- 关键词检索：基于 BM25 算法进行精确匹配
- 混合检索：结合向量和关键词检索，使用 RRF 融合排序

**支持的文档格式：**
- 文本文件（.txt）
- Markdown（.md）
- Word 文档（.docx）
- PDF 文件（.pdf）

### 2. 技能插件

技能插件是可扩展的功能模块，通过 SKILL.md 文件定义。每个技能可以包含工具调用、知识库引用和工作流步骤。

**内置技能示例：**
- 专利检索：支持多维度专利搜索
- 专利报告：自动生成专利分析报告
- 客服助手：基于知识库的智能问答
- 通知服务：多渠道消息推送

### 3. 工作流编排

工作流编排（Beta）允许您通过可视化界面设计复杂的对话流程，包括条件分支、循环和外部 API 调用。

**节点类型：**
- 开始节点：定义工作流的入口
- 对话节点：与用户进行交互
- 工具节点：调用外部 API 或技能
- 条件节点：根据条件进行分支
- 结束节点：工作流的出口

## 部署方式

### Docker 部署

```bash
# 拉取最新镜像
docker pull mchat/mchat:latest

# 启动服务
docker compose up -d
```

### 本地开发

```bash
# 安装依赖
make install

# 启动开发服务器
make dev

# 运行测试
make test
```

## 配置说明

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| DATABASE_URL | 数据库连接地址 | mysql+aiomysql://... |
| MILVUS_HOST | Milvus 服务地址 | localhost |
| EMBEDDING_PROVIDER | Embedding 提供商 | ollama |
| EMBEDDING_MODEL | Embedding 模型 | nomic-embed-text |

### API 密钥配置

支持以下 LLM 提供商：
- OpenAI (gpt-4o, gpt-4o-mini)
- Anthropic (claude-3-5-sonnet)
- DeepSeek (deepseek-v4-flash, deepseek-v4-pro)
- Ollama 本地模型 (llama3.2, qwen2.5, deepseek-r1)

## 常见问题

**Q: 如何添加知识库文档？**
A: 进入管理后台，选择「知识库管理」，点击「新建知识库」，然后上传文档即可。

**Q: 支持哪些 Embedding 模型？**
A: 支持 Ollama 本地模型（如 nomic-embed-text）、OpenAI 兼容接口和本地上传的 sentence-transformers 模型。

**Q: 如何配置本地模型？**
A: 安装 Ollama 后，使用 `ollama pull nomic-embed-text` 拉取 Embedding 模型，`ollama pull qwen2.5` 拉取对话模型。然后在管理后台将 AI 配置的提供商设为 ollama。
