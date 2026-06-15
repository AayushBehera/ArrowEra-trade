"""Domain-specific exceptions with HTTP mapping."""


class ArrowEraError(Exception):
    """Base exception for all domain errors."""

    def __init__(self, message: str = "An error occurred", status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(ArrowEraError):
    def __init__(self, resource: str = "Resource", identifier: str = ""):
        detail = f"{resource} not found" + (f": {identifier}" if identifier else "")
        super().__init__(message=detail, status_code=404)


class ValidationError(ArrowEraError):
    def __init__(self, message: str = "Validation failed"):
        super().__init__(message=message, status_code=422)


class ForbiddenError(ArrowEraError):
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message=message, status_code=403)


class ConflictError(ArrowEraError):
    def __init__(self, message: str = "Resource already exists"):
        super().__init__(message=message, status_code=409)


class RateLimitExceededError(ArrowEraError):
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message=message, status_code=429)


class ExternalServiceError(ArrowEraError):
    def __init__(self, service: str = "External service", detail: str = ""):
        msg = f"{service} unavailable" + (f": {detail}" if detail else "")
        super().__init__(message=msg, status_code=502)
