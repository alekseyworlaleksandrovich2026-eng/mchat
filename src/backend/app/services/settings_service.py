"""Settings service - business logic for system configuration."""

from collections import deque
import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.knowledge.milvus_client import milvus_client
from app.knowledge.milvus_runtime import apply_milvus_runtime
from app.models.setting import Setting
from app.schemas.settings import AppSettingsResponse, AppSettingsUpdate


DEFAULT_SETTINGS = AppSettingsResponse()


class SettingsService:
    """Handles system settings persistence."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_settings(self) -> AppSettingsResponse:
        """Get all system settings with defaults."""
        result = await self.db.execute(select(Setting))
        rows = {r.key: r.value for r in result.scalars().all()}

        def get_val(key: str, default):
            if key not in rows:
                return default
            raw = rows[key]
            if isinstance(default, bool):
                return raw.lower() in ("true", "1", "yes")
            if isinstance(default, int):
                try:
                    return int(raw)
                except (ValueError, TypeError):
                    return default
            if isinstance(default, list):
                try:
                    return json.loads(raw)
                except (json.JSONDecodeError, TypeError):
                    return default
            return raw

        milvus_enabled = get_val("milvus_enabled", DEFAULT_SETTINGS.milvus_enabled)
        milvus_host = get_val("milvus_host", DEFAULT_SETTINGS.milvus_host)
        milvus_port = get_val("milvus_port", DEFAULT_SETTINGS.milvus_port)
        storage_backend = get_val("storage_backend", DEFAULT_SETTINGS.storage_backend)
        upload_dir = get_val("upload_dir", DEFAULT_SETTINGS.upload_dir)
        max_upload_size_mb = get_val(
            "max_upload_size_mb", DEFAULT_SETTINGS.max_upload_size_mb
        )
        s3_endpoint = get_val("s3_endpoint", DEFAULT_SETTINGS.s3_endpoint)
        s3_region = get_val("s3_region", DEFAULT_SETTINGS.s3_region)
        s3_access_key = get_val("s3_access_key", DEFAULT_SETTINGS.s3_access_key)
        s3_secret_key = get_val("s3_secret_key", DEFAULT_SETTINGS.s3_secret_key)
        s3_bucket = get_val("s3_bucket", DEFAULT_SETTINGS.s3_bucket)
        s3_use_ssl = get_val("s3_use_ssl", DEFAULT_SETTINGS.s3_use_ssl)
        s3_public_base_url = get_val(
            "s3_public_base_url", DEFAULT_SETTINGS.s3_public_base_url
        )
        s3_force_path_style = get_val(
            "s3_force_path_style", DEFAULT_SETTINGS.s3_force_path_style
        )

        apply_milvus_runtime(
            enabled=milvus_enabled,
            host=milvus_host,
            port=milvus_port,
        )

        # Keep runtime storage settings in sync with persisted settings.
        settings.storage_backend = storage_backend
        settings.upload_dir = upload_dir
        settings.max_upload_size_mb = max_upload_size_mb
        settings.s3_endpoint = s3_endpoint
        settings.s3_region = s3_region
        settings.s3_access_key = s3_access_key
        settings.s3_secret_key = s3_secret_key
        settings.s3_bucket = s3_bucket
        settings.s3_use_ssl = s3_use_ssl
        settings.s3_public_base_url = s3_public_base_url
        settings.s3_force_path_style = s3_force_path_style

        return AppSettingsResponse(
            site_name=get_val("site_name", DEFAULT_SETTINGS.site_name),
            site_description=get_val("site_description", DEFAULT_SETTINGS.site_description),
            language=get_val("language", DEFAULT_SETTINGS.language),
            timezone=get_val("timezone", DEFAULT_SETTINGS.timezone),
            max_file_size=get_val("max_file_size", DEFAULT_SETTINGS.max_file_size),
            allowed_file_types=get_val("allowed_file_types", DEFAULT_SETTINGS.allowed_file_types),
            enable_websocket=get_val("enable_websocket", DEFAULT_SETTINGS.enable_websocket),
            enable_streaming=get_val("enable_streaming", DEFAULT_SETTINGS.enable_streaming),
            rate_limit_per_min=get_val("rate_limit_per_min", DEFAULT_SETTINGS.rate_limit_per_min),
            maintenance_mode=get_val("maintenance_mode", DEFAULT_SETTINGS.maintenance_mode),
            milvus_enabled=milvus_enabled,
            milvus_host=milvus_host,
            milvus_port=milvus_port,
            storage_backend=storage_backend,
            upload_dir=upload_dir,
            max_upload_size_mb=max_upload_size_mb,
            s3_endpoint=s3_endpoint,
            s3_region=s3_region,
            s3_access_key=s3_access_key,
            s3_secret_key=s3_secret_key,
            s3_bucket=s3_bucket,
            s3_use_ssl=s3_use_ssl,
            s3_public_base_url=s3_public_base_url,
            s3_force_path_style=s3_force_path_style,
        )

    async def update_settings(self, data: AppSettingsUpdate) -> AppSettingsResponse:
        """Update settings, creating keys that don't exist."""
        updates = data.model_dump(exclude_unset=True)

        # Fetch existing settings
        result = await self.db.execute(select(Setting))
        existing: dict[str, Setting] = {r.key: r for r in result.scalars().all()}

        for db_key, new_val in updates.items():
            val_str: str
            if isinstance(new_val, list):
                val_str = json.dumps(new_val, ensure_ascii=False)
            elif isinstance(new_val, bool):
                val_str = "true" if new_val else "false"
            else:
                val_str = str(new_val)

            if db_key in existing:
                existing[db_key].value = val_str
            else:
                self.db.add(Setting(key=db_key, value=val_str, category="general"))

        await self.db.flush()

        result = await self.get_settings()
        if any(k.startswith("milvus_") for k in updates):
            await milvus_client.reconnect()
        return result

    async def test_milvus_connection(
        self, *, enabled: bool, host: str, port: int
    ) -> dict:
        """Test Milvus connectivity with given settings (does not persist)."""
        from app.knowledge import milvus_runtime

        saved = milvus_runtime.get_milvus_runtime()
        apply_milvus_runtime(enabled=enabled, host=host, port=port)
        try:
            ok = await milvus_client.reconnect()
            if ok:
                return {"ok": True, "message": f"已连接 Milvus {host}:{port}"}
            if not enabled:
                return {"ok": True, "message": "Milvus 已禁用（仅使用数据库全文检索）"}
            return {"ok": False, "message": f"无法连接 Milvus {host}:{port}"}
        finally:
            apply_milvus_runtime(
                enabled=saved.enabled,
                host=saved.host,
                port=saved.port,
            )
            await milvus_client.reconnect()

    async def get_log_tail(
        self,
        *,
        source: str = "app",
        lines: int = 200,
    ) -> dict:
        """Read the last N lines from backend log files."""
        safe_lines = max(20, min(lines, 1000))
        log_file = "error.log" if source == "error" else "app.log"
        path = Path("logs") / log_file

        if not path.exists():
            return {
                "source": source,
                "lines": [f"日志文件不存在: {path}"],
            }

        try:
            with path.open("r", encoding="utf-8", errors="replace") as f:
                tail = list(deque(f, maxlen=safe_lines))
        except Exception as e:
            return {
                "source": source,
                "lines": [f"读取日志失败: {e}"],
            }

        return {
            "source": source,
            "lines": [line.rstrip("\n") for line in tail],
        }
