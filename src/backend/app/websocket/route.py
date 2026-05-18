"""WebSocket route for real-time chat."""

import json
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory
from app.models.user import User
from app.websocket import ws_manager

router = APIRouter()


async def _authenticate_ws(token: str | None) -> User | None:
    """Validate token and return user, or None."""
    if not token:
        return None
    try:
        from app.core.security import verify_access_token
        payload = verify_access_token(token)
        user_id = payload.get("sub")
        if not user_id:
            return None
        async with async_session_factory() as db:
            result = await db.execute(select(User).where(User.id == user_id))
            return result.scalar_one_or_none()
    except Exception:
        return None


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str | None = Query(None),
):
    """WebSocket endpoint for real-time chat streaming.

    Client messages:
    - { "type": "subscribe", "conversation_id": "..." }
    - { "type": "unsubscribe", "conversation_id": "..." }
    - { "type": "chat:message", "conversationId": "...", "content": "..." }  (HTTP is preferred)

    Server messages:
    - { "type": "chat:stream", "conversation_id": "...", "content": "..." }
    - { "type": "chat:stream:end", "conversation_id": "..." }
    - { "type": "chat:message", "message": {...} }
    """
    user = await _authenticate_ws(token)
    if user:
        logger.info(f"WebSocket authenticated as {user.username}")
    else:
        logger.info("WebSocket connected (anonymous)")

    await websocket.accept()
    current_conversation: str | None = None

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                continue

            msg_type = data.get("type", "")

            if msg_type == "ping":
                await websocket.send_json({"type": "pong"})

            elif msg_type == "subscribe":
                conv_id = data.get("conversation_id") or data.get("conversationId")
                if conv_id:
                    # Unsubscribe from previous
                    if current_conversation:
                        ws_manager.disconnect(websocket)
                    # Subscribe to new
                    ws_manager._conversation_connections[conv_id].append(websocket)
                    ws_manager._ws_conversation[websocket] = conv_id
                    current_conversation = conv_id
                    logger.debug(f"WebSocket subscribed to conversation {conv_id}")
                    await websocket.send_json({"type": "subscribed", "conversation_id": conv_id})

            elif msg_type == "unsubscribe":
                ws_manager.disconnect(websocket)
                current_conversation = None

            elif msg_type == "chat:message":
                # Process chat message via WebSocket (same as HTTP POST /api/chat/send)
                conv_id = data.get("conversationId") or data.get("conversation_id")
                content = data.get("content", "")
                if conv_id and content:
                    try:
                        from app.services.chat_service import ChatService
                        async with async_session_factory() as db:
                            chat_service = ChatService(db)
                            await chat_service.send_message(
                                conversation_id=conv_id,
                                content=content,
                                role="user",
                                user=user,
                            )
                    except Exception as e:
                        logger.error(f"WebSocket chat:message error: {e}")
                        await websocket.send_json({
                            "type": "chat:error",
                            "message": f"发送失败: {e}",
                        })

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket error: {e}")

    finally:
        ws_manager.disconnect(websocket)
