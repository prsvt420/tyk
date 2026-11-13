from dataclasses import dataclass, field

from src.domain.exceptions import InvalidPasswordError


@dataclass(frozen=True, slots=True, kw_only=True)
class Password:
    """Password value object."""

    value: str = field(repr=False)

    def __post_init__(self) -> None:
        """Validate password."""
        if len(self.value) < 8:
            raise InvalidPasswordError("Password is too short.")

        if len(self.value) > 128:
            raise InvalidPasswordError("Password is too long.")
