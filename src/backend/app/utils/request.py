"""HTTP request helpers."""

from __future__ import annotations

from fastapi import Request


def extract_client_ip(request: Request | None) -> str | None:
    """Extract best-effort client IP from common proxy headers."""
    if request is None:
        return None

    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        first = forwarded.split(",", 1)[0].strip()
        if first:
            return first

    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        real_ip = real_ip.strip()
        if real_ip:
            return real_ip

    if request.client and request.client.host:
        return request.client.host
    return None
