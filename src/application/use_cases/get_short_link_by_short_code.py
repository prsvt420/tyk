from src.application.dtos.short_link import ShortLinkDTO
from src.application.exceptions import (
    ShortLinkExpiredError,
    ShortLinkNotFoundError,
)
from src.application.interfaces.short_link_repository import (
    ShortLinkRepository,
)
from src.domain.entities.short_link import ShortLink
from src.domain.value_objects.short_code import ShortCode


class GetShortLinkByShortCodeUseCase:
    """Get short link by short code use case."""

    def __init__(
        self,
        short_link_repository: ShortLinkRepository,
    ) -> None:
        self._short_link_repository: ShortLinkRepository = (
            short_link_repository
        )

    async def execute(self, short_code: str) -> ShortLinkDTO:
        """Get short link by short code."""
        short_link: ShortLink | None = (
            await self._short_link_repository.get_by_short_code(
                short_code=ShortCode(value=short_code),
            )
        )

        if short_link is None:
            raise ShortLinkNotFoundError("Short link not found.")

        if short_link.is_expired():
            raise ShortLinkExpiredError("Short link has expired.")

        return ShortLinkDTO(
            id=short_link.id,
            original_url=short_link.original_url.value,
            short_code=short_link.short_code.value,
            created_at=short_link.created_at,
            expires_at=short_link.expires_at,
        )
