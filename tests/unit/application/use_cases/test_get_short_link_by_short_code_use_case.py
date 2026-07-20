from datetime import datetime, timezone

import pytest

from src.application.dtos import ShortLinkDTO
from src.application.exceptions import (
    ShortLinkExpiredError,
    ShortLinkNotFoundError,
)
from src.application.use_cases import GetShortLinkByShortCodeUseCase
from src.domain.entities import ShortLink
from src.domain.exceptions import InvalidShortCodeError
from src.domain.value_objects import ShortCode
from tests.factories import ShortLinkFactory
from tests.unit.application.stubs import ShortLinkRepositoryStub


@pytest.mark.anyio
async def test_get_short_link_use_case_returns_short_link() -> None:
    """Return an active short link from the repository."""
    short_link: ShortLink = ShortLinkFactory.create()
    short_link_repository: ShortLinkRepositoryStub = ShortLinkRepositoryStub(
        short_link=short_link
    )
    use_case: GetShortLinkByShortCodeUseCase = GetShortLinkByShortCodeUseCase(
        short_link_repository=short_link_repository
    )

    short_link_dto: ShortLinkDTO = await use_case.execute(
        short_code=short_link.short_code.value
    )

    assert short_link_dto.id == short_link.id
    assert short_link_dto.original_url == short_link.original_url.value
    assert short_link_dto.short_code == short_link.short_code.value
    assert short_link_dto.created_at == short_link.created_at
    assert short_link_dto.expires_at == short_link.expires_at
    assert short_link_repository.requested_short_codes == [
        short_link.short_code
    ]


@pytest.mark.anyio
async def test_get_short_link_use_case_rejects_missing_link() -> None:
    """Raise an error when the short link does not exist."""
    short_link_repository: ShortLinkRepositoryStub = ShortLinkRepositoryStub()
    use_case: GetShortLinkByShortCodeUseCase = GetShortLinkByShortCodeUseCase(
        short_link_repository=short_link_repository
    )

    with pytest.raises(
        expected_exception=ShortLinkNotFoundError,
        match=r"^Short link not found\.$",
    ):
        await use_case.execute(short_code="abcd")

    assert short_link_repository.requested_short_codes == [
        ShortCode(value="abcd")
    ]


@pytest.mark.anyio
async def test_get_short_link_use_case_rejects_expired_link() -> None:
    """Raise an error when the short link has expired."""
    short_link: ShortLink = ShortLinkFactory.create(
        created_at=datetime(
            year=2000,
            month=1,
            day=1,
            tzinfo=timezone.utc,
        ),
        expires_at=datetime(
            year=2000,
            month=1,
            day=2,
            tzinfo=timezone.utc,
        ),
    )
    short_link_repository: ShortLinkRepositoryStub = ShortLinkRepositoryStub(
        short_link=short_link
    )
    use_case: GetShortLinkByShortCodeUseCase = GetShortLinkByShortCodeUseCase(
        short_link_repository=short_link_repository
    )

    with pytest.raises(
        expected_exception=ShortLinkExpiredError,
        match=r"^Short link has expired\.$",
    ):
        await use_case.execute(short_code=short_link.short_code.value)


@pytest.mark.anyio
async def test_get_short_link_use_case_rejects_invalid_code() -> None:
    """Reject an invalid short code before querying the repository."""
    short_link_repository: ShortLinkRepositoryStub = ShortLinkRepositoryStub()
    use_case: GetShortLinkByShortCodeUseCase = GetShortLinkByShortCodeUseCase(
        short_link_repository=short_link_repository
    )

    with pytest.raises(
        expected_exception=InvalidShortCodeError,
        match=r"^Short code must contain only allowed characters\.$",
    ):
        await use_case.execute(short_code="abc-")

    assert short_link_repository.requested_short_codes == []
