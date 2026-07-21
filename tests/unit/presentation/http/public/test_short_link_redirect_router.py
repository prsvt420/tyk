from collections.abc import Generator
from contextlib import contextmanager

import pytest
from fastapi import FastAPI, status
from httpx import AsyncClient, Response

from src.application.dtos import ShortLinkDTO
from src.application.exceptions import (
    ShortLinkExpiredError,
    ShortLinkNotFoundError,
)
from src.application.mappers import ShortLinkMapper
from src.domain.exceptions import InvalidShortCodeError
from src.presentation.http.dependencies import (
    provide_get_short_link_by_short_code_use_case,
)
from tests.factories import ShortLinkFactory
from tests.unit.presentation.http.stubs import GetShortLinkUseCaseStub


@contextmanager
def _override_get_use_case(
    *,
    http_app: FastAPI,
    result: ShortLinkDTO | Exception,
) -> Generator[GetShortLinkUseCaseStub]:
    """Override and restore the short link retrieval dependency."""
    use_case_stub: GetShortLinkUseCaseStub = GetShortLinkUseCaseStub(
        result=result
    )

    def provide_use_case_stub() -> GetShortLinkUseCaseStub:
        """Provide the short link retrieval use case stub."""
        return use_case_stub

    http_app.dependency_overrides[
        provide_get_short_link_by_short_code_use_case
    ] = provide_use_case_stub

    try:
        yield use_case_stub
    finally:
        http_app.dependency_overrides.pop(
            provide_get_short_link_by_short_code_use_case
        )


@pytest.mark.anyio
async def test_redirect_endpoint_redirects_to_original_url(
    http_app: FastAPI,
    http_client: AsyncClient,
) -> None:
    """Redirect an active short link to its original URL."""
    short_link_dto: ShortLinkDTO = ShortLinkMapper.to_dto(
        short_link=ShortLinkFactory.create()
    )

    with _override_get_use_case(
        http_app=http_app,
        result=short_link_dto,
    ) as use_case_stub:
        response: Response = await http_client.get(
            url=f"/r/{short_link_dto.short_code}",
            follow_redirects=False,
        )

    assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
    assert response.headers["location"] == short_link_dto.original_url
    assert use_case_stub.requested_short_codes == [short_link_dto.short_code]


@pytest.mark.anyio
@pytest.mark.parametrize(
    argnames=("error", "status_code", "detail"),
    argvalues=[
        (
            InvalidShortCodeError("Invalid short code."),
            status.HTTP_404_NOT_FOUND,
            "Short link not found.",
        ),
        (
            ShortLinkNotFoundError(),
            status.HTTP_404_NOT_FOUND,
            "Short link not found.",
        ),
        (
            ShortLinkExpiredError(),
            status.HTTP_410_GONE,
            "Short link has expired.",
        ),
    ],
)
async def test_redirect_endpoint_translates_application_error(
    error: Exception,
    status_code: int,
    detail: str,
    http_app: FastAPI,
    http_client: AsyncClient,
) -> None:
    """Translate retrieval errors to public HTTP responses."""
    with _override_get_use_case(
        http_app=http_app,
        result=error,
    ) as use_case_stub:
        response: Response = await http_client.get(
            url="/r/abcd",
            follow_redirects=False,
        )

    assert response.status_code == status_code
    assert response.json() == {"detail": detail}
    assert use_case_stub.requested_short_codes == ["abcd"]
