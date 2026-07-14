from contextvars import ContextVar, Token


class RequestIDContextVar:
    """Manage the request ID for the current execution context."""

    def __init__(self) -> None:
        self._request_id_context_var: ContextVar[str | None] = ContextVar(
            "request_id",
            default=None,
        )

    def get(
        self,
    ) -> str | None:
        """Return the current request ID."""
        return self._request_id_context_var.get()

    def set(self, request_id: str) -> Token[str | None]:
        """Set the current request ID."""
        return self._request_id_context_var.set(request_id)

    def reset(self, token: Token[str | None]) -> None:
        """Restore the previous request ID."""
        self._request_id_context_var.reset(token)


request_id_context_var: RequestIDContextVar = RequestIDContextVar()
