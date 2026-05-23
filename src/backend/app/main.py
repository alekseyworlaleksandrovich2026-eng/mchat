"""FastAPI application entry point."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from loguru import logger

from app.core.config import settings
from app.core.database import close_db, init_db
from app.core.event_bus import event_bus
from app.knowledge.milvus_client import milvus_client
from app.utils.logger import setup_logger


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan: startup and shutdown events."""
    # Startup
    logger.info("Starting mchat backend server...")

    if settings.jwt_secret == "change-this-to-a-random-secret-key":
        logger.warning(
            "⚠️  JWT_SECRET 为默认值，请在生产环境中修改为随机字符串！"
        )

    # Initialize database
    await init_db()

    # Create default admin user
    from app.core.database import async_session_factory
    from app.services.auth_service import AuthService
    async with async_session_factory() as db:
        auth_service = AuthService(db)
        await auth_service.create_default_admin(
            username=settings.admin_username,
            password=settings.admin_password,
        )
        await db.commit()

    # Auto-reload skills from filesystem for the primary admin user
    from app.services.skill_service import SkillService
    from app.models.user import User
    from sqlalchemy import select
    async with async_session_factory() as db:
        user_result = await db.execute(
            select(User).where(User.username == settings.admin_username)
        )
        primary_user = user_result.scalar_one_or_none()
        if primary_user is not None:
            skill_service = SkillService(db)
            await skill_service.reload_skills(user_id=primary_user.id)
        await db.commit()

    # Load Milvus settings from DB, then connect
    from app.services.settings_service import SettingsService

    async with async_session_factory() as db:
        await SettingsService(db).get_settings()
        await db.commit()
    await milvus_client.connect()
    if milvus_client._connected:
        await milvus_client.create_collection()

    logger.info("mchat backend server started successfully")
    yield

    # Shutdown
    logger.info("Shutting down mchat backend server...")
    await close_db()
    await milvus_client.close()
    event_bus.clear()
    logger.info("mchat backend server stopped")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    import os

    # Ensure required directories exist
    use_local_storage = settings.storage_backend.strip().lower() == "local"
    if use_local_storage:
        os.makedirs(settings.upload_path, exist_ok=True)
    os.makedirs(settings.skills_path, exist_ok=True)
    os.makedirs("logs", exist_ok=True)

    # Setup logging
    setup_logger()

    app = FastAPI(
        title="mchat Backend",
        description="Multi-tenant AI chat platform backend API",
        version="1.0.0",
        lifespan=lifespan,
    )

    # CORS middleware
    cors_origins_raw = settings.cors_origins.strip()
    if cors_origins_raw == "*":
        allow_origins = ["*"]
        allow_credentials = False
    else:
        allow_origins = [o.strip() for o in cors_origins_raw.split(",") if o.strip()]
        allow_credentials = True

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Rate limiting (when enabled)
    if settings.rate_limit_enabled:
        from app.middleware.ratelimit import RateLimitMiddleware
        app.add_middleware(
            RateLimitMiddleware,
            rate=settings.rate_limit_requests,
            per_seconds=settings.rate_limit_period,
        )

    # Static files mount
    upload_path = settings.upload_path
    if use_local_storage and upload_path.exists():
        app.mount(
            "/uploads",
            StaticFiles(directory=str(upload_path)),
            name="uploads",
        )

    # Include API routers
    from app.api import api_router
    app.include_router(api_router)

    # Include WebSocket router
    from app.websocket.route import router as ws_router
    app.include_router(ws_router)

    # Initialize bot engine (subscribes to message_created events)
    from app.bot.handler import init_bot_engine
    init_bot_engine()

    # Root endpoint
    @app.get("/")
    async def root():
        return {
            "name": "mchat Backend",
            "version": "1.0.0",
            "docs": "/docs",
        }

    @app.get("/go/{short_code}")
    async def redirect_by_short_code(short_code: str, request: Request):
        """Redirect short code to widget page, e.g. /go/gdz → /widget.html?agentId=xxx"""
        from urllib.parse import urlencode
        from fastapi.responses import RedirectResponse, PlainTextResponse
        from sqlalchemy import select
        from app.core.database import async_session_factory
        from app.models.customer import CustomerConfig
        from app.services.widget_chat_service import ensure_widget_domain_allowed

        sw_code = short_code.strip().lower()
        async with async_session_factory() as db:
            result = await db.execute(
                select(CustomerConfig).where(
                    CustomerConfig.short_code == sw_code,
                    CustomerConfig.enabled == True,
                )
            )
            config = result.scalar_one_or_none()
            if config is None:
                return PlainTextResponse("Not Found", status_code=404)

            ensure_widget_domain_allowed(config, request)
            params = {"agentId": config.id}
            widget_url = f"/widget.html?{urlencode(params)}"
            return RedirectResponse(url=widget_url, status_code=302)

    return app


app = create_app()


def main() -> None:
    """Run the application with uvicorn."""
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.server_host,
        port=settings.server_port,
        reload=True,
        log_level="info",
    )


if __name__ == "__main__":
    main()
