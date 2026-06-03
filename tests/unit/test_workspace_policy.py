"""Tests for workspace container eligibility policy."""

from __future__ import annotations

import pytest

from app.core.config import settings
from app.workspace.policy import container_block_reason, plan_allows_container_auto
from app.workspace.resolver import resolve_workspace_mode
from app.workspace.types import WorkspaceMode


@pytest.fixture(autouse=True)
def _container_enabled(monkeypatch):
    monkeypatch.setattr(settings, "workspace_container_enabled", True)
    monkeypatch.setattr(settings, "workspace_default_mode", "local")


def test_plan_allows_container_auto():
    assert plan_allows_container_auto("free", subscription_active=True) is False
    assert plan_allows_container_auto("pro", subscription_active=True) is True
    assert plan_allows_container_auto("pro", subscription_active=False) is False


def test_channel_container_override_allowed_on_free():
    assert (
        resolve_workspace_mode(
            plan="free",
            workspace_mode_override="container",
        )
        == WorkspaceMode.CONTAINER
    )
    assert (
        container_block_reason(
            plan="free",
            subscription_active=True,
            workspace_mode_override="container",
            requested_mode=WorkspaceMode.CONTAINER,
        )
        is None
    )


def test_pro_plan_auto_container():
    assert (
        resolve_workspace_mode(
            plan="pro",
            workspace_mode_override=None,
            subscription_active=True,
        )
        == WorkspaceMode.CONTAINER
    )


def test_free_plan_defaults_local():
    assert (
        resolve_workspace_mode(
            plan="free",
            workspace_mode_override=None,
        )
        == WorkspaceMode.LOCAL
    )


def test_global_disabled_blocks_container(monkeypatch):
    monkeypatch.setattr(settings, "workspace_container_enabled", False)
    reason = container_block_reason(
        plan="pro",
        subscription_active=True,
        workspace_mode_override="container",
        requested_mode=WorkspaceMode.CONTAINER,
    )
    assert reason == "container_disabled_globally"
    assert (
        resolve_workspace_mode(
            plan="pro",
            workspace_mode_override="container",
        )
        == WorkspaceMode.LOCAL
    )
