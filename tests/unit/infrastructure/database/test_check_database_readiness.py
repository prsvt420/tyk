from importlib import import_module
from types import ModuleType
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.sql.elements import TextClause

from src.infrastructure.database import check_database_readiness

CHECK_DATABASE_READINESS_MODULE: ModuleType = import_module(
    name="src.infrastructure.database.check_database_readiness"
)


def _create_async_engine_mock(
    *, execute_error: BaseException | None = None
) -> tuple[MagicMock, MagicMock]:
    """Create an engine mock with an asynchronous connection."""
    database_async_connection_mock: MagicMock = MagicMock()
    database_async_connection_mock.execute = AsyncMock(
        side_effect=execute_error
    )
    database_connection_context_mock: MagicMock = MagicMock()
    database_connection_context_mock.__aenter__ = AsyncMock(
        return_value=database_async_connection_mock
    )
    database_connection_context_mock.__aexit__ = AsyncMock(return_value=None)
    database_async_engine_mock: MagicMock = MagicMock(spec=AsyncEngine)
    database_async_engine_mock.connect.return_value = (
        database_connection_context_mock
    )

    return database_async_engine_mock, database_async_connection_mock


@pytest.mark.anyio
async def test_check_database_readiness_returns_true(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Return True when the database executes a probe query."""
    database_async_engine_mock: MagicMock
    database_async_connection_mock: MagicMock
    database_async_engine_mock, database_async_connection_mock = (
        _create_async_engine_mock()
    )

    monkeypatch.setattr(
        target=CHECK_DATABASE_READINESS_MODULE,
        name="database_async_engine",
        value=database_async_engine_mock,
    )

    database_ready: bool = await check_database_readiness()

    statement: TextClause = (
        database_async_connection_mock.execute.await_args.kwargs["statement"]
    )

    assert database_ready is True
    assert str(statement) == "SELECT 1"
    database_async_engine_mock.connect.assert_called_once_with()
    database_async_connection_mock.execute.assert_awaited_once()


@pytest.mark.anyio
@pytest.mark.parametrize(
    argnames="execute_error",
    argvalues=[
        SQLAlchemyError(),
        TimeoutError(),
    ],
)
async def test_check_database_readiness_returns_false(
    execute_error: BaseException,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Return False when the database probe fails or times out."""
    database_async_engine_mock: MagicMock
    database_async_connection_mock: MagicMock
    database_async_engine_mock, database_async_connection_mock = (
        _create_async_engine_mock(execute_error=execute_error)
    )

    monkeypatch.setattr(
        target=CHECK_DATABASE_READINESS_MODULE,
        name="database_async_engine",
        value=database_async_engine_mock,
    )

    database_ready: bool = await check_database_readiness()

    assert database_ready is False
    database_async_connection_mock.execute.assert_awaited_once()
