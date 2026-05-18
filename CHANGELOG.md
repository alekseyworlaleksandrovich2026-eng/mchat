# Changelog

All notable changes to mchat will be documented in this file.

## [1.0.0] - 2026-05-17

### Added
- **Core Chat Platform**: Multi-tenant AI chat with real-time streaming via WebSocket
- **Bot Engine**: Modular message processing pipeline with tool calling
- **LLM Providers**: OpenAI, Anthropic, Google Gemini, DeepSeek, Ollama, Groq, and OpenAI-compatible providers
- **Skill System**: File-based skill plugins with hot-reload support
- **Knowledge Base**: Milvus vector store integration for RAG (Retrieval-Augmented Generation)
- **Admin Dashboard**: React + Tailwind CSS admin panel for managing AI configs, conversations, skills, and knowledge bases
- **Embedded Widget**: Lightweight JavaScript chat widget for website embedding (< 50KB)
- **Multi-tenant**: Independent AI configurations per customer service agent
- **WebSocket**: Real-time bidirectional communication with JWT authentication
- **Docker Deployment**: One-command Docker Compose setup (MySQL + Milvus + Backend + Frontend)
- **CLI**: Command-line interface for project management (`mchat init`, `mchat run`, `mchat skill create`)
- **Rate Limiting**: Optional token bucket rate limiter middleware
- **API Documentation**: Auto-generated Swagger UI at `/docs`
- **CI/CD**: GitHub Actions workflow for automated testing and Docker builds
- **Tests**: Backend test suite with pytest
