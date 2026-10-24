from redis.asyncio import Redis as AsyncRedis

from src.config import app_settings

cache_async_client: AsyncRedis = AsyncRedis.from_url(
    url=app_settings.cache_url,
    decode_responses=True,
)
