"""Chat service - business logic for conversations and messages."""

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.event_bus import event_bus
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.user import User
from app.schemas.chat import ConversationResponse, MessageResponse


class ChatService:
    """Handles chat business logic."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def init_visitor_conversation(
        self,
        visitor_id: str | None = None,
        title: str | None = None,
        ai_config_id: str | None = None,
        contact_info: str | None = None,
    ) -> ConversationResponse:
        """Initialize a conversation for a visitor (no auth)."""
        import uuid

        conversation = Conversation(
            id=str(uuid.uuid4()),
            visitor_id=visitor_id or f"visitor_{uuid.uuid4().hex[:8]}",
            ai_config_id=ai_config_id,
            title=title or "Visitor Chat",
            contact_info=contact_info,
            status="active",
        )
        self.db.add(conversation)
        await self.db.flush()
        await self.db.refresh(conversation)

        await event_bus.publish("conversation_created", conversation=conversation)

        return ConversationResponse.model_validate(conversation)

    async def send_message(
        self,
        conversation_id: str | None,
        content: str,
        role: str = "user",
        user: User | None = None,
    ) -> MessageResponse:
        """Send a message and trigger AI response processing."""
        # Find or create conversation
        if conversation_id:
            result = await self.db.execute(
                select(Conversation).where(
                    Conversation.id == conversation_id,
                    Conversation.status == "active",
                )
            )
            conversation = result.scalar_one_or_none()
            if conversation is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Active conversation not found",
                )
        else:
            import uuid
            conversation = Conversation(
                id=str(uuid.uuid4()),
                user_id=user.id if user else None,
                title=content[:100] if content else "New Chat",
                status="active",
            )
            self.db.add(conversation)
            await self.db.flush()

        # Save user message
        message = Message(
            conversation_id=conversation.id,
            user_id=user.id if user else None,
            role=role,
            content=content,
        )
        self.db.add(message)
        await self.db.flush()

        # Update conversation timestamps
        conversation.updated_at = datetime.now(timezone.utc)
        conversation.last_seen_at = datetime.now(timezone.utc)

        # Commit BEFORE publishing event so the bot handler can see
        # this message and update the conversation without lock contention.
        await self.db.commit()

        # Publish event for bot engine to process
        await event_bus.publish(
            "message_created",
            message=message,
            conversation=conversation,
            user=user,
        )

        return MessageResponse.model_validate(message)

    async def list_conversations(
        self,
        user_id: str | None = None,
        skip: int = 0,
        limit: int = 20,
        status: str | None = None,
    ) -> tuple[list[ConversationResponse], int]:
        """List conversations (optionally filtered by user)."""
        query = select(Conversation)
        count_query = select(func.count()).select_from(Conversation)

        if user_id:
            query = query.where(Conversation.user_id == user_id)
            count_query = count_query.where(Conversation.user_id == user_id)

        if status:
            query = query.where(Conversation.status == status)
            count_query = count_query.where(Conversation.status == status)

        query = (
            query
            .order_by(Conversation.updated_at.desc())
            .offset(skip)
            .limit(limit)
        )

        result = await self.db.execute(query)
        conversations = result.scalars().all()

        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0

        return [
            ConversationResponse.model_validate(c) for c in conversations
        ], total

    async def get_conversation(
        self,
        conversation_id: str,
        user_id: str | None = None,
    ) -> ConversationResponse | None:
        """Get a conversation with its messages."""
        query = select(Conversation).where(
            Conversation.id == conversation_id
        )
        if user_id:
            query = query.where(Conversation.user_id == user_id)

        result = await self.db.execute(query)
        conversation = result.scalar_one_or_none()

        if conversation is None:
            return None

        return ConversationResponse.model_validate(conversation)

    async def create_conversation(
        self,
        user_id: str,
        title: str | None = None,
        ai_config_id: str | None = None,
        visitor_id: str | None = None,
    ) -> ConversationResponse:
        """Create a new conversation for an authenticated user."""
        import uuid
        conversation = Conversation(
            id=str(uuid.uuid4()),
            user_id=user_id,
            ai_config_id=ai_config_id,
            visitor_id=visitor_id,
            title=title or "New Chat",
            status="active",
        )
        self.db.add(conversation)
        await self.db.flush()
        await self.db.refresh(conversation)
        return ConversationResponse.model_validate(conversation)

    async def close_conversation(
        self,
        conversation_id: str,
        user_id: str | None = None,
    ) -> bool:
        """Close a conversation."""
        query = select(Conversation).where(
            Conversation.id == conversation_id
        )
        if user_id:
            query = query.where(Conversation.user_id == user_id)

        result = await self.db.execute(query)
        conversation = result.scalar_one_or_none()

        if conversation is None:
            return False

        conversation.status = "closed"
        conversation.updated_at = datetime.now(timezone.utc)

        await event_bus.publish(
            "conversation_closed", conversation=conversation
        )

        return True
