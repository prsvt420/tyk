import json
from datetime import datetime, timezone
from logging import WARNING, LogRecord
from typing import cast
from unittest.mock import AsyncMock, MagicMock

import pytest
from redis.asyncio import Redis as AsyncRedis
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import RedisError
from redis.exceptions import TimeoutError as RedisTimeoutError

from src.application.exceptions import ShortCodeAlreadyExistsError
from src.application.interfaces import ShortLinkRepositoryInterface
from src.domain.entities import ShortLink
from src.domain.value_objects import ShortCode
from src.infrastructure.repositories import RedisCachedShortLinkRepository
from tests.factories import ShortLinkFactory

LOGGER_NAME: str = (
    "src.infrastructure.repositories.redis_cached_short_link_repository"
)


def _assert_cache_warning(
    *,
    caplog: pytest.LogCaptureFixture,
    message: str,
    event: str,
    short_code: ShortCode,
    error: RedisError,
) -> None:
    """Check a structured warning with the original cache failure."""
    records: list[LogRecord] = [
        record for record in caplog.records if record.name == LOGGER_NAME
    ]

    assert len(records) == 1
    record: LogRecord = records[0]
    assert record.name == LOGGER_NAME
    assert record.levelno == WARNING
    assert record.getMessage() == message
    assert record.__dict__["event"] == event
    assert record.__dict__["short_code"] == short_code.value
    assert record.exc_info is not None
    assert record.exc_info[1] is error


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
@pytest.mark.parametrize(argnames="link_exists", argvalues=[True, False])
@pytest.mark.parametrize(
    argnames="cache_error_type",
    argvalues=[RedisConnectionError, RedisTimeoutError],
)
async def test_redis_cached_repository_falls_back_after_read_error(
    link_exists: bool,
    cache_error_type: type[RedisError],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Log a cache read failure and use the repository without cache writes."""
    short_code: ShortCode = ShortCode(value="aB12")
    short_link: ShortLink | None = (
        ShortLinkFactory.create(short_code=short_code.value)
        if link_exists
        else None
    )
    (
        short_link_repository,
        short_link_repository_mock,
        cache_async_client_mock,
    ) = _create_cached_repository(short_link=short_link)
    cache_error: RedisError = cache_error_type("Cache read failed.")
    cache_async_client_mock.get.side_effect = cache_error

    with caplog.at_level(level=WARNING, logger=LOGGER_NAME):
        stored_short_link: ShortLink | None = (
            await short_link_repository.get_by_short_code(
                short_code=short_code
            )
        )

    assert stored_short_link is short_link
    cache_async_client_mock.get.assert_awaited_once_with(
        name="short_link:aB12"
    )
    short_link_repository_mock.get_by_short_code.assert_awaited_once_with(
        short_code=short_code
    )
    cache_async_client_mock.set.assert_not_called()
    short_link_repository_mock.save.assert_not_called()
    _assert_cache_warning(
        caplog=caplog,
        message="Short link cache read failed.",
        event="short_link_cache_read_failed",
        short_code=short_code,
        error=cache_error,
    )


@pytest.mark.anyio
@pytest.mark.parametrize(
    argnames="cache_error_type",
    argvalues=[RedisConnectionError, RedisTimeoutError],
)
async def test_redis_cached_repository_logs_write_error(
    cache_error_type: type[RedisError],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Log a failed cache write and return the link from the repository."""
    short_link: ShortLink = ShortLinkFactory.create(short_code="aB12")
    (
        short_link_repository,
        short_link_repository_mock,
        cache_async_client_mock,
    ) = _create_cached_repository(short_link=short_link)
    cache_error: RedisError = cache_error_type("Cache write failed.")
    cache_async_client_mock.set.side_effect = cache_error

    with caplog.at_level(level=WARNING, logger=LOGGER_NAME):
        stored_short_link: ShortLink | None = (
            await short_link_repository.get_by_short_code(
                short_code=short_link.short_code
            )
        )

    assert stored_short_link is short_link
    cache_async_client_mock.get.assert_awaited_once_with(
        name="short_link:aB12"
    )
    short_link_repository_mock.get_by_short_code.assert_awaited_once_with(
        short_code=short_link.short_code
    )
    cache_async_client_mock.set.assert_awaited_once()
    short_link_repository_mock.save.assert_not_called()
    _assert_cache_warning(
        caplog=caplog,
        message="Short link cache write failed.",
        event="short_link_cache_write_failed",
        short_code=short_link.short_code,
        error=cache_error,
    )


@pytest.mark.anyio
async def test_redis_cached_repository_preserves_fallback_error(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Preserve a repository failure after a logged cache read failure."""
    short_code: ShortCode = ShortCode(value="aB12")
    (
        short_link_repository,
        short_link_repository_mock,
        cache_async_client_mock,
    ) = _create_cached_repository()
    cache_error: RedisError = RedisConnectionError("Cache read failed.")
    cache_async_client_mock.get.side_effect = cache_error
    read_error: RuntimeError = RuntimeError("Underlying read failed.")
    short_link_repository_mock.get_by_short_code.side_effect = read_error

    with caplog.at_level(level=WARNING, logger=LOGGER_NAME):
        with pytest.raises(
            expected_exception=RuntimeError,
        ) as exception_info:
            await short_link_repository.get_by_short_code(
                short_code=short_code
            )

    assert exception_info.value is read_error
    cache_async_client_mock.get.assert_awaited_once_with(
        name="short_link:aB12"
    )
    short_link_repository_mock.get_by_short_code.assert_awaited_once_with(
        short_code=short_code
    )
    cache_async_client_mock.set.assert_not_called()
    _assert_cache_warning(
        caplog=caplog,
        message="Short link cache read failed.",
        event="short_link_cache_read_failed",
        short_code=short_code,
        error=cache_error,
    )


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
