from dataclasses import FrozenInstanceError

import pytest

from src.domain.exceptions import InvalidPasswordError
from src.domain.value_objects import Password


@pytest.mark.parametrize(
    argnames="value",
    argvalues=["a" * 8, "a" * 128, "пароль123", " abc def "],
)
def test_password_preserves_valid_value(value: str) -> None:
    """Accept length boundaries and preserve Unicode and whitespace."""
    password: Password = Password(value=value)

    assert password.value == value


@pytest.mark.parametrize(argnames="value", argvalues=["", "a" * 7])
def test_password_rejects_short_value(value: str) -> None:
    """Reject values below the minimum length."""
    with pytest.raises(
        expected_exception=InvalidPasswordError,
        match=r"^Password is too short\.$",
    ):
        Password(value=value)


def test_password_rejects_long_value() -> None:
    """Reject values above the maximum length."""
    with pytest.raises(
        expected_exception=InvalidPasswordError,
        match=r"^Password is too long\.$",
    ):
        Password(value="a" * 129)


def test_password_hides_value_from_repr() -> None:
    """Keep the original value out of the object representation."""
    value: str = "Example123!"
    password: Password = Password(value=value)

    assert value not in repr(password)
    assert "value=" not in repr(password)


def test_password_is_immutable() -> None:
    """Prevent changing the value after validation."""
    password: Password = Password(value="Example123!")

    with pytest.raises(expected_exception=FrozenInstanceError):
        password.value = "changed123!"  # type: ignore[misc]
