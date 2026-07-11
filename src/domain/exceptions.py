class DomainError(Exception):
    """Base domain error."""


class InvalidOriginalURLError(DomainError):
    """Raised when original URL is invalid."""


class InvalidShortCodeError(DomainError):
    """Raised when short code is invalid."""


class InvalidShortLinkError(DomainError):
    """Raised when short link entity is invalid."""
