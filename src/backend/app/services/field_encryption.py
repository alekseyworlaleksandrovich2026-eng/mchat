"""Encrypt sensitive JSON fields (skill_bindings secrets) at rest."""

from __future__ import annotations

import base64
import hashlib
from typing import Any

from cryptography.fernet import Fernet, InvalidToken
from loguru import logger

from app.core.config import settings

_ENC_PREFIX = "enc:v1:"


def encryption_enabled() -> bool:
    return bool((settings.secrets_encryption_key or "").strip())


def _fernet() -> Fernet | None:
    raw = (settings.secrets_encryption_key or "").strip()
    if not raw:
        return None
    try:
        key_bytes = raw.encode()
        if len(key_bytes) != 44 or not raw.endswith("="):
            digest = hashlib.sha256(key_bytes).digest()
            key_bytes = base64.urlsafe_b64encode(digest)
        return Fernet(key_bytes)
    except Exception as e:
        logger.error("Invalid secrets_encryption_key: {}", e)
        return None


def encrypt_value(plain: str) -> str:
    if not plain or plain.startswith(_ENC_PREFIX):
        return plain
    f = _fernet()
    if f is None:
        return plain
    token = f.encrypt(plain.encode("utf-8")).decode("ascii")
    return f"{_ENC_PREFIX}{token}"


def decrypt_value(stored: str) -> str:
    if not stored or not isinstance(stored, str):
        return stored or ""
    if not stored.startswith(_ENC_PREFIX):
        return stored
    f = _fernet()
    if f is None:
        logger.warning("Encrypted value present but secrets_encryption_key is unset")
        return ""
    token = stored[len(_ENC_PREFIX) :]
    try:
        return f.decrypt(token.encode("ascii")).decode("utf-8")
    except InvalidToken:
        logger.error("Failed to decrypt field value")
        return ""


def _encrypt_secrets_dict(secrets: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k, v in secrets.items():
        if isinstance(v, str) and v:
            out[k] = encrypt_value(v)
        else:
            out[k] = v
    return out


def _decrypt_secrets_dict(secrets: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k, v in secrets.items():
        if isinstance(v, str):
            out[k] = decrypt_value(v)
        else:
            out[k] = v
    return out


def encrypt_skill_bindings(bindings: dict | None) -> dict | None:
    if not bindings or not isinstance(bindings, dict):
        return bindings
    if not encryption_enabled():
        return bindings
    result: dict[str, Any] = {}
    for skill_name, binding in bindings.items():
        if not isinstance(binding, dict):
            result[skill_name] = binding
            continue
        entry = dict(binding)
        secrets = entry.get("secrets") or entry.get("env")
        if isinstance(secrets, dict):
            entry["secrets"] = _encrypt_secrets_dict(secrets)
            entry.pop("env", None)
        result[skill_name] = entry
    return result


def decrypt_skill_bindings(bindings: dict | None) -> dict | None:
    if not bindings or not isinstance(bindings, dict):
        return bindings
    result: dict[str, Any] = {}
    for skill_name, binding in bindings.items():
        if not isinstance(binding, dict):
            result[skill_name] = binding
            continue
        entry = dict(binding)
        secrets = entry.get("secrets") or entry.get("env")
        if isinstance(secrets, dict):
            entry["secrets"] = _decrypt_secrets_dict(secrets)
            entry.pop("env", None)
        result[skill_name] = entry
    return result
