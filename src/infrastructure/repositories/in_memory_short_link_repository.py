from typing import Dict

from src.application.interfaces.short_link_repository_interface import (
    ShortLinkRepository,
)
from src.domain.entities.short_link_entity import ShortLink
from src.domain.value_objects.short_code_value_object import ShortCode


class InMemoryShortLinkRepository(ShortLinkRepository):
    """In-memory short link repository."""

    def __init__(self) -> None:
        self._short_links: Dict[ShortCode, ShortLink] = {}

    async def save(self, short_link: ShortLink) -> None:
        """Save short link."""
        self._short_links[short_link.short_code] = short_link

    async def exists_by_short_code(self, short_code: ShortCode) -> bool:
        """Return whether short code exists."""
        return short_code in self._short_links

    async def get_by_short_code(
        self, short_code: ShortCode
    ) -> ShortLink | None:
        """Return short link by short code."""
        return self._short_links.get(short_code)
