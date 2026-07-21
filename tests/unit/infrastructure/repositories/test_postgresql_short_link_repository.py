from typing import cast
from unittest.mock import AsyncMock, MagicMock

import pytest
from asyncpg import UniqueViolationError
from sqlalchemy import ScalarResult
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.exceptions import ShortCodeAlreadyExistsError
from src.domain.entities import ShortLink
from src.domain.value_objects import ShortCode
from src.infrastructure.database.model_mappers import ShortLinkModelMapper
from src.infrastructure.database.models import ShortLinkModel
from src.infrastructure.repositories import PostgreSQLShortLinkRepository
from tests.factories import ShortLinkFactory


def _create_async_session_mock(
    *, flush_error: IntegrityError | None = None
) -> MagicMock:
    """Create an asynchronous session mock."""
    async_session_mock: MagicMock = MagicMock(spec=AsyncSession)
    async_session_mock.flush = AsyncMock(side_effect=flush_error)

    return async_session_mock


def _create_integrity_error(*, constraint_name: str) -> IntegrityError:
    """Create an integrity error caused by a unique violation."""
    database_error: UniqueViolationError = UniqueViolationError()
    database_error.constraint_name = constraint_name
    original_error: Exception = Exception()
    original_error.__cause__ = database_error

    return IntegrityError(
        statement=None,
        params=None,
        orig=original_error,
    )


@pytest.mark.anyio
async def test_postgresql_repository_saves_short_link() -> None:
    """Map and add a short link to an asynchronous session."""
    async_session_mock: MagicMock = _create_async_session_mock()
    async_session: AsyncSession = cast(AsyncSession, async_session_mock)
    short_link: ShortLink = ShortLinkFactory.create()
    short_link_repository: PostgreSQLShortLinkRepository = (
        PostgreSQLShortLinkRepository(async_session=async_session)
    )

    await short_link_repository.save(short_link=short_link)

    short_link_model: ShortLinkModel = async_session_mock.add.call_args.kwargs[
        "instance"
    ]

    assert short_link_model.id == short_link.id
    assert short_link_model.original_url == short_link.original_url.value
    assert short_link_model.short_code == short_link.short_code.value
    assert short_link_model.created_at == short_link.created_at
    assert short_link_model.expires_at == short_link.expires_at
    async_session_mock.flush.assert_awaited_once_with()


@pytest.mark.anyio
async def test_postgresql_repository_translates_short_code_conflict() -> None:
    """Translate the short code unique constraint violation."""
    integrity_error: IntegrityError = _create_integrity_error(
        constraint_name="uq_short_links_short_code"
    )
    async_session_mock: MagicMock = _create_async_session_mock(
        flush_error=integrity_error
    )
    async_session: AsyncSession = cast(AsyncSession, async_session_mock)
    short_link_repository: PostgreSQLShortLinkRepository = (
        PostgreSQLShortLinkRepository(async_session=async_session)
    )

    with pytest.raises(
        expected_exception=ShortCodeAlreadyExistsError,
    ) as exception_info:
        await short_link_repository.save(short_link=ShortLinkFactory.create())

    assert exception_info.value.__cause__ is integrity_error


@pytest.mark.anyio
async def test_postgresql_repository_reraises_other_constraint_error() -> None:
    """Preserve another unique constraint violation."""
    integrity_error: IntegrityError = _create_integrity_error(
        constraint_name="pk_short_links"
    )
    async_session_mock: MagicMock = _create_async_session_mock(
        flush_error=integrity_error
    )
    async_session: AsyncSession = cast(AsyncSession, async_session_mock)
    short_link_repository: PostgreSQLShortLinkRepository = (
        PostgreSQLShortLinkRepository(async_session=async_session)
    )

    with pytest.raises(
        expected_exception=IntegrityError,
    ) as exception_info:
        await short_link_repository.save(short_link=ShortLinkFactory.create())

    assert exception_info.value is integrity_error


@pytest.mark.anyio
async def test_postgresql_repository_reraises_error_without_origin() -> None:
    """Preserve an integrity error without an original database error."""
    integrity_error: IntegrityError = IntegrityError(
        statement=None,
        params=None,
        orig=cast(BaseException, None),
    )
    async_session_mock: MagicMock = MagicMock(spec=AsyncSession)
    async_session_mock.flush = AsyncMock(side_effect=integrity_error)
    async_session: AsyncSession = cast(AsyncSession, async_session_mock)
    short_link: ShortLink = ShortLinkFactory.create()
    short_link_repository: PostgreSQLShortLinkRepository = (
        PostgreSQLShortLinkRepository(async_session=async_session)
    )

    with pytest.raises(
        expected_exception=IntegrityError,
    ) as exception_info:
        await short_link_repository.save(short_link=short_link)

    assert exception_info.value is integrity_error


@pytest.mark.anyio
async def test_postgresql_repository_returns_short_link() -> None:
    """Map and return a stored short link."""
    short_link: ShortLink = ShortLinkFactory.create()
    short_link_model: ShortLinkModel = ShortLinkModelMapper.to_model(
        short_link=short_link
    )
    short_link_models_mock: MagicMock = MagicMock(spec=ScalarResult)
    short_link_models_mock.one_or_none.return_value = short_link_model
    async_session_mock: MagicMock = _create_async_session_mock()
    async_session_mock.scalars = AsyncMock(return_value=short_link_models_mock)
    async_session: AsyncSession = cast(AsyncSession, async_session_mock)
    short_link_repository: PostgreSQLShortLinkRepository = (
        PostgreSQLShortLinkRepository(async_session=async_session)
    )

    stored_short_link: ShortLink | None = (
        await short_link_repository.get_by_short_code(
            short_code=short_link.short_code
        )
    )

    assert stored_short_link == short_link
    async_session_mock.scalars.assert_awaited_once()


@pytest.mark.anyio
async def test_postgresql_repository_returns_none_for_missing_link() -> None:
    """Return None when the database does not contain a short link."""
    short_link_models_mock: MagicMock = MagicMock(spec=ScalarResult)
    short_link_models_mock.one_or_none.return_value = None
    async_session_mock: MagicMock = _create_async_session_mock()
    async_session_mock.scalars = AsyncMock(return_value=short_link_models_mock)
    async_session: AsyncSession = cast(AsyncSession, async_session_mock)
    short_link_repository: PostgreSQLShortLinkRepository = (
        PostgreSQLShortLinkRepository(async_session=async_session)
    )

    stored_short_link: ShortLink | None = (
        await short_link_repository.get_by_short_code(
            short_code=ShortCode(value="abcd")
        )
    )

    assert stored_short_link is None
