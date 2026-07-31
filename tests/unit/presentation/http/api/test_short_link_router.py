from datetime import datetime, timezone

import pytest
from fastapi import FastAPI, status
from httpx import AsyncClient, Response
from pydantic import HttpUrl

from src.application.dtos import CreateShortLinkDTO, ShortLinkDTO
from src.application.mappers import ShortLinkMapper
from src.config import app_settings
from src.presentation.http.dependencies import (
    provide_create_short_link_use_case,
)
from tests.factories import ShortLinkFactory
from tests.unit.presentation.http.stubs import CreateShortLinkUseCaseStub

EXPIRES_AT: datetime = datetime(
    year=2030,
    month=1,
    day=2,
    tzinfo=timezone.utc,
)


@pytest.mark.anyio
@pytest.mark.parametrize(
    argnames=("expires_at", "serialized_expires_at"),
    argvalues=[
        (None, None),
        (EXPIRES_AT, "2030-01-02T00:00:00Z"),
    ],
)
async def test_create_short_link_endpoint_returns_created_link(
    expires_at: datetime | None,
    serialized_expires_at: str | None,
    http_app: FastAPI,
    http_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Create a short link and return its public URL."""
    short_link_dto: ShortLinkDTO = ShortLinkMapper.to_dto(
        short_link=ShortLinkFactory.create(expires_at=expires_at)
    )
    use_case_stub: CreateShortLinkUseCaseStub = CreateShortLinkUseCaseStub(
        short_link_dto=short_link_dto
    )

    def provide_use_case_stub() -> CreateShortLinkUseCaseStub:
        """Provide the create short link use case stub."""
        return use_case_stub

    http_app.dependency_overrides[provide_create_short_link_use_case] = (
        provide_use_case_stub
    )
    monkeypatch.setattr(
        target=app_settings,
        name="public_base_url",
        value=HttpUrl("https://sho.rt/"),
    )

    response: Response = await http_client.post(
        url="/api/v1/short-links",
        json={
            "original_url": short_link_dto.original_url,
            "expires_at": serialized_expires_at,
        },
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.headers["location"] == "https://sho.rt/r/abcd"
    assert response.json() == {
        "id": str(short_link_dto.id),
        "original_url": short_link_dto.original_url,
        "short_code": short_link_dto.short_code,
        "short_link_url": "https://sho.rt/r/abcd",
        "created_at": "2030-01-01T00:00:00Z",
        "expires_at": serialized_expires_at,
    }
    assert use_case_stub.create_short_link_dtos == [
        CreateShortLinkDTO(
            original_url=short_link_dto.original_url,
            expires_at=expires_at,
        )
    ]


@pytest.mark.anyio
@pytest.mark.parametrize(
    argnames="request_body",
    argvalues=[
        {
            "original_url": "invalid-url",
            "expires_at": None,
        },
        {
            "original_url": "https://example.com/path",
            "expires_at": "2030-01-02T00:00:00",
        },
    ],
)
async def test_create_short_link_endpoint_rejects_invalid_request(
    request_body: dict[str, str | None],
    http_client: AsyncClient,
) -> None:
    """Reject a request with invalid schema fields."""
    response: Response = await http_client.post(
        url="/api/v1/short-links",
        json=request_body,
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
