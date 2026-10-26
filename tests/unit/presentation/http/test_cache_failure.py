from collections.abc import Generator
from datetime import datetime, timezone
from typing import cast
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI, status
from httpx import AsyncClient, Response
from redis.asyncio import Redis as AsyncRedis
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import RedisError
from redis.exceptions import TimeoutError as RedisTimeoutError

from src.application.interfaces import ShortLinkRepositoryInterface
from src.domain.entities import ShortLink
from src.domain.value_objects import ShortCode
from src.infrastructure.cache.cache_mappers import ShortLinkCacheMapper
from src.infrastructure.repositories import (
    InMemoryShortLinkRepository,
    RedisCachedShortLinkRepository,
)
from src.presentation.http import dependencies
from src.presentation.http.dependencies import provide_short_link_repository
from tests.factories import ShortLinkFactory


@pytest.fixture(params=[RedisConnectionError, RedisTimeoutError])
def unavailable_cache_async_client(
    request: pytest.FixtureRequest,
) -> MagicMock:
    """Provide a cache client that fails on network operations."""
    cache_error_type: type[RedisError] = request.param
    cache_async_client_mock: MagicMock = MagicMock(spec=AsyncRedis)
    cache_async_client_mock.get = AsyncMock(
        side_effect=cache_error_type("Cache read failed.")
    )
    cache_async_client_mock.set = AsyncMock(
        side_effect=cache_error_type("Cache write failed.")
    )
    cache_async_client_mock.ping = AsyncMock(
        side_effect=cache_error_type("Cache ping failed.")
    )
    return cache_async_client_mock


@pytest.fixture
def fallback_short_link_repository(
    http_app: FastAPI,
    unavailable_cache_async_client: MagicMock,
) -> Generator[InMemoryShortLinkRepository]:
    """Use the real cache decorator with an isolated underlying repository."""
    short_link_repository: InMemoryShortLinkRepository = (
        InMemoryShortLinkRepository()
    )
    cached_short_link_repository: RedisCachedShortLinkRepository = (
        RedisCachedShortLinkRepository(
            short_link_repository=short_link_repository,
            cache_async_client=cast(
                AsyncRedis, unavailable_cache_async_client
            ),
            cache_short_link_ttl_seconds=60,
        )
    )

    def provide_cached_repository() -> ShortLinkRepositoryInterface:
        """Provide the same cached repository for every HTTP request."""
        return cached_short_link_repository

    http_app.dependency_overrides[provide_short_link_repository] = (
        provide_cached_repository
    )
    try:
        yield short_link_repository
    finally:
        http_app.dependency_overrides.pop(provide_short_link_repository)


@pytest.mark.anyio
async def test_create_short_link_succeeds_when_cache_is_unavailable(
    http_client: AsyncClient,
    fallback_short_link_repository: InMemoryShortLinkRepository,
    unavailable_cache_async_client: MagicMock,
) -> None:
    """Create and persist a link without accessing the unavailable cache."""
    response: Response = await http_client.post(
        url="/api/v1/short-links",
        json={"original_url": "https://example.com/path"},
    )

    assert response.status_code == status.HTTP_201_CREATED
    stored_short_link: ShortLink | None = (
        await fallback_short_link_repository.get_by_short_code(
            short_code=ShortCode(value=response.json()["short_code"])
        )
    )
    assert stored_short_link is not None
    assert stored_short_link.original_url.value == "https://example.com/path"
    unavailable_cache_async_client.get.assert_not_called()
    unavailable_cache_async_client.set.assert_not_called()


@pytest.mark.anyio
async def test_redirect_succeeds_when_cache_is_unavailable(
    http_client: AsyncClient,
    fallback_short_link_repository: InMemoryShortLinkRepository,
    unavailable_cache_async_client: MagicMock,
) -> None:
    """Redirect using the underlying repository after a cache failure."""
    short_link: ShortLink = ShortLinkFactory.create()
    await fallback_short_link_repository.save(short_link=short_link)

    response: Response = await http_client.get(
        url=f"/r/{short_link.short_code.value}",
        follow_redirects=False,
    )

    assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
    assert response.headers["location"] == short_link.original_url.value
    unavailable_cache_async_client.get.assert_awaited_once_with(
        name=f"short_link:{short_link.short_code.value}"
    )
    unavailable_cache_async_client.set.assert_not_called()


@pytest.mark.anyio
async def test_missing_short_link_returns_not_found_during_cache_outage(
    http_client: AsyncClient,
    fallback_short_link_repository: InMemoryShortLinkRepository,
    unavailable_cache_async_client: MagicMock,
) -> None:
    """Preserve the not-found response while the cache is unavailable."""
    response: Response = await http_client.get(url="/r/abcd")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Short link not found."}
    unavailable_cache_async_client.get.assert_awaited_once_with(
        name="short_link:abcd"
    )
    unavailable_cache_async_client.set.assert_not_called()


@pytest.mark.anyio
async def test_expired_short_link_returns_gone_during_cache_outage(
    http_client: AsyncClient,
    fallback_short_link_repository: InMemoryShortLinkRepository,
    unavailable_cache_async_client: MagicMock,
) -> None:
    """Enforce link expiration on the fallback lookup path."""
    short_link: ShortLink = ShortLinkFactory.create(
        created_at=datetime(year=2000, month=1, day=1, tzinfo=timezone.utc),
        expires_at=datetime(year=2000, month=1, day=2, tzinfo=timezone.utc),
    )
    await fallback_short_link_repository.save(short_link=short_link)

    response: Response = await http_client.get(
        url=f"/r/{short_link.short_code.value}",
        follow_redirects=False,
    )

    assert response.status_code == status.HTTP_410_GONE
    assert response.json() == {"detail": "Short link has expired."}
    unavailable_cache_async_client.get.assert_awaited_once_with(
        name=f"short_link:{short_link.short_code.value}"
    )
    unavailable_cache_async_client.set.assert_not_called()


@pytest.mark.anyio
async def test_readyz_succeeds_during_cache_outage(
    http_client: AsyncClient,
    unavailable_cache_async_client: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Keep readiness successful when the required database is available."""
    database_readiness_check: AsyncMock = AsyncMock(return_value=True)
    monkeypatch.setattr(
        target=dependencies,
        name="check_database_readiness",
        value=database_readiness_check,
    )
    monkeypatch.setattr(
        target=dependencies,
        name="_cache_async_client",
        value=unavailable_cache_async_client,
    )

    response: Response = await http_client.get(url="/readyz")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "ready"}
    database_readiness_check.assert_awaited_once_with()
    unavailable_cache_async_client.ping.assert_not_called()
    unavailable_cache_async_client.get.assert_not_called()
    unavailable_cache_async_client.set.assert_not_called()


@pytest.mark.anyio
async def test_redirect_resumes_caching_after_cache_recovery(
    http_client: AsyncClient,
    fallback_short_link_repository: InMemoryShortLinkRepository,
    unavailable_cache_async_client: MagicMock,
) -> None:
    """Resume cache writes on the same repository after a transient failure."""
    short_link: ShortLink = ShortLinkFactory.create()
    await fallback_short_link_repository.save(short_link=short_link)
    redirect_url: str = f"/r/{short_link.short_code.value}"

    outage_response: Response = await http_client.get(
        url=redirect_url,
        follow_redirects=False,
    )
    assert outage_response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
    unavailable_cache_async_client.set.assert_not_called()

    unavailable_cache_async_client.get.side_effect = None
    unavailable_cache_async_client.get.return_value = None
    unavailable_cache_async_client.set.side_effect = None
    unavailable_cache_async_client.set.return_value = True

    recovered_response: Response = await http_client.get(
        url=redirect_url,
        follow_redirects=False,
    )

    assert recovered_response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
    assert (
        recovered_response.headers["location"] == short_link.original_url.value
    )
    assert unavailable_cache_async_client.get.await_count == 2
    unavailable_cache_async_client.set.assert_awaited_once_with(
        name=f"short_link:{short_link.short_code.value}",
        value=ShortLinkCacheMapper.to_cache(short_link=short_link),
        ex=60,
    )
