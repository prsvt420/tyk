from src.application.interfaces.short_code_generator import ShortCodeGenerator
from src.application.interfaces.short_link_repository import (
    ShortLinkRepository,
)
from src.application.use_cases.create_short_link import CreateShortLinkUseCase
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
