"""WeChat Official Account — signature, decrypt, XML reply."""

from __future__ import annotations

import hashlib
import time
import xml.etree.ElementTree as ET
from typing import Any
from xml.etree.ElementTree import Element

from loguru import logger


def verify_signature(
    token: str, timestamp: str, nonce: str, signature: str
) -> bool:
    if not token:
        return False
    check = hashlib.sha1(
        "".join(sorted([token, timestamp, nonce])).encode()
    ).hexdigest()
    return check == signature


def _cdata(el: Element | None) -> str:
    if el is None or el.text is None:
        return ""
    return el.text.strip()


def parse_plain_xml(body: bytes) -> dict[str, str]:
    """Parse WeChat plaintext XML push."""
    root = ET.fromstring(body)
    return {
        "to_user": _cdata(root.find("ToUserName")),
        "from_user": _cdata(root.find("FromUserName")),
        "create_time": _cdata(root.find("CreateTime")),
        "msg_type": _cdata(root.find("MsgType")),
        "content": _cdata(root.find("Content")),
        "msg_id": _cdata(root.find("MsgId")),
        "event": _cdata(root.find("Event")),
        "event_key": _cdata(root.find("EventKey")),
    }


def decrypt_message_body(
    body: bytes,
    *,
    token: str,
    encoding_aes_key: str,
    app_id: str,
    msg_signature: str,
    timestamp: str,
    nonce: str,
) -> bytes:
    """Decrypt safe/compatible mode payload to plaintext XML bytes."""
    try:
        from wechatpy.crypto import WeChatCrypto
    except ImportError as e:
        raise RuntimeError(
            "安全模式需要安装 wechatpy：pip install wechatpy"
        ) from e

    crypto = WeChatCrypto(token, encoding_aes_key, app_id)
    return crypto.decrypt_message(
        body.decode("utf-8", errors="replace"),
        msg_signature,
        timestamp,
        nonce,
    ).encode("utf-8")


def encrypt_reply_xml(
    reply_xml: str,
    *,
    token: str,
    encoding_aes_key: str,
    app_id: str,
    timestamp: str,
    nonce: str,
) -> str:
    try:
        from wechatpy.crypto import WeChatCrypto
    except ImportError as e:
        raise RuntimeError(
            "安全模式需要安装 wechatpy：pip install wechatpy"
        ) from e

    crypto = WeChatCrypto(token, encoding_aes_key, app_id)
    return crypto.encrypt_message(reply_xml, nonce, timestamp)


def build_text_reply(
    to_user: str, from_user: str, content: str
) -> str:
    """Passive reply XML (swap To/From vs incoming)."""
    ts = int(time.time())
    safe = content.replace("]]>", "]]]]><![CDATA[>")
    return f"""<xml>
<ToUserName><![CDATA[{to_user}]]></ToUserName>
<FromUserName><![CDATA[{from_user}]]></FromUserName>
<CreateTime>{ts}</CreateTime>
<MsgType><![CDATA[text]]></MsgType>
<Content><![CDATA[{safe}]]></Content>
</xml>"""


def parse_incoming(
    body: bytes,
    *,
    token: str,
    app_id: str,
    encoding_aes_key: str,
    encrypt_type: str | None,
    msg_signature: str | None,
    timestamp: str,
    nonce: str,
) -> dict[str, str]:
    """Decrypt (if needed) and parse WeChat push message."""
    xml_bytes = body
    if encrypt_type == "aes" and encoding_aes_key:
        if not msg_signature or not app_id:
            raise ValueError("安全模式需要 App ID 与 msg_signature")
        xml_bytes = decrypt_message_body(
            body,
            token=token,
            encoding_aes_key=encoding_aes_key,
            app_id=app_id,
            msg_signature=msg_signature,
            timestamp=timestamp,
            nonce=nonce,
        )
    elif encrypt_type == "aes":
        logger.warning("WeChat encrypt_type=aes but encoding_aes_key missing")
    return parse_plain_xml(xml_bytes)
