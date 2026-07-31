import pytest
from fastapi import FastAPI, status
from httpx import AsyncClient, Response

from src.presentation.http.dependencies import provide_app_readiness


@pytest.mark.anyio
async def test_livez_endpoint_returns_alive_status(
    http_client: AsyncClient,
) -> None:
    """Report that the app process is alive."""
    response: Response = await http_client.get(url="/livez")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "alive"}


@pytest.mark.anyio
@pytest.mark.parametrize(
    argnames=("app_ready", "status_code", "response_body"),
    argvalues=[
        (
            True,
            status.HTTP_200_OK,
            {"status": "ready"},
        ),
        (
            False,
            status.HTTP_503_SERVICE_UNAVAILABLE,
            {"status": "not_ready"},
        ),
    ],
)
async def test_readyz_endpoint_reports_app_readiness(
    app_ready: bool,
    status_code: int,
    response_body: dict[str, str],
    http_app: FastAPI,
    http_client: AsyncClient,
) -> None:
    """Report whether the app can serve traffic."""

    async def provide_readiness_stub() -> bool:
        """Provide the predefined app readiness."""
        return app_ready

    http_app.dependency_overrides[provide_app_readiness] = (
        provide_readiness_stub
    )

    response: Response = await http_client.get(url="/readyz")

    assert response.status_code == status_code
    assert response.json() == response_body
