from uuid import uuid4

from src.application.constants import MAX_SHORT_CODE_GENERATION_ATTEMPTS
from src.application.dtos.short_link import CreateShortLinkDTO, ShortLinkDTO
from src.application.exceptions import ShortCodeGenerationError
from src.application.interfaces.short_code_generator import ShortCodeGenerator
from src.application.interfaces.short_link_repository import (
    ShortLinkRepository,
)
from src.domain.entities.short_link import ShortLink
from src.domain.value_objects.original_url import OriginalUrl
from src.domain.value_objects.short_code import ShortCode


class CreateShortLinkUseCase:
    """Create short link use case."""

    def __init__(
        self,
        short_link_repository: ShortLinkRepository,
        short_code_generator: ShortCodeGenerator,
    ) -> None:
        self._short_link_repository: ShortLinkRepository = (
            short_link_repository
        )
        self._short_code_generator: ShortCodeGenerator = short_code_generator

    async def execute(
        self, create_short_link_dto: CreateShortLinkDTO
    ) -> ShortLinkDTO:
        """Create short link."""
        original_url: OriginalUrl = OriginalUrl(
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

        return ShortLinkDTO(
            id=short_link.id,
            original_url=short_link.original_url.value,
            short_code=short_link.short_code.value,
            created_at=short_link.created_at,
            expires_at=short_link.expires_at,
        )

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
