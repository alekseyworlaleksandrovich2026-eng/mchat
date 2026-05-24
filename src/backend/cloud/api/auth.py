"""Cloud auth API router — public signup endpoint."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.auth import TokenResponse
from app.services.auth_service import AuthService
from cloud.schemas.auth import SignupRequest

router = APIRouter()


@router.post("/signup", response_model=TokenResponse)
async def signup(
    request: SignupRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Public user signup — creates a 'user' role account."""
    auth_service = AuthService(db)
    try:
        result = await auth_service.signup(
            username=request.username,
            password=request.password,
            email=request.email,
            display_name=request.display_name,
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Signup failed: {e}",
        )
