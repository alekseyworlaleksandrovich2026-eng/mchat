"""Tests for widget domain allowlist."""

from app.utils.domain import is_domain_allowed, normalize_host


def test_normalize_host_from_origin():
    assert normalize_host("https://www.example.com/path") == "www.example.com"


def test_normalize_host_bare_domain():
    assert normalize_host("example.com") == "example.com"


def test_allow_all_when_empty_allowlist():
    assert is_domain_allowed(None, "https://evil.com", None) is True
    assert is_domain_allowed("", "https://evil.com", None) is True


def test_allow_matching_domain():
    allowed = "example.com, foo.bar"
    assert is_domain_allowed(allowed, "https://app.example.com", None) is True
    assert is_domain_allowed(allowed, None, "https://foo.bar/page") is True


def test_reject_unknown_domain():
    allowed = "example.com"
    assert is_domain_allowed(allowed, "https://other.com", None) is False


def test_allow_missing_origin_for_server_side_calls():
    assert is_domain_allowed("example.com", None, None) is True
