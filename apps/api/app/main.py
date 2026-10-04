"""FastAPI application factory for RALLY."""

from __future__ import annotations

import asyncio
import logging
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.errors import register_exception_handlers
from app.api.v1 import api_router
from app.api.v1.health import health as _health
from app.core.config import settings
from app.middleware.security_headers import SecurityHeadersMiddleware

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("rally")


def _refresh_events_once() -> None:
    """Run the demo-event refresh in its own session; never raise."""
    from app.db.session import SessionLocal
    from app.services.event_refresh import refresh_events

    db = SessionLocal()
    try:
        refresh_events(db)
    except Exception:  # noqa: BLE001 - a refresh failure must never break boot
        logger.exception("event refresh failed (ignored)")
    finally:
        db.close()


async def _event_refresh_loop() -> None:
    """Re-run the refresh every ``REFRESH_INTERVAL_HOURS`` while the server is up."""
    from app.services.event_refresh import REFRESH_INTERVAL_HOURS

    interval = REFRESH_INTERVAL_HOURS * 3600
    while True:
        try:
            await asyncio.sleep(interval)
            await asyncio.to_thread(_refresh_events_once)
        except asyncio.CancelledError:
            raise
        except Exception:  # noqa: BLE001 - keep the loop alive on any error
            logger.exception("scheduled event refresh failed (ignored)")


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    # Ensure the media root exists so StaticFiles can mount and serve uploads.
    Path(settings.MEDIA_ROOT).mkdir(parents=True, exist_ok=True)
    logger.info("%s API starting (env=%s)", settings.BRAND_NAME, settings.ENVIRONMENT)

    # Self-refreshing demo events: only for the local SQLite dev/e2e database,
    # so tests and production never touch demo rows. The initial pass runs after
    # DB init (serve_sqlite.py) and is wrapped so it can never crash startup.
    task: asyncio.Task[None] | None = None
    if (
        settings.EVENT_REFRESH_ENABLED
        and settings.DATABASE_URL.startswith("sqlite")
        and "pytest" not in sys.modules
    ):
        await asyncio.to_thread(_refresh_events_once)
        task = asyncio.create_task(_event_refresh_loop())

    try:
        yield
    finally:
        if task is not None:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task
        logger.info("%s API shutting down", settings.BRAND_NAME)


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.VERSION,
        description=f"{settings.BRAND_NAME} - {settings.BRAND_TAGLINE}",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # NOTE: CORSMiddleware is registered before any router so preflight OPTIONS
    # requests are answered by the middleware, never a 405 from a route.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    # Outermost: baseline security headers on every response (incl. errors).
    app.add_middleware(SecurityHeadersMiddleware)

    register_exception_handlers(app)
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    # Read-only static mount for user uploads. It lives OUTSIDE the /api/v1
    # prefix, so it can never shadow API routes.
    media_root = Path(settings.MEDIA_ROOT)
    media_root.mkdir(parents=True, exist_ok=True)
    app.mount(
        settings.MEDIA_URL_PREFIX,
        StaticFiles(directory=str(media_root)),
        name="media",
    )

    @app.get("/health", tags=["system"])
    def root_health() -> dict[str, str]:
        """Top-level liveness alias (also available under the v1 prefix)."""
        return _health().model_dump()

    return app


app = create_app()
