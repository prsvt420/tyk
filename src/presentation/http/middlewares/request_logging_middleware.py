from logging import Logger, getLogger
from time import perf_counter_ns

from starlette.types import ASGIApp, Message, Receive, Scope, Send

logger: Logger = getLogger(name=__name__)


class RequestLoggingMiddleware:
    """Log HTTP request completion and duration."""

    def __init__(self, app: ASGIApp) -> None:
        self._app = app

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        """Log an HTTP request outcome and duration."""
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return

        started_at_ns: int = perf_counter_ns()
        status_code: int | None = None

        async def send_with_status_code(message: Message) -> None:
            nonlocal status_code

            if message["type"] == "http.response.start":
                status_code = int(message["status"])

            await send(message)

        def get_duration_ms() -> float:
            return round(
                (perf_counter_ns() - started_at_ns) / 1_000_000,
                3,
            )

        try:
            await self._app(scope, receive, send_with_status_code)
        except Exception as error:
            logger.exception(
                msg="HTTP request failed.",
                extra={
                    "event": "http_request_failed",
                    "method": scope["method"],
                    "path": scope["path"],
                    "status_code": status_code or 500,
                    "duration_ms": get_duration_ms(),
                    "exception_type": type(error).__name__,
                },
            )
            raise
        else:
            logger.info(
                msg="HTTP request completed.",
                extra={
                    "event": "http_request_completed",
                    "method": scope["method"],
                    "path": scope["path"],
                    "status_code": status_code,
                    "duration_ms": get_duration_ms(),
                },
            )
