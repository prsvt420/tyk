from src.application.interfaces import ShortCodeGeneratorInterface
from src.domain.value_objects import ShortCode


class ShortCodeGeneratorStub(ShortCodeGeneratorInterface):
    """Return predefined short codes."""

    def __init__(self, *, short_codes: tuple[ShortCode, ...]) -> None:
        self._short_codes: tuple[ShortCode, ...] = short_codes
        self.call_count: int = 0

    async def generate(self) -> ShortCode:
        """Return the next predefined short code."""
        short_code: ShortCode = self._short_codes[self.call_count]
        self.call_count += 1

        return short_code
