from contextvars import Token
from uuid import UUID

import pytest
from starlette.datastructures import MutableHeaders
from starlette.types import Message, Receive, Scope, Send

from src.infrastructure.context_vars import request_id_context_var
from src.presentation.http.middlewares import RequestIDMiddleware


def _create_http_scope() -> Scope:
    """Create a minimal HTTP scope."""
    return {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.3"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": "/test",
        "raw_path": b"/test",
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


@pytest.mark.anyio
async def test_request_id_middleware_adds_request_id() -> None:
    """Expose one request ID to the app and response."""
    observed_request_id: str | None = None
    sent_messages: list[Message] = []

    async def app(
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        """Observe the context and return an empty response."""
        nonlocal observed_request_id
        observed_request_id = request_id_context_var.get()
        await send(
            {
                "type": "http.response.start",
                "status": 204,
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

    middleware: RequestIDMiddleware = RequestIDMiddleware(app=app)

    await middleware(
        scope=_create_http_scope(),
        receive=_receive,
        send=send,
    )

    response_headers: MutableHeaders = MutableHeaders(scope=sent_messages[0])
    response_request_id: str = response_headers["X-Request-ID"]

    assert observed_request_id == response_request_id
    assert str(UUID(hex=response_request_id)) == response_request_id
    assert sent_messages[1]["type"] == "http.response.body"
    assert request_id_context_var.get() is None


@pytest.mark.anyio
async def test_request_id_middleware_bypasses_non_http_scope() -> None:
    """Pass a non-HTTP scope directly to the wrapped app."""
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

    middleware: RequestIDMiddleware = RequestIDMiddleware(app=app)

    await middleware(
        scope=scope,
        receive=_receive,
        send=send,
    )

    assert observed_scope is scope
    assert request_id_context_var.get() is None


@pytest.mark.anyio
async def test_request_id_middleware_restores_context_after_error() -> None:
    """Restore the previous request ID when the wrapped app fails."""
    previous_token: Token[str | None] = request_id_context_var.set(
        request_id="outer-request"
    )
    observed_request_id: str | None = None

    async def app(
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        """Observe a new request ID and fail."""
        nonlocal observed_request_id
        observed_request_id = request_id_context_var.get()
        raise RuntimeError("Request failed.")

    async def send(message: Message) -> None:
        """Accept an unused response message."""

    middleware: RequestIDMiddleware = RequestIDMiddleware(app=app)

    try:
        with pytest.raises(
            expected_exception=RuntimeError,
            match=r"^Request failed\.$",
        ):
            await middleware(
                scope=_create_http_scope(),
                receive=_receive,
                send=send,
            )

        assert observed_request_id is not None
        assert observed_request_id != "outer-request"
        assert request_id_context_var.get() == "outer-request"
    finally:
        request_id_context_var.reset(token=previous_token)
