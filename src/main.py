from fastapi import FastAPI

from src.config.settings import settings
from src.presentation.api.redirect.router import router as redirect_router
from src.presentation.api.v1.router import router as v1_router


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app: FastAPI = FastAPI(
        debug=settings.app_debug,
        title=settings.app_title,
        version=settings.app_version,
        description=settings.app_description,
    )

    app.include_router(router=redirect_router)
    app.include_router(router=v1_router, prefix="/api/v1")

    return app


app: FastAPI = create_app()
