"""Public payment notify callbacks (no JWT)."""

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from cloud.services.portal_payment_service import PortalPaymentService

router = APIRouter()


@router.post("/alipay/notify")
async def alipay_notify(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Response:
    form = await request.form()
    data = {k: v for k, v in form.items()}
    svc = PortalPaymentService(db)
    result = await svc.handle_alipay_notify(data)
    return Response(content=result, media_type="text/plain")


@router.post("/wechat/notify")
async def wechat_notify(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Response:
    body = (await request.body()).decode("utf-8")
    svc = PortalPaymentService(db)
    xml = await svc.handle_wechat_notify(body)
    return Response(content=xml, media_type="application/xml")
