from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID

from src.domain.exceptions import InvalidUserError
from src.domain.value_objects.email_value_object import Email


@dataclass(slots=True, kw_only=True)
class User:
    """User entity."""

    id: UUID
    email: Email
    password: str = field(repr=False)
    is_active: bool = field(default=True)
    last_login_at: datetime | None = field(default=None)
    created_at: datetime = field(
        default_factory=lambda: datetime.now(tz=timezone.utc)
    )
    updated_at: datetime = field(
        default_factory=lambda: datetime.now(tz=timezone.utc)
    )
    deleted_at: datetime | None = field(default=None)

    def __post_init__(self) -> None:
        """Validate user entity."""
        if self.last_login_at is not None:
            if (
                self.last_login_at.tzinfo is None
                or self.last_login_at.utcoffset() is None
            ):
                raise InvalidUserError("last_login_at must be timezone-aware.")

            self.last_login_at = self.last_login_at.astimezone(tz=timezone.utc)

        if (
            self.created_at.tzinfo is None
            or self.created_at.utcoffset() is None
        ):
            raise InvalidUserError("created_at must be timezone-aware.")

        self.created_at: datetime = self.created_at.astimezone(tz=timezone.utc)

        if (
            self.updated_at.tzinfo is None
            or self.updated_at.utcoffset() is None
        ):
            raise InvalidUserError("updated_at must be timezone-aware.")

        self.updated_at: datetime = self.updated_at.astimezone(tz=timezone.utc)

        if self.deleted_at is not None:
            if (
                self.deleted_at.tzinfo is None
                or self.deleted_at.utcoffset() is None
            ):
                raise InvalidUserError("deleted_at must be timezone-aware.")

            self.deleted_at = self.deleted_at.astimezone(tz=timezone.utc)
