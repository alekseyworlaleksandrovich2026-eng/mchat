"""Mask sensitive settings values for API responses."""

from __future__ import annotations

MASK_PLACEHOLDER = "********"


def mask_secret(value: str | None) -> str:
    """Return a non-reversible placeholder when a secret is set."""
    if not value or not str(value).strip():
        return ""
    return MASK_PLACEHOLDER


def is_secret_mask(value: str | None) -> bool:
    """True when the client did not supply a new secret (empty or placeholder)."""
    if value is None:
        return True
    text = str(value).strip()
    if not text:
        return True
    if text == MASK_PLACEHOLDER:
        return True
    return text.replace("*", "") == ""
