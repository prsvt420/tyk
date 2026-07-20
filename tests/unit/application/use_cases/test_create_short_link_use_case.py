from datetime import datetime, timezone
from logging import INFO
from uuid import UUID

import pytest

from src.application.constants import MAX_SHORT_CODE_GENERATION_ATTEMPTS
from src.application.dtos import CreateShortLinkDTO, ShortLinkDTO
from src.application.exceptions import (
    ShortCodeAlreadyExistsError,
    ShortCodeGenerationError,
)
from src.application.use_cases import CreateShortLinkUseCase
from src.domain.entities import ShortLink
from src.domain.value_objects import ShortCode
from tests.unit.application.stubs import (
    ShortCodeGeneratorStub,
    ShortLinkRepositoryStub,
)

LOGGER_NAME: str = "src.application.use_cases.create_short_link_use_case"


@pytest.mark.anyio
async def test_create_short_link_use_case_creates_short_link(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Create and persist a short link on the first attempt."""
    short_code: ShortCode = ShortCode(value="abcd")
    short_code_generator: ShortCodeGeneratorStub = ShortCodeGeneratorStub(
        short_codes=(short_code,)
    )
    short_link_repository: ShortLinkRepositoryStub = ShortLinkRepositoryStub()
    use_case: CreateShortLinkUseCase = CreateShortLinkUseCase(
        short_link_repository=short_link_repository,
        short_code_generator=short_code_generator,
    )
    create_short_link_dto: CreateShortLinkDTO = CreateShortLinkDTO(
        original_url="https://example.com/path"
    )

    with caplog.at_level(level=INFO, logger=LOGGER_NAME):
        short_link_dto: ShortLinkDTO = await use_case.execute(
            create_short_link_dto=create_short_link_dto
        )

    saved_short_link: ShortLink = short_link_repository.saved_short_links[0]

    assert isinstance(short_link_dto.id, UUID)
    assert short_link_dto.id == saved_short_link.id
    assert short_link_dto.original_url == create_short_link_dto.original_url
    assert short_link_dto.short_code == short_code.value
    assert short_link_dto.created_at == saved_short_link.created_at
    assert short_link_dto.expires_at is None
    assert short_code_generator.call_count == 1
    assert short_link_repository.save_call_count == 1
    assert caplog.messages == ["Short link created."]


@pytest.mark.anyio
async def test_create_short_link_use_case_retries_after_conflict(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Retry creation when a generated short code already exists."""
    first_short_code: ShortCode = ShortCode(value="abcd")
    second_short_code: ShortCode = ShortCode(value="efgh")
    expires_at: datetime = datetime(
        year=2100,
        month=1,
        day=1,
        tzinfo=timezone.utc,
    )
    short_code_generator: ShortCodeGeneratorStub = ShortCodeGeneratorStub(
        short_codes=(first_short_code, second_short_code)
    )
    short_link_repository: ShortLinkRepositoryStub = ShortLinkRepositoryStub(
        save_errors=(ShortCodeAlreadyExistsError(), None)
    )
    use_case: CreateShortLinkUseCase = CreateShortLinkUseCase(
        short_link_repository=short_link_repository,
        short_code_generator=short_code_generator,
    )

    with caplog.at_level(level=INFO, logger=LOGGER_NAME):
        short_link_dto: ShortLinkDTO = await use_case.execute(
            create_short_link_dto=CreateShortLinkDTO(
                original_url="https://example.com/path",
                expires_at=expires_at,
            )
        )

    saved_short_codes: list[str] = [
        short_link.short_code.value
        for short_link in short_link_repository.saved_short_links
    ]

    assert short_link_dto.short_code == second_short_code.value
    assert short_link_dto.expires_at == expires_at
    assert saved_short_codes == [
        first_short_code.value,
        second_short_code.value,
    ]
    assert short_code_generator.call_count == 2
    assert short_link_repository.save_call_count == 2
    assert caplog.messages == ["Short link created."]


@pytest.mark.anyio
async def test_create_short_link_use_case_rejects_exhausted_attempts() -> None:
    """Raise an error after every generated short code conflicts."""
    short_codes: tuple[ShortCode, ...] = tuple(
        ShortCode(value=f"a{index:03d}")
        for index in range(MAX_SHORT_CODE_GENERATION_ATTEMPTS)
    )
    save_errors: tuple[Exception | None, ...] = tuple(
        ShortCodeAlreadyExistsError()
        for _ in range(MAX_SHORT_CODE_GENERATION_ATTEMPTS)
    )
    short_code_generator: ShortCodeGeneratorStub = ShortCodeGeneratorStub(
        short_codes=short_codes
    )
    short_link_repository: ShortLinkRepositoryStub = ShortLinkRepositoryStub(
        save_errors=save_errors
    )
    use_case: CreateShortLinkUseCase = CreateShortLinkUseCase(
        short_link_repository=short_link_repository,
        short_code_generator=short_code_generator,
    )

    with pytest.raises(
        expected_exception=ShortCodeGenerationError,
        match=r"^Could not generate unique short code\.$",
    ):
        await use_case.execute(
            create_short_link_dto=CreateShortLinkDTO(
                original_url="https://example.com/path"
            )
        )

    assert (
        short_code_generator.call_count == MAX_SHORT_CODE_GENERATION_ATTEMPTS
    )
    assert (
        short_link_repository.save_call_count
        == MAX_SHORT_CODE_GENERATION_ATTEMPTS
    )
