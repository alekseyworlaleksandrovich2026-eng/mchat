# 更新日志

mchat 的所有重要变更都会记录在这个文件中。

## [1.0.0] - 2026-05-17

### 新增
- **核心聊天平台**：支持 WebSocket 实时流式输出的多租户 AI 对话平台。
- **Bot 引擎**：支持工具调用的模块化消息处理链路。
- **大模型提供商**：支持 OpenAI、Anthropic、Google Gemini、DeepSeek、Ollama、Groq 和 OpenAI 兼容接口。
- **技能系统**：基于文件的技能插件，支持热重载。
- **知识库**：集成 Milvus 的 RAG（检索增强生成）能力。
- **管理后台**：基于 React + Tailwind CSS 的后台，用于管理 AI 配置、对话、技能和知识库。
- **嵌入式 Widget**：轻量级网站聊天组件（小于 50KB）。
- **多租户**：每个客服 Agent 拥有独立的 AI 配置。
- **WebSocket**：基于 JWT 认证的实时双向通信。
- **Docker 部署**：一条 Docker Compose 命令即可启动 MySQL + Milvus + Backend + Frontend。
- **CLI**：项目管理命令行工具（`mchat init`、`mchat run`、`mchat skill create`）。
- **限流**：可选的令牌桶限流中间件。
- **API 文档**：`/docs` 自动生成 Swagger UI。
- **CI/CD**：GitHub Actions 自动化测试和 Docker 构建工作流。
- **测试**：基于 pytest 的后端测试集。
