"""Match customer-config asset rules against user messages."""

from __future__ import annotations

import math
from typing import Any

from app.knowledge.embedder import embedder
from app.utils.outbound_assets import normalize_outbound_asset

_DEFAULT_THRESHOLD = 0.78
_MAX_MATCHES = 3
_SUPPORTED_CHANNELS = {"widget", "wechat", "admin"}
_WIDGET_CONTACT_PREFIX = "widget_customer:"
_WECHAT_CONTACT_PREFIX = "wechat_channel:"


def _clean_rule_text(value: object) -> str:
    return str(value or "").strip()


def _clean_keywords(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    out: list[str] = []
    for item in value:
        text = _clean_rule_text(item)
        if text:
            out.append(text)
    return out


def normalize_rule_channels(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    out: list[str] = []
    for item in value:
        text = _clean_rule_text(item).lower()
        if text and text in _SUPPORTED_CHANNELS and text not in out:
            out.append(text)
    return out


def detect_message_channel(contact_info: object) -> str:
    contact = _clean_rule_text(contact_info)
    if contact.startswith(_WIDGET_CONTACT_PREFIX):
        return "widget"
    if contact.startswith(_WECHAT_CONTACT_PREFIX):
        return "wechat"
    return "admin"


def _cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _keyword_score(query: str, phrases: list[str]) -> tuple[float, list[str]]:
    normalized_query = query.lower()
    matched = [phrase for phrase in phrases if phrase.lower() in normalized_query]
    if not matched:
        return 0.0, []
    longest = max(len(item) for item in matched)
    query_len = max(len(normalized_query), 1)
    score = max(0.9, min(1.0, longest / query_len + 0.6))
    return score, matched


async def match_auto_reply_rules(
    query: str,
    rules: object,
    channel: str | None = None,
) -> list[dict[str, Any]]:
    """Return matched auto-reply asset rules sorted by confidence."""
    if not isinstance(rules, list):
        return []

    normalized_query = _clean_rule_text(query)
    if not normalized_query:
        return []
    normalized_channel = _clean_rule_text(channel).lower()

    prepared: list[dict[str, Any]] = []
    for index, raw_rule in enumerate(rules):
        if not isinstance(raw_rule, dict):
            continue
        if raw_rule.get("enabled") is False:
            continue

        trigger_text = _clean_rule_text(raw_rule.get("trigger_text"))
        keywords = _clean_keywords(raw_rule.get("keywords"))
        channels = normalize_rule_channels(raw_rule.get("channels"))
        if not trigger_text and not keywords:
            continue
        if channels and normalized_channel and normalized_channel not in channels:
            continue

        normalized_asset = normalize_outbound_asset(
            raw_rule.get("asset"),
            default_source="auto_reply_rule",
        )
        if normalized_asset is None:
            continue

        threshold_raw = raw_rule.get("threshold")
        try:
            threshold = float(threshold_raw)
        except (TypeError, ValueError):
            threshold = _DEFAULT_THRESHOLD
        threshold = max(0.0, min(1.0, threshold))

        rule_name = _clean_rule_text(raw_rule.get("name")) or f"rule-{index + 1}"
        semantic_text = "\n".join([rule_name, trigger_text, *keywords]).strip()
        keyword_score, matched_keywords = _keyword_score(
            normalized_query,
            [trigger_text, *keywords],
        )
        prepared.append(
            {
                "rule_id": _clean_rule_text(raw_rule.get("id")) or f"rule-{index + 1}",
                "rule_name": rule_name,
                "reply_text": _clean_rule_text(raw_rule.get("reply_text")) or None,
                "threshold": threshold,
                "channels": channels,
                "asset": normalized_asset,
                "semantic_text": semantic_text,
                "keyword_score": keyword_score,
                "matched_keywords": matched_keywords,
            }
        )

    if not prepared:
        return []

    query_embedding = await embedder.embed_query(normalized_query)
    semantic_inputs = [item["semantic_text"] for item in prepared]
    semantic_embeddings = await embedder.embed_documents(semantic_inputs)

    matches: list[dict[str, Any]] = []
    for item, rule_embedding in zip(prepared, semantic_embeddings):
        semantic_score = _cosine_similarity(query_embedding, rule_embedding)
        final_score = max(item["keyword_score"], semantic_score)
        if final_score < item["threshold"]:
            continue
        matches.append(
            {
                "rule_id": item["rule_id"],
                "rule_name": item["rule_name"],
                "reply_text": item["reply_text"],
                "score": final_score,
                "semantic_score": semantic_score,
                "keyword_score": item["keyword_score"],
                "channels": item["channels"],
                "matched_keywords": item["matched_keywords"],
                "asset": item["asset"],
            }
        )

    matches.sort(key=lambda match: match["score"], reverse=True)
    return matches[:_MAX_MATCHES]


def build_auto_reply_note(matches: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for match in matches:
        reply_text = _clean_rule_text(match.get("reply_text"))
        if reply_text and reply_text not in lines:
            lines.append(reply_text)
            continue
        asset = match.get("asset") or {}
        asset_name = (
            _clean_rule_text(asset.get("title"))
            or _clean_rule_text(asset.get("name"))
            or _clean_rule_text(asset.get("url"))
        )
        if asset_name:
            lines.append(f"已为你附上：{asset_name}")
    return "\n\n".join(lines)
