from uuid import UUID

from pydantic import AwareDatetime, BaseModel, Field, HttpUrl


class CreateShortLinkRequest(BaseModel):
    """Create short link request schema."""

    original_url: HttpUrl = Field(examples=["https://yandex.ru/"])
    expires_at: AwareDatetime | None = None


class ShortLinkResponse(BaseModel):
    """Short link response schema."""

    id: UUID
    original_url: str
    short_code: str
    created_at: AwareDatetime
    expires_at: AwareDatetime | None
