"""Admin: portal orders and revenue (Cloud)."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.auth import Permission, require_permission
from app.models.portal_order import PortalOrder
from app.models.user import User
from cloud.schemas.portal import AdminOrderResponse, AdminRevenueStats

router = APIRouter()


@router.get("/admin/orders", response_model=list[AdminOrderResponse])
async def admin_list_orders(
    status: str | None = None,
    limit: int = 200,
    _admin: User = Depends(require_permission(Permission.USERS_WRITE)),
    db: AsyncSession = Depends(get_db),
) -> list[AdminOrderResponse]:
    """All portal checkout orders (admin)."""
    q = select(PortalOrder).order_by(PortalOrder.created_at.desc()).limit(min(limit, 500))
    if status:
        q = q.where(PortalOrder.status == status)
    result = await db.execute(q)
    orders = list(result.scalars().all())
    if not orders:
        return []

    user_ids = {o.user_id for o in orders}
    users_result = await db.execute(select(User).where(User.id.in_(user_ids)))
    users = {u.id: u for u in users_result.scalars().all()}

    out: list[AdminOrderResponse] = []
    for o in orders:
        u = users.get(o.user_id)
        data = AdminOrderResponse.model_validate(o)
        data.user_username = u.username if u else None
        data.user_phone = getattr(u, "phone", None) if u else None
        data.user_email = u.email if u else None
        out.append(data)
    return out


@router.get("/admin/orders/revenue", response_model=AdminRevenueStats)
async def admin_revenue_stats(
    _admin: User = Depends(require_permission(Permission.USERS_WRITE)),
    db: AsyncSession = Depends(get_db),
) -> AdminRevenueStats:
    """Paid order totals for admin dashboard."""
    paid_q = select(
        func.count(PortalOrder.id),
        func.coalesce(func.sum(PortalOrder.amount_cents), 0),
    ).where(PortalOrder.status == "paid")
    row = (await db.execute(paid_q)).one()
    paid_count = int(row[0] or 0)
    total_cents = int(row[1] or 0)

    month_start = datetime.now(timezone.utc).replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    )
    month_q = select(func.coalesce(func.sum(PortalOrder.amount_cents), 0)).where(
        PortalOrder.status == "paid",
        PortalOrder.paid_at >= month_start,
    )
    month_cents = int((await db.execute(month_q)).scalar_one() or 0)

    pending_q = select(func.count(PortalOrder.id)).where(
        PortalOrder.status == "pending"
    )
    pending_count = int((await db.execute(pending_q)).scalar_one() or 0)

    return AdminRevenueStats(
        paid_order_count=paid_count,
        total_revenue_cents=total_cents,
        month_revenue_cents=month_cents,
        pending_order_count=pending_count,
    )
