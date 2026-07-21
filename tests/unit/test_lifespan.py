from importlib import import_module
from logging import Logger
from types import ModuleType
from unittest.mock import AsyncMock, MagicMock, call

import pytest
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncEngine

from src.main import lifespan

MAIN_MODULE: ModuleType = import_module(name="src.main")


@pytest.mark.anyio
async def test_lifespan_logs_and_disposes_database_engine(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Log application lifetime and dispose the database engine."""
    app: FastAPI = FastAPI(
        debug=True,
        title="Test application",
        version="1.2.3",
    )
    dispose_mock: AsyncMock = AsyncMock()
    async_engine_mock: MagicMock = MagicMock(spec=AsyncEngine)
    async_engine_mock.dispose = dispose_mock
    monotonic_mock: MagicMock = MagicMock(side_effect=[1.0, 3.3456])
    logger_mock: MagicMock = MagicMock(spec=Logger)
    monkeypatch.setattr(
        target=MAIN_MODULE,
        name="async_engine",
        value=async_engine_mock,
    )
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
        dispose_mock.assert_not_awaited()

    dispose_mock.assert_awaited_once_with()
    assert logger_mock.info.call_args_list == [
        call(
            msg="Application started.",
            extra={
                "event": "application_started",
                "debug": True,
                "title": "Test application",
                "version": "1.2.3",
            },
        ),
        call(
            msg="Application stopped.",
            extra={
                "event": "application_stopped",
                "uptime_seconds": 2.346,
            },
        ),
    ]
