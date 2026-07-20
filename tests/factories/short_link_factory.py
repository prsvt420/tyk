from datetime import datetime, timezone
from uuid import UUID

from src.domain.entities import ShortLink
from src.domain.value_objects import OriginalURL, ShortCode

DEFAULT_SHORT_LINK_ID: UUID = UUID(hex="4f4c2514-26b0-4c75-a77b-130e7858024e")
DEFAULT_ORIGINAL_URL: str = "https://example.com/path"
DEFAULT_SHORT_CODE: str = "abcd"
DEFAULT_CREATED_AT: datetime = datetime(
    year=2030,
    month=1,
    day=1,
    tzinfo=timezone.utc,
)


class ShortLinkFactory:
    """Create short links for tests."""

    @staticmethod
    def create(
        *,
        short_link_id: UUID = DEFAULT_SHORT_LINK_ID,
        original_url: str = DEFAULT_ORIGINAL_URL,
        short_code: str = DEFAULT_SHORT_CODE,
        created_at: datetime = DEFAULT_CREATED_AT,
        expires_at: datetime | None = None,
    ) -> ShortLink:
        """Create a short link with deterministic defaults."""
        return ShortLink(
            id=short_link_id,
            original_url=OriginalURL(value=original_url),
            short_code=ShortCode(value=short_code),
            created_at=created_at,
            expires_at=expires_at,
        )
