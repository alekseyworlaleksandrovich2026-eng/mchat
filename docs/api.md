# mchat API 文档

基础 URL: `http://localhost:3001/api`

## 认证

### POST /auth/login

登录获取 JWT Token。

**请求体:**
```json
{
  "username": "admin",
  "password": "your_password"
}
```

**响应:**
```json
{
  "access_token": "eyJhbGciOi...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "username": "admin",
    "role": "admin",
    "display_name": "管理员"
  }
}
```

### POST /auth/register

注册新用户（Agent）。

### GET /auth/me

获取当前用户信息。需要 Bearer Token。

---

## 聊天

### POST /chat/send

发送消息（支持 SSE 流式响应）。

**请求头:** `Authorization: Bearer <token>` 或 visitor token

**请求体:**
```json
{
  "conversation_id": "uuid",
  "content": "你好",
  "role": "user"
}
```

**流式响应 (SSE):**
```
data: {"type": "token", "content": "你"}
data: {"type": "token", "content": "好"}
data: {"type": "tool_call", "name": "search", "args": {...}}
data: {"type": "tool_result", "content": "..."}
data: {"type": "done", "message_id": "uuid"}
```

### POST /chat/conversations/init

初始化访客对话（无需认证）。

**请求体:**
```json
{
  "customer_id": "uuid (客户配置ID)",
  "visitor_id": "optional visitor ID"
}
```

### GET /chat/conversations

获取对话列表（分页）。

**参数:** `?page=1&size=20&status=active`

### GET /chat/conversations/{id}

获取对话详情（含消息列表）。

### POST /chat/conversations/{id}/close

关闭对话。

---

## 客服管理 (Agent)

### AI 配置

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/agent/ai-config` | 创建 AI 配置 |
| GET | `/agent/ai-config` | 获取配置列表 |
| GET | `/agent/ai-config/{id}` | 获取配置详情 |
| PUT | `/agent/ai-config/{id}` | 更新配置 |
| DELETE | `/agent/ai-config/{id}` | 删除配置 |

**AIConfig 对象:**
```json
{
  "name": "GPT-4 客服",
  "provider": "openai",
  "model": "gpt-4o-mini",
  "api_key": "sk-...",
  "api_base": "https://api.openai.com/v1",
  "system_prompt": "你是一个专业的客服助手...",
  "temperature": 0.7,
  "max_tokens": 4096,
  "is_default": true
}
```

### 客户配置

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/agent/customer-config` | 创建客户配置 |
| GET | `/agent/customer-config` | 获取配置列表 |
| PUT | `/agent/customer-config/{id}` | 更新配置 |
| DELETE | `/agent/customer-config/{id}` | 删除配置 |

**CustomerConfig 对象:**
```json
{
  "name": "主站客服",
  "ai_config_id": "uuid",
  "welcome_message": "你好！有什么可以帮你的？",
  "offline_message": "当前不在线，请留言",
  "theme": {
    "primary_color": "#3b82f6",
    "position": "bottom-right"
  },
  "domains": "example.com,www.example.com",
  "enabled": true
}
```

---

## 知识库

### 知识库

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/knowledge/bases` | 创建知识库 |
| GET | `/knowledge/bases` | 获取知识库列表 |
| GET | `/knowledge/bases/{id}` | 获取知识库详情 |
| PUT | `/knowledge/bases/{id}` | 更新知识库 |
| DELETE | `/knowledge/bases/{id}` | 删除知识库 |

### 文档

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/knowledge/documents` | 创建文档 |
| GET | `/knowledge/documents` | 获取文档列表 |
| GET | `/knowledge/documents/{id}` | 获取文档详情 |
| PUT | `/knowledge/documents/{id}` | 更新文档 |
| DELETE | `/knowledge/documents/{id}` | 删除文档 |
| POST | `/knowledge/search` | 向量搜索 |

### 文档导入

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/knowledge/import/file` | 上传文件导入 (multipart) |
| POST | `/knowledge/import/url` | URL 导入 |

**搜索请求:**
```json
{
  "query": "如何退款",
  "knowledge_base_id": "uuid",
  "top_k": 5
}
```

---

## 技能

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/skills` | 获取技能列表 |
| PUT | `/skills/{id}` | 启用/禁用技能 |
| POST | `/skills/reload` | 重新加载技能 |
| POST | `/skills/upload` | 上传技能包 (zip) |

---

## Widget 公开 API

### GET /widget/config/{customer_id}

获取 Widget 嵌入配置（无需认证）。

### POST /widget/conversation

创建访客对话。

### GET /visitor/online-agents

获取在线客服列表。

---

## 健康检查

### GET /health

```json
{
  "status": "ok",
  "database": "connected",
  "milvus": "connected",
  "version": "1.0.0"
}
```

### GET /health/metrics

```json
{
  "active_conversations": 12,
  "total_messages_today": 345,
  "active_agents": 3,
  "uptime_seconds": 86400
}
```

---

## WebSocket

连接: `ws://localhost:3001/ws?token=<jwt_token>&conversation_id=<uuid>`

**发送消息:**
```json
{"type": "message", "content": "你好"}
```

**接收消息:**
```json
{"type": "message", "content": "你好！有什么可以帮你的？", "role": "assistant"}
{"type": "token", "content": "你"}
{"type": "typing", "status": "start"}
{"type": "typing", "status": "stop"}
```

## 错误响应

```json
{
  "detail": "错误描述信息",
  "code": "ERROR_CODE"
}
```

HTTP 状态码:
- 200: 成功
- 201: 创建成功
- 400: 请求参数错误
- 401: 未认证
- 403: 无权限
- 404: 资源不存在
- 500: 服务器错误
