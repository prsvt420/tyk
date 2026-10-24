from importlib import import_module
from types import ModuleType
from unittest.mock import MagicMock, call

import pytest
from fastapi import FastAPI

from src.config.app_settings import AppSettings
from src.domain.exceptions import DomainError
from src.main import create_app, lifespan
from src.presentation.http import domain_error_handler
from src.presentation.http.api.v1 import api_v1_router
from src.presentation.http.middlewares import (
    RequestIDMiddleware,
    RequestLoggingMiddleware,
)
from src.presentation.http.operational import probe_router
from src.presentation.http.public import short_link_redirect_router

MAIN_MODULE: ModuleType = import_module(name="src.main")


def test_create_app_configures_fastapi(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Create a FastAPI app with configured HTTP components."""
    app_settings: AppSettings = AppSettings.model_validate(
        obj={
            "app_debug": True,
            "app_title": "Test app",
            "app_version": "1.2.3",
            "log_level": "DEBUG",
            "app_description": "Test description",
            "public_base_url": "https://example.com",
            "database_url": (
                "postgresql+asyncpg://user:password@localhost:5432/tyk"
            ),
            "cache_url": "redis://localhost:6379/0",
        }
    )
    app_mock: MagicMock = MagicMock(spec=FastAPI)
    fastapi_mock: MagicMock = MagicMock(return_value=app_mock)
    configure_logging_mock: MagicMock = MagicMock()
    monkeypatch.setattr(
        target=MAIN_MODULE,
        name="app_settings",
        value=app_settings,
    )
    monkeypatch.setattr(
        target=MAIN_MODULE,
        name="FastAPI",
        value=fastapi_mock,
    )
    monkeypatch.setattr(
        target=MAIN_MODULE,
        name="configure_logging",
        value=configure_logging_mock,
    )

    app: FastAPI = create_app()

    assert app is app_mock
    configure_logging_mock.assert_called_once_with(log_level="DEBUG")
    fastapi_mock.assert_called_once_with(
        debug=True,
        title="Test app",
        version="1.2.3",
        description="Test description",
        lifespan=lifespan,
    )
    assert app_mock.include_router.call_args_list == [
        call(router=probe_router),
        call(router=short_link_redirect_router),
        call(router=api_v1_router, prefix="/api/v1"),
    ]
    app_mock.add_exception_handler.assert_called_once_with(
        exc_class_or_status_code=DomainError,
        handler=domain_error_handler,
    )
    assert app_mock.add_middleware.call_args_list == [
        call(middleware_class=RequestLoggingMiddleware),
        call(middleware_class=RequestIDMiddleware),
    ]
