from src.application.interfaces import ShortLinkRepositoryInterface
from src.domain.entities import ShortLink
from src.domain.value_objects import ShortCode


class ShortLinkRepositoryStub(ShortLinkRepositoryInterface):
    """Store calls and return predefined repository results."""

    def __init__(
        self,
        *,
        short_link: ShortLink | None = None,
        save_errors: tuple[Exception | None, ...] = (),
    ) -> None:
        self.short_link: ShortLink | None = short_link
        self._save_errors: tuple[Exception | None, ...] = save_errors
        self.saved_short_links: list[ShortLink] = []
        self.requested_short_codes: list[ShortCode] = []
        self.save_call_count: int = 0

    async def save(self, short_link: ShortLink) -> None:
        """Store a short link or raise a predefined error."""
        self.saved_short_links.append(short_link)

        save_error: Exception | None = (
            self._save_errors[self.save_call_count]
            if self.save_call_count < len(self._save_errors)
            else None
        )
        self.save_call_count += 1

        if save_error is not None:
            raise save_error

    async def get_by_short_code(
        self, short_code: ShortCode
    ) -> ShortLink | None:
        """Return the predefined short link."""
        self.requested_short_codes.append(short_code)

        return self.short_link
