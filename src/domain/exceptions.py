class DomainError(Exception):
    """Base domain error."""


class InvalidOriginalURLError(DomainError):
    """Raised when original URL value object is invalid."""


class InvalidShortCodeError(DomainError):
    """Raised when short code value object is invalid."""


class InvalidShortLinkError(DomainError):
    """Raised when short link entity is invalid."""


class InvalidEmailError(DomainError):
    """Raised when email value object is invalid."""


class InvalidUserError(DomainError):
    """Raised when user entity is invalid."""
