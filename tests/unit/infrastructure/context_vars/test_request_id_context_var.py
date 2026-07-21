from contextvars import Context, Token

from src.infrastructure.context_vars.request_id_context_var import (
    RequestIDContextVar,
)


def test_request_id_context_var_returns_none_by_default() -> None:
    """Return None before a request ID is assigned."""
    request_id_context_var: RequestIDContextVar = RequestIDContextVar()

    assert request_id_context_var.get() is None


def test_request_id_context_var_sets_and_restores_values() -> None:
    """Restore request IDs in reverse token order."""
    request_id_context_var: RequestIDContextVar = RequestIDContextVar()
    first_token: Token[str | None] = request_id_context_var.set(
        request_id="request-1"
    )
    second_token: Token[str | None] = request_id_context_var.set(
        request_id="request-2"
    )

    assert request_id_context_var.get() == "request-2"

    request_id_context_var.reset(token=second_token)

    assert request_id_context_var.get() == "request-1"

    request_id_context_var.reset(token=first_token)

    assert request_id_context_var.get() is None


def test_request_id_context_var_isolates_execution_contexts() -> None:
    """Keep request IDs isolated between execution contexts."""
    request_id_context_var: RequestIDContextVar = RequestIDContextVar()
    request_context: Context = Context()

    request_context.run(request_id_context_var.set, "request-1")

    assert request_id_context_var.get() is None
    assert request_context.run(request_id_context_var.get) == "request-1"
