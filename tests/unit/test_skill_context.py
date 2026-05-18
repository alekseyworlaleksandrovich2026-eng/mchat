"""Tests for skill type detection and prompt skill loading."""

from pathlib import Path

from app.skill.loader import SkillLoader


def test_wheelchair_skill_parsed_as_prompt():
    skills_dir = Path(__file__).resolve().parents[2] / "skills"
    loader = SkillLoader(str(skills_dir))
    skills = loader.scan_skills()
    wheelchair = next(
        (s for s in skills if s.get("name") == "wheelchair-advisor"),
        None,
    )
    assert wheelchair is not None
    assert wheelchair["type"] == "prompt"
    assert "prompt_body" in (wheelchair.get("config") or {})
    assert "对话流程" in wheelchair["config"]["prompt_body"]
