class ServiceError(Exception):
    """Base service exception."""


class DuplicateResourceError(ServiceError):
    """Raised when a unique external identifier already exists."""


class ResourceNotFoundError(ServiceError):
    """Raised when a requested dependency or resource does not exist."""
