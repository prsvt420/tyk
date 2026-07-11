from typing import List

from src.presentation.api.v1.schemas.create_short_link_request_schema import (
    CreateShortLinkRequestSchema,
)
from src.presentation.api.v1.schemas.short_link_response_schema import (
    ShortLinkResponseSchema,
)

__all__: List[str] = [
    "CreateShortLinkRequestSchema",
    "ShortLinkResponseSchema",
]
