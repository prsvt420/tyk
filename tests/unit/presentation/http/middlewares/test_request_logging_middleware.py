from importlib import import_module
from logging import ERROR, INFO, LogRecord
from types import ModuleType
from unittest.mock import MagicMock

import pytest
from starlette.types import Message, Receive, Scope, Send

from src.presentation.http.middlewares import RequestLoggingMiddleware

LOGGER_NAME: str = (
    "src.presentation.http.middlewares.request_logging_middleware"
)
REQUEST_LOGGING_MIDDLEWARE_MODULE: ModuleType = import_module(name=LOGGER_NAME)


def _create_http_scope() -> Scope:
    """Create a minimal HTTP scope."""
    return {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.3"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": "/api/v1/short-links",
        "raw_path": b"/api/v1/short-links",
        "query_string": b"",
        "root_path": "",
        "headers": [],
        "client": ("127.0.0.1", 12345),
        "server": ("test", 80),
    }


async def _receive() -> Message:
    """Return an empty HTTP request."""
    return {
        "type": "http.request",
        "body": b"",
        "more_body": False,
    }


def _patch_timer(monkeypatch: pytest.MonkeyPatch) -> None:
    """Provide deterministic start and finish timestamps."""
    perf_counter_ns_mock: MagicMock = MagicMock(
        side_effect=[1_000_000, 3_345_000]
    )
    monkeypatch.setattr(
        target=REQUEST_LOGGING_MIDDLEWARE_MODULE,
        name="perf_counter_ns",
        value=perf_counter_ns_mock,
    )


@pytest.mark.anyio
async def test_request_logging_middleware_logs_completed_request(
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Log a completed HTTP request with status and duration."""
    sent_messages: list[Message] = []

    async def app(
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        """Return an empty created response."""
        await send(
            {
                "type": "http.response.start",
                "status": 201,
                "headers": [],
            }
        )
        await send(
            {
                "type": "http.response.body",
                "body": b"",
                "more_body": False,
            }
        )

    async def send(message: Message) -> None:
        """Capture a response message."""
        sent_messages.append(message)

    _patch_timer(monkeypatch=monkeypatch)
    middleware: RequestLoggingMiddleware = RequestLoggingMiddleware(app=app)

    with caplog.at_level(level=INFO, logger=LOGGER_NAME):
        await middleware(
            scope=_create_http_scope(),
            receive=_receive,
            send=send,
        )

    record: LogRecord = caplog.records[0]

    assert record.getMessage() == "HTTP request completed."
    assert record.__dict__["event"] == "http_request_completed"
    assert record.__dict__["method"] == "POST"
    assert record.__dict__["path"] == "/api/v1/short-links"
    assert record.__dict__["status_code"] == 201
    assert record.__dict__["duration_ms"] == 2.345
    assert [message["type"] for message in sent_messages] == [
        "http.response.start",
        "http.response.body",
    ]


@pytest.mark.anyio
async def test_request_logging_middleware_bypasses_non_http_scope(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Pass a non-HTTP scope without logging it."""
    observed_scope: Scope | None = None
    scope: Scope = {
        "type": "lifespan",
        "asgi": {"version": "3.0", "spec_version": "2.0"},
        "state": {},
    }

    async def app(
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        """Capture the delegated scope."""
        nonlocal observed_scope
        observed_scope = scope

    async def send(message: Message) -> None:
        """Accept an unused response message."""

    middleware: RequestLoggingMiddleware = RequestLoggingMiddleware(app=app)

    with caplog.at_level(level=INFO, logger=LOGGER_NAME):
        await middleware(
            scope=scope,
            receive=_receive,
            send=send,
        )

    assert observed_scope is scope
    assert caplog.records == []


@pytest.mark.anyio
@pytest.mark.parametrize(
    argnames=("response_status_code", "logged_status_code"),
    argvalues=[
        (None, 500),
        (418, 418),
    ],
)
async def test_request_logging_middleware_logs_failed_request(
    response_status_code: int | None,
    logged_status_code: int,
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Log and propagate an HTTP request failure."""

    async def app(
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        """Optionally start a response and fail."""
        if response_status_code is not None:
            await send(
                {
                    "type": "http.response.start",
                    "status": response_status_code,
                    "headers": [],
                }
            )
        raise RuntimeError("Request failed.")

    async def send(message: Message) -> None:
        """Accept a response message."""

    _patch_timer(monkeypatch=monkeypatch)
    middleware: RequestLoggingMiddleware = RequestLoggingMiddleware(app=app)

    with caplog.at_level(level=ERROR, logger=LOGGER_NAME):
        with pytest.raises(
            expected_exception=RuntimeError,
            match=r"^Request failed\.$",
        ):
            await middleware(
                scope=_create_http_scope(),
                receive=_receive,
                send=send,
            )

    record: LogRecord = caplog.records[0]

    assert record.getMessage() == "HTTP request failed."
    assert record.__dict__["event"] == "http_request_failed"
    assert record.__dict__["method"] == "POST"
    assert record.__dict__["path"] == "/api/v1/short-links"
    assert record.__dict__["status_code"] == logged_status_code
    assert record.__dict__["duration_ms"] == 2.345
    assert record.__dict__["exception_type"] == "RuntimeError"
    assert record.exc_info is not None
