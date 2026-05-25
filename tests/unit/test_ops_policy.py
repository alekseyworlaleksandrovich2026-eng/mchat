"""Tests for server_ops skill policy."""

from types import SimpleNamespace

from app.skill.ops_policy import (
    SCOPE_SERVER_OPS,
    filter_skills_by_ops_policy,
    is_server_ops_skill,
    skill_scope,
)


def _skill(name: str, scope: str = "tenant") -> SimpleNamespace:
    return SimpleNamespace(
        name=name,
        config={"scope": scope},
    )


def test_skill_scope_defaults_tenant():
    assert skill_scope(_skill("patent-search")) == "tenant"
    assert skill_scope(_skill("mchat-ops", SCOPE_SERVER_OPS)) == SCOPE_SERVER_OPS


def test_filter_drops_server_ops_when_disabled():
    skills = [_skill("a"), _skill("mchat-ops", SCOPE_SERVER_OPS)]
    out = filter_skills_by_ops_policy(
        skills, allow_server_ops=False, allowlist=None
    )
    assert [s.name for s in out] == ["a"]


def test_filter_allowlist():
    skills = [_skill("mchat-ops", SCOPE_SERVER_OPS), _skill("other-ops", SCOPE_SERVER_OPS)]
    out = filter_skills_by_ops_policy(
        skills,
        allow_server_ops=True,
        allowlist=["mchat-ops"],
    )
    assert [s.name for s in out] == ["mchat-ops"]


def test_is_server_ops_skill():
    assert is_server_ops_skill(_skill("mchat-ops", SCOPE_SERVER_OPS))
    assert not is_server_ops_skill(_skill("patent-search"))
