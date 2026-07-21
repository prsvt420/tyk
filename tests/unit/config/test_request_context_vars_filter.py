from importlib import import_module
from logging import INFO, LogRecord
from types import ModuleType
from unittest.mock import MagicMock

import pytest

from src.config.logging_config import RequestContextVarsFilter

LOGGING_CONFIG_MODULE: ModuleType = import_module(
    name="src.config.logging_config"
)


@pytest.mark.parametrize(
    argnames="request_id",
    argvalues=[
        None,
        "request-1",
    ],
)
def test_request_context_vars_filter_adds_available_context(
    request_id: str | None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Add only available request context values to a log record."""
    request_id_context_var_mock: MagicMock = MagicMock()
    request_id_context_var_mock.get.return_value = request_id
    monkeypatch.setattr(
        target=LOGGING_CONFIG_MODULE,
        name="request_id_context_var",
        value=request_id_context_var_mock,
    )
    record: LogRecord = LogRecord(
        name="test",
        level=INFO,
        pathname=__file__,
        lineno=1,
        msg="Test log record.",
        args=(),
        exc_info=None,
    )
    request_context_vars_filter: RequestContextVarsFilter = (
        RequestContextVarsFilter()
    )

    filter_result: bool = request_context_vars_filter.filter(record=record)

    assert filter_result is True
    request_id_context_var_mock.get.assert_called_once_with()

    if request_id is None:
        assert "request_id" not in record.__dict__
    else:
        assert record.__dict__["request_id"] == request_id
