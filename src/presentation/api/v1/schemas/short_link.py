from uuid import UUID

from pydantic import AwareDatetime, BaseModel, Field, HttpUrl


class CreateShortLinkRequest(BaseModel):
    """Create short link request schema."""

    original_url: HttpUrl = Field(examples=["https://yandex.ru/"])
    expires_at: AwareDatetime | None = Field(examples=["2030-01-01T00:00:00Z"])


class ShortLinkResponse(BaseModel):
    """Short link response schema."""

    id: UUID
    original_url: str
    short_code: str
    created_at: AwareDatetime
    expires_at: AwareDatetime | None
