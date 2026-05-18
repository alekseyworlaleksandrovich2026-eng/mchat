"""Test authentication API."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    """Admin login should succeed."""
    # First register
    await client.post(
        "/api/auth/register",
        json={"username": "testuser", "password": "testpass123"},
    )
    # Then login
    response = await client.post(
        "/api/auth/login",
        json={"username": "testuser", "password": "testpass123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_password(client: AsyncClient):
    """Login with wrong password should fail."""
    await client.post(
        "/api/auth/register",
        json={"username": "testuser2", "password": "correctpass"},
    )
    response = await client.post(
        "/api/auth/login",
        json={"username": "testuser2", "password": "wrongpass"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_register_duplicate(client: AsyncClient):
    """Duplicate registration should fail."""
    await client.post(
        "/api/auth/register",
        json={"username": "dupuser", "password": "pass123"},
    )
    response = await client.post(
        "/api/auth/register",
        json={"username": "dupuser", "password": "pass456"},
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_protected_route_requires_auth(client: AsyncClient):
    """Protected routes should require authentication."""
    response = await client.get("/api/chat/conversations")
    assert response.status_code in (401, 403)
