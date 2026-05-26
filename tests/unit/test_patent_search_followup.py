"""Tests for patent-search follow-up prompts."""

from types import SimpleNamespace

from app.bot.patent_search_followup import (
    is_patent_search_success,
    patent_search_presentation_nudge,
    patent_search_tool_hint,
)


def test_presentation_nudge_default_chinese():
    text = patent_search_presentation_nudge(None)
    assert "用户看不到" in text
    assert "🔍 搜索完成" in text
    assert "制表符分隔表格" in text


def test_is_patent_search_success_markers():
    assert is_patent_search_success(
        "patent-search",
        "search",
        "🔍 搜索完成\nfoo",
    )
    assert is_patent_search_success(
        "patent-search", "search", "Search complete\nfoo"
    )
    assert not is_patent_search_success("patent-search", "detail", "ok")


def test_custom_nudge_from_skill_config():
    skill = SimpleNamespace(
        name="patent-search",
        config={"presentation_nudge": "Custom presentation prompt."},
    )
    assert patent_search_presentation_nudge(skill) == "Custom presentation prompt."
    assert "patent-search" in patent_search_tool_hint(skill).lower()
