"""Domain errors and the single handler that maps them to HTTP responses."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class DomainError(Exception):
    """Base class for business-rule violations. The message is shown to the user."""

    status_code = 400

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NotFoundError(DomainError):
    """The requested record does not exist (404)."""

    status_code = 404


class ConflictError(DomainError):
    """The action conflicts with existing data or state (409)."""

    status_code = 409


class PermissionDeniedError(DomainError):
    """The user's role does not allow the action (403)."""

    status_code = 403


class AuthenticationError(DomainError):
    """The caller is not (or no longer) authenticated (401)."""

    status_code = 401


class ValidationRuleError(DomainError):
    """Input breaks a business validation rule (422)."""

    status_code = 422


async def domain_error_handler(_: Request, exc: DomainError) -> JSONResponse:
    """Return ``{"detail": message}`` with the error's status code."""
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


def register_exception_handlers(app: FastAPI) -> None:
    """Install the DomainError handler on the app."""
    app.add_exception_handler(DomainError, domain_error_handler)  # type: ignore[arg-type]
