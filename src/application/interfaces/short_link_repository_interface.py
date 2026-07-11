from abc import ABC, abstractmethod

from src.domain.entities import ShortLink
from src.domain.value_objects import ShortCode


class ShortLinkRepositoryInterface(ABC):
    """Short link repository interface."""

    @abstractmethod
    async def save(self, short_link: ShortLink) -> None:
        """Save short link."""
        ...

    @abstractmethod
    async def exists_by_short_code(self, short_code: ShortCode) -> bool:
        """Return whether short code exists."""
        ...

    @abstractmethod
    async def get_by_short_code(
        self, short_code: ShortCode
    ) -> ShortLink | None:
        """Return short link by short code."""
        ...
