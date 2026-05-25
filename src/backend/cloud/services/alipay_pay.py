"""Alipay face-to-face precreate (same SDK pattern as buycdk / patentapi)."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from loguru import logger

from app.core.config import settings

_alipay_client: Any = None


def _format_pem(key: str, *, private: bool) -> str:
    header = "RSA PRIVATE KEY" if private else "PUBLIC KEY"
    lines = [f"-----BEGIN {header}-----"]
    raw = key.replace("\n", "").strip()
    for i in range(0, len(raw), 64):
        lines.append(raw[i : i + 64])
    lines.append(f"-----END {header}-----")
    return "\n".join(lines)


@lru_cache
def _get_alipay():
    global _alipay_client
    if _alipay_client is not None:
        return _alipay_client
    app_id = settings.alipay_app_id.strip()
    priv = settings.alipay_private_key.strip()
    pub = settings.alipay_public_key.strip()
    if not app_id or not priv or not pub:
        return None
    try:
        from alipay import AliPay
    except ImportError:
        logger.error("python-alipay-sdk not installed")
        return None
    _alipay_client = AliPay(
        appid=app_id,
        app_private_key_string=_format_pem(priv, private=True),
        alipay_public_key_string=_format_pem(pub, private=False),
        sign_type="RSA2",
        debug=False,
    )
    return _alipay_client


def notify_url() -> str:
    base = settings.mchat_public_base_url.rstrip("/")
    return f"{base}{settings.alipay_notify_path}"


def precreate_qr(
    order_no: str,
    amount_yuan: str,
    subject: str,
    body: str,
) -> str:
    client = _get_alipay()
    if client is None:
        raise RuntimeError("Alipay not configured")
    result = client.api_alipay_trade_precreate(
        out_trade_no=order_no,
        total_amount=amount_yuan,
        subject=subject,
        body=body,
        timeout_express="30m",
        notify_url=notify_url(),
    )
    qr = result.get("qr_code") if isinstance(result, dict) else None
    if not qr:
        raise RuntimeError(result.get("sub_msg") or result.get("msg") or "Alipay precreate failed")
    return qr


def query_trade(order_no: str) -> dict[str, Any]:
    client = _get_alipay()
    if client is None:
        raise RuntimeError("Alipay not configured")
    return client.api_alipay_trade_query(out_trade_no=order_no)


def verify_notify(data: dict[str, str]) -> bool:
    client = _get_alipay()
    if client is None:
        return False
    payload = dict(data)
    signature = payload.pop("sign", None)
    if not signature:
        return False
    return bool(client.verify(payload, signature))
