from logging import Logger, getLogger

from redis.asyncio import Redis as AsyncRedis
from redis.exceptions import RedisError

from src.application.interfaces import ShortLinkRepositoryInterface
from src.domain.entities import ShortLink
from src.domain.value_objects import ShortCode
from src.infrastructure.cache.cache_mappers import ShortLinkCacheMapper

logger: Logger = getLogger(name=__name__)


class RedisCachedShortLinkRepository(ShortLinkRepositoryInterface):
    """Redis cached short link repository."""

    def __init__(
        self,
        short_link_repository: ShortLinkRepositoryInterface,
        cache_async_client: AsyncRedis,
        cache_short_link_ttl_seconds: int,
    ) -> None:
        self._short_link_repository: ShortLinkRepositoryInterface = (
            short_link_repository
        )
        self._cache_async_client: AsyncRedis = cache_async_client
        self._cache_short_link_ttl_seconds: int = cache_short_link_ttl_seconds

    async def save(self, short_link: ShortLink) -> None:
        """Save short link."""
        await self._short_link_repository.save(short_link=short_link)

    async def get_by_short_code(
        self, short_code: ShortCode
    ) -> ShortLink | None:
        """Return short link by short code."""
        cache_key: str = f"short_link:{short_code.value}"

        try:
            short_link_cache: bytes | str | None = (
                await self._cache_async_client.get(name=cache_key)
            )
        except RedisError:
            logger.warning(
                msg="Short link cache read failed.",
                exc_info=True,
                extra={
                    "event": "short_link_cache_read_failed",
                    "short_code": short_code.value,
                },
            )
            return await self._short_link_repository.get_by_short_code(
                short_code=short_code
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
            try:
                await self._cache_async_client.set(
                    name=cache_key,
                    value=ShortLinkCacheMapper().to_cache(
                        short_link=short_link
                    ),
                    ex=self._cache_short_link_ttl_seconds,
                )
            except RedisError:
                logger.warning(
                    msg="Short link cache write failed.",
                    exc_info=True,
                    extra={
                        "event": "short_link_cache_write_failed",
                        "short_code": short_code.value,
                    },
                )

            return short_link

        return None
