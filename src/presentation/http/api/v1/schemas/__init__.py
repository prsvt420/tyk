from typing import List

from src.presentation.http.api.v1.schemas.create_short_link_request_schema import (  # noqa: E501
    CreateShortLinkRequestSchema,
)
from src.presentation.http.api.v1.schemas.short_link_response_schema import (
    ShortLinkResponseSchema,
)

__all__: List[str] = [
    "CreateShortLinkRequestSchema",
    "ShortLinkResponseSchema",
]
