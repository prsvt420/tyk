from uuid import UUID

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.exceptions import ShortCodeAlreadyExistsError
from src.domain.entities import ShortLink
from src.domain.value_objects import ShortCode
from src.infrastructure.repositories import PostgreSQLShortLinkRepository
from tests.factories import ShortLinkFactory


@pytest.mark.integration
@pytest.mark.anyio
async def test_postgresql_repository_saves_and_returns_short_link(
    postgresql_async_session: AsyncSession,
) -> None:
    """Persist and retrieve a short link."""
    short_link: ShortLink = ShortLinkFactory.create()
    short_link_repository: PostgreSQLShortLinkRepository = (
        PostgreSQLShortLinkRepository(async_session=postgresql_async_session)
    )

    await short_link_repository.save(short_link=short_link)
    stored_short_link: ShortLink | None = (
        await short_link_repository.get_by_short_code(
            short_code=short_link.short_code
        )
    )

    assert stored_short_link == short_link


@pytest.mark.integration
@pytest.mark.anyio
async def test_postgresql_repository_returns_none_for_missing_link(
    postgresql_async_session: AsyncSession,
) -> None:
    """Return None when a short link does not exist."""
    short_link_repository: PostgreSQLShortLinkRepository = (
        PostgreSQLShortLinkRepository(async_session=postgresql_async_session)
    )

    stored_short_link: ShortLink | None = (
        await short_link_repository.get_by_short_code(
            short_code=ShortCode(value="abcd")
        )
    )

    assert stored_short_link is None


@pytest.mark.integration
@pytest.mark.anyio
async def test_postgresql_repository_rejects_duplicate_short_code(
    postgresql_async_session: AsyncSession,
) -> None:
    """Translate a short code constraint violation."""
    first_short_link: ShortLink = ShortLinkFactory.create()
    second_short_link: ShortLink = ShortLinkFactory.create(
        short_link_id=UUID(hex="dfd7aaa7-1b1d-4ef0-9be2-cf671652710e"),
        original_url="https://example.org/path",
    )
    short_link_repository: PostgreSQLShortLinkRepository = (
        PostgreSQLShortLinkRepository(async_session=postgresql_async_session)
    )
    await short_link_repository.save(short_link=first_short_link)

    with pytest.raises(
        expected_exception=ShortCodeAlreadyExistsError,
    ):
        await short_link_repository.save(short_link=second_short_link)


@pytest.mark.integration
@pytest.mark.anyio
async def test_postgresql_repository_reraises_other_integrity_error(
    postgresql_async_session: AsyncSession,
) -> None:
    """Preserve an unrelated database integrity error."""
    first_short_link: ShortLink = ShortLinkFactory.create()
    second_short_link: ShortLink = ShortLinkFactory.create(
        original_url="https://example.org/path",
        short_code="efgh",
    )
    short_link_repository: PostgreSQLShortLinkRepository = (
        PostgreSQLShortLinkRepository(async_session=postgresql_async_session)
    )
    await short_link_repository.save(short_link=first_short_link)

    with pytest.raises(
        expected_exception=IntegrityError,
    ):
        await short_link_repository.save(short_link=second_short_link)
