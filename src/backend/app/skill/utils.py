"""Shared helpers for skill filesystem layout and prompt bodies."""

from __future__ import annotations

from pathlib import Path


def skill_directory(skill_path: str | None) -> Path | None:
    if not skill_path:
        return None
    p = Path(skill_path)
    return p.parent if p.is_file() else p


def has_executable_script(skill_path: str | None) -> bool:
    """True when skill folder contains main.py or tool.py."""
    skill_dir = skill_directory(skill_path)
    if skill_dir is None or not skill_dir.is_dir():
        return False
    return (skill_dir / "main.py").exists() or (skill_dir / "tool.py").exists()


def get_prompt_body(skill: object) -> str:
    """Read prompt instructions from skill config or description."""
    config = getattr(skill, "config", None) or {}
    if isinstance(config, dict):
        body = config.get("prompt_body") or ""
        if body:
            return str(body).strip()
    desc = getattr(skill, "description", None) or ""
    return str(desc).strip()
