from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.interfaces import (
    ShortCodeGeneratorInterface,
    ShortLinkRepositoryInterface,
)
from src.application.use_cases import (
    CreateShortLinkUseCase,
    GetShortLinkByShortCodeUseCase,
)
from src.infrastructure.database.async_session_factory import (
    async_session_factory,
)
from src.infrastructure.generators import RandomShortCodeGenerator
from src.infrastructure.repositories import PostgreSQLShortLinkRepository

_short_code_generator: ShortCodeGeneratorInterface = RandomShortCodeGenerator()


async def provide_async_session() -> AsyncIterator[AsyncSession]:
    """Provide async session."""
    async with async_session_factory() as async_session:
        yield async_session


def provide_short_link_repository(
    async_session: Annotated[
        AsyncSession,
        Depends(dependency=provide_async_session),
    ],
) -> ShortLinkRepositoryInterface:
    """Provide short link repository."""
    return PostgreSQLShortLinkRepository(async_session=async_session)


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
