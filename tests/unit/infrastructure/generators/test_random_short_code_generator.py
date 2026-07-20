import pytest

from src.domain.constants import (
    SHORT_CODE_ALLOWED_CHARS,
    SHORT_CODE_MAX_LENGTH,
    SHORT_CODE_MIN_LENGTH,
)
from src.domain.value_objects import ShortCode
from src.infrastructure.exceptions import ShortCodeGeneratorError
from src.infrastructure.generators import RandomShortCodeGenerator
from src.infrastructure.generators.random_short_code_generator import (
    DEFAULT_SHORT_CODE_LENGTH,
)


@pytest.mark.anyio
async def test_random_short_code_generator_uses_default_length() -> None:
    """Generate a short code with the default length."""
    short_code_generator: RandomShortCodeGenerator = RandomShortCodeGenerator()

    short_code: ShortCode = await short_code_generator.generate()

    assert len(short_code.value) == DEFAULT_SHORT_CODE_LENGTH
    assert set(short_code.value) <= SHORT_CODE_ALLOWED_CHARS


@pytest.mark.anyio
@pytest.mark.parametrize(
    argnames="short_code_length",
    argvalues=[
        SHORT_CODE_MIN_LENGTH,
        SHORT_CODE_MAX_LENGTH,
    ],
)
async def test_random_short_code_generator_uses_custom_length(
    short_code_length: int,
) -> None:
    """Generate a short code with a valid custom length."""
    short_code_generator: RandomShortCodeGenerator = RandomShortCodeGenerator(
        short_code_length=short_code_length
    )

    short_code: ShortCode = await short_code_generator.generate()

    assert len(short_code.value) == short_code_length
    assert set(short_code.value) <= SHORT_CODE_ALLOWED_CHARS


def test_random_short_code_generator_rejects_short_length() -> None:
    """Reject a length below the minimum."""
    with pytest.raises(
        expected_exception=ShortCodeGeneratorError,
        match=r"^Short code is too short\.$",
    ):
        RandomShortCodeGenerator(short_code_length=SHORT_CODE_MIN_LENGTH - 1)


def test_random_short_code_generator_rejects_long_length() -> None:
    """Reject a length above the maximum."""
    with pytest.raises(
        expected_exception=ShortCodeGeneratorError,
        match=r"^Short code is too long\.$",
    ):
        RandomShortCodeGenerator(short_code_length=SHORT_CODE_MAX_LENGTH + 1)
