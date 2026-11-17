from logging import INFO
from typing import cast
from unittest.mock import AsyncMock, create_autospec
from uuid import UUID

import pytest

from src.application.dtos import CreateUserDTO, UserDTO
from src.application.interfaces import (
    PasswordHasherInterface,
    UserRepositoryInterface,
)
from src.application.use_cases import CreateUserUseCase
from src.domain.entities import User
from src.domain.exceptions import InvalidEmailError, InvalidPasswordError

LOGGER_NAME: str = "src.application.use_cases.create_user_use_case"
RAW_VALUE: str = "Example123!"
HASH_VALUE: str = "stored-test-hash"


@pytest.fixture
def repository() -> UserRepositoryInterface:
    """Create an isolated repository mock matching the interface."""
    return cast(
        UserRepositoryInterface,
        create_autospec(spec=UserRepositoryInterface, instance=True),
    )


@pytest.fixture
def hasher() -> PasswordHasherInterface:
    """Create an isolated hasher mock matching the interface."""
    mock = create_autospec(spec=PasswordHasherInterface, instance=True)
    mock.hash.return_value = HASH_VALUE
    return cast(PasswordHasherInterface, mock)


@pytest.mark.anyio
async def test_create_user_persists_hashed_credentials(
    repository: UserRepositoryInterface,
    hasher: PasswordHasherInterface,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Normalize email, persist a hash and return the saved user data."""
    use_case: CreateUserUseCase = CreateUserUseCase(
        user_repository=repository, password_hasher=hasher
    )
    with caplog.at_level(level=INFO, logger=LOGGER_NAME):
        result: UserDTO = await use_case.execute(
            create_user_dto=CreateUserDTO(
                email="User@EXAMPLE.COM", password=RAW_VALUE
            )
        )

    assert isinstance(hasher.hash, AsyncMock)
    assert isinstance(repository.save, AsyncMock)
    hasher.hash.assert_awaited_once_with(password=RAW_VALUE)
    repository.save.assert_awaited_once()
    saved: User = repository.save.call_args.kwargs["user"]
    assert isinstance(saved.id, UUID)
    assert saved.id.version == 4
    assert saved.email.value == "User@example.com"
    assert saved.password == HASH_VALUE
    assert saved.password != RAW_VALUE
    assert result.id == saved.id
    assert result.email == saved.email.value
    assert result.created_at == saved.created_at
    assert result.updated_at == saved.updated_at
    assert result.is_active is True
    assert result.last_login_at is None
    assert result.deleted_at is None
    assert caplog.messages == ["User created."]
    assert caplog.records[0].__dict__["user_id"] == str(saved.id)
    assert RAW_VALUE not in caplog.text
    assert HASH_VALUE not in caplog.text


@pytest.mark.anyio
@pytest.mark.parametrize(
    argnames=("email", "value", "error_type"),
    argvalues=[
        ("invalid", RAW_VALUE, InvalidEmailError),
        ("user@example.com", "short", InvalidPasswordError),
        ("user@example.com", "a" * 129, InvalidPasswordError),
    ],
)
async def test_create_user_rejects_invalid_data_before_dependencies(
    repository: UserRepositoryInterface,
    hasher: PasswordHasherInterface,
    email: str,
    value: str,
    error_type: type[Exception],
) -> None:
    """Avoid hashing and saving when domain validation fails."""
    use_case: CreateUserUseCase = CreateUserUseCase(
        user_repository=repository, password_hasher=hasher
    )
    with pytest.raises(expected_exception=error_type):
        await use_case.execute(
            create_user_dto=CreateUserDTO(email=email, password=value)
        )

    assert isinstance(hasher.hash, AsyncMock)
    assert isinstance(repository.save, AsyncMock)
    hasher.hash.assert_not_awaited()
    repository.save.assert_not_awaited()


@pytest.mark.anyio
@pytest.mark.parametrize(argnames="failure_source", argvalues=["hash", "save"])
async def test_create_user_propagates_dependency_failure(
    repository: UserRepositoryInterface,
    hasher: PasswordHasherInterface,
    caplog: pytest.LogCaptureFixture,
    failure_source: str,
) -> None:
    """Preserve dependency failures and avoid logging successful creation."""
    error: RuntimeError = RuntimeError("Dependency failed.")
    assert isinstance(hasher.hash, AsyncMock)
    assert isinstance(repository.save, AsyncMock)
    target: AsyncMock = (
        hasher.hash if failure_source == "hash" else repository.save
    )
    target.side_effect = error
    use_case: CreateUserUseCase = CreateUserUseCase(
        user_repository=repository, password_hasher=hasher
    )
    with caplog.at_level(level=INFO, logger=LOGGER_NAME):
        with pytest.raises(expected_exception=RuntimeError) as caught:
            await use_case.execute(
                create_user_dto=CreateUserDTO(
                    email="user@example.com", password=RAW_VALUE
                )
            )

    assert caught.value is error
    hasher.hash.assert_awaited_once_with(password=RAW_VALUE)
    if failure_source == "hash":
        repository.save.assert_not_awaited()
    else:
        repository.save.assert_awaited_once()
    assert "User created." not in caplog.messages
