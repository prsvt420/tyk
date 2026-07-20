from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest

from src.domain.entities import ShortLink
from src.domain.exceptions import InvalidShortLinkError
from src.domain.value_objects import OriginalURL, ShortCode

SHORT_LINK_ID: UUID = UUID(hex="4f4c2514-26b0-4c75-a77b-130e7858024e")
ORIGINAL_URL: OriginalURL = OriginalURL(value="https://example.com")
SHORT_CODE: ShortCode = ShortCode(value="abcd")
CREATED_AT: datetime = datetime(
    year=2030,
    month=1,
    day=1,
    tzinfo=timezone.utc,
)
EXPIRES_AT: datetime = datetime(
    year=2030,
    month=1,
    day=2,
    tzinfo=timezone.utc,
)


def _create_short_link(
    *,
    created_at: datetime = CREATED_AT,
    expires_at: datetime | None = EXPIRES_AT,
) -> ShortLink:
    """Create a short link with deterministic test values."""
    return ShortLink(
        id=SHORT_LINK_ID,
        original_url=ORIGINAL_URL,
        short_code=SHORT_CODE,
        created_at=created_at,
        expires_at=expires_at,
    )


def test_short_link_creates_without_expiration() -> None:
    """Create a short link without an expiration time."""
    short_link: ShortLink = ShortLink(
        id=SHORT_LINK_ID,
        original_url=ORIGINAL_URL,
        short_code=SHORT_CODE,
    )

    assert short_link.created_at.tzinfo is timezone.utc
    assert short_link.expires_at is None


def test_short_link_normalizes_datetimes_to_utc() -> None:
    """Normalize aware creation and expiration times to UTC."""
    irkutsk_timezone: timezone = timezone(offset=timedelta(hours=8))
    created_at: datetime = datetime(
        year=2030,
        month=1,
        day=1,
        hour=8,
        tzinfo=irkutsk_timezone,
    )
    expires_at: datetime = datetime(
        year=2030,
        month=1,
        day=2,
        hour=8,
        tzinfo=irkutsk_timezone,
    )

    short_link: ShortLink = _create_short_link(
        created_at=created_at,
        expires_at=expires_at,
    )

    assert short_link.created_at == CREATED_AT
    assert short_link.expires_at == EXPIRES_AT
    assert short_link.created_at.tzinfo is timezone.utc
    assert short_link.expires_at.tzinfo is timezone.utc


def test_short_link_rejects_naive_creation_time() -> None:
    """Reject a creation time without timezone information."""
    with pytest.raises(
        expected_exception=InvalidShortLinkError,
        match=r"^created_at must be timezone-aware\.$",
    ):
        _create_short_link(created_at=datetime(year=2030, month=1, day=1))


def test_short_link_rejects_naive_expiration_time() -> None:
    """Reject an expiration time without timezone information."""
    with pytest.raises(
        expected_exception=InvalidShortLinkError,
        match=r"^expires_at must be timezone-aware\.$",
    ):
        _create_short_link(expires_at=datetime(year=2030, month=1, day=2))


@pytest.mark.parametrize(
    argnames="expires_at",
    argvalues=[
        CREATED_AT,
        CREATED_AT - timedelta(seconds=1),
    ],
)
def test_short_link_rejects_non_future_expiration(
    expires_at: datetime,
) -> None:
    """Reject expiration at or before the creation time."""
    with pytest.raises(
        expected_exception=InvalidShortLinkError,
        match=r"^expires_at must be later than created_at\.$",
    ):
        _create_short_link(expires_at=expires_at)


def test_short_link_without_expiration_is_not_expired() -> None:
    """Treat a short link without expiration as active."""
    short_link: ShortLink = _create_short_link(expires_at=None)

    assert short_link.is_expired(now=EXPIRES_AT) is False


@pytest.mark.parametrize(
    argnames=("now", "expected"),
    argvalues=[
        (EXPIRES_AT - timedelta(seconds=1), False),
        (EXPIRES_AT, True),
        (EXPIRES_AT + timedelta(seconds=1), True),
    ],
)
def test_short_link_checks_expiration(
    now: datetime,
    expected: bool,
) -> None:
    """Compare the expiration time with the supplied current time."""
    short_link: ShortLink = _create_short_link()

    assert short_link.is_expired(now=now) is expected


def test_short_link_uses_current_time_for_expiration() -> None:
    """Use the current UTC time when no comparison time is supplied."""
    short_link: ShortLink = _create_short_link(
        created_at=datetime(
            year=2000,
            month=1,
            day=1,
            tzinfo=timezone.utc,
        ),
        expires_at=datetime(
            year=2000,
            month=1,
            day=2,
            tzinfo=timezone.utc,
        ),
    )

    assert short_link.is_expired() is True


@pytest.mark.parametrize(
    argnames=("now", "expected"),
    argvalues=[
        (EXPIRES_AT - timedelta(seconds=1), True),
        (EXPIRES_AT, False),
    ],
)
def test_short_link_checks_redirect_availability(
    now: datetime,
    expected: bool,
) -> None:
    """Allow redirects only while the short link is active."""
    short_link: ShortLink = _create_short_link()

    assert short_link.can_redirect(now=now) is expected
