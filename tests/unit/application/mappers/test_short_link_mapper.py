from datetime import datetime, timezone

import pytest

from src.application.dtos import ShortLinkDTO
from src.application.mappers import ShortLinkMapper
from src.domain.entities import ShortLink
from tests.factories import ShortLinkFactory


@pytest.mark.parametrize(
    argnames="expires_at",
    argvalues=[
        None,
        datetime(
            year=2030,
            month=1,
            day=2,
            tzinfo=timezone.utc,
        ),
    ],
)
def test_short_link_mapper_maps_entity_to_dto(
    expires_at: datetime | None,
) -> None:
    """Map every short link field to a DTO."""
    short_link: ShortLink = ShortLinkFactory.create(expires_at=expires_at)

    short_link_dto: ShortLinkDTO = ShortLinkMapper.to_dto(
        short_link=short_link
    )

    assert short_link_dto == ShortLinkDTO(
        id=short_link.id,
        original_url=short_link.original_url.value,
        short_code=short_link.short_code.value,
        created_at=short_link.created_at,
        expires_at=short_link.expires_at,
    )
