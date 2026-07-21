import pytest


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    """Use asyncio for asynchronous tests."""
    return "asyncio"
