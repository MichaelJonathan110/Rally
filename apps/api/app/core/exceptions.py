"""Domain exceptions raised by services and translated to HTTP by handlers.

Services raise these (business-rule) errors; a single set of FastAPI exception
handlers maps them to the correct status codes. This keeps HTTP concerns out of
the service layer while guaranteeing consistent 400/403/404/409 responses.
"""
from __future__ import annotations


class DomainError(Exception):
    """Base class for all domain-level errors."""

    status_code: int = 400
    default_detail: str = "Domain error"

    def __init__(self, detail: str | None = None) -> None:
        self.detail = detail or self.default_detail
        super().__init__(self.detail)


class NotFoundError(DomainError):
    status_code = 404
    default_detail = "Resource not found"


class PermissionDeniedError(DomainError):
    status_code = 403
    default_detail = "You do not have permission to perform this action"


class ConflictError(DomainError):
    status_code = 409
    default_detail = "Resource conflict"


class ValidationError(DomainError):
    status_code = 400
    default_detail = "Invalid request"


class CapacityError(DomainError):
    """The activity/venue is full - a client error (400)."""

    status_code = 400
    default_detail = "Capacity exceeded"


class PaymentDeclinedError(DomainError):
    """The payment provider declined the charge - retry with another method (402)."""

    status_code = 402
    default_detail = "Payment was declined"
