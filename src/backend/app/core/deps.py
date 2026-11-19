"""Shared FastAPI dependencies: settings, services, current user, role guard."""

from collections.abc import Callable

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.clock import Clock
from app.core.config import Settings
from app.core.database import get_db
from app.core.exceptions import PermissionDeniedError
from app.core.security import PasswordHasher, TokenService
from app.modules.usr.models import Role, User
from app.modules.usr.repository import SessionRepository, UserRepository
from app.modules.usr.service import (
    MSG_PASSWORD_CHANGE_REQUIRED,
    AccessControl,
    AuthService,
)
from app.shared.audit import AuditLog

_bearer = HTTPBearer(auto_error=False)


def get_settings(request: Request) -> Settings:
    """The Settings the app was built with."""
    return request.app.state.settings


def get_clock(request: Request) -> Clock:
    """The app clock (replaceable in tests via ``app.state.clock``)."""
    return request.app.state.clock


def get_hasher(settings: Settings = Depends(get_settings)) -> PasswordHasher:
    """Password hasher configured from settings."""
    return PasswordHasher(settings.bcrypt_rounds)


def get_audit_log(db: Session = Depends(get_db), clock: Clock = Depends(get_clock)) -> AuditLog:
    """Audit log bound to the request's transaction and the app clock."""
    return AuditLog(db, clock)


def get_auth_service(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    clock: Clock = Depends(get_clock),
    hasher: PasswordHasher = Depends(get_hasher),
    audit: AuditLog = Depends(get_audit_log),
) -> AuthService:
    """Auth service for the request."""
    return AuthService(
        UserRepository(db), SessionRepository(db), hasher,
        TokenService(settings.secret_key), audit, settings, clock,
    )


def get_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> str | None:
    """Bearer token from the Authorization header, if any."""
    return credentials.credentials if credentials else None


def get_current_user_allow_temp(
    token: str | None = Depends(get_token),
    auth: AuthService = Depends(get_auth_service),
) -> User:
    """Logged-in user, even if a temporary password is still in place."""
    return auth.authenticate(token)


def get_current_user(user: User = Depends(get_current_user_allow_temp)) -> User:
    """Logged-in user; temporary-password users must change it first (FR-USR-09)."""
    if user.must_change_password:
        raise PermissionDeniedError(MSG_PASSWORD_CHANGE_REQUIRED)
    return user


def require_role(*roles: Role) -> Callable[..., User]:
    """Dependency factory: current user must have one of the roles (FR-USR-05)."""

    def dependency(user: User = Depends(get_current_user)) -> User:
        AccessControl.require_role(user, *roles)
        return user

    return dependency
