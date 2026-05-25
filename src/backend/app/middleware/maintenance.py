"""Block public/chat traffic when maintenance_mode is enabled."""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import settings

# Paths always allowed (health, docs, login).
_MAINTENANCE_ALLOW_PREFIXES = (
    "/api/health",
    "/docs",
    "/redoc",
    "/openapi.json",
)

# Admin can use these during maintenance (manage & recover).
_MAINTENANCE_ADMIN_PREFIXES = (
    "/api/auth/",
    "/api/settings",
    "/api/skills",
    "/api/knowledge",
    "/api/agents",
    "/api/dashboard",
    "/api/users",
    "/api/roles",
    "/api/conversations",
    "/api/chat",
    "/api/speech",
)

# Blocked for everyone during maintenance (tenant-facing).
_MAINTENANCE_BLOCK_PREFIXES = (
    "/api/widget",
    "/api/portal",
    "/api/pay",
    "/api/templates",
)


def _is_admin_request(request: Request) -> bool:
    auth = (request.headers.get("authorization") or "").strip()
    if not auth.lower().startswith("bearer "):
        return False
    token = auth[7:].strip()
    if not token:
        return False
    try:
        from app.core.security import verify_access_token

        payload = verify_access_token(token)
        role = str(payload.get("role") or "").strip().lower()
        return role == "admin"
    except Exception:
        return False


class MaintenanceModeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        if not getattr(settings, "maintenance_mode", False):
            return await call_next(request)

        path = request.url.path
        if any(path.startswith(p) for p in _MAINTENANCE_ALLOW_PREFIXES):
            return await call_next(request)
        if any(path.startswith(p) for p in _MAINTENANCE_BLOCK_PREFIXES):
            return self._maintenance_response()
        if _is_admin_request(request) and any(
            path.startswith(p) for p in _MAINTENANCE_ADMIN_PREFIXES
        ):
            return await call_next(request)
        return self._maintenance_response()

    @staticmethod
    def _maintenance_response() -> JSONResponse:
        return JSONResponse(
            status_code=503,
            content={
                "detail": "系统维护中，请稍后再试。",
                "maintenance": True,
            },
        )


def register_maintenance_middleware(app) -> None:
    app.add_middleware(MaintenanceModeMiddleware)
