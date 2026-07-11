from typing import Annotated

from fastapi import APIRouter, Depends, status

from src.application.dtos import (
    CreateShortLinkDTO,
    ShortLinkDTO,
)
from src.application.use_cases import CreateShortLinkUseCase
from src.presentation.api.dependencies import (
    provide_create_short_link_use_case,
)
from src.presentation.api.v1.schemas import (
    CreateShortLinkRequestSchema,
    ShortLinkResponseSchema,
)

router: APIRouter = APIRouter()


@router.post(
    path="/short-links",
    response_model=ShortLinkResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_short_link(
    request: CreateShortLinkRequestSchema,
    use_case: Annotated[
        CreateShortLinkUseCase,
        Depends(provide_create_short_link_use_case),
    ],
) -> ShortLinkResponseSchema:
    """Create short link."""
    short_link_dto: ShortLinkDTO = await use_case.execute(
        create_short_link_dto=CreateShortLinkDTO(
            original_url=str(request.original_url),
            expires_at=request.expires_at,
        )
    )

    return ShortLinkResponseSchema(
        id=short_link_dto.id,
        original_url=short_link_dto.original_url,
        short_code=short_link_dto.short_code,
        created_at=short_link_dto.created_at,
        expires_at=short_link_dto.expires_at,
    )
