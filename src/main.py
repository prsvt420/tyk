from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from logging import Logger, getLogger
from time import monotonic

from fastapi import FastAPI

from src.config.application_settings import application_settings
from src.config.logging import configure_logging
from src.domain.exceptions import DomainError
from src.presentation.http.api.v1.router import api_v1_router
from src.presentation.http.exception_handlers import handle_domain_error
from src.presentation.http.public import short_link_redirect_router

logger: Logger = getLogger(name=__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage application lifespan."""
    started_at: float = monotonic()

    logger.info(
        msg="Application started.",
        extra={
            "event": "application_started",
            "debug": app.debug,
            "title": app.title,
            "version": app.version,
        },
    )

    try:
        yield
    finally:
        logger.info(
            msg="Application stopped.",
            extra={
                "event": "application_stopped",
                "uptime_seconds": round(monotonic() - started_at, 3),
            },
        )


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    configure_logging(log_level=application_settings.log_level)

    app: FastAPI = FastAPI(
        debug=application_settings.app_debug,
        title=application_settings.app_title,
        version=application_settings.app_version,
        description=application_settings.app_description,
        lifespan=lifespan,
    )

    app.include_router(router=short_link_redirect_router)
    app.include_router(router=api_v1_router, prefix="/api/v1")

    app.add_exception_handler(
        exc_class_or_status_code=DomainError, handler=handle_domain_error
    )

    return app


app: FastAPI = create_app()
