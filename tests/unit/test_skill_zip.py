"""Tests for skill zip extraction."""

import zipfile
from io import BytesIO
from pathlib import Path

from app.skill.zip_utils import extract_skill_zip, find_skill_md_entry


def _make_zip(files: dict[str, str]) -> bytes:
    buf = BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, content in files.items():
            zf.writestr(name, content)
    return buf.getvalue()


def test_find_skill_md_at_root():
    names = ["SKILL.md", "handler.py"]
    assert find_skill_md_entry(names) == "SKILL.md"


def test_find_skill_md_in_subfolder():
    names = ["my-skill/SKILL.md", "my-skill/handler.py"]
    assert find_skill_md_entry(names) == "my-skill/SKILL.md"


def test_find_skill_md_case_insensitive():
    names = ["folder/skill.md"]
    assert find_skill_md_entry(names) == "folder/skill.md"


def test_extract_nested_folder(tmp_path: Path):
    content = _make_zip(
        {
            "demo-skill/SKILL.md": "---\nname: demo-skill\ndescription: test\n---\n",
            "demo-skill/handler.py": "# handler\n",
        }
    )
    target = tmp_path / "demo-skill"
    extract_skill_zip(content, target)
    assert (target / "SKILL.md").exists()
    assert (target / "handler.py").exists()
