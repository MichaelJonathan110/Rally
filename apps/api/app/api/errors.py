"""Register domain-error -> HTTP exception handlers on the app."""
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.exceptions import DomainError


def register_exception_handlers(app: FastAPI) -> None:
    """Map :class:`DomainError` subclasses to their declared status codes."""

    @app.exception_handler(DomainError)
    async def _domain_error_handler(_request: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
