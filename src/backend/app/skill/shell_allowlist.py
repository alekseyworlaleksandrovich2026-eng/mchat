"""Parse and run admin-configured shell command allowlist (server_ops)."""

from __future__ import annotations

import re
import shlex
import subprocess
from typing import Any

_FORBIDDEN_SHELL_FRAGMENTS = (
    ";",
    "|",
    "&&",
    "||",
    ">",
    "<",
    "`",
    "$(",
    "${",
    "\n",
    "\r",
)


def _slug_id(raw: str, fallback: str = "cmd") -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "-", raw).strip("-._")
    return cleaned[:80] or fallback


def parse_shell_allowlist_lines(text: str) -> list[dict[str, Any]]:
    """Parse textarea lines: ``id | argv command`` or bare command (auto id)."""
    entries: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "|" in line:
            entry_id, command = line.split("|", 1)
            entry_id = entry_id.strip()
            command = command.strip()
        else:
            command = line
            entry_id = _slug_id(command.split()[0] if command.split() else "cmd")
        if not entry_id or not command:
            continue
        for frag in _FORBIDDEN_SHELL_FRAGMENTS:
            if frag in command:
                raise ValueError(f"命令不允许包含 {frag!r}: {command[:120]}")
        argv = shlex.split(command)
        if not argv:
            continue
        if entry_id in seen_ids:
            raise ValueError(f"重复的命令 id: {entry_id}")
        seen_ids.add(entry_id)
        entries.append(
            {
                "id": entry_id,
                "command": command,
                "argv": argv,
            }
        )
    return entries


def allowlist_to_text(entries: list[dict[str, Any]] | None) -> str:
    if not entries:
        return ""
    lines: list[str] = []
    for item in entries:
        entry_id = str(item.get("id") or "").strip()
        command = str(item.get("command") or "").strip()
        if not command and item.get("argv"):
            command = shlex.join([str(x) for x in item["argv"]])
        if entry_id and command:
            lines.append(f"{entry_id} | {command}")
    return "\n".join(lines)


def normalize_allowlist_entries(raw: Any) -> list[dict[str, Any]]:
    if not raw:
        return []
    if isinstance(raw, str):
        return parse_shell_allowlist_lines(raw)
    if not isinstance(raw, list):
        return []
    out: list[dict[str, Any]] = []
    for item in raw:
        if isinstance(item, str):
            parsed = parse_shell_allowlist_lines(item)
            out.extend(parsed)
            continue
        if not isinstance(item, dict):
            continue
        entry_id = str(item.get("id") or "").strip()
        command = str(item.get("command") or "").strip()
        argv = item.get("argv")
        if argv and isinstance(argv, list):
            argv = [str(x) for x in argv]
        elif command:
            for frag in _FORBIDDEN_SHELL_FRAGMENTS:
                if frag in command:
                    raise ValueError(f"命令不允许包含 {frag!r}")
            argv = shlex.split(command)
        else:
            continue
        if not entry_id:
            entry_id = _slug_id(argv[0] if argv else "cmd")
        if not command:
            command = shlex.join(argv)
        out.append({"id": entry_id, "command": command, "argv": argv})
    return out


def run_allowlisted_command(
    shell_id: str | None,
    *,
    allowlist: list[dict[str, Any]] | None,
    timeout_sec: int = 60,
) -> dict[str, Any]:
    """Execute argv from allowlist entry (no shell=True)."""
    sid = (shell_id or "").strip()
    if not sid:
        return {
            "ok": False,
            "error": "缺少 shell_id",
            "allowed_ids": [e.get("id") for e in (allowlist or [])],
        }
    entries = allowlist or []
    match = next((e for e in entries if str(e.get("id")) == sid), None)
    if match is None:
        return {
            "ok": False,
            "error": f"shell_id 不在白名单: {sid}",
            "allowed_ids": [e.get("id") for e in entries],
        }
    argv = match.get("argv") or []
    if not argv:
        return {"ok": False, "error": f"白名单项 {sid} 无有效 argv"}
    command_display = str(match.get("command") or shlex.join(argv))
    try:
        proc = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=timeout_sec,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": f"命令超时 ({timeout_sec}s)", "command": command_display}
    except OSError as e:
        return {"ok": False, "error": str(e), "command": command_display}

    stdout = (proc.stdout or "")[-12000:]
    stderr = (proc.stderr or "")[-3000:]

    return {
        "ok": proc.returncode == 0,
        "message": format_command_output_message(
            command_display, stdout, stderr, proc.returncode
        ),
        "command": command_display,
        "stdout": stdout,
        "stderr": stderr,
        "exit_code": proc.returncode,
        "shell_id": sid,
    }


def format_command_output_message(
    command: str,
    stdout: str,
    stderr: str,
    exit_code: int,
) -> str:
    """Markdown for chat UI (preserves newlines in kubectl/logs output)."""
    header = f"**命令** `{command}` · exit `{exit_code}`"
    blocks: list[str] = [header]
    if stdout and stdout.strip():
        blocks.append("```text\n" + stdout.rstrip() + "\n```")
    if stderr and stderr.strip():
        blocks.append("**stderr**\n```text\n" + stderr.rstrip() + "\n```")
    if not stdout.strip() and not stderr.strip():
        blocks.append("（无输出）")
    return "\n\n".join(blocks)
