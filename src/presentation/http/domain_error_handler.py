from typing import cast

from fastapi import Request, status
from fastapi.responses import JSONResponse

from src.domain.exceptions import DomainError


async def domain_error_handler(
    request: Request,
    error: Exception,
) -> JSONResponse:
    """Convert domain error to HTTP response."""
    domain_error: DomainError = cast(DomainError, error)

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={"detail": str(domain_error)},
    )
