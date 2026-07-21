from datetime import datetime, timezone

import pytest

from src.domain.entities import ShortLink
from src.infrastructure.database.model_mappers import ShortLinkModelMapper
from src.infrastructure.database.models import ShortLinkModel
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
def test_short_link_model_mapper_maps_entity_and_model(
    expires_at: datetime | None,
) -> None:
    """Map every field between a domain entity and database model."""
    short_link: ShortLink = ShortLinkFactory.create(expires_at=expires_at)

    short_link_model: ShortLinkModel = ShortLinkModelMapper.to_model(
        short_link=short_link
    )
    mapped_short_link: ShortLink = ShortLinkModelMapper.to_entity(
        short_link_model=short_link_model
    )

    assert short_link_model.id == short_link.id
    assert short_link_model.original_url == short_link.original_url.value
    assert short_link_model.short_code == short_link.short_code.value
    assert short_link_model.created_at == short_link.created_at
    assert short_link_model.expires_at == short_link.expires_at
    assert mapped_short_link == short_link
