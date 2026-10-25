from collections.abc import AsyncGenerator
from importlib import import_module
from types import ModuleType
from typing import cast
from unittest.mock import AsyncMock, MagicMock

import pytest
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
from src.infrastructure.generators import RandomShortCodeGenerator
from src.infrastructure.repositories import (
    PostgreSQLShortLinkRepository,
    RedisCachedShortLinkRepository,
)
from src.presentation.http.dependencies import (
    provide_app_readiness,
    provide_cache_async_client,
    provide_create_short_link_use_case,
    provide_database_async_session,
    provide_get_short_link_by_short_code_use_case,
    provide_short_code_generator,
    provide_short_link_repository,
)
from tests.unit.application.stubs import (
    ShortCodeGeneratorStub,
    ShortLinkRepositoryStub,
)

DEPENDENCIES_MODULE: ModuleType = import_module(
    name="src.presentation.http.dependencies"
)


@pytest.mark.anyio
async def test_provide_database_async_session_manages_lifecycle(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Yield and close a session from the configured factory."""
    database_async_session: AsyncSession = cast(
        AsyncSession,
        MagicMock(spec=AsyncSession),
    )
    database_session_context_mock: MagicMock = MagicMock()
    database_session_context_mock.__aenter__ = AsyncMock(
        return_value=database_async_session
    )
    database_session_context_mock.__aexit__ = AsyncMock(return_value=None)
    database_async_session_factory_mock: MagicMock = MagicMock(
        return_value=database_session_context_mock
    )
    monkeypatch.setattr(
        target=DEPENDENCIES_MODULE,
        name="database_async_session_factory",
        value=database_async_session_factory_mock,
    )
    database_session_provider: AsyncGenerator[AsyncSession, None] = cast(
        AsyncGenerator[AsyncSession, None],
        provide_database_async_session(),
    )

    provided_database_async_session: AsyncSession = await anext(
        database_session_provider
    )
    await database_session_provider.aclose()

    assert provided_database_async_session is database_async_session
    database_async_session_factory_mock.assert_called_once_with()
    database_session_context_mock.__aenter__.assert_awaited_once_with()
    database_session_context_mock.__aexit__.assert_awaited_once()


@pytest.mark.anyio
async def test_provide_cache_async_client_returns_shared_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Return the configured cache client across provider calls."""
    cache_async_client: AsyncRedis = cast(
        AsyncRedis,
        MagicMock(spec=AsyncRedis),
    )
    monkeypatch.setattr(
        target=DEPENDENCIES_MODULE,
        name="_cache_async_client",
        value=cache_async_client,
    )

    first_cache_async_client: AsyncRedis = await provide_cache_async_client()
    second_cache_async_client: AsyncRedis = await provide_cache_async_client()

    assert first_cache_async_client is cache_async_client
    assert second_cache_async_client is cache_async_client


@pytest.mark.anyio
@pytest.mark.parametrize(
    argnames="app_ready",
    argvalues=[True, False],
)
async def test_provide_app_readiness_returns_database_status(
    app_ready: bool,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Return the database readiness result."""
    check_database_readiness_mock: AsyncMock = AsyncMock(
        return_value=app_ready
    )
    monkeypatch.setattr(
        target=DEPENDENCIES_MODULE,
        name="check_database_readiness",
        value=check_database_readiness_mock,
    )

    provided_app_ready: bool = await provide_app_readiness()

    assert provided_app_ready is app_ready
    check_database_readiness_mock.assert_awaited_once_with()


def test_provide_short_link_repository_wraps_postgresql(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Wrap PostgreSQL with the session, cache client and configured TTL."""
    database_async_session: AsyncSession = cast(
        AsyncSession,
        MagicMock(spec=AsyncSession),
    )
    cache_async_client: AsyncRedis = cast(
        AsyncRedis,
        MagicMock(spec=AsyncRedis),
    )
    monkeypatch.setattr(
        target=DEPENDENCIES_MODULE.app_settings,
        name="cache_short_link_ttl_seconds",
        value=120,
    )

    short_link_repository: ShortLinkRepositoryInterface = (
        provide_short_link_repository(
            database_async_session=database_async_session,
            cache_async_client=cache_async_client,
        )
    )

    assert isinstance(
        short_link_repository,
        RedisCachedShortLinkRepository,
    )
    assert short_link_repository._cache_async_client is cache_async_client
    assert short_link_repository._cache_short_link_ttl_seconds == 120
    database_short_link_repository: ShortLinkRepositoryInterface = (
        short_link_repository._short_link_repository
    )
    assert isinstance(
        database_short_link_repository,
        PostgreSQLShortLinkRepository,
    )
    assert (
        database_short_link_repository._database_async_session
        is database_async_session
    )


def test_provide_short_code_generator_returns_singleton() -> None:
    """Return the configured random short code generator."""
    first_short_code_generator: ShortCodeGeneratorInterface = (
        provide_short_code_generator()
    )
    second_short_code_generator: ShortCodeGeneratorInterface = (
        provide_short_code_generator()
    )

    assert isinstance(
        first_short_code_generator,
        RandomShortCodeGenerator,
    )
    assert second_short_code_generator is first_short_code_generator


def test_provide_create_short_link_use_case_wires_dependencies() -> None:
    """Create a use case with repository and generator dependencies."""
    short_link_repository: ShortLinkRepositoryStub = ShortLinkRepositoryStub()
    short_code_generator: ShortCodeGeneratorStub = ShortCodeGeneratorStub(
        short_codes=()
    )

    use_case: CreateShortLinkUseCase = provide_create_short_link_use_case(
        short_link_repository=short_link_repository,
        short_code_generator=short_code_generator,
    )

    assert use_case._short_link_repository is short_link_repository
    assert use_case._short_code_generator is short_code_generator


def test_provide_get_short_link_use_case_wires_repository() -> None:
    """Create a retrieval use case with its repository dependency."""
    short_link_repository: ShortLinkRepositoryStub = ShortLinkRepositoryStub()

    use_case: GetShortLinkByShortCodeUseCase = (
        provide_get_short_link_by_short_code_use_case(
            short_link_repository=short_link_repository
        )
    )

    assert use_case._short_link_repository is short_link_repository
