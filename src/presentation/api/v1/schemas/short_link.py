from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl


class CreateShortLinkRequest(BaseModel):
    """Create short link request schema."""

    original_url: HttpUrl = Field(examples=["https://yandex.ru/"])
    expires_at: datetime | None = Field(
        default=None,
        examples=[None],
    )


class ShortLinkResponse(BaseModel):
    """Short link response schema."""

    id: UUID
    original_url: str
    short_code: str
    created_at: datetime
    expires_at: datetime | None
