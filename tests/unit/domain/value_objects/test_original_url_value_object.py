import pytest

from src.domain.exceptions import InvalidOriginalURLError
from src.domain.value_objects import OriginalURL


@pytest.mark.parametrize(
    argnames="value",
    argvalues=[
        "http://example.com",
        "https://example.com/path?query=value#fragment",
    ],
)
def test_original_url_accepts_http_urls(value: str) -> None:
    """Accept HTTP and HTTPS URLs containing a host."""
    original_url: OriginalURL = OriginalURL(value=value)

    assert original_url.value == value


@pytest.mark.parametrize(
    argnames="value",
    argvalues=[
        "example.com",
        "ftp://example.com",
    ],
)
def test_original_url_rejects_unsupported_scheme(value: str) -> None:
    """Reject URLs without a supported scheme."""
    with pytest.raises(
        expected_exception=InvalidOriginalURLError,
        match=r"^URL scheme must be HTTP or HTTPS\.$",
    ):
        OriginalURL(value=value)


def test_original_url_rejects_missing_host() -> None:
    """Reject HTTP URLs without a host."""
    with pytest.raises(
        expected_exception=InvalidOriginalURLError,
        match=r"^URL must contain a host\.$",
    ):
        OriginalURL(value="https:///path")
