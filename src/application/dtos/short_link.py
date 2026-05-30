from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True, kw_only=True)
class ShortLinkDTO:
    """Short link data transfer object."""

    id: UUID
    original_url: str
    short_code: str
    created_at: datetime
    expires_at: datetime | None


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateShortLinkDTO:
    """Create short link data transfer object."""

    original_url: str
    expires_at: datetime | None = None
