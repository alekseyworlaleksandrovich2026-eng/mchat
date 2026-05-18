"""Agent management API router."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.schemas.agent import (
    AIConfigCreate,
    AIConfigResponse,
    AIConfigUpdate,
    ConnectionTestRequest,
    ConnectionTestResponse,
    CustomerConfigCreate,
    CustomerConfigResponse,
    ModelCatalogRequest,
    ModelCatalogResponse,
)
from app.services.agent_service import AgentService
from app.services.model_catalog import ConnectionParams, list_models, test_connection

router = APIRouter()


@router.post("/ai-configs", response_model=AIConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_ai_config(
    request: AIConfigCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new AI configuration."""
    service = AgentService(db)
    return await service.create_ai_config(user_id=current_user.id, data=request)


@router.get("/ai-configs", response_model=list[AIConfigResponse])
async def list_ai_configs(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all AI configurations for current user."""
    service = AgentService(db)
    return await service.list_ai_configs(user_id=current_user.id)


@router.get("/ai-configs/{config_id}", response_model=AIConfigResponse)
async def get_ai_config(
    config_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific AI configuration."""
    service = AgentService(db)
    config = await service.get_ai_config(
        config_id=config_id, user_id=current_user.id
    )
    if config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI config not found",
        )
    return config


@router.put("/ai-configs/{config_id}", response_model=AIConfigResponse)
async def update_ai_config(
    config_id: str,
    request: AIConfigUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an AI configuration."""
    service = AgentService(db)
    config = await service.update_ai_config(
        config_id=config_id, user_id=current_user.id, data=request
    )
    if config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI config not found",
        )
    return config


@router.post("/ai-configs/models", response_model=ModelCatalogResponse)
async def fetch_model_catalog(
    request: ModelCatalogRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List models from provider API (OpenAI-compatible, Anthropic, Google)."""
    api_key = request.api_key
    if not api_key.strip() and request.config_id:
        service = AgentService(db)
        cfg = await service.get_ai_config(request.config_id, current_user.id)
        if cfg:
            api_key = cfg.api_key
    models = await list_models(
        ConnectionParams(
            provider=request.provider,
            api_key=api_key,
            api_base=request.api_base,
        )
    )
    return ModelCatalogResponse(models=models)


@router.post("/ai-configs/test", response_model=ConnectionTestResponse)
async def test_ai_connection(
    request: ConnectionTestRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Send a minimal chat request to verify API credentials."""
    api_key = request.api_key
    api_base = request.api_base
    if request.config_id:
        service = AgentService(db)
        cfg = await service.get_ai_config(request.config_id, current_user.id)
        if cfg is None:
            raise HTTPException(status_code=404, detail="AI config not found")
        if not api_key.strip():
            api_key = cfg.api_key
        if api_base is None:
            api_base = cfg.api_base
    ok, message = await test_connection(
        ConnectionParams(
            provider=request.provider,
            api_key=api_key,
            api_base=api_base,
        ),
        model=request.model,
    )
    return ConnectionTestResponse(ok=ok, message=message)


@router.delete("/ai-configs/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ai_config(
    config_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete an AI configuration."""
    service = AgentService(db)
    success = await service.delete_ai_config(
        config_id=config_id, user_id=current_user.id
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI config not found",
        )
    return None


@router.post("/customer-configs", response_model=CustomerConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_customer_config(
    request: CustomerConfigCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new customer service configuration."""
    service = AgentService(db)
    return await service.create_customer_config(
        user_id=current_user.id, data=request
    )


@router.get("/customer-configs", response_model=list[CustomerConfigResponse])
async def list_customer_configs(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all customer configurations for current user."""
    service = AgentService(db)
    return await service.list_customer_configs(user_id=current_user.id)


@router.put("/customer-configs/{config_id}", response_model=CustomerConfigResponse)
async def update_customer_config(
    config_id: str,
    request: CustomerConfigCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a customer configuration."""
    service = AgentService(db)
    config = await service.update_customer_config(
        config_id=config_id, user_id=current_user.id, data=request
    )
    if config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer config not found",
        )
    return config


@router.get("/customer-configs/{config_id}", response_model=CustomerConfigResponse)
async def get_customer_config(
    config_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific customer configuration."""
    service = AgentService(db)
    config = await service.get_customer_config(
        config_id=config_id, user_id=current_user.id
    )
    if config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer config not found",
        )
    return config
