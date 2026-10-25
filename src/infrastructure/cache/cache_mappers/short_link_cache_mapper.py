import json
from datetime import datetime
from typing import Any
from uuid import UUID

from src.domain.entities import ShortLink
from src.domain.value_objects import OriginalURL, ShortCode


class ShortLinkCacheMapper:
    """Short link cache mapper."""

    @staticmethod
    def to_cache(short_link: ShortLink) -> str:
        """Map short link to cache."""
        return json.dumps(
            obj={
                "id": str(short_link.id),
                "original_url": short_link.original_url.value,
                "short_code": short_link.short_code.value,
                "created_at": short_link.created_at.isoformat(),
                "expires_at": (
                    short_link.expires_at.isoformat()
                    if short_link.expires_at is not None
                    else None
                ),
            }
        )

    @staticmethod
    def to_entity(short_link_cache: str) -> ShortLink:
        """Map short link cache to entity."""
        short_link_cache_data: dict[str, Any] = json.loads(s=short_link_cache)
        expires_at: str | None = short_link_cache_data["expires_at"]

        return ShortLink(
            id=UUID(hex=short_link_cache_data["id"]),
            original_url=OriginalURL(
                value=short_link_cache_data["original_url"]
            ),
            short_code=ShortCode(value=short_link_cache_data["short_code"]),
            created_at=datetime.fromisoformat(
                short_link_cache_data["created_at"]
            ),
            expires_at=(
                datetime.fromisoformat(expires_at)
                if expires_at is not None
                else None
            ),
        )
