"""Tests for secret masking helpers."""

from app.utils.secret_mask import MASK_PLACEHOLDER, is_secret_mask, mask_secret


def test_mask_secret_non_empty():
    assert mask_secret("sk-live-secret") == MASK_PLACEHOLDER


def test_mask_secret_empty():
    assert mask_secret("") == ""
    assert mask_secret(None) == ""


def test_is_secret_mask():
    assert is_secret_mask(None)
    assert is_secret_mask("")
    assert is_secret_mask(MASK_PLACEHOLDER)
    assert not is_secret_mask("new-secret-value")
