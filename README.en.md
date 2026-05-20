# MChat — Multi-Tenant AI Customer Service Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/)
[![Node 20+](https://img.shields.io/badge/node-20+-green.svg)](https://nodejs.org/)

**[中文文档](README.zh-CN.md)** · **[GitHub](https://github.com/windinwing/mchat)**

MChat is a **lightweight, embeddable, multi-tenant AI customer service platform**. It combines a streaming Bot engine, RAG knowledge base, Skill plugin system, and an embeddable chat Widget — with support for **10+ LLM providers** and multi-channel connectivity (Web Widget, WebSocket, REST API, WeChat Official Account, and more).

## Features

- **Bot engine** — Streaming LLM inference + tool calling; OpenAI, Anthropic, Google, DeepSeek, Ollama, Groq, and more
- **Skill plugins** — Hot-reload `SKILL.md` packages from disk/zip/URL, including OpenClaw-compatible formats
- **RAG knowledge base** — Document import, chunking, Milvus vector search, context injection
- **Embeddable Widget** — One `<script>` tag for branded chat on any website
- **Multi-tenant** — Multiple customer agents with isolated AI config, skills, and knowledge bases
- **Multi-channel** — Web Widget, REST, WebSocket, WeChat Official Account
- **Speech input** — Voice-to-text via OpenAI Whisper (optional local models)
- **Security** — JWT authentication and API key management
- **Docker** — `docker compose up -d` for full stack deployment

## Quick start

### Docker (recommended)
```bash
git clone https://github.com/windinwing/mchat.git
cd mchat

docker compose -f ops/docker/docker-compose.lite.yml up -d

# Admin UI:  http://localhost:5173
# API docs:  http://localhost:3001/docs
# Landing:   http://localhost:5173/
```

**Default admin credentials** (created on first startup): `admin` / `admin123`  
Change the password under **Admin → Users** after sign-in. Override via `ADMIN_USERNAME` / `ADMIN_PASSWORD` in `.env`. Set `SHOW_BOOTSTRAP_CREDENTIALS=false` to hide the hint on the login page in production.

### Embed the Widget

```html
<script
  src="http://localhost:5173/widget-loader.js"
  data-mchat-url="http://localhost:3001"
  data-agent-id="YOUR_AGENT_ID"
  data-primary-color="#3b82f6"
  data-welcome-message="Hello! How can I help you?"
  data-bot-name="Support"
></script>
```

### Local development

```bash
make install   # install dependencies
make dev       # start backend + frontend

# Backend:  http://localhost:3001  (/docs for Swagger)
# Frontend: http://localhost:5173
```
```bash
make test      # run tests
make lint      # lint
mchat run      # start via CLI
```

## Project structure

```raw
mchat/
├── src/
│   ├── backend/          # FastAPI (Python 3.12+)
│   │   └── app/
│   │       ├── api/      # REST routes
│   │       ├── bot/      # Bot engine + LLM providers
│   │       ├── knowledge/# RAG + Milvus
│   │       ├── skill/    # Skill system
│   │       └── channels/ # WeChat & channel adapters
│   └── frontend/         # React + Vite + Tailwind
│       └── src/
│           ├── i18n/     # zh / en (react-i18next)
│           └── pages/    # Landing + admin console
├── skills/               # Skill packages
├── docs/                 # Architecture, API, deployment
├── ops/docker/           # Docker Compose
└── Makefile
```

## Supported LLM providers

| Provider | Default API base | Notes |
|----------|------------------|-------|
| `openai` | https://api.openai.com/v1 | GPT-4o, o1, etc. |
| `anthropic` | https://api.anthropic.com | Claude |
| `google` | https://generativelanguage.googleapis.com | Gemini |
| `deepseek` | https://api.deepseek.com | OpenAI-compatible |
| `ollama` | http://localhost:11434/v1 | Local models |
| `groq` | https://api.groq.com/openai/v1 | Fast inference |
| `zhipu` / `moonshot` / `siliconflow` / `together` | *(configure `api_base`)* | Regional / hosted APIs |
| `openai-compatible` | *(configure `api_base`)* | Any OpenAI-compatible endpoint |

## API overview

| Group | Path | Description |
|-------|------|-------------|
| Chat | `/api/chat/*` | Conversations and messages |
| Agents | `/api/agents/*` | AI configuration |
| Knowledge | `/api/knowledge/*` | Documents and retrieval |
| Widget | `/api/widget/*` | Embedded chat API |
| Skills | `/api/skills/*` | Skill management |
| Channels | `/api/channels/*` | WeChat and other channels |
| Speech | `/api/speech/*` | Voice transcription |
| Auth | `/api/auth/*` | Login / JWT |
| WebSocket | `/ws` | Real-time streaming |
| Health | `/api/health` | Service status |

See [docs/api.md](docs/api.md) or `/docs` (Swagger) after startup.

## Internationalization

The admin console and landing page support **English** and **简体中文**. Language preference is stored in `localStorage` (`mchat_lang`). Switch language from the header or sidebar.

## CLI

```bash
mchat init
mchat run
mchat config show
mchat skill list
mchat skill create <name>
mchat skill install <url-or-name>
mchat db init
mchat db seed
```
## Skill compatibility

- Supports standard frontmatter `SKILL.md` skill packages
- Supports OpenClaw-style `SKILL.md` locale blocks
- Admin can install skills by zip upload or URL (`/api/skills/install-url`)
- CLI supports direct URL or ClawHub name install, for example: `mchat skill install patent-search`

## Docker variants

| File | Services | Use case |
|------|----------|----------|
| `docker-compose.lite.yml` | MySQL + Backend + Frontend | Dev / lightweight |
| `docker-compose.yml` | + Milvus, etcd, MinIO, Redis | Full RAG |
| `docker-compose.prod.yml` | + Nginx HTTPS | Production |
| `docker-compose.dev.yml` | Hot reload | Local dev |

## Tech stack

**Backend:** FastAPI, SQLAlchemy 2.0, Milvus, OpenAI / Anthropic SDKs, JWT, Loguru  

**Frontend:** React 19, TypeScript, Vite, Tailwind CSS 4, Zustand, react-i18next

## License

[MIT License](LICENSE)

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) if present.
