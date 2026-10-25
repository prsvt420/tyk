from redis.asyncio import Redis as AsyncRedis

from src.application.interfaces import ShortLinkRepositoryInterface
from src.domain.entities import ShortLink
from src.domain.value_objects import ShortCode
from src.infrastructure.cache.cache_mappers import ShortLinkCacheMapper


class RedisCachedShortLinkRepository(ShortLinkRepositoryInterface):
    """Redis cached short link repository."""

    def __init__(
        self,
        short_link_repository: ShortLinkRepositoryInterface,
        cache_async_client: AsyncRedis,
    ) -> None:
        self._short_link_repository: ShortLinkRepositoryInterface = (
            short_link_repository
        )
        self._cache_async_client: AsyncRedis = cache_async_client

    async def save(self, short_link: ShortLink) -> None:
        """Save short link."""
        await self._short_link_repository.save(short_link=short_link)

    async def get_by_short_code(
        self, short_code: ShortCode
    ) -> ShortLink | None:
        """Return short link by short code."""
        cache_key: str = f"short_link:{short_code.value}"
        short_link_cache: bytes | str | None = (
            await self._cache_async_client.get(name=cache_key)
        )

        if isinstance(short_link_cache, str):
            return ShortLinkCacheMapper().to_entity(
                short_link_cache=short_link_cache
            )

        short_link: ShortLink | None = (
            await self._short_link_repository.get_by_short_code(
                short_code=short_code
            )
        )

        if short_link:
            await self._cache_async_client.set(
                name=cache_key,
                value=ShortLinkCacheMapper().to_cache(short_link=short_link),
                ex=86400,
            )

            return short_link

        return None
