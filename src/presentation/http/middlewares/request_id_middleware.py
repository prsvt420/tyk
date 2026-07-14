from contextvars import Token
from uuid import uuid4

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from src.infrastructure.context_vars import request_id_context_var


class RequestIDMiddleware:
    """Add a unique request ID to HTTP requests and responses."""

    def __init__(self, app: ASGIApp) -> None:
        self._app = app

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        """Set the request ID context for an HTTP request."""
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return

        request_id: str = str(uuid4())
        token: Token[str | None] = request_id_context_var.set(
            request_id=request_id
        )

        async def send_with_request_id(message: Message) -> None:
            if message["type"] == "http.response.start":
                mutable_headers: MutableHeaders = MutableHeaders(scope=message)
                mutable_headers["X-Request-ID"] = request_id

            await send(message)

        try:
            await self._app(scope, receive, send_with_request_id)
        finally:
            request_id_context_var.reset(token=token)
