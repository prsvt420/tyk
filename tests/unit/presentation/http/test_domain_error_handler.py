import json
from typing import cast
from unittest.mock import MagicMock

import pytest
from fastapi import Request, status
from fastapi.responses import JSONResponse

from src.domain.exceptions import InvalidOriginalURLError
from src.presentation.http import domain_error_handler


@pytest.mark.anyio
async def test_domain_error_handler_returns_unprocessable_entity() -> None:
    """Convert a domain error to a JSON response."""
    request: Request = cast(Request, MagicMock(spec=Request))
    error: InvalidOriginalURLError = InvalidOriginalURLError(
        "Original URL is invalid."
    )

    response: JSONResponse = await domain_error_handler(
        request=request,
        error=error,
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert json.loads(bytes(response.body)) == {
        "detail": "Original URL is invalid."
    }
