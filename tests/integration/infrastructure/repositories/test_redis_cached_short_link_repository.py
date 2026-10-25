from time import monotonic
from unittest.mock import AsyncMock, patch

import pytest
from anyio import fail_after, sleep
from redis.asyncio import Redis as AsyncRedis
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities import ShortLink
from src.infrastructure.repositories import (
    PostgreSQLShortLinkRepository,
    RedisCachedShortLinkRepository,
)


@pytest.fixture
def postgresql_short_link_repository(
    postgresql_async_session: AsyncSession,
) -> PostgreSQLShortLinkRepository:
    """Provide the real repository wrapped by the Redis cache."""
    return PostgreSQLShortLinkRepository(
        database_async_session=postgresql_async_session
    )


@pytest.mark.integration
@pytest.mark.anyio
async def test_redis_cached_repository_saves_without_populating_cache(
    redis_async_client: AsyncRedis,
    redis_short_link: ShortLink,
    postgresql_short_link_repository: PostgreSQLShortLinkRepository,
) -> None:
    """Persist through the decorator and populate Redis only on lookup."""
    short_link_repository: RedisCachedShortLinkRepository = (
        RedisCachedShortLinkRepository(
            short_link_repository=postgresql_short_link_repository,
            cache_async_client=redis_async_client,
            cache_short_link_ttl_seconds=60,
        )
    )

    await short_link_repository.save(short_link=redis_short_link)

    assert (
        await postgresql_short_link_repository.get_by_short_code(
            short_code=redis_short_link.short_code
        )
        == redis_short_link
    )
    assert (
        await redis_async_client.get(
            name=f"short_link:{redis_short_link.short_code.value}"
        )
        is None
    )


@pytest.mark.integration
@pytest.mark.anyio
@pytest.mark.parametrize(
    argnames="cache_short_link_ttl_seconds", argvalues=[60, 86400]
)
async def test_redis_cached_repository_populates_cache_on_miss(
    redis_async_client: AsyncRedis,
    redis_short_link: ShortLink,
    postgresql_short_link_repository: PostgreSQLShortLinkRepository,
    cache_short_link_ttl_seconds: int,
) -> None:
    """Load a database record into Redis with the configured lifetime."""
    short_link_repository: RedisCachedShortLinkRepository = (
        RedisCachedShortLinkRepository(
            short_link_repository=postgresql_short_link_repository,
            cache_async_client=redis_async_client,
            cache_short_link_ttl_seconds=cache_short_link_ttl_seconds,
        )
    )
    cache_key: str = f"short_link:{redis_short_link.short_code.value}"
    await postgresql_short_link_repository.save(short_link=redis_short_link)
    assert await redis_async_client.get(name=cache_key) is None

    lookup_started_at: float = monotonic()
    stored_short_link: ShortLink | None = (
        await short_link_repository.get_by_short_code(
            short_code=redis_short_link.short_code
        )
    )

    assert stored_short_link == redis_short_link
    assert await redis_async_client.get(name=cache_key) is not None
    remaining_ttl_ms: int = await redis_async_client.pttl(name=cache_key)
    elapsed_ms: float = (monotonic() - lookup_started_at) * 1000
    assert 0 < remaining_ttl_ms <= cache_short_link_ttl_seconds * 1000
    assert (
        remaining_ttl_ms
        >= cache_short_link_ttl_seconds * 1000 - elapsed_ms - 100
    )


@pytest.mark.integration
@pytest.mark.anyio
async def test_redis_cached_repository_reads_cache_without_database_lookup(
    redis_async_client: AsyncRedis,
    redis_short_link: ShortLink,
    postgresql_short_link_repository: PostgreSQLShortLinkRepository,
) -> None:
    """Rebuild a cached entity without looking it up in PostgreSQL again."""
    short_link_repository: RedisCachedShortLinkRepository = (
        RedisCachedShortLinkRepository(
            short_link_repository=postgresql_short_link_repository,
            cache_async_client=redis_async_client,
            cache_short_link_ttl_seconds=60,
        )
    )
    await postgresql_short_link_repository.save(short_link=redis_short_link)
    assert (
        await short_link_repository.get_by_short_code(
            short_code=redis_short_link.short_code
        )
        == redis_short_link
    )
    database_lookup: AsyncMock = AsyncMock(
        wraps=postgresql_short_link_repository.get_by_short_code
    )

    with patch.object(
        target=postgresql_short_link_repository,
        attribute="get_by_short_code",
        new=database_lookup,
    ):
        stored_short_link: ShortLink | None = (
            await short_link_repository.get_by_short_code(
                short_code=redis_short_link.short_code
            )
        )

    assert stored_short_link == redis_short_link
    database_lookup.assert_not_awaited()


@pytest.mark.integration
@pytest.mark.anyio
async def test_redis_cached_repository_does_not_cache_missing_links(
    redis_async_client: AsyncRedis,
    redis_short_link: ShortLink,
    postgresql_short_link_repository: PostgreSQLShortLinkRepository,
) -> None:
    """Look up a missing link in PostgreSQL on every request."""
    short_link_repository: RedisCachedShortLinkRepository = (
        RedisCachedShortLinkRepository(
            short_link_repository=postgresql_short_link_repository,
            cache_async_client=redis_async_client,
            cache_short_link_ttl_seconds=60,
        )
    )
    database_lookup: AsyncMock = AsyncMock(
        wraps=postgresql_short_link_repository.get_by_short_code
    )

    with patch.object(
        target=postgresql_short_link_repository,
        attribute="get_by_short_code",
        new=database_lookup,
    ):
        for _ in range(2):
            assert (
                await short_link_repository.get_by_short_code(
                    short_code=redis_short_link.short_code
                )
                is None
            )

    assert database_lookup.await_count == 2
    assert (
        await redis_async_client.get(
            name=f"short_link:{redis_short_link.short_code.value}"
        )
        is None
    )


@pytest.mark.integration
@pytest.mark.anyio
async def test_redis_cached_repository_reloads_after_cache_expiration(
    redis_async_client: AsyncRedis,
    redis_short_link: ShortLink,
    postgresql_short_link_repository: PostgreSQLShortLinkRepository,
) -> None:
    """Reload and cache the database record after Redis expires its key."""
    short_link_repository: RedisCachedShortLinkRepository = (
        RedisCachedShortLinkRepository(
            short_link_repository=postgresql_short_link_repository,
            cache_async_client=redis_async_client,
            cache_short_link_ttl_seconds=2,
        )
    )
    cache_key: str = f"short_link:{redis_short_link.short_code.value}"
    await postgresql_short_link_repository.save(short_link=redis_short_link)
    assert (
        await short_link_repository.get_by_short_code(
            short_code=redis_short_link.short_code
        )
        == redis_short_link
    )
    assert await redis_async_client.exists(cache_key) == 1

    with fail_after(delay=5):
        while await redis_async_client.exists(cache_key):
            await sleep(delay=0.05)

    database_lookup: AsyncMock = AsyncMock(
        wraps=postgresql_short_link_repository.get_by_short_code
    )
    with patch.object(
        target=postgresql_short_link_repository,
        attribute="get_by_short_code",
        new=database_lookup,
    ):
        stored_short_link: ShortLink | None = (
            await short_link_repository.get_by_short_code(
                short_code=redis_short_link.short_code
            )
        )

    assert stored_short_link == redis_short_link
    database_lookup.assert_awaited_once_with(
        short_code=redis_short_link.short_code
    )
    assert await redis_async_client.get(name=cache_key) is not None
