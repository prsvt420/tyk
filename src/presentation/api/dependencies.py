from src.application.interfaces.short_code_generator import ShortCodeGenerator
from src.application.interfaces.short_link_repository import (
    ShortLinkRepository,
)
from src.application.use_cases.create_short_link import CreateShortLinkUseCase
from src.application.use_cases.get_short_link_by_short_code import (
    GetShortLinkByShortCodeUseCase,
)
from src.infrastructure.generators.random_short_code_generator import (
    RandomShortCodeGenerator,
)
from src.infrastructure.repositories.in_memory_short_link_repository import (
    InMemoryShortLinkRepository,
)

_short_link_repository: ShortLinkRepository = InMemoryShortLinkRepository()
_short_code_generator: ShortCodeGenerator = RandomShortCodeGenerator()


def provide_short_link_repository() -> ShortLinkRepository:
    """Provide short link repository."""
    return _short_link_repository


def provide_short_code_generator() -> ShortCodeGenerator:
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
