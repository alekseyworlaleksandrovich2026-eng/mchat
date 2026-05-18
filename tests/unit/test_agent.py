"""Test agent/AI config API."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_ai_config(client: AsyncClient, auth_headers: dict):
    """Create AI config should succeed."""
    response = await client.post(
        "/api/agents/ai-configs",
        json={
            "name": "Test Config",
            "provider": "openai",
            "model": "gpt-4o",
            "api_key": "sk-test-key",
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Config"
    assert data["provider"] == "openai"
    assert "api_key" in data


@pytest.mark.asyncio
async def test_create_ai_config_empty_key(client: AsyncClient, auth_headers: dict):
    """Create AI config with empty API key should work."""
    response = await client.post(
        "/api/agents/ai-configs",
        json={
            "name": "No Key Config",
            "provider": "openai",
            "model": "gpt-4o",
        },
        headers=auth_headers,
    )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_list_ai_configs(client: AsyncClient, auth_headers: dict):
    """List AI configs should return all."""
    # Create one
    await client.post(
        "/api/agents/ai-configs",
        json={
            "name": "List Test",
            "provider": "openai",
            "model": "gpt-4o",
            "api_key": "sk-test",
        },
        headers=auth_headers,
    )
    response = await client.get(
        "/api/agents/ai-configs",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_update_ai_config(client: AsyncClient, auth_headers: dict):
    """Update AI config should preserve or update API key."""
    # Create
    create_resp = await client.post(
        "/api/agents/ai-configs",
        json={
            "name": "Update Test",
            "provider": "openai",
            "model": "gpt-4o",
            "api_key": "sk-original",
        },
        headers=auth_headers,
    )
    config_id = create_resp.json()["id"]

    # Update (without changing key)
    response = await client.put(
        f"/api/agents/ai-configs/{config_id}",
        json={
            "name": "Updated Name",
            "provider": "openai",
            "model": "gpt-4o",
            "api_key": "sk-original",
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["api_key"] == "sk-original"


@pytest.mark.asyncio
async def test_delete_ai_config(client: AsyncClient, auth_headers: dict):
    """Delete AI config should succeed."""
    create_resp = await client.post(
        "/api/agents/ai-configs",
        json={
            "name": "Delete Test",
            "provider": "openai",
            "model": "gpt-4o",
            "api_key": "sk-test",
        },
        headers=auth_headers,
    )
    config_id = create_resp.json()["id"]

    response = await client.delete(
        f"/api/agents/ai-configs/{config_id}",
        headers=auth_headers,
    )
    assert response.status_code == 204
