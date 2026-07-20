import pytest


@pytest.fixture
def anyio_backend() -> str:
    """Use asyncio for asynchronous tests."""
    return "asyncio"
