from src.application.dtos import ShortLinkDTO
from src.application.exceptions import (
    ShortLinkExpiredError,
    ShortLinkNotFoundError,
)
from src.application.interfaces import ShortLinkRepositoryInterface
from src.application.mappers import ShortLinkMapper
from src.domain.entities import ShortLink
from src.domain.value_objects import ShortCode


class GetShortLinkByShortCodeUseCase:
    """Get short link by short code use case."""

    def __init__(
        self,
        short_link_repository: ShortLinkRepositoryInterface,
    ) -> None:
        self._short_link_repository: ShortLinkRepositoryInterface = (
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

        return ShortLinkMapper.to_dto(short_link=short_link)
