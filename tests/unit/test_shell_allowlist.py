"""Tests for server_ops shell allowlist parsing."""

import pytest

from app.skill.shell_allowlist import (
    allowlist_to_text,
    format_command_output_message,
    parse_shell_allowlist_lines,
)


def test_parse_allowlist_lines():
    entries = parse_shell_allowlist_lines(
        "# comment\n"
        "k8s-pods | kubectl get pods -n default -o wide\n"
        "docker-ps | docker ps\n"
    )
    assert len(entries) == 2
    assert entries[0]["id"] == "k8s-pods"
    assert entries[0]["argv"][:3] == ["kubectl", "get", "pods"]


def test_parse_rejects_shell_metachar():
    with pytest.raises(ValueError):
        parse_shell_allowlist_lines("bad | echo ok; rm -rf /")


def test_format_command_output_preserves_newlines():
    out = format_command_output_message(
        "kubectl get pods",
        "NAME\npod-a\npod-b\n",
        "",
        0,
    )
    assert "pod-a" in out
    assert "```text" in out


def test_allowlist_roundtrip_text():
    entries = [{"id": "a", "command": "kubectl get nodes", "argv": ["kubectl", "get", "nodes"]}]
    text = allowlist_to_text(entries)
    assert "a | kubectl get nodes" in text
