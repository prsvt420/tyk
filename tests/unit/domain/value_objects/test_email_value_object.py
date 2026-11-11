from dataclasses import FrozenInstanceError

import pytest

from src.domain.exceptions import InvalidEmailError
from src.domain.value_objects import Email


@pytest.mark.parametrize(
    argnames="value",
    argvalues=[
        "user@example.com",
        "first.last+tag@sub.example.com",
        "user@my-domain.com",
        "a" * 64 + "@example.com",
        "user@" + "a" * 63 + ".com",
        "a" * 64 + "@" + ".".join(["b" * 63, "c" * 63, "d" * 61]),
    ],
)
def test_email_accepts_valid_value(value: str) -> None:
    """Accept supported addresses including length boundaries."""
    assert Email(value=value).value == value


@pytest.mark.parametrize(
    argnames="value",
    argvalues=[
        "",
        "user.example.com",
        "user@@example.com",
        "@example.com",
        "a" * 65 + "@example.com",
        "a" * 64 + "@" + ".".join(["b" * 63, "c" * 63, "d" * 62]),
        "user name@example.com",
        "user@example.com\n",
        "user@example.com ",
        " user@example.com",
        "юзер@example.com",
        ".user@example.com",
        "user.@example.com",
        "user..name@example.com",
        "user@",
        "user@localhost",
        "user@.example.com",
        "user@example.com.",
        "user@example..com",
        "user@-example.com",
        "user@example-.com",
        "user@exam_ple.com",
        "user@" + "a" * 64 + ".com",
    ],
)
def test_email_rejects_invalid_value(value: str) -> None:
    """Reject malformed addresses and exceeded length limits."""
    with pytest.raises(expected_exception=InvalidEmailError):
        Email(value=value)


def test_email_normalizes_domain_only() -> None:
    """Lowercase the domain while preserving local part case."""
    email: Email = Email(value="User.Name@SUB.EXAMPLE.COM")

    assert email.value == "User.Name@sub.example.com"
    assert email == Email(value="User.Name@sub.example.com")


def test_email_is_immutable() -> None:
    """Prevent changing an address after validation."""
    email: Email = Email(value="user@example.com")

    with pytest.raises(expected_exception=FrozenInstanceError):
        email.value = "invalid"  # type: ignore[misc]
