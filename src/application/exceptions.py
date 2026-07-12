class ApplicationError(Exception):
    """Base application error."""


class ShortCodeGenerationError(ApplicationError):
    """Raised when unique short code cannot be generated."""


class ShortLinkNotFoundError(ApplicationError):
    """Raised when short link does not exist."""


class ShortLinkExpiredError(ApplicationError):
    """Raised when short link has expired."""


class ShortCodeAlreadyExistsError(ApplicationError):
    """Raised when short code already exists."""
