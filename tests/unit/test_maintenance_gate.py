"""Tests for public API maintenance gate."""

from unittest.mock import patch

import pytest
from fastapi import HTTPException

from app.services.maintenance_gate import (
    ensure_public_api_available,
    maintenance_blocks_public,
    maintenance_public_message,
)


def test_maintenance_off_by_default():
    with patch("app.services.maintenance_gate.settings") as s:
        s.maintenance_mode = False
        assert not maintenance_blocks_public()
        ensure_public_api_available()


def test_maintenance_blocks_with_503():
    with patch("app.services.maintenance_gate.settings") as s:
        s.maintenance_mode = True
        s.language = "zh-CN"
        assert maintenance_blocks_public()
        with pytest.raises(HTTPException) as exc:
            ensure_public_api_available()
        assert exc.value.status_code == 503
        assert exc.value.detail["maintenance"] is True


def test_maintenance_message_en():
    with patch("app.services.maintenance_gate.settings") as s:
        s.language = "en-US"
        assert "maintenance" in maintenance_public_message("en").lower()
