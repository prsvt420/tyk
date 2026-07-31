from collections.abc import AsyncGenerator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from src.domain.exceptions import DomainError
from src.presentation.http import domain_error_handler
from src.presentation.http.api.v1 import api_v1_router
from src.presentation.http.operational import probe_router
from src.presentation.http.public import short_link_redirect_router


@pytest.fixture
def http_app() -> FastAPI:
    """Create an HTTP app without middleware or lifespan."""
    app: FastAPI = FastAPI()
    app.include_router(router=probe_router)
    app.include_router(router=short_link_redirect_router)
    app.include_router(router=api_v1_router, prefix="/api/v1")
    app.add_exception_handler(
        exc_class_or_status_code=DomainError,
        handler=domain_error_handler,
    )

    return app


@pytest.fixture
async def http_client(
    http_app: FastAPI,
) -> AsyncGenerator[AsyncClient]:
    """Provide an asynchronous HTTP client."""
    transport: ASGITransport = ASGITransport(app=http_app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        yield client
