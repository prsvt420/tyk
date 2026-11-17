from unittest.mock import patch

import pytest
from pwdlib import PasswordHash
from pwdlib.exceptions import (
    HashGenerationError,
    HashVerificationError,
    UnknownHashError,
)

from src.infrastructure.password_hashers import Argon2PasswordHasher

RAW_VALUE: str = "Example123!"
STORED_VALUE: str = "stored-hash"


@pytest.mark.anyio
@pytest.mark.parametrize(
    argnames="value",
    argvalues=[RAW_VALUE, "пароль123!", " leading and trailing spaces "],
)
async def test_hasher_round_trips_password(value: str) -> None:
    """Create an Argon2id hash that can be verified by another instance."""
    hasher: Argon2PasswordHasher = Argon2PasswordHasher()

    hashed_value: str = await hasher.hash(password=value)

    assert hashed_value.startswith("$argon2id$")
    assert hashed_value != value
    assert await Argon2PasswordHasher().verify(
        password=value, hashed_password=hashed_value
    )


@pytest.mark.anyio
async def test_hasher_uses_random_salts() -> None:
    """Produce different valid hashes for the same input."""
    hasher: Argon2PasswordHasher = Argon2PasswordHasher()

    first: str = await hasher.hash(password=RAW_VALUE)
    second: str = await hasher.hash(password=RAW_VALUE)

    assert first != second
    assert await hasher.verify(password=RAW_VALUE, hashed_password=first)
    assert await hasher.verify(password=RAW_VALUE, hashed_password=second)


@pytest.mark.anyio
async def test_hasher_rejects_different_password() -> None:
    """Return false for a mismatch without modifying or trimming input."""
    hasher: Argon2PasswordHasher = Argon2PasswordHasher()
    hashed_value: str = await hasher.hash(password=RAW_VALUE)

    assert not await hasher.verify(
        password=RAW_VALUE.lower(), hashed_password=hashed_value
    )
    assert not await hasher.verify(
        password=f" {RAW_VALUE} ", hashed_password=hashed_value
    )


@pytest.mark.anyio
@pytest.mark.parametrize(argnames="hashed_value", argvalues=["", "invalid"])
async def test_hasher_rejects_unknown_hash(hashed_value: str) -> None:
    """Keep an unrecognized stored hash distinct from a password mismatch."""
    hasher: Argon2PasswordHasher = Argon2PasswordHasher()

    with pytest.raises(expected_exception=UnknownHashError):
        await hasher.verify(password=RAW_VALUE, hashed_password=hashed_value)


@pytest.mark.anyio
@pytest.mark.parametrize(argnames="operation", argvalues=["hash", "verify"])
async def test_hasher_propagates_backend_errors(operation: str) -> None:
    """Preserve backend failures instead of treating them as mismatches."""
    hasher: Argon2PasswordHasher = Argon2PasswordHasher()
    error: Exception = (
        HashGenerationError()
        if operation == "hash"
        else HashVerificationError()
    )

    with patch.object(
        target=PasswordHash,
        attribute=operation,
        side_effect=error,
    ):
        with pytest.raises(expected_exception=type(error)) as caught:
            if operation == "hash":
                await hasher.hash(password=RAW_VALUE)
            else:
                await hasher.verify(
                    password=RAW_VALUE, hashed_password=STORED_VALUE
                )

    assert caught.value is error
