from pydantic import AwareDatetime, BaseModel, Field, HttpUrl


class CreateShortLinkRequestSchema(BaseModel):
    """Create short link request schema."""

    original_url: HttpUrl = Field(examples=["https://yandex.ru/"])
    expires_at: AwareDatetime | None = Field(
        default=None, examples=["2030-01-01T00:00:00Z"]
    )
