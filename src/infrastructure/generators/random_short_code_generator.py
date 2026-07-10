import secrets

from src.application.interfaces.short_code_generator_interface import (
    ShortCodeGenerator,
)
from src.domain.constants import (
    SHORT_CODE_ALPHABET,
    SHORT_CODE_MAX_LENGTH,
    SHORT_CODE_MIN_LENGTH,
)
from src.domain.value_objects.short_code_value_object import ShortCode
from src.infrastructure.exceptions import ShortCodeGeneratorError

DEFAULT_SHORT_CODE_LENGTH: int = 7


class RandomShortCodeGenerator(ShortCodeGenerator):
    """Random short code generator."""

    def __init__(
        self, short_code_length: int = DEFAULT_SHORT_CODE_LENGTH
    ) -> None:
        if short_code_length < SHORT_CODE_MIN_LENGTH:
            raise ShortCodeGeneratorError("Short code is too short.")

        if short_code_length > SHORT_CODE_MAX_LENGTH:
            raise ShortCodeGeneratorError("Short code is too long.")

        self._short_code_length: int = short_code_length

    async def generate(self) -> ShortCode:
        """Generate short code."""
        return ShortCode(
            value="".join(
                secrets.choice(seq=SHORT_CODE_ALPHABET)
                for _ in range(self._short_code_length)
            )
        )
