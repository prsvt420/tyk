from uuid import UUID

from pydantic import AwareDatetime, BaseModel, HttpUrl


class ShortLinkResponseSchema(BaseModel):
    """Short link response schema."""

    id: UUID
    original_url: str
    short_code: str
    short_link_url: HttpUrl
    created_at: AwareDatetime
    expires_at: AwareDatetime | None
