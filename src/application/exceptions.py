class ApplicationError(Exception):
    """Base application error."""


class ShortCodeGenerationError(ApplicationError):
    """Raised when unique short code cannot be generated."""
