from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse

from src.application.dtos.short_link import ShortLinkDTO
from src.application.exceptions import (
    ShortLinkExpiredError,
    ShortLinkNotFoundError,
)
from src.application.use_cases.get_short_link_by_short_code import (
    GetShortLinkByShortCodeUseCase,
)
from src.domain.exceptions import InvalidShortCodeError
from src.presentation.api.dependencies import (
    provide_get_short_link_by_short_code_use_case,
)

router: APIRouter = APIRouter()


@router.get(
    path="/r/{short_code}",
    response_class=RedirectResponse,
    status_code=status.HTTP_307_TEMPORARY_REDIRECT,
)
async def redirect_short_link(
    short_code: str,
    use_case: Annotated[
        GetShortLinkByShortCodeUseCase,
        Depends(provide_get_short_link_by_short_code_use_case),
    ],
) -> RedirectResponse:
    """Redirect short link."""
    try:
        short_link_dto: ShortLinkDTO = await use_case.execute(
            short_code=short_code
        )
    except (InvalidShortCodeError, ShortLinkNotFoundError) as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Short link not found.",
        ) from error
    except ShortLinkExpiredError as error:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Short link has expired.",
        ) from error

    return RedirectResponse(
        url=short_link_dto.original_url,
        status_code=status.HTTP_307_TEMPORARY_REDIRECT,
    )
