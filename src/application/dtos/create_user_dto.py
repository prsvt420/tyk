from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateUserDTO:
    """Create user data transfer object."""

    email: str
    password: str = field(repr=False)
