"""Tests for masked secrets in settings service."""

import pytest

from app.models.setting import Setting
from app.schemas.settings import AppSettingsUpdate
from app.services.settings_service import SettingsService
from app.utils.secret_mask import MASK_PLACEHOLDER


@pytest.mark.asyncio
async def test_get_settings_masks_secrets(db_session):
    db_session.add(
        Setting(key="s3_secret_key", value="super-secret", category="general")
    )
    db_session.add(
        Setting(key="embedding_api_key", value="embed-key", category="general")
    )
    await db_session.flush()

    service = SettingsService(db_session)
    settings = await service.get_settings()
    assert settings.s3_secret_key == MASK_PLACEHOLDER
    assert settings.embedding_api_key == MASK_PLACEHOLDER


@pytest.mark.asyncio
async def test_update_settings_skips_masked_secret_placeholder(db_session):
    db_session.add(
        Setting(key="s3_secret_key", value="keep-me", category="general")
    )
    await db_session.flush()

    service = SettingsService(db_session)
    await service.update_settings(
        AppSettingsUpdate(s3_secret_key=MASK_PLACEHOLDER, site_name="Test Site")
    )

    result = await db_session.execute(
        Setting.__table__.select().where(Setting.key == "s3_secret_key")
    )
    row = result.first()
    assert row is not None
    assert row.value == "keep-me"

    updated = await service.get_settings()
    assert updated.site_name == "Test Site"
    assert updated.s3_secret_key == MASK_PLACEHOLDER
