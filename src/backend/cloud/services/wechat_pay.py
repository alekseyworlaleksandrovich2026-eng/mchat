"""WeChat Native pay (unifiedorder) — same params as patentapi PayUtil."""

from __future__ import annotations

import hashlib
import random
import string
import xml.etree.ElementTree as ET
from typing import Any

import httpx
from loguru import logger

from app.core.config import settings

_UNIFIED = "https://api.mch.weixin.qq.com/pay/unifiedorder"


def _nonce(n: int = 32) -> str:
    return "".join(random.choices(string.ascii_letters + string.digits, k=n))


def _sign(params: dict[str, str], api_key: str) -> str:
    items = sorted((k, v) for k, v in params.items() if v and k not in ("sign", "key"))
    raw = "&".join(f"{k}={v}" for k, v in items) + f"&key={api_key}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest().upper()


def _to_xml(params: dict[str, str]) -> str:
    parts = ["<xml>"]
    for k, v in params.items():
        parts.append(f"<{k}><![CDATA[{v}]]></{k}>")
    parts.append("</xml>")
    return "".join(parts)


def _from_xml(text: str) -> dict[str, str]:
    root = ET.fromstring(text)
    return {child.tag: (child.text or "") for child in root}


def notify_url() -> str:
    base = settings.mchat_public_base_url.rstrip("/")
    return f"{base}{settings.wechat_pay_notify_path}"


def native_qr(
    order_no: str,
    amount_cents: int,
    body: str,
    client_ip: str,
) -> str:
    app_id = settings.wechat_pay_app_id.strip()
    mch_id = settings.wechat_pay_mch_id.strip()
    key = settings.wechat_pay_api_key.strip()
    if not app_id or not mch_id or not key:
        raise RuntimeError("WeChat pay not configured")

    params = {
        "appid": app_id,
        "mch_id": mch_id,
        "nonce_str": _nonce(),
        "body": body[:128],
        "out_trade_no": order_no,
        "total_fee": str(amount_cents),
        "spbill_create_ip": client_ip or "127.0.0.1",
        "notify_url": notify_url(),
        "trade_type": "NATIVE",
    }
    params["sign"] = _sign(params, key)
    xml = _to_xml(params)
    with httpx.Client(timeout=15.0) as client:
        resp = client.post(_UNIFIED, content=xml.encode("utf-8"))
        resp.raise_for_status()
        data = _from_xml(resp.text)
    if data.get("return_code") != "SUCCESS" or data.get("result_code") != "SUCCESS":
        logger.error("WeChat unifiedorder failed: {}", data)
        raise RuntimeError(data.get("err_code_des") or data.get("return_msg") or "WeChat pay failed")
    code_url = data.get("code_url")
    if not code_url:
        raise RuntimeError("WeChat pay missing code_url")
    return code_url


def verify_notify_xml(xml_body: str) -> tuple[bool, dict[str, str]]:
    key = settings.wechat_pay_api_key.strip()
    data = _from_xml(xml_body)
    sign = data.get("sign", "")
    expected = _sign({k: v for k, v in data.items() if k != "sign"}, key)
    return sign == expected, data
