import json
from datetime import datetime, timezone
from uuid import UUID

import pytest

from src.domain.entities import ShortLink
from src.domain.value_objects import OriginalURL, ShortCode
from src.infrastructure.cache.cache_mappers import ShortLinkCacheMapper
from tests.factories import ShortLinkFactory


@pytest.mark.parametrize(
    argnames=("expires_at", "expires_at_cache"),
    argvalues=[
        (None, None),
        (
            datetime(year=2030, month=1, day=2, tzinfo=timezone.utc),
            "2030-01-02T00:00:00+00:00",
        ),
    ],
)
def test_short_link_cache_mapper_maps_entity_to_json(
    expires_at: datetime | None,
    expires_at_cache: str | None,
) -> None:
    """Serialize every field to JSON with an optional expiration date."""
    short_link: ShortLink = ShortLinkFactory.create(expires_at=expires_at)

    short_link_cache: str = ShortLinkCacheMapper.to_cache(
        short_link=short_link
    )

    assert isinstance(short_link_cache, str)
    assert json.loads(s=short_link_cache) == {
        "id": str(short_link.id),
        "original_url": short_link.original_url.value,
        "short_code": short_link.short_code.value,
        "created_at": "2030-01-01T00:00:00+00:00",
        "expires_at": expires_at_cache,
    }


@pytest.mark.parametrize(
    argnames=("expires_at_cache", "expires_at"),
    argvalues=[
        (None, None),
        (
            "2030-01-02T08:00:00+08:00",
            datetime(year=2030, month=1, day=2, tzinfo=timezone.utc),
        ),
    ],
)
def test_short_link_cache_mapper_maps_json_to_entity(
    expires_at_cache: str | None,
    expires_at: datetime | None,
) -> None:
    """Restore domain types and normalize aware dates from cached JSON."""
    short_link_cache: str = json.dumps(
        obj={
            "id": "4f4c2514-26b0-4c75-a77b-130e7858024e",
            "original_url": "https://example.com/path",
            "short_code": "abcd",
            "created_at": "2030-01-01T08:00:00+08:00",
            "expires_at": expires_at_cache,
        }
    )

    short_link: ShortLink = ShortLinkCacheMapper.to_entity(
        short_link_cache=short_link_cache
    )

    assert short_link == ShortLinkFactory.create(expires_at=expires_at)
    assert isinstance(short_link.id, UUID)
    assert isinstance(short_link.original_url, OriginalURL)
    assert isinstance(short_link.short_code, ShortCode)
    assert isinstance(short_link.created_at, datetime)
    assert short_link.created_at.tzinfo == timezone.utc
    if expires_at is None:
        assert short_link.expires_at is None
    else:
        assert isinstance(short_link.expires_at, datetime)
        assert short_link.expires_at.tzinfo == timezone.utc
