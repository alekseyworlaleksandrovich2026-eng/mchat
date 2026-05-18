"""System settings Pydantic schemas."""

from pydantic import BaseModel, Field


class AppSettingsResponse(BaseModel):
    """System-wide application settings."""
    site_name: str = "MChat"
    site_description: str = "智能客服管理平台"
    language: str = "zh-CN"
    timezone: str = "Asia/Shanghai"
    max_file_size: int = 10
    allowed_file_types: list[str] = ["txt", "pdf", "doc", "docx", "md"]
    enable_websocket: bool = True
    enable_streaming: bool = True
    rate_limit_per_min: int = 60
    maintenance_mode: bool = False
    milvus_enabled: bool = False
    milvus_host: str = "localhost"
    milvus_port: int = 19530


class AppSettingsUpdate(BaseModel):
    """Update system settings."""
    site_name: str | None = None
    site_description: str | None = None
    language: str | None = None
    timezone: str | None = None
    max_file_size: int | None = None
    allowed_file_types: list[str] | None = None
    enable_websocket: bool | None = None
    enable_streaming: bool | None = None
    rate_limit_per_min: int | None = None
    maintenance_mode: bool | None = None
    milvus_enabled: bool | None = None
    milvus_host: str | None = None
    milvus_port: int | None = None
