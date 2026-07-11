from uuid import UUID

from pydantic import AwareDatetime, BaseModel


class ShortLinkResponseSchema(BaseModel):
    """Short link response schema."""

    id: UUID
    original_url: str
    short_code: str
    created_at: AwareDatetime
    expires_at: AwareDatetime | None
