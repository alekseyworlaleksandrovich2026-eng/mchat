"""Production startup security validation."""

import pytest

from app.main import _validate_production_security


def test_production_security_allows_development_defaults(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "environment", "development")
    monkeypatch.setattr(settings, "jwt_secret", "change-this-to-a-random-secret-key")
    monkeypatch.setattr(settings, "admin_password", "admin123")
    monkeypatch.setattr(settings, "show_bootstrap_credentials", True)
    _validate_production_security()


def test_production_security_rejects_default_secrets(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "environment", "production")
    monkeypatch.setattr(settings, "jwt_secret", "change-this-to-a-random-secret-key")
    monkeypatch.setattr(settings, "admin_password", "admin123")
    monkeypatch.setattr(settings, "show_bootstrap_credentials", True)

    with pytest.raises(RuntimeError, match="JWT_SECRET"):
        _validate_production_security()
