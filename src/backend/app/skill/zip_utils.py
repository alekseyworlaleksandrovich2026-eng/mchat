"""Utilities for validating and extracting skill zip archives."""

from __future__ import annotations

import zipfile
from io import BytesIO
from pathlib import Path, PurePosixPath


def _normalize_zip_name(name: str) -> str:
    return name.replace("\\", "/").lstrip("/")


def find_skill_md_entry(names: list[str]) -> str | None:
    """Find SKILL.md inside a zip (root or nested), case-insensitive."""
    for raw in names:
        norm = _normalize_zip_name(raw)
        if not norm or norm.endswith("/"):
            continue
        if "__MACOSX" in norm or "/." in norm:
            continue
        base = PurePosixPath(norm).name
        if base.lower() == "skill.md":
            return raw
    return None


def skill_root_prefix(skill_md_entry: str) -> str:
    """Directory prefix containing SKILL.md (POSIX, may be empty)."""
    norm = _normalize_zip_name(skill_md_entry)
    parent = str(PurePosixPath(norm).parent)
    if parent in (".", ""):
        return ""
    return parent.rstrip("/") + "/"


def read_skill_meta_from_zip(content: bytes) -> dict[str, str]:
    """Read skill name from SKILL.md inside a zip without extracting to disk."""
    try:
        zf = zipfile.ZipFile(BytesIO(content))
    except zipfile.BadZipFile as e:
        raise ValueError("Invalid zip file") from e

    skill_entry = find_skill_md_entry(zf.namelist())
    if not skill_entry:
        raise ValueError("Zip file must contain SKILL.md")

    prefix = skill_root_prefix(skill_entry)
    norm_entry = _normalize_zip_name(skill_entry)
    folder_name = PurePosixPath(norm_entry).parent.name
    if folder_name in (".", ""):
        folder_name = PurePosixPath(
            prefix.rstrip("/") if prefix else norm_entry
        ).name

    raw = zf.read(skill_entry).decode("utf-8", errors="replace")
    name = folder_name or "skill"
    description = ""

    if raw.startswith("---"):
        parts = raw.split("---", 2)
        if len(parts) >= 3:
            for line in parts[1].split("\n"):
                line = line.strip()
                if ":" in line:
                    key, _, value = line.partition(":")
                    key = key.strip().lower()
                    value = value.strip().strip('"').strip("'")
                    if key == "name" and value:
                        name = value
                    elif key == "description" and value:
                        description = value

    return {"name": name, "description": description, "folder_hint": folder_name}


def extract_skill_zip(content: bytes, extract_path: Path) -> str:
    """Extract zip so SKILL.md ends up at extract_path/SKILL.md.

    Supports:
    - SKILL.md at zip root
    - my-skill/SKILL.md (single top-level folder)
    - ignores __MACOSX metadata

    Returns:
        The skill_md entry path inside the zip.

    Raises:
        ValueError: invalid zip or missing SKILL.md
    """
    try:
        zf = zipfile.ZipFile(BytesIO(content))
    except zipfile.BadZipFile as e:
        raise ValueError("Invalid zip file") from e

    skill_entry = find_skill_md_entry(zf.namelist())
    if not skill_entry:
        raise ValueError(
            "Zip file must contain SKILL.md (at root or in a subfolder)"
        )

    prefix = skill_root_prefix(skill_entry)
    extract_path.mkdir(parents=True, exist_ok=True)

    for member in zf.infolist():
        raw_name = member.filename
        norm = _normalize_zip_name(raw_name)
        if not norm or norm.endswith("/"):
            continue
        if "__MACOSX" in norm or "/." in norm:
            continue
        if prefix and not norm.startswith(prefix):
            continue
        relative = norm[len(prefix) :] if prefix else norm
        if not relative:
            continue
        target = extract_path / relative
        if member.is_dir() or raw_name.endswith("/"):
            target.mkdir(parents=True, exist_ok=True)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        with zf.open(member) as src, open(target, "wb") as dst:
            dst.write(src.read())

    if not (extract_path / "SKILL.md").exists():
        # Case mismatch on disk (e.g. skill.md) — rename if found
        for child in extract_path.rglob("*"):
            if child.is_file() and child.name.lower() == "skill.md":
                child.rename(extract_path / "SKILL.md")
                break

    if not (extract_path / "SKILL.md").exists():
        raise ValueError("Failed to extract SKILL.md")

    return skill_entry
