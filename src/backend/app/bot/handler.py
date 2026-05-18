"""Bot engine event handler - processes messages and streams AI responses."""

from loguru import logger
from sqlalchemy import select

from app.bot.engine import process_message
from app.core.database import async_session_factory
from app.core.event_bus import event_bus
from app.models.ai_config import AIConfig
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.user import User
from app.websocket import ws_manager


async def on_message_created(
    message: Message,
    conversation: Conversation,
    user: User | None = None,
) -> None:
    """Handle message_created event: process with bot engine and stream response.

    Opens a fresh DB session, reloads the conversation, loads AI config,
    and streams AI-generated tokens to WebSocket subscribers.
    """
    cov_id = conversation.id
    logger.info(f"Bot processing message {message.id} in conversation {cov_id}")

    try:
        async with async_session_factory() as db:
            # Reload conversation in this session so ORM changes are tracked
            conv_result = await db.execute(
                select(Conversation).where(Conversation.id == cov_id)
            )
            conv = conv_result.scalar_one_or_none()
            if conv is None:
                logger.warning(f"Conversation {cov_id} not found")
                return

            # Load AI config (use conversation's ai_config_id or default)
            ai_config = None
            if conv.ai_config_id:
                cfg_result = await db.execute(
                    select(AIConfig).where(AIConfig.id == conv.ai_config_id)
                )
                ai_config = cfg_result.scalar_one_or_none()

            if ai_config is None:
                cfg_result = await db.execute(
                    select(AIConfig).where(AIConfig.is_default == True)
                )
                ai_config = cfg_result.scalar_one_or_none()

            if ai_config is None:
                error_msg = (
                    "No AI configuration found. "
                    "Please configure an AI provider in the admin panel."
                )
                logger.warning(error_msg)
                await ws_manager.send_to_conversation(
                    cov_id,
                    {
                        "type": "chat:message",
                        "message": {
                            "id": f"ai-error-{message.id}",
                            "role": "assistant",
                            "content": error_msg,
                            "conversation_id": cov_id,
                            "created_at": "2025-01-01T00:00:00Z",
                        },
                    },
                )
                return

            # Stream AI response tokens to WebSocket
            full_content = ""
            async for token in process_message(conv, message, ai_config, db):
                full_content += token
                await ws_manager.send_to_conversation(
                    cov_id,
                    {
                        "type": "chat:stream",
                        "conversation_id": cov_id,
                        "content": token,
                    },
                )

            # Signal stream end
            await ws_manager.send_to_conversation(
                cov_id,
                {
                    "type": "chat:stream:end",
                    "conversation_id": cov_id,
                    "content": full_content,
                },
            )

            await db.commit()
            logger.info(f"Bot completed response for conversation {cov_id}")

    except Exception as e:
        logger.error(f"Bot engine error: {e}", exc_info=True)
        await ws_manager.send_to_conversation(
            cov_id,
            {
                "type": "chat:message",
                "message": {
                    "id": f"ai-error-{message.id}",
                    "role": "assistant",
                    "content": f"Sorry, I encountered an error: {str(e)}",
                    "conversation_id": cov_id,
                    "created_at": "2025-01-01T00:00:00Z",
                },
            },
        )


def init_bot_engine() -> None:
    """Subscribe bot engine handler to message_created events."""
    event_bus.subscribe("message_created", on_message_created)
    logger.info("Bot engine initialized and listening for messages")
