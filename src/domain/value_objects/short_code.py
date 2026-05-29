from dataclasses import dataclass

from src.domain.constants import (
    SHORT_CODE_MAX_LENGTH,
    SHORT_CODE_MIN_LENGTH,
    SHORT_CODE_PATTERN,
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

        if SHORT_CODE_PATTERN.fullmatch(string=self.value) is None:
            raise InvalidShortCodeError(
                "Short code must contain only pattern characters."
            )
