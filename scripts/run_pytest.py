from pathlib import Path

import pytest

TESTS_DIRECTORY: Path = Path("tests")
TEST_MODULE_PATTERN: str = "test_*.py"


def main() -> int:
    """Run the test suite when test modules exist."""
    if not any(TESTS_DIRECTORY.rglob(pattern=TEST_MODULE_PATTERN)):
        return 0

    return int(pytest.main())


if __name__ == "__main__":
    raise SystemExit(main())
