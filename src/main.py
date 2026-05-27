from fastapi import FastAPI

from src.config.settings import settings


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app: FastAPI = FastAPI(
        debug=settings.app_debug,
        title=settings.app_title,
        version=settings.app_version,
        description=settings.app_description,
    )
    return app


app: FastAPI = create_app()
