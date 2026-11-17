from datetime import datetime, timezone
from typing import cast
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest
from asyncpg import UniqueViolationError
from sqlalchemy import ScalarResult
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.exceptions import EmailAlreadyExistsError
from src.domain.entities import User
from src.domain.value_objects import Email
from src.infrastructure.database.model_mappers import UserModelMapper
from src.infrastructure.database.models import UserModel
from src.infrastructure.repositories.postgresql_user_repository import (
    PostgreSQLUserRepository,
)

STORED_HASH: str = "stored-test-hash"


def _create_user() -> User:
    """Create deterministic user data for repository tests."""
    return User(
        id=UUID(hex="4f4c2514-26b0-4c75-a77b-130e7858024e"),
        email=Email(value="user@example.com"),
        password=STORED_HASH,
        is_active=False,
        created_at=datetime(year=2030, month=1, day=1, tzinfo=timezone.utc),
        updated_at=datetime(year=2030, month=1, day=2, tzinfo=timezone.utc),
    )


def _create_repository(
    session: MagicMock,
) -> PostgreSQLUserRepository:
    """Wrap a mocked session with the repository adapter."""
    return PostgreSQLUserRepository(
        database_async_session=cast(AsyncSession, session)
    )


@pytest.mark.anyio
async def test_user_repository_saves_user_in_transaction() -> None:
    """Persist every user field and complete the transaction."""
    session: MagicMock = MagicMock(spec=AsyncSession)
    user: User = _create_user()

    await _create_repository(session=session).save(user=user)

    model: UserModel = session.add.call_args.kwargs["instance"]
    assert UserModelMapper.to_entity(user_model=model) == user
    session.add.assert_called_once()
    session.flush.assert_awaited_once_with()
    transaction: MagicMock = session.begin.return_value
    transaction.__aenter__.assert_awaited_once()
    transaction.__aexit__.assert_awaited_once_with(None, None, None)


@pytest.mark.anyio
@pytest.mark.parametrize(
    argnames="origin_kind",
    argvalues=["email", "primary_key", "other", "no_cause", "no_origin"],
)
async def test_user_repository_translates_only_email_conflict(
    origin_kind: str,
) -> None:
    """Translate email conflicts and preserve other integrity errors."""
    origin: Exception | None = Exception()
    if origin_kind in {"email", "primary_key"}:
        assert origin is not None
        cause: UniqueViolationError = UniqueViolationError()
        cause.constraint_name = (
            "uq_users_email" if origin_kind == "email" else "pk_users"
        )
        origin.__cause__ = cause
    elif origin_kind == "other":
        assert origin is not None
        origin.__cause__ = ValueError("Other database failure.")
    elif origin_kind == "no_origin":
        origin = None
    error: IntegrityError = IntegrityError(
        statement=None, params=None, orig=cast(BaseException, origin)
    )
    session: MagicMock = MagicMock(spec=AsyncSession)
    session.flush = AsyncMock(side_effect=error)
    expected: type[Exception] = (
        EmailAlreadyExistsError if origin_kind == "email" else IntegrityError
    )

    with pytest.raises(expected_exception=expected) as caught:
        await _create_repository(session=session).save(user=_create_user())

    if origin_kind == "email":
        assert caught.value.__cause__ is error
    else:
        assert caught.value is error
    session.begin.return_value.__aexit__.assert_awaited_once()
    assert session.begin.return_value.__aexit__.call_args.args[1] is error


@pytest.mark.anyio
async def test_user_repository_preserves_save_failure() -> None:
    """Propagate unexpected storage failures without translating them."""
    session: MagicMock = MagicMock(spec=AsyncSession)
    error: RuntimeError = RuntimeError("Database unavailable.")
    session.flush = AsyncMock(side_effect=error)

    with pytest.raises(expected_exception=RuntimeError) as caught:
        await _create_repository(session=session).save(user=_create_user())

    assert caught.value is error


@pytest.mark.anyio
@pytest.mark.parametrize(argnames="lookup", argvalues=["id", "email"])
@pytest.mark.parametrize(argnames="exists", argvalues=[False, True])
async def test_user_repository_queries_matching_user(
    lookup: str,
    exists: bool,
) -> None:
    """Filter by the requested identifier and map a result or return None."""
    user: User = _create_user()
    rows: MagicMock = MagicMock(spec=ScalarResult)
    rows.one_or_none.return_value = (
        UserModelMapper.to_model(user=user) if exists else None
    )
    session: MagicMock = MagicMock(spec=AsyncSession)
    session.scalars = AsyncMock(return_value=rows)
    repository: PostgreSQLUserRepository = _create_repository(session=session)

    result: User | None
    if lookup == "id":
        result = await repository.get_by_id(id=user.id)
    else:
        result = await repository.get_by_email(email=user.email)

    assert result == (user if exists else None)
    session.scalars.assert_awaited_once()
    statement = session.scalars.call_args.kwargs["statement"]
    compiled = statement.compile()
    assert f"users.{lookup} =" in str(compiled)
    assert list(compiled.params.values()) == [
        user.id if lookup == "id" else user.email.value
    ]
    rows.one_or_none.assert_called_once_with()


@pytest.mark.anyio
@pytest.mark.parametrize(argnames="lookup", argvalues=["id", "email"])
async def test_user_repository_preserves_query_failure(lookup: str) -> None:
    """Keep failed reads distinct from an absent user."""
    session: MagicMock = MagicMock(spec=AsyncSession)
    error: RuntimeError = RuntimeError("Query failed.")
    session.scalars = AsyncMock(side_effect=error)
    repository: PostgreSQLUserRepository = _create_repository(session=session)
    user: User = _create_user()

    with pytest.raises(expected_exception=RuntimeError) as caught:
        if lookup == "id":
            await repository.get_by_id(id=user.id)
        else:
            await repository.get_by_email(email=user.email)

    assert caught.value is error
