"""Portal checkout API (authenticated)."""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from cloud.schemas.payment import (
    CheckoutResponse,
    CreateCheckoutRequest,
    OrderStatusResponse,
)
from cloud.services.portal_payment_service import (
    PortalPaymentService,
    client_ip_from_request,
)

router = APIRouter()


@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout(
    body: CreateCheckoutRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CheckoutResponse:
    """Create order and return payment QR content (Alipay / WeChat)."""
    svc = PortalPaymentService(db)
    data = await svc.create_checkout(
        current_user,
        template_id=body.template_id,
        billing_period=body.billing_period,
        channel_name=body.channel_name,
        channel_id=body.channel_id,
        payment_method=body.payment_method,
        client_ip=client_ip_from_request(request),
    )
    await db.commit()
    return CheckoutResponse(**data)


@router.get("/orders/{order_id}/status", response_model=OrderStatusResponse)
async def check_order_status(
    order_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> OrderStatusResponse:
    """Poll payment status; provisions channel when paid."""
    svc = PortalPaymentService(db)
    data = await svc.check_and_fulfill(current_user, order_id)
    await db.commit()
    return OrderStatusResponse(**data)
