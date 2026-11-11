import re
from dataclasses import dataclass

from src.domain.exceptions import InvalidEmailError


@dataclass(frozen=True, slots=True, kw_only=True)
class Email:
    """Email value object."""

    value: str

    def __post_init__(self) -> None:
        """Validate email."""
        if len(self.value) > 254:
            raise InvalidEmailError("Email is too long.")

        if self.value.count("@") != 1:
            raise InvalidEmailError("Email must contain one @ character.")

        local_part, domain = self.value.split(sep="@")

        if not local_part or len(local_part) > 64:
            raise InvalidEmailError("Email local part length is invalid.")

        if not re.fullmatch(
            pattern=r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+",
            string=local_part,
        ):
            raise InvalidEmailError("Email local part is invalid.")

        if (
            local_part.startswith(".")
            or local_part.endswith(".")
            or ".." in local_part
        ):
            raise InvalidEmailError("Email local part dots are invalid.")

        labels: list[str] = domain.split(sep=".")

        if len(labels) < 2:
            raise InvalidEmailError("Email domain must contain a dot.")

        for label in labels:
            if not re.fullmatch(
                pattern=r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?",
                string=label,
            ):
                raise InvalidEmailError("Email domain label is invalid.")

        object.__setattr__(self, "value", f"{local_part}@{domain.lower()}")
