"""Application configuration using pydantic-settings."""

from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database
    database_url: str = "mysql+aiomysql://mchat:mchat_password@localhost:3306/mchat"

    # JWT
    jwt_secret: str = "change-this-to-a-random-secret-key"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440

    # Milvus
    milvus_host: str = "localhost"
    milvus_port: int = 19530
    milvus_enabled: bool = False

    # Embedding (global defaults; per knowledge base can override)
    # Prefer local Ollama in dev; override with EMBEDDING_* in .env if needed
    embedding_provider: str = "ollama"
    embedding_model: str = "nomic-embed-text"
    embedding_api_base: str = "http://localhost:11434"
    embedding_dimension: int = 768
    embedding_model_max_mb: int = 2048

    # Server ops skills (persisted in settings DB; admin-only at runtime)
    server_ops_skills_enabled: bool = False
    server_ops_skill_allowlist: list[str] | None = None

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Default admin (created on first startup if missing)
    admin_username: str = "admin"
    admin_password: str = "admin123"
    show_bootstrap_credentials: bool = True

    # CORS
    cors_origins: str = "*"

    # Server
    server_host: str = "0.0.0.0"
    server_port: int = 3001

    # Rate limiting
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 60
    rate_limit_period: int = 60
    login_rate_limit: int = 5
    login_rate_limit_period: int = 60

    # Skills
    skills_dir: str = "../../skills"

    # File uploads
    upload_dir: str = "../../uploads"
    max_upload_size_mb: int = 50
    storage_backend: str = "local"  # local | s3 | minio
    s3_endpoint: str = ""
    s3_region: str = ""
    s3_access_key: str = ""
    s3_secret_key: str = ""
    s3_bucket: str = "mchat-uploads"
    s3_use_ssl: bool = False
    s3_public_base_url: str = ""
    s3_force_path_style: bool = True

    # LLM provider API keys (optional env fallback when DB config key is empty)
    openai_api_key: str = ""
    deepseek_api_key: str = ""
    moonshot_api_key: str = ""
    zhipu_api_key: str = ""
    groq_api_key: str = ""
    siliconflow_api_key: str = ""
    together_api_key: str = ""

    # Embedding API key (falls back to openai_api_key)
    embedding_api_key: str = ""

    # Reranker (global defaults; per KB can override)
    rerank_provider: str = "lexical"  # none, lexical, cohere, bge, cross-encoder
    rerank_model: str = ""
    cohere_api_key: str = ""

    # Speech-to-text (STT)
    stt_enabled: bool = True
    # openai = Whisper API; local = faster-whisper (optional pip install)
    stt_provider: str = "openai"
    stt_openai_api_key: str = ""
    stt_model: str = "whisper-1"
    stt_language: str = "zh"
    stt_max_audio_mb: int = 10
    # local faster-whisper model size: tiny, base, small, medium, large-v3
    stt_local_model: str = "base"

    @property
    def upload_path(self) -> Path:
        return Path(self.upload_dir)

    @property
    def skills_path(self) -> Path:
        return Path(self.skills_dir)


settings = Settings()
