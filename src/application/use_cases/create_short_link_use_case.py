from uuid import uuid4

from src.application.constants import MAX_SHORT_CODE_GENERATION_ATTEMPTS
from src.application.dtos import (
    CreateShortLinkDTO,
    ShortLinkDTO,
)
from src.application.exceptions import ShortCodeGenerationError
from src.application.interfaces import (
    ShortCodeGeneratorInterface,
    ShortLinkRepositoryInterface,
)
from src.application.mappers import ShortLinkMapper
from src.domain.entities import ShortLink
from src.domain.value_objects import OriginalURL, ShortCode


class CreateShortLinkUseCase:
    """Create short link use case."""

    def __init__(
        self,
        short_link_repository: ShortLinkRepositoryInterface,
        short_code_generator: ShortCodeGeneratorInterface,
    ) -> None:
        self._short_link_repository: ShortLinkRepositoryInterface = (
            short_link_repository
        )
        self._short_code_generator: ShortCodeGeneratorInterface = (
            short_code_generator
        )

    async def execute(
        self, create_short_link_dto: CreateShortLinkDTO
    ) -> ShortLinkDTO:
        """Create short link."""
        original_url: OriginalURL = OriginalURL(
            value=create_short_link_dto.original_url
        )
        short_code: ShortCode = await self._generate_unique_short_code()

        short_link: ShortLink = ShortLink(
            id=uuid4(),
            original_url=original_url,
            short_code=short_code,
            expires_at=create_short_link_dto.expires_at,
        )

        await self._short_link_repository.save(short_link=short_link)

        return ShortLinkMapper.to_dto(short_link=short_link)

    async def _generate_unique_short_code(self) -> ShortCode:
        """Generate unique short code."""
        for _ in range(MAX_SHORT_CODE_GENERATION_ATTEMPTS):
            short_code: ShortCode = await self._short_code_generator.generate()

            short_code_exists: bool = (
                await self._short_link_repository.exists_by_short_code(
                    short_code=short_code
                )
            )

            if not short_code_exists:
                return short_code

        raise ShortCodeGenerationError("Could not generate unique short code.")
