"""Test chat API endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_conversation(client: AsyncClient, auth_headers: dict):
    """Admin should be able to create a conversation."""
    response = await client.post(
        "/api/chat/conversations",
        json={"title": "Test Conversation"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Conversation"
    assert data["status"] == "active"
    assert "id" in data


@pytest.mark.asyncio
async def test_list_conversations(client: AsyncClient, auth_headers: dict):
    """List conversations should return created ones."""
    # Create one first
    await client.post(
        "/api/chat/conversations",
        json={"title": "Test Conv"},
        headers=auth_headers,
    )
    response = await client.get(
        "/api/chat/conversations",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data or isinstance(data, list)


@pytest.mark.asyncio
async def test_send_message(client: AsyncClient, auth_headers: dict):
    """Sending a message should create it and trigger bot engine."""
    # Create conversation
    conv_resp = await client.post(
        "/api/chat/conversations",
        json={"title": "Message Test"},
        headers=auth_headers,
    )
    conv_id = conv_resp.json()["id"]

    # Send message
    response = await client.post(
        "/api/chat/send",
        json={
            "conversation_id": conv_id,
            "content": "Hello, bot!",
            "role": "user",
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "user"
    assert data["content"] == "Hello, bot!"


@pytest.mark.asyncio
async def test_get_conversation(client: AsyncClient, auth_headers: dict):
    """Get conversation should return messages."""
    conv_resp = await client.post(
        "/api/chat/conversations",
        json={"title": "Get Test"},
        headers=auth_headers,
    )
    conv_id = conv_resp.json()["id"]

    # Send a message
    await client.post(
        "/api/chat/send",
        json={"conversation_id": conv_id, "content": "Hi!", "role": "user"},
        headers=auth_headers,
    )

    # Get conversation
    response = await client.get(
        f"/api/chat/conversations/{conv_id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "messages" in data
