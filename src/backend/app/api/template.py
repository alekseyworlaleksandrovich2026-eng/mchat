"""Template marketplace API router — public, no auth required."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.portal import ChannelTemplateResponse
from app.services.portal_service import PortalService

router = APIRouter()


@router.get("", response_model=list[ChannelTemplateResponse])
async def list_templates(
    db: AsyncSession = Depends(get_db),
) -> list[ChannelTemplateResponse]:
    """List all published channel templates."""
    return await PortalService(db).list_published_templates()


@router.get("/{template_id}", response_model=ChannelTemplateResponse)
async def get_template(
    template_id: str,
    db: AsyncSession = Depends(get_db),
) -> ChannelTemplateResponse:
    """Get a published channel template by ID."""
    return await PortalService(db).get_template(template_id)
