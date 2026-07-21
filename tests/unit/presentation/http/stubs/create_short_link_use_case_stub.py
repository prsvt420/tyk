from src.application.dtos import CreateShortLinkDTO, ShortLinkDTO


class CreateShortLinkUseCaseStub:
    """Record create requests and return a predefined short link."""

    def __init__(self, *, short_link_dto: ShortLinkDTO) -> None:
        self._short_link_dto: ShortLinkDTO = short_link_dto
        self.create_short_link_dtos: list[CreateShortLinkDTO] = []

    async def execute(
        self,
        create_short_link_dto: CreateShortLinkDTO,
    ) -> ShortLinkDTO:
        """Record a request and return the predefined short link."""
        self.create_short_link_dtos.append(create_short_link_dto)

        return self._short_link_dto
