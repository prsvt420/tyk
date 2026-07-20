import pytest

from src.domain.constants import (
    SHORT_CODE_MAX_LENGTH,
    SHORT_CODE_MIN_LENGTH,
)
from src.domain.exceptions import InvalidShortCodeError
from src.domain.value_objects import ShortCode


@pytest.mark.parametrize(
    argnames="value",
    argvalues=[
        "a" * SHORT_CODE_MIN_LENGTH,
        "Z" * SHORT_CODE_MAX_LENGTH,
        "0aAZ",
    ],
)
def test_short_code_accepts_valid_value(value: str) -> None:
    """Accept values with valid length and characters."""
    short_code: ShortCode = ShortCode(value=value)

    assert short_code.value == value


def test_short_code_rejects_value_below_minimum_length() -> None:
    """Reject values below the minimum length."""
    with pytest.raises(
        expected_exception=InvalidShortCodeError,
        match=r"^Short code is too short\.$",
    ):
        ShortCode(value="a" * (SHORT_CODE_MIN_LENGTH - 1))


def test_short_code_rejects_value_above_maximum_length() -> None:
    """Reject values above the maximum length."""
    with pytest.raises(
        expected_exception=InvalidShortCodeError,
        match=r"^Short code is too long\.$",
    ):
        ShortCode(value="a" * (SHORT_CODE_MAX_LENGTH + 1))


def test_short_code_rejects_disallowed_character() -> None:
    """Reject values containing a disallowed character."""
    with pytest.raises(
        expected_exception=InvalidShortCodeError,
        match=r"^Short code must contain only allowed characters\.$",
    ):
        ShortCode(value="abc-")
