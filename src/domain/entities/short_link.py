from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID

from src.domain.exceptions import InvalidShortLinkError
from src.domain.value_objects.original_url import OriginalUrl
from src.domain.value_objects.short_code import ShortCode


@dataclass(slots=True, kw_only=True)
class ShortLink:
    """Short link entity."""

    id: UUID
    original_url: OriginalUrl
    short_code: ShortCode
    created_at: datetime = field(
        default_factory=lambda: datetime.now(tz=timezone.utc)
    )
    expires_at: datetime | None = None

    def __post_init__(self) -> None:
        """Validate short link."""
        if (
            self.created_at.tzinfo is None
            or self.created_at.utcoffset() is None
        ):
            raise InvalidShortLinkError("created_at must be timezone-aware.")

        self.created_at: datetime = self.created_at.astimezone(tz=timezone.utc)

        if self.expires_at is None:
            return

        if (
            self.expires_at.tzinfo is None
            or self.created_at.utcoffset() is None
        ):
            raise InvalidShortLinkError("expires_at must be timezone-aware.")

        self.expires_at: datetime = self.expires_at.astimezone(tz=timezone.utc)

        if self.expires_at <= self.created_at:
            raise InvalidShortLinkError(
                "expires_at must be later than created_at."
            )

    def is_expired(self, now: datetime | None = None) -> bool:
        """Return whether the short link is expired."""
        if self.expires_at is None:
            return False

        return self.expires_at <= (now or datetime.now(tz=timezone.utc))

    def can_redirect(self, now: datetime | None = None) -> bool:
        """Return whether the short link can be used for redirect."""
        return not self.is_expired(now=now)
