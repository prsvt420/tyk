class InfrastructureError(Exception):
    """Base infrastructure error."""


class ShortCodeGeneratorError(InfrastructureError):
    """Raised when short code generator fails."""
