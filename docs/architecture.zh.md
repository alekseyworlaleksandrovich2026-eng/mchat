# mchat 架构设计

## 概述

mchat 是一个多租户 AI 对话平台，整合了智能客服、技能插件系统和知识库（Milvus RAG）功能。前后端分离架构，支持 Docker 一键部署。

## 技术栈

| 组件 | 技术 | 说明 |
|------|------|------|
| **后端框架** | Python + FastAPI | 异步高性能 API 框架 |
| **数据库 ORM** | SQLAlchemy 2.0 (async) | 异步数据库操作 |
| **数据库** | MySQL 8.0 | 主数据存储 |
| **向量数据库** | Milvus | 知识库向量检索 |
| **前端框架** | React 19 + Vite | 现代化前端构建 |
| **样式** | Tailwind CSS 4 | 原子化 CSS |
| **状态管理** | Zustand | 轻量级状态管理 |
| **容器化** | Docker + Compose | 一键部署 |

## 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        客户端层                               │
├──────────────┬──────────────┬──────────────┬────────────────┤
│  管理后台     │  聊天页面     │  嵌入 Widget  │  第三方 API    │
│  (React SPA) │  (React SPA) │  (Vanilla JS)│  (REST/WS)    │
└──────┬───────┴──────┬───────┴──────┬───────┴───────┬────────┘
       │              │              │               │
       ▼              ▼              ▼               ▼
┌─────────────────────────────────────────────────────────────┐
│                      Nginx 反向代理                          │
│              路由分发 / 静态资源 / SSL 终止                    │
└─────────────────────────┬───────────────────────────────────┘
                          │
       ┌──────────────────┴──────────────────┐
       ▼                                      ▼
┌──────────────┐                      ┌──────────────┐
│   Frontend   │                      │   Backend    │
│  React+Vite  │────── REST/WS ──────▶│   FastAPI    │
│   (Port 80)  │                      │  (Port 3001) │
└──────────────┘                      └──────┬───────┘
                                             │
              ┌──────────────────────────────┼──────────────┐
              │                              │              │
              ▼                              ▼              ▼
       ┌──────────┐                  ┌──────────┐   ┌──────────┐
       │  MySQL   │                  │  Milvus  │   │  Redis   │
       │ (数据)   │                  │ (向量)   │   │ (缓存)   │
       └──────────┘                  └──────────┘   └──────────┘
```

## 后端架构

```
app/
├── main.py              # FastAPI 应用入口
├── core/                # 核心模块
│   ├── config.py        # 配置管理 (pydantic-settings)
│   ├── database.py      # 数据库连接
│   ├── security.py      # 安全工具 (JWT, 密码)
│   └── event_bus.py     # 事件总线
├── models/              # SQLAlchemy 数据模型
│   ├── user.py
│   ├── ai_config.py
│   ├── conversation.py
│   ├── message.py
│   ├── skill.py
│   ├── knowledge.py
│   └── customer.py
├── schemas/             # Pydantic 请求/响应模型
│   ├── auth.py
│   ├── chat.py
│   ├── agent.py
│   ├── knowledge.py
│   └── skill.py
├── api/                 # API 路由
│   ├── auth.py          # 认证
│   ├── chat.py          # 聊天
│   ├── agent.py         # 客服管理
│   ├── knowledge.py     # 知识库
│   ├── skill.py         # 技能
│   ├── widget.py        # 公开 Widget API
│   └── health.py        # 健康检查
├── services/            # 业务逻辑层
│   ├── auth_service.py
│   ├── chat_service.py
│   ├── agent_service.py
│   ├── knowledge_service.py
│   └── skill_service.py
├── bot/                 # Bot 引擎
│   ├── engine.py        # 核心对话引擎
│   └── provider.py      # LLM Provider 抽象
├── knowledge/           # 知识库模块
│   ├── milvus_client.py # Milvus 客户端
│   ├── embedder.py      # 向量嵌入
│   ├── rag.py           # RAG 检索增强
│   └── importer.py      # 文档导入
├── skill/               # 技能系统
│   ├── loader.py        # 技能加载器
│   └── executor.py      # 技能执行器
├── customer/            # 多租户客服
│   └── manager.py       # 客服实例管理
├── middleware/           # 中间件
│   └── auth.py          # JWT 认证
└── utils/               # 工具
    └── logger.py
```

## 数据流

### 对话流程

```
用户消息 → Widget/API
  → FastAPI Route (chat/send)
    → ChatService.send_message()
      → BotEngine.process_message()
        1. 加载 AI 配置 (model, system prompt)
        2. 加载技能工具 (skill tool definitions)
        3. RAG 检索知识库 (相关文档片段)
        4. 构建消息上下文
        5. 调用 LLM Provider (streaming)
        6. 处理 Tool Calls (递归)
        7. 保存消息到数据库
      ← SSE 流式响应
    ← StreamingResponse
  ← 实时展示给用户
```

### 知识库导入流程

```
文件上传 → KnowledgeService.import_document()
  → Document.status = "processing"
    → Importer.parse_file() → 提取文本
    → Importer.chunk_text() → 文本分块
    → Embedder.embed() → 向量化
    → MilvusClient.insert() → 存储向量
  → Document.status = "ready"
```

### 技能系统

```
skills/
├── example-skill/
│   └── SKILL.md          # 技能定义文件

SKILL.md 结构:
---
name: example-skill
description: 示例技能
tools:
  - name: search
    description: 搜索功能
    parameters:
      query:
        type: string
        description: 搜索关键词
---

SkillLoader 扫描 skills/ 目录 → 解析 SKILL.md → 
注册工具到 Bot Engine → LLM 可调用工具
```

## 多租户设计

每个"客服 Agent"是一个独立的租户：
- **独立 AI 配置**: 不同的模型、System Prompt、Temperature
- **独立知识库**: 不同的文档集合
- **独立技能**: 不同的工具集
- **独立外观**: 不同的 Widget 主题、欢迎语
- **域名绑定**: CustomerConfig.domains 限制嵌入域名

## 安全设计

- **JWT 认证**: 后台管理 API 使用 JWT
- **API Key**: 第三方集成使用 API Key
- **Visitor Token**: 访客使用临时 token
- **RBAC**: admin / agent 角色分离
- **域名白名单**: Widget 嵌入域名限制
- **密码加密**: bcrypt 哈希
