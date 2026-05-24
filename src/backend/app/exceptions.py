"""Centralized exception classes for the MChat API."""

from fastapi import status


class MChatError(Exception):
    """Base exception for all MChat-specific errors."""

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(MChatError):
    """Resource not found (404)."""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status.HTTP_404_NOT_FOUND)


class PermissionDeniedError(MChatError):
    """Permission denied / forbidden (403)."""

    def __init__(self, message: str = "Permission denied"):
        super().__init__(message, status.HTTP_403_FORBIDDEN)


class UnauthorizedError(MChatError):
    """Authentication required (401)."""

    def __init__(self, message: str = "Authentication required"):
        super().__init__(message, status.HTTP_401_UNAUTHORIZED)


class ValidationError(MChatError):
    """Request validation error (422)."""

    def __init__(self, message: str = "Validation failed"):
        super().__init__(message, status.HTTP_422_UNPROCESSABLE_ENTITY)


class BusinessError(MChatError):
    """Business rule violation (400)."""

    def __init__(self, message: str = "Bad request"):
        super().__init__(message, status.HTTP_400_BAD_REQUEST)


class ConflictError(MChatError):
    """Resource conflict / duplicate (409)."""

    def __init__(self, message: str = "Resource already exists"):
        super().__init__(message, status.HTTP_409_CONFLICT)


class TooManyRequestsError(MChatError):
    """Rate limit exceeded (429)."""

    def __init__(self, message: str = "Too many requests"):
        super().__init__(message, status.HTTP_429_TOO_MANY_REQUESTS)
