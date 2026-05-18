"""Domain allowlist helpers for embeddable widget APIs."""

from urllib.parse import urlparse


def normalize_host(value: str) -> str:
    """Extract hostname from origin, referer, or bare domain string."""
    value = (value or "").strip().lower()
    if not value:
        return ""
    if "://" not in value:
        value = f"https://{value}"
    parsed = urlparse(value)
    return (parsed.hostname or "").lower()


def is_domain_allowed(allowed_domains: str | None, origin: str | None, referer: str | None) -> bool:
    """Return True if request origin/referer matches configured allowlist.

    Empty allowlist means all domains are permitted.
    Missing origin/referer is allowed (e.g. curl, same-origin admin preview).
    """
    if not allowed_domains or not allowed_domains.strip():
        return True

    allowed = [
        normalize_host(part)
        for part in allowed_domains.split(",")
        if part.strip()
    ]
    allowed = [h for h in allowed if h]
    if not allowed:
        return True

    request_host = normalize_host(origin or "") or normalize_host(referer or "")
    if not request_host:
        return True

    for host in allowed:
        if request_host == host or request_host.endswith(f".{host}"):
            return True
    return False
