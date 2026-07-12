from asyncio import Lock

from src.application.exceptions import ShortCodeAlreadyExistsError
from src.application.interfaces import ShortLinkRepositoryInterface
from src.domain.entities import ShortLink
from src.domain.value_objects import ShortCode


class InMemoryShortLinkRepository(ShortLinkRepositoryInterface):
    """In-memory short link repository."""

    def __init__(self) -> None:
        self._short_links: dict[ShortCode, ShortLink] = {}
        self._lock: Lock = Lock()

    async def save(self, short_link: ShortLink) -> None:
        """Save short link."""
        async with self._lock:
            if short_link.short_code in self._short_links:
                raise ShortCodeAlreadyExistsError()
            self._short_links[short_link.short_code] = short_link

    async def get_by_short_code(
        self, short_code: ShortCode
    ) -> ShortLink | None:
        """Return short link by short code."""
        return self._short_links.get(short_code)
