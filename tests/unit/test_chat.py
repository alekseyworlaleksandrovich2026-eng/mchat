"""Test chat API endpoints."""

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.models.conversation import Conversation
from app.models.message import Message
from app.models.user import User
from app.services.chat_service import ChatService


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
async def test_list_conversations_supports_server_side_search(client: AsyncClient, auth_headers: dict, db_session):
    admin_user = (
        await db_session.execute(select(User).where(User.username == "admin"))
    ).scalar_one()

    widget_conv = Conversation(
        user_id=admin_user.id,
        title="Widget: Sales",
        visitor_id="visitor_widget_1",
        contact_info="widget_customer:test-widget",
        status="active",
    )
    admin_conv = Conversation(
        user_id=admin_user.id,
        title="Internal Follow-up",
        visitor_id="visitor_admin_1",
        contact_info="manual:admin",
        status="active",
    )
    db_session.add_all([widget_conv, admin_conv])
    await db_session.flush()

    db_session.add_all(
        [
            Message(conversation_id=widget_conv.id, role="user", content="pricing question"),
            Message(conversation_id=admin_conv.id, role="user", content="billing request"),
        ]
    )
    await db_session.commit()

    search_resp = await client.get(
        "/api/chat/conversations",
        params={"search": "pricing"},
        headers=auth_headers,
    )
    assert search_resp.status_code == 200
    search_data = search_resp.json()
    assert search_data["total"] == 1
    assert search_data["items"][0]["id"] == widget_conv.id
    assert search_data["items"][0]["first_user_message_preview"] == "pricing question"

    type_resp = await client.get(
        "/api/chat/conversations",
        params={"search": "widget"},
        headers=auth_headers,
    )
    assert type_resp.status_code == 200
    type_data = type_resp.json()
    ids = {item["id"] for item in type_data["items"]}
    assert widget_conv.id in ids


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
async def test_send_message_with_outbound_assets(client: AsyncClient, auth_headers: dict):
    """Chat send should normalize provided outbound assets into message extra_data."""
    conv_resp = await client.post(
        "/api/chat/conversations",
        json={"title": "Asset Test"},
        headers=auth_headers,
    )
    conv_id = conv_resp.json()["id"]

    response = await client.post(
        "/api/chat/send",
        json={
            "conversation_id": conv_id,
            "content": "请查看附件",
            "role": "assistant",
            "extra_data": {
                "outbound_assets": [
                    {
                        "type": "image",
                        "name": "商品图",
                        "url": "https://cdn.example.com/item.png",
                    }
                ]
            },
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["extra_data"]["outbound_assets"] == [
        {
            "type": "image",
            "name": "商品图",
            "url": "https://cdn.example.com/item.png",
            "source": "explicit",
        }
    ]


@pytest.mark.asyncio
async def test_upload_attachment_as_assistant_with_link_asset(client: AsyncClient, auth_headers: dict):
    conv_resp = await client.post(
        "/api/chat/conversations",
        json={"title": "Assistant Asset Test"},
        headers=auth_headers,
    )
    conv_id = conv_resp.json()["id"]

    response = await client.post(
        "/api/chat/upload",
        headers=auth_headers,
        files={"file": ("note.txt", b"hello", "text/plain")},
        data={
            "conversation_id": conv_id,
            "role": "assistant",
            "content": "资料如下",
            "extraData": '{"outbound_assets":[{"type":"link","name":"官网","url":"https://example.com"}]}',
        },
    )

    assert response.status_code == 200
    data = response.json()
    assets = data["extra_data"]["outbound_assets"]
    assert {asset["url"] for asset in assets} == {
        "https://example.com",
        data["extra_data"]["attachments"][0]["url"],
    }
    assert data["role"] == "assistant"


@pytest.mark.asyncio
async def test_assistant_message_does_not_publish_bot_event(db_session, monkeypatch):
    published_events: list[str] = []

    async def fake_publish(event: str, **_: object):
        published_events.append(event)

    monkeypatch.setattr("app.services.chat_service.event_bus.publish", fake_publish)

    user = User(username="agent_1", password_hash="x", role="agent")
    db_session.add(user)
    await db_session.flush()

    conversation = Conversation(user_id=user.id, title="Manual reply")
    db_session.add(conversation)
    await db_session.flush()

    service = ChatService(db_session)
    message = await service.send_message(
        conversation_id=conversation.id,
        content="这是人工客服回复",
        role="assistant",
        user=user,
    )

    assert message.role == "assistant"
    assert published_events == []


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
