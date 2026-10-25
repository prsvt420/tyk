from importlib import import_module
from logging import Logger
from types import ModuleType
from unittest.mock import AsyncMock, MagicMock, call

import pytest
from fastapi import FastAPI
from redis.asyncio import Redis as AsyncRedis
from sqlalchemy.ext.asyncio import AsyncEngine

from src.main import lifespan

MAIN_MODULE: ModuleType = import_module(name="src.main")


def _mock_lifespan_resources(
    monkeypatch: pytest.MonkeyPatch,
    *,
    cache_close_error: Exception | None = None,
) -> tuple[AsyncMock, AsyncMock]:
    """Replace shared resources with isolated asynchronous mocks."""
    cache_aclose_mock: AsyncMock = AsyncMock(side_effect=cache_close_error)
    cache_async_client_mock: MagicMock = MagicMock(spec=AsyncRedis)
    cache_async_client_mock.aclose = cache_aclose_mock
    database_dispose_mock: AsyncMock = AsyncMock()
    database_async_engine_mock: MagicMock = MagicMock(spec=AsyncEngine)
    database_async_engine_mock.dispose = database_dispose_mock
    monkeypatch.setattr(
        target=MAIN_MODULE,
        name="cache_async_client",
        value=cache_async_client_mock,
    )
    monkeypatch.setattr(
        target=MAIN_MODULE,
        name="database_async_engine",
        value=database_async_engine_mock,
    )

    return cache_aclose_mock, database_dispose_mock


@pytest.mark.anyio
async def test_lifespan_logs_and_closes_resources(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Log app lifetime and close shared resources only during shutdown."""
    app: FastAPI = FastAPI(
        debug=True,
        title="Test app",
        version="1.2.3",
    )
    cache_aclose_mock, database_dispose_mock = _mock_lifespan_resources(
        monkeypatch=monkeypatch
    )
    monotonic_mock: MagicMock = MagicMock(side_effect=[1.0, 3.3456])
    logger_mock: MagicMock = MagicMock(spec=Logger)
    monkeypatch.setattr(
        target=MAIN_MODULE,
        name="monotonic",
        value=monotonic_mock,
    )
    monkeypatch.setattr(
        target=MAIN_MODULE,
        name="logger",
        value=logger_mock,
    )

    async with lifespan(app=app):
        cache_aclose_mock.assert_not_awaited()
        database_dispose_mock.assert_not_awaited()

    cache_aclose_mock.assert_awaited_once_with()
    database_dispose_mock.assert_awaited_once_with()
    assert logger_mock.info.call_args_list == [
        call(
            msg="App started.",
            extra={
                "event": "app_started",
                "debug": True,
                "title": "Test app",
                "version": "1.2.3",
            },
        ),
        call(
            msg="App stopped.",
            extra={
                "event": "app_stopped",
                "uptime_seconds": 2.346,
            },
        ),
    ]


@pytest.mark.anyio
async def test_lifespan_closes_resources_after_body_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Close both resources and preserve an error from the running app."""
    app: FastAPI = FastAPI()
    cache_aclose_mock, database_dispose_mock = _mock_lifespan_resources(
        monkeypatch=monkeypatch
    )
    body_error: RuntimeError = RuntimeError("App operation failed.")

    with pytest.raises(expected_exception=RuntimeError) as exception_info:
        async with lifespan(app=app):
            cache_aclose_mock.assert_not_awaited()
            database_dispose_mock.assert_not_awaited()
            raise body_error

    assert exception_info.value is body_error
    cache_aclose_mock.assert_awaited_once_with()
    database_dispose_mock.assert_awaited_once_with()


@pytest.mark.anyio
async def test_lifespan_preserves_cache_close_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Preserve a Redis close error after disposing the database."""
    app: FastAPI = FastAPI()
    cache_close_error: RuntimeError = RuntimeError("Cache close failed.")
    cache_aclose_mock, database_dispose_mock = _mock_lifespan_resources(
        monkeypatch=monkeypatch,
        cache_close_error=cache_close_error,
    )

    with pytest.raises(expected_exception=RuntimeError) as exception_info:
        async with lifespan(app=app):
            cache_aclose_mock.assert_not_awaited()
            database_dispose_mock.assert_not_awaited()

    assert exception_info.value is cache_close_error
    cache_aclose_mock.assert_awaited_once_with()
    database_dispose_mock.assert_awaited_once_with()
