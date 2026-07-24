from importlib import import_module
from types import ModuleType
from typing import Any, Literal
from unittest.mock import MagicMock

import pytest

from src.config.logging_config import (
    RequestContextVarsFilter,
    configure_logging,
)

LOGGING_CONFIG_MODULE: ModuleType = import_module(
    name="src.config.logging_config"
)


@pytest.mark.parametrize(
    argnames=("log_level", "sqlalchemy_log_level"),
    argvalues=[
        ("DEBUG", "INFO"),
        ("INFO", "WARNING"),
    ],
)
def test_configure_logging_builds_logging_configuration(
    log_level: Literal["DEBUG", "INFO"],
    sqlalchemy_log_level: Literal["WARNING", "INFO"],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Configure handlers and dependency log levels."""
    dict_config_mock: MagicMock = MagicMock()
    monkeypatch.setattr(
        target=LOGGING_CONFIG_MODULE.config,
        name="dictConfig",
        value=dict_config_mock,
    )

    configure_logging(log_level=log_level)

    logging_config: dict[str, Any] = dict_config_mock.call_args.kwargs[
        "config"
    ]

    dict_config_mock.assert_called_once_with(config=logging_config)
    assert logging_config["version"] == 1
    assert logging_config["disable_existing_loggers"] is False
    assert (
        logging_config["filters"]["request_context"]["()"]
        is RequestContextVarsFilter
    )
    assert "file" not in logging_config["handlers"]
    assert logging_config["root"] == {
        "handlers": ["console"],
        "level": log_level,
    }
    assert logging_config["loggers"]["uvicorn"]["handlers"] == ["console"]
    assert logging_config["loggers"]["uvicorn.error"]["handlers"] == [
        "console"
    ]
    assert logging_config["loggers"]["uvicorn.access"]["handlers"] == [
        "console"
    ]
    assert (
        logging_config["loggers"]["sqlalchemy.engine"]["level"]
        == sqlalchemy_log_level
    )
