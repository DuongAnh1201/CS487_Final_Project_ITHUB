"""USR routes: /auth/* and /users/*."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.clock import Clock
from app.core.database import get_db
from app.core.config import Settings
from app.core.deps import (
    get_audit_log,
    get_auth_service,
    get_clock,
    get_current_user_allow_temp,
    get_hasher,
    get_settings,
    get_token,
    require_role,
)
from app.core.security import PasswordHasher
from app.modules.usr.models import Role, User, UserStatus
from app.modules.usr.repository import SessionRepository, UserRepository
from app.modules.usr.schemas import (
    AuthConfig,
    ChangePasswordRequest,
    GoogleLoginRequest,
    LoginRequest,
    LoginResponse,
    MessageResponse,
    ResetPasswordRequest,
    UserCreate,
    UserRead,
    UserUpdate,
)
from app.modules.usr.service import AuthService, LoginResult, UserManager
from app.shared.audit import AuditLog

auth_router = APIRouter(prefix="/auth", tags=["auth"])
users_router = APIRouter(prefix="/users", tags=["users"])


def get_user_manager(
    db: Session = Depends(get_db),
    hasher: PasswordHasher = Depends(get_hasher),
    audit: AuditLog = Depends(get_audit_log),
    clock: Clock = Depends(get_clock),
) -> UserManager:
    """UserManager for the request."""
    return UserManager(UserRepository(db), SessionRepository(db), hasher, audit, clock)


def _login_response(result: LoginResult) -> LoginResponse:
    return LoginResponse(
        access_token=result.token,
        must_change_password=result.must_change_password,
        user=UserRead.model_validate(result.user),
    )


@auth_router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest, auth: AuthService = Depends(get_auth_service)) -> LoginResponse:
    """Log in with school email and password (FR-USR-01)."""
    return _login_response(auth.login(body.email, body.password))


@auth_router.post("/google", response_model=LoginResponse)
def login_with_google(body: GoogleLoginRequest,
                      auth: AuthService = Depends(get_auth_service)) -> LoginResponse:
    """Sign in an existing user with a Google ID token (503 until configured)."""
    return _login_response(auth.login_with_google(body.id_token))


@auth_router.get("/config", response_model=AuthConfig)
def auth_config(settings: Settings = Depends(get_settings)) -> AuthConfig:
    """Tell the frontend whether Google sign-in is available."""
    return AuthConfig(
        google_enabled=settings.google_enabled,
        google_client_id=settings.google_client_ids[0] if settings.google_client_ids else None,
    )


@auth_router.post("/logout", response_model=MessageResponse)
def logout(
    token: str | None = Depends(get_token),
    user: User = Depends(get_current_user_allow_temp),
    auth: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    """Log out (FR-USR-02)."""
    auth.logout(token or "", user)
    return MessageResponse(message="Logged out.")


@auth_router.get("/me", response_model=UserRead)
def me(user: User = Depends(get_current_user_allow_temp)) -> User:
    """The logged-in user."""
    return user


@auth_router.post("/change-password", response_model=MessageResponse)
def change_password(
    body: ChangePasswordRequest,
    user: User = Depends(get_current_user_allow_temp),
    manager: UserManager = Depends(get_user_manager),
) -> MessageResponse:
    """Change the caller's own password (FR-USR-08)."""
    manager.change_own_password(user, body.current_password, body.new_password)
    return MessageResponse(message="Password changed.")


@users_router.post("", response_model=UserRead, status_code=201)
def create_user(
    body: UserCreate,
    actor: User = Depends(require_role(Role.ADMIN)),
    manager: UserManager = Depends(get_user_manager),
) -> User:
    """Create an account (FR-USR-03)."""
    return manager.create_user(actor, body)


@users_router.get("", response_model=list[UserRead])
def list_users(
    role: Role | None = None,
    status: UserStatus | None = None,
    actor: User = Depends(require_role(Role.ADMIN)),
    manager: UserManager = Depends(get_user_manager),
) -> list[User]:
    """List users, filtered by role and status (FR-USR-10)."""
    return manager.list_users(actor, role, status)


@users_router.get("/{user_id}", response_model=UserRead)
def get_user(
    user_id: int,
    actor: User = Depends(require_role(Role.ADMIN)),
    manager: UserManager = Depends(get_user_manager),
) -> User:
    """Fetch one user."""
    return manager.get_user(actor, user_id)


@users_router.patch("/{user_id}", response_model=UserRead)
def update_user(
    user_id: int,
    body: UserUpdate,
    actor: User = Depends(require_role(Role.ADMIN)),
    manager: UserManager = Depends(get_user_manager),
) -> User:
    """Change a user's role or status (FR-USR-04)."""
    return manager.update_user(actor, user_id, body.role, body.status)


@users_router.post("/{user_id}/reset-password", response_model=UserRead)
def reset_password(
    user_id: int,
    body: ResetPasswordRequest,
    actor: User = Depends(require_role(Role.ADMIN)),
    manager: UserManager = Depends(get_user_manager),
) -> User:
    """Set a temporary password (FR-USR-09)."""
    return manager.reset_password(actor, user_id, body.temporary_password)
