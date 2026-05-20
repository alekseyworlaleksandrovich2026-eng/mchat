import pytest

from app.bot.auto_reply_rules import (
    build_auto_reply_note,
    detect_message_channel,
    match_auto_reply_rules,
)


async def _fake_embed_query(_: str) -> list[float]:
    return [1.0, 0.0]


async def _fake_embed_documents(texts: list[str]) -> list[list[float]]:
    out: list[list[float]] = []
    for text in texts:
        lowered = text.lower()
        if "manual" in lowered or "操作手册" in lowered:
            out.append([1.0, 0.0])
        elif "video" in lowered or "演示视频" in lowered:
            out.append([0.9, 0.1])
        else:
            out.append([0.0, 1.0])
    return out


@pytest.mark.asyncio
async def test_match_auto_reply_rules_supports_semantic_and_keyword(monkeypatch):
    monkeypatch.setattr("app.bot.auto_reply_rules.embedder.embed_query", _fake_embed_query)
    monkeypatch.setattr("app.bot.auto_reply_rules.embedder.embed_documents", _fake_embed_documents)

    matches = await match_auto_reply_rules(
        "把操作说明发我看看",
        [
            {
                "id": "manual",
                "name": "操作手册",
                "trigger_text": "用户想要操作手册或说明书",
                "keywords": ["manual", "说明书"],
                "reply_text": "这是操作手册，请查收。",
                "asset": {
                    "url": "https://example.com/manual.pdf",
                    "name": "操作手册.pdf",
                    "mime": "application/pdf",
                },
            },
            {
                "id": "video",
                "name": "演示视频",
                "trigger_text": "用户想看操作视频",
                "keywords": ["视频"],
                "asset": {
                    "url": "https://example.com/demo.mp4",
                    "name": "演示视频.mp4",
                    "mime": "video/mp4",
                },
            },
        ],
    )

    assert matches
    assert matches[0]["rule_id"] == "manual"
    assert matches[0]["asset"]["url"] == "https://example.com/manual.pdf"


@pytest.mark.asyncio
async def test_build_auto_reply_note_prefers_configured_reply_text():
    note = build_auto_reply_note(
        [
            {
                "reply_text": "这是演示视频，请查收。",
                "asset": {"name": "演示视频.mp4"},
            }
        ]
    )

    assert note == "这是演示视频，请查收。"


def test_detect_message_channel_from_conversation_contact():
    assert detect_message_channel("widget_customer:abc") == "widget"
    assert detect_message_channel("wechat_channel:abc") == "wechat"
    assert detect_message_channel(None) == "admin"


@pytest.mark.asyncio
async def test_match_auto_reply_rules_respects_channel_restrictions(monkeypatch):
    monkeypatch.setattr("app.bot.auto_reply_rules.embedder.embed_query", _fake_embed_query)
    monkeypatch.setattr("app.bot.auto_reply_rules.embedder.embed_documents", _fake_embed_documents)

    rules = [
        {
            "id": "manual-widget",
            "name": "操作手册",
            "trigger_text": "用户想要操作手册或说明书",
            "keywords": ["manual", "说明书"],
            "channels": ["widget"],
            "asset": {
                "url": "https://example.com/manual.pdf",
                "name": "操作手册.pdf",
                "mime": "application/pdf",
            },
        }
    ]

    widget_matches = await match_auto_reply_rules(
        "把操作说明发我看看",
        rules,
        channel="widget",
    )
    wechat_matches = await match_auto_reply_rules(
        "把操作说明发我看看",
        rules,
        channel="wechat",
    )

    assert widget_matches
    assert widget_matches[0]["rule_id"] == "manual-widget"
    assert wechat_matches == []