from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from pydantic import HttpUrl

from src.application.dtos import (
    CreateShortLinkDTO,
    ShortLinkDTO,
)
from src.application.use_cases import CreateShortLinkUseCase
from src.config import application_settings
from src.presentation.http.api.v1.schemas import (
    CreateShortLinkRequestSchema,
    ShortLinkResponseSchema,
)
from src.presentation.http.dependencies import (
    provide_create_short_link_use_case,
)

short_link_router: APIRouter = APIRouter(tags=["short-links"])


@short_link_router.post(
    path="/short-links",
    response_model=ShortLinkResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_short_link(
    request: CreateShortLinkRequestSchema,
    response: Response,
    use_case: Annotated[
        CreateShortLinkUseCase,
        Depends(dependency=provide_create_short_link_use_case),
    ],
) -> ShortLinkResponseSchema:
    """Create short link."""
    short_link_dto: ShortLinkDTO = await use_case.execute(
        create_short_link_dto=CreateShortLinkDTO(
            original_url=str(request.original_url),
            expires_at=request.expires_at,
        )
    )

    short_link_url: HttpUrl = HttpUrl(
        f"{str(application_settings.public_base_url).rstrip('/')}"
        f"/r/{short_link_dto.short_code}"
    )

    response.headers["Location"] = str(short_link_url)

    return ShortLinkResponseSchema(
        id=short_link_dto.id,
        original_url=short_link_dto.original_url,
        short_code=short_link_dto.short_code,
        short_link_url=short_link_url,
        created_at=short_link_dto.created_at,
        expires_at=short_link_dto.expires_at,
    )
