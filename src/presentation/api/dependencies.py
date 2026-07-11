from src.application.interfaces import (
    ShortCodeGeneratorInterface,
    ShortLinkRepositoryInterface,
)
from src.application.use_cases import (
    CreateShortLinkUseCase,
    GetShortLinkByShortCodeUseCase,
)
from src.infrastructure.generators import RandomShortCodeGenerator
from src.infrastructure.repositories import InMemoryShortLinkRepository

_short_link_repository: ShortLinkRepositoryInterface = (
    InMemoryShortLinkRepository()
)
_short_code_generator: ShortCodeGeneratorInterface = RandomShortCodeGenerator()


def provide_short_link_repository() -> ShortLinkRepositoryInterface:
    """Provide short link repository."""
    return _short_link_repository


def provide_short_code_generator() -> ShortCodeGeneratorInterface:
    """Provide short code generator."""
    return _short_code_generator


def provide_create_short_link_use_case() -> CreateShortLinkUseCase:
    """Provide create short link use case."""
    return CreateShortLinkUseCase(
        short_link_repository=provide_short_link_repository(),
        short_code_generator=provide_short_code_generator(),
    )


def provide_get_short_link_by_short_code_use_case() -> (
    GetShortLinkByShortCodeUseCase
):
    """Provide get short link by short code use case."""
    return GetShortLinkByShortCodeUseCase(
        short_link_repository=provide_short_link_repository(),
    )
