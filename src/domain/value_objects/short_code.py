from dataclasses import dataclass

from src.domain.constants import (
    SHORT_CODE_ALLOWED_CHARS,
    SHORT_CODE_MAX_LENGTH,
    SHORT_CODE_MIN_LENGTH,
)
from src.domain.exceptions import InvalidShortCodeError


@dataclass(frozen=True, slots=True, kw_only=True)
class ShortCode:
    """Short code value object."""

    value: str

    def __post_init__(self) -> None:
        """Validate short code."""
        if len(self.value) < SHORT_CODE_MIN_LENGTH:
            raise InvalidShortCodeError("Short code is too short.")

        if len(self.value) > SHORT_CODE_MAX_LENGTH:
            raise InvalidShortCodeError("Short code is too long.")

        if any(char not in SHORT_CODE_ALLOWED_CHARS for char in self.value):
            raise InvalidShortCodeError(
                "Short code must contain only allowed characters."
            )
