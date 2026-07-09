from src.application.dtos.short_link import ShortLinkDTO
from src.domain.entities.short_link import ShortLink


class ShortLinkMapper:
    """Short link mapper."""

    @staticmethod
    def to_dto(short_link: ShortLink) -> ShortLinkDTO:
        """Map short link to DTO."""
        return ShortLinkDTO(
            id=short_link.id,
            original_url=short_link.original_url.value,
            short_code=short_link.short_code.value,
            created_at=short_link.created_at,
            expires_at=short_link.expires_at,
        )
