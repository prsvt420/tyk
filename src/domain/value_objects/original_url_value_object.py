from dataclasses import dataclass
from urllib.parse import ParseResult, urlparse

from src.domain.exceptions import InvalidOriginalURLError


@dataclass(frozen=True, slots=True, kw_only=True)
class OriginalURL:
    """Original URL value object."""

    value: str

    def __post_init__(self) -> None:
        """Validate original URL."""
        parse_result: ParseResult = urlparse(url=self.value)

        if parse_result.scheme not in {"http", "https"}:
            raise InvalidOriginalURLError("URL scheme must be HTTP or HTTPS.")

        if not parse_result.netloc:
            raise InvalidOriginalURLError("URL must contain a host.")
