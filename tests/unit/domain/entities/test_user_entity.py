from datetime import datetime, timedelta, timezone, tzinfo
from typing import TypedDict
from uuid import UUID

import pytest

from src.domain.entities import User
from src.domain.exceptions import InvalidUserError
from src.domain.value_objects import Email

USER_ID: UUID = UUID(hex="4f4c2514-26b0-4c75-a77b-130e7858024e")
EMAIL: Email = Email(value="user@example.com")
STORED_HASH: str = "test-hash"
DATE_FIELDS: tuple[str, ...] = (
    "created_at",
    "updated_at",
    "last_login_at",
    "deleted_at",
)


class UserDates(TypedDict, total=False):
    """Describe date overrides when restoring a user."""

    created_at: datetime
    updated_at: datetime
    last_login_at: datetime | None
    deleted_at: datetime | None


def _date_overrides(*, field_name: str, date: datetime) -> UserDates:
    """Build typed date overrides for a selected user field."""
    if field_name == "created_at":
        return {"created_at": date}
    if field_name == "updated_at":
        return {"updated_at": date}
    if field_name == "last_login_at":
        return {"last_login_at": date}
    return {"deleted_at": date}


class UndefinedOffsetTimezone(tzinfo):
    """Represent timezone information without a defined UTC offset."""

    def utcoffset(self, dt: datetime | None) -> timedelta | None:
        """Return an undefined offset."""
        return None

    def dst(self, dt: datetime | None) -> timedelta | None:
        """Return an undefined daylight saving offset."""
        return None

    def tzname(self, dt: datetime | None) -> str | None:
        """Return no timezone name."""
        return None


def test_user_creates_with_defaults() -> None:
    """Set active status and current UTC dates for a new user."""
    before: datetime = datetime.now(tz=timezone.utc)
    user: User = User(id=USER_ID, email=EMAIL, password=STORED_HASH)
    after: datetime = datetime.now(tz=timezone.utc)

    assert user.id == USER_ID
    assert user.email == EMAIL
    assert user.is_active is True
    assert user.last_login_at is None
    assert user.deleted_at is None
    assert before <= user.created_at <= after
    assert before <= user.updated_at <= after
    assert user.created_at.tzinfo is timezone.utc
    assert user.updated_at.tzinfo is timezone.utc


def test_user_hides_password_from_repr() -> None:
    """Keep the stored password out of the entity representation."""
    user: User = User(id=USER_ID, email=EMAIL, password=STORED_HASH)

    assert user.password == STORED_HASH
    assert STORED_HASH not in repr(user)
    assert "password=" not in repr(user)


def test_user_preserves_inactive_status() -> None:
    """Restore an inactive user without enabling the account."""
    user: User = User(
        id=USER_ID, email=EMAIL, password=STORED_HASH, is_active=False
    )

    assert user.is_active is False


@pytest.mark.parametrize(argnames="field_name", argvalues=DATE_FIELDS)
@pytest.mark.parametrize(
    argnames="date_timezone",
    argvalues=[None, UndefinedOffsetTimezone()],
)
def test_user_rejects_dates_without_offset(
    field_name: str,
    date_timezone: tzinfo | None,
) -> None:
    """Reject naive dates and timezones without a defined offset."""
    date: datetime = datetime(year=2030, month=1, day=1, tzinfo=date_timezone)
    dates: UserDates = _date_overrides(field_name=field_name, date=date)

    with pytest.raises(
        expected_exception=InvalidUserError,
        match=rf"^{field_name} must be timezone-aware\.$",
    ):
        User(id=USER_ID, email=EMAIL, password=STORED_HASH, **dates)


@pytest.mark.parametrize(argnames="field_name", argvalues=DATE_FIELDS)
@pytest.mark.parametrize(argnames="offset_hours", argvalues=[0, 7, -5])
def test_user_normalizes_dates_to_utc(
    field_name: str,
    offset_hours: int,
) -> None:
    """Preserve stored instants while converting dates to UTC."""
    date: datetime = datetime(
        year=2030,
        month=1,
        day=1,
        hour=12,
        tzinfo=timezone(offset=timedelta(hours=offset_hours)),
    )
    dates: UserDates = _date_overrides(field_name=field_name, date=date)
    user: User = User(id=USER_ID, email=EMAIL, password=STORED_HASH, **dates)
    normalized: datetime = getattr(user, field_name)

    assert normalized == date
    assert normalized.hour == 12 - offset_hours
    assert normalized.tzinfo is timezone.utc
