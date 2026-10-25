from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends
from redis.asyncio import Redis as AsyncRedis
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.interfaces import (
    ShortCodeGeneratorInterface,
    ShortLinkRepositoryInterface,
)
from src.application.use_cases import (
    CreateShortLinkUseCase,
    GetShortLinkByShortCodeUseCase,
)
from src.config import app_settings
from src.infrastructure.cache import cache_async_client as _cache_async_client
from src.infrastructure.database import (
    check_database_readiness,
    database_async_session_factory,
)
from src.infrastructure.generators import RandomShortCodeGenerator
from src.infrastructure.repositories import (
    PostgreSQLShortLinkRepository,
    RedisCachedShortLinkRepository,
)

_short_code_generator: ShortCodeGeneratorInterface = RandomShortCodeGenerator()


async def provide_database_async_session() -> AsyncIterator[AsyncSession]:
    """Provide database async session."""
    async with database_async_session_factory() as database_async_session:
        yield database_async_session


async def provide_cache_async_client() -> AsyncRedis:
    """Provide cache async client."""
    return _cache_async_client


async def provide_app_readiness() -> bool:
    """Provide app readiness."""
    return await check_database_readiness()


def provide_short_link_repository(
    database_async_session: Annotated[
        AsyncSession,
        Depends(dependency=provide_database_async_session),
    ],
    cache_async_client: Annotated[
        AsyncRedis,
        Depends(dependency=provide_cache_async_client),
    ],
) -> ShortLinkRepositoryInterface:
    """Provide short link repository."""
    return RedisCachedShortLinkRepository(
        short_link_repository=PostgreSQLShortLinkRepository(
            database_async_session=database_async_session,
        ),
        cache_async_client=cache_async_client,
        cache_short_link_ttl_seconds=app_settings.cache_short_link_ttl_seconds,
    )


def provide_short_code_generator() -> ShortCodeGeneratorInterface:
    """Provide short code generator."""
    return _short_code_generator


def provide_create_short_link_use_case(
    short_link_repository: Annotated[
        ShortLinkRepositoryInterface,
        Depends(dependency=provide_short_link_repository),
    ],
    short_code_generator: Annotated[
        ShortCodeGeneratorInterface,
        Depends(dependency=provide_short_code_generator),
    ],
) -> CreateShortLinkUseCase:
    """Provide create short link use case."""
    return CreateShortLinkUseCase(
        short_link_repository=short_link_repository,
        short_code_generator=short_code_generator,
    )


def provide_get_short_link_by_short_code_use_case(
    short_link_repository: Annotated[
        ShortLinkRepositoryInterface,
        Depends(dependency=provide_short_link_repository),
    ],
) -> GetShortLinkByShortCodeUseCase:
    """Provide get short link by short code use case."""
    return GetShortLinkByShortCodeUseCase(
        short_link_repository=short_link_repository,
    )
