"""SKILL.md scope frontmatter is parsed into config."""

from pathlib import Path

from app.skill.loader import SkillLoader


def test_mchat_ops_scope_parsed():
    skills_dir = Path(__file__).resolve().parents[2] / "skills"
    loader = SkillLoader(str(skills_dir))
    skills = loader.scan_skills()
    ops = next((s for s in skills if s.get("name") == "mchat-ops"), None)
    assert ops is not None
    assert (ops.get("config") or {}).get("scope") == "server_ops"
