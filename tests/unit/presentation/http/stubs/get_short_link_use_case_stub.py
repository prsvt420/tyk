from src.application.dtos import ShortLinkDTO


class GetShortLinkUseCaseStub:
    """Record retrieval requests and return a predefined result."""

    def __init__(self, *, result: ShortLinkDTO | Exception) -> None:
        self._result: ShortLinkDTO | Exception = result
        self.requested_short_codes: list[str] = []

    async def execute(self, short_code: str) -> ShortLinkDTO:
        """Record a request and return or raise the predefined result."""
        self.requested_short_codes.append(short_code)

        if isinstance(self._result, Exception):
            raise self._result

        return self._result
