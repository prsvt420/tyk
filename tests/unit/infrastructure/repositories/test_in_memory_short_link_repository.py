from uuid import UUID

import pytest

from src.application.exceptions import ShortCodeAlreadyExistsError
from src.domain.entities import ShortLink
from src.domain.value_objects import ShortCode
from src.infrastructure.repositories import InMemoryShortLinkRepository
from tests.factories import ShortLinkFactory


@pytest.mark.anyio
async def test_in_memory_repository_saves_and_returns_short_link() -> None:
    """Save and return a short link by its short code."""
    short_link: ShortLink = ShortLinkFactory.create()
    short_link_repository: InMemoryShortLinkRepository = (
        InMemoryShortLinkRepository()
    )

    await short_link_repository.save(short_link=short_link)

    stored_short_link: ShortLink | None = (
        await short_link_repository.get_by_short_code(
            short_code=short_link.short_code
        )
    )

    assert stored_short_link == short_link


@pytest.mark.anyio
async def test_in_memory_repository_returns_none_for_missing_link() -> None:
    """Return None when a short link does not exist."""
    short_link_repository: InMemoryShortLinkRepository = (
        InMemoryShortLinkRepository()
    )

    stored_short_link: ShortLink | None = (
        await short_link_repository.get_by_short_code(
            short_code=ShortCode(value="abcd")
        )
    )

    assert stored_short_link is None


@pytest.mark.anyio
async def test_in_memory_repository_rejects_duplicate_short_code() -> None:
    """Reject a different short link with an existing short code."""
    first_short_link: ShortLink = ShortLinkFactory.create()
    second_short_link: ShortLink = ShortLinkFactory.create(
        short_link_id=UUID(hex="dfd7aaa7-1b1d-4ef0-9be2-cf671652710e"),
        original_url="https://example.org/path",
    )
    short_link_repository: InMemoryShortLinkRepository = (
        InMemoryShortLinkRepository()
    )
    await short_link_repository.save(short_link=first_short_link)

    with pytest.raises(
        expected_exception=ShortCodeAlreadyExistsError,
    ):
        await short_link_repository.save(short_link=second_short_link)

    stored_short_link: ShortLink | None = (
        await short_link_repository.get_by_short_code(
            short_code=first_short_link.short_code
        )
    )

    assert stored_short_link == first_short_link
