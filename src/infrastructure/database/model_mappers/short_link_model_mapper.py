from src.domain.entities import ShortLink
from src.domain.value_objects import OriginalURL, ShortCode
from src.infrastructure.database.models import ShortLinkModel


class ShortLinkModelMapper:
    """Short link model mapper."""

    @staticmethod
    def to_model(short_link: ShortLink) -> ShortLinkModel:
        """Map short link to model."""
        return ShortLinkModel(
            id=short_link.id,
            original_url=short_link.original_url.value,
            short_code=short_link.short_code.value,
            created_at=short_link.created_at,
            expires_at=short_link.expires_at,
        )

    @staticmethod
    def to_entity(short_link_model: ShortLinkModel) -> ShortLink:
        """Map short link model to entity."""
        return ShortLink(
            id=short_link_model.id,
            original_url=OriginalURL(value=short_link_model.original_url),
            short_code=ShortCode(value=short_link_model.short_code),
            created_at=short_link_model.created_at,
            expires_at=short_link_model.expires_at,
        )
