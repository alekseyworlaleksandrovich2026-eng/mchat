"""Chat API router."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.auth import get_current_user, get_current_agent
from app.models.user import User
from app.schemas.chat import (
    ConversationList,
    ConversationResponse,
    CreateConversationRequest,
    InitConversationRequest,
    MessageCreate,
    MessageResponse,
)
from app.services.chat_service import ChatService

router = APIRouter()


@router.post("/send", response_model=MessageResponse)
async def send_message(
    request: MessageCreate,
    current_user: User | None = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Send a message and get AI response."""
    chat_service = ChatService(db)
    try:
        result = await chat_service.send_message(
            conversation_id=request.conversation_id,
            content=request.content,
            role=request.role,
            user=current_user,
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send message: {e}",
        )


@router.get("/conversations", response_model=ConversationList)
async def list_conversations(
    skip: int = 0,
    limit: int = 20,
    status_filter: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List conversations (admin sees all, agent sees own)."""
    chat_service = ChatService(db)
    user_id = None if current_user.role == "admin" else current_user.id
    conversations, total = await chat_service.list_conversations(
        user_id=user_id,
        skip=skip,
        limit=limit,
        status=status_filter,
    )
    return ConversationList(items=conversations, total=total)


@router.post("/conversations", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    request: CreateConversationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new conversation."""
    chat_service = ChatService(db)
    conversation = await chat_service.create_conversation(
        user_id=current_user.id,
        title=request.title,
        ai_config_id=request.ai_config_id,
        visitor_id=request.visitor_id,
    )
    return conversation


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get conversation with messages."""
    chat_service = ChatService(db)
    user_id = None if current_user.role == "admin" else current_user.id
    conversation = await chat_service.get_conversation(
        conversation_id=conversation_id,
        user_id=user_id,
    )
    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )
    return conversation


@router.post("/conversations/{conversation_id}/close")
async def close_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Close a conversation."""
    chat_service = ChatService(db)
    user_id = None if current_user.role == "admin" else current_user.id
    success = await chat_service.close_conversation(
        conversation_id=conversation_id,
        user_id=user_id,
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )
    return {"status": "closed"}


@router.post("/conversations/init", response_model=ConversationResponse)
async def init_conversation(
    request: InitConversationRequest,
    db: AsyncSession = Depends(get_db),
):
    """Initialize a visitor conversation (no auth required)."""
    chat_service = ChatService(db)
    conversation = await chat_service.init_visitor_conversation(
        visitor_id=request.visitor_id,
        title=request.title,
        ai_config_id=request.ai_config_id,
        contact_info=request.contact_info,
    )
    return conversation
