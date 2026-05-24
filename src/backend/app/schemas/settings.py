"""System settings Pydantic schemas."""

from pydantic import BaseModel, Field


class AppSettingsResponse(BaseModel):
    """System-wide application settings."""
    site_name: str = "MChat"
    site_description: str = "垂直 RAG 管理平台"
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
    storage_backend: str = "local"
    upload_dir: str = "../../uploads"
    max_upload_size_mb: int = 50
    s3_endpoint: str = ""
    s3_region: str = ""
    s3_access_key: str = ""
    s3_secret_key: str = ""
    s3_bucket: str = "mchat-uploads"
    s3_use_ssl: bool = False
    s3_public_base_url: str = ""
    s3_force_path_style: bool = True


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
    storage_backend: str | None = None
    upload_dir: str | None = None
    max_upload_size_mb: int | None = None
    s3_endpoint: str | None = None
    s3_region: str | None = None
    s3_access_key: str | None = None
    s3_secret_key: str | None = None
    s3_bucket: str | None = None
    s3_use_ssl: bool | None = None
    s3_public_base_url: str | None = None
    s3_force_path_style: bool | None = None


class AppLogResponse(BaseModel):
    """Backend log tail response."""
    source: str
    lines: list[str]
