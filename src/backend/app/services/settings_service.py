"""Settings service - business logic for system configuration."""

import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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

        apply_milvus_runtime(
            enabled=milvus_enabled,
            host=milvus_host,
            port=milvus_port,
        )

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
