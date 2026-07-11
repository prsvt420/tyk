from typing import cast

from fastapi import Request, status
from fastapi.responses import JSONResponse

from src.domain.exceptions import DomainError


async def handle_domain_error(
    request: Request,
    error: Exception,
) -> JSONResponse:
    """Convert domain errors to HTTP responses."""
    domain_error: DomainError = cast(DomainError, error)

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": str(domain_error)},
    )
