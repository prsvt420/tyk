from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateShortLinkDTO:
    """Create short link data transfer object."""

    original_url: str
    expires_at: datetime | None = None
