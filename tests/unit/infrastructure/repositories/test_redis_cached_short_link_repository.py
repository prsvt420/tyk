import json
from datetime import datetime, timezone
from typing import cast
from unittest.mock import AsyncMock, MagicMock

import pytest
from redis.asyncio import Redis as AsyncRedis

from src.application.exceptions import ShortCodeAlreadyExistsError
from src.application.interfaces import ShortLinkRepositoryInterface
from src.domain.entities import ShortLink
from src.domain.value_objects import ShortCode
from src.infrastructure.repositories import RedisCachedShortLinkRepository
from tests.factories import ShortLinkFactory


def _create_cached_repository(
    *,
    short_link: ShortLink | None = None,
    short_link_cache: str | None = None,
) -> tuple[RedisCachedShortLinkRepository, MagicMock, MagicMock]:
    """Create a cached repository with isolated asynchronous dependencies."""
    short_link_repository_mock: MagicMock = MagicMock(
        spec=ShortLinkRepositoryInterface
    )
    short_link_repository_mock.save = AsyncMock()
    short_link_repository_mock.get_by_short_code = AsyncMock(
        return_value=short_link
    )
    cache_async_client_mock: MagicMock = MagicMock(spec=AsyncRedis)
    cache_async_client_mock.get = AsyncMock(return_value=short_link_cache)
    cache_async_client_mock.set = AsyncMock(return_value=True)
    short_link_repository: RedisCachedShortLinkRepository = (
        RedisCachedShortLinkRepository(
            short_link_repository=cast(
                ShortLinkRepositoryInterface, short_link_repository_mock
            ),
            cache_async_client=cast(AsyncRedis, cache_async_client_mock),
        )
    )

    return (
        short_link_repository,
        short_link_repository_mock,
        cache_async_client_mock,
    )


@pytest.mark.anyio
async def test_redis_cached_repository_delegates_save() -> None:
    """Delegate saving to the underlying repository without accessing Redis."""
    short_link: ShortLink = ShortLinkFactory.create()
    (
        short_link_repository,
        short_link_repository_mock,
        cache_async_client_mock,
    ) = _create_cached_repository()

    await short_link_repository.save(short_link=short_link)

    short_link_repository_mock.save.assert_awaited_once_with(
        short_link=short_link
    )
    short_link_repository_mock.get_by_short_code.assert_not_called()
    cache_async_client_mock.get.assert_not_called()
    cache_async_client_mock.set.assert_not_called()


@pytest.mark.anyio
async def test_redis_cached_repository_returns_cached_short_link() -> None:
    """Return a cached entity without querying or writing either store."""
    short_link: ShortLink = ShortLinkFactory.create(
        expires_at=datetime(year=2030, month=1, day=2, tzinfo=timezone.utc)
    )
    short_link_cache: str = json.dumps(
        obj={
            "id": "4f4c2514-26b0-4c75-a77b-130e7858024e",
            "original_url": "https://example.com/path",
            "short_code": "abcd",
            "created_at": "2030-01-01T00:00:00+00:00",
            "expires_at": "2030-01-02T00:00:00+00:00",
        }
    )
    (
        short_link_repository,
        short_link_repository_mock,
        cache_async_client_mock,
    ) = _create_cached_repository(short_link_cache=short_link_cache)

    stored_short_link: ShortLink | None = (
        await short_link_repository.get_by_short_code(
            short_code=short_link.short_code
        )
    )

    assert stored_short_link == short_link
    cache_async_client_mock.get.assert_awaited_once_with(
        name="short_link:abcd"
    )
    short_link_repository_mock.get_by_short_code.assert_not_called()
    short_link_repository_mock.save.assert_not_called()
    cache_async_client_mock.set.assert_not_called()


@pytest.mark.anyio
async def test_redis_cached_repository_populates_cache_after_miss() -> None:
    """Cache a link loaded from the underlying repository for one day."""
    short_link: ShortLink = ShortLinkFactory.create()
    (
        short_link_repository,
        short_link_repository_mock,
        cache_async_client_mock,
    ) = _create_cached_repository(short_link=short_link)

    stored_short_link: ShortLink | None = (
        await short_link_repository.get_by_short_code(
            short_code=short_link.short_code
        )
    )

    assert stored_short_link is short_link
    cache_async_client_mock.get.assert_awaited_once_with(
        name="short_link:abcd"
    )
    short_link_repository_mock.get_by_short_code.assert_awaited_once_with(
        short_code=short_link.short_code
    )
    cache_async_client_mock.set.assert_awaited_once()
    cache_arguments: dict[str, object] = (
        cache_async_client_mock.set.call_args.kwargs
    )
    assert set(cache_arguments) == {"name", "value", "ex"}
    assert cache_arguments["name"] == "short_link:abcd"
    assert cache_arguments["ex"] == 86400
    short_link_cache: object = cache_arguments["value"]
    assert isinstance(short_link_cache, str)
    assert json.loads(s=short_link_cache) == {
        "id": "4f4c2514-26b0-4c75-a77b-130e7858024e",
        "original_url": "https://example.com/path",
        "short_code": "abcd",
        "created_at": "2030-01-01T00:00:00+00:00",
        "expires_at": None,
    }
    short_link_repository_mock.save.assert_not_called()


@pytest.mark.anyio
async def test_redis_cached_repository_returns_none_for_missing_link() -> None:
    """Return None without caching when neither store contains the link."""
    short_code: ShortCode = ShortCode(value="abcd")
    (
        short_link_repository,
        short_link_repository_mock,
        cache_async_client_mock,
    ) = _create_cached_repository()

    stored_short_link: ShortLink | None = (
        await short_link_repository.get_by_short_code(short_code=short_code)
    )

    assert stored_short_link is None
    cache_async_client_mock.get.assert_awaited_once_with(
        name="short_link:abcd"
    )
    short_link_repository_mock.get_by_short_code.assert_awaited_once_with(
        short_code=short_code
    )
    cache_async_client_mock.set.assert_not_called()
    short_link_repository_mock.save.assert_not_called()


@pytest.mark.anyio
async def test_redis_cached_repository_preserves_short_code_conflict() -> None:
    """Preserve the underlying save conflict for application-level retries."""
    short_link: ShortLink = ShortLinkFactory.create()
    save_error: ShortCodeAlreadyExistsError = ShortCodeAlreadyExistsError()
    (
        short_link_repository,
        short_link_repository_mock,
        cache_async_client_mock,
    ) = _create_cached_repository()
    short_link_repository_mock.save.side_effect = save_error

    with pytest.raises(
        expected_exception=ShortCodeAlreadyExistsError,
    ) as exception_info:
        await short_link_repository.save(short_link=short_link)

    assert exception_info.value is save_error
    short_link_repository_mock.save.assert_awaited_once_with(
        short_link=short_link
    )
    cache_async_client_mock.get.assert_not_called()
    cache_async_client_mock.set.assert_not_called()


@pytest.mark.anyio
async def test_redis_cached_repository_preserves_read_error() -> None:
    """Propagate an underlying read failure without writing to the cache."""
    short_code: ShortCode = ShortCode(value="abcd")
    read_error: RuntimeError = RuntimeError("Underlying read failed.")
    (
        short_link_repository,
        short_link_repository_mock,
        cache_async_client_mock,
    ) = _create_cached_repository()
    short_link_repository_mock.get_by_short_code.side_effect = read_error

    with pytest.raises(
        expected_exception=RuntimeError,
    ) as exception_info:
        await short_link_repository.get_by_short_code(short_code=short_code)

    assert exception_info.value is read_error
    cache_async_client_mock.get.assert_awaited_once_with(
        name="short_link:abcd"
    )
    short_link_repository_mock.get_by_short_code.assert_awaited_once_with(
        short_code=short_code
    )
    cache_async_client_mock.set.assert_not_called()
