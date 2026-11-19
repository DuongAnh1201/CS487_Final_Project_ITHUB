"""USR business rules: AccessControl, AuthService and UserManager (SP4 §9.3, §11)."""

import re
from dataclasses import dataclass
from datetime import datetime, timedelta

from app.core.clock import Clock
from app.core.config import Settings
from app.core.exceptions import (
    AuthenticationError,
    ConflictError,
    PermissionDeniedError,
    ValidationRuleError,
)
from app.core.security import PasswordHasher, TokenService
from app.modules.usr.models import Role, User, UserSession, UserStatus
from app.modules.usr.repository import SessionRepository, UserRepository
from app.modules.usr.schemas import UserCreate
from app.shared.audit import AuditLog

MSG_INVALID = "Invalid email or password."
MSG_LOCKED = "Account locked. Try again in 15 minutes."
MSG_EXPIRED = "Session expired. Please log in again."
MSG_LOGIN_REQUIRED = "Please log in to continue."
MSG_DENIED = "Access denied."
MSG_DUPLICATE = "An account with this email or school ID already exists."
MSG_PASSWORD_RULE = "Password must be at least 10 characters and include letters and digits."
MSG_LAST_ADMIN = "At least one active Admin is required."
MSG_PASSWORD_CHANGE_REQUIRED = "Password change required."
MSG_WRONG_CURRENT = "Current password is incorrect."


class AccessControl:
    """Role checks (FR-USR-05, US-USR-06)."""

    @staticmethod
    def require_role(user: User, *roles: Role) -> None:
        """Raise PermissionDeniedError unless the user has one of the roles."""
        if user.role not in roles:
            raise PermissionDeniedError(MSG_DENIED)


@dataclass
class LoginResult:
    """Outcome of a successful login."""

    token: str
    user: User


def check_password_rule(password: str) -> None:
    """BR-USR-03: at least 10 characters with letters and digits."""
    if not (
        len(password) >= 10
        and re.search(r"[A-Za-z]", password)
        and re.search(r"\d", password)
    ):
        raise ValidationRuleError(MSG_PASSWORD_RULE)


class AuthService:
    """Log in, log out and validate sessions (US-USR-01)."""

    def __init__(
        self,
        users: UserRepository,
        sessions: SessionRepository,
        hasher: PasswordHasher,
        tokens: TokenService,
        audit: AuditLog,
        settings: Settings,
        clock: Clock,
    ) -> None:
        self.users = users
        self.sessions = sessions
        self.hasher = hasher
        self.tokens = tokens
        self.audit = audit
        self.settings = settings
        self.clock = clock

    def login(self, email: str, password: str) -> LoginResult:
        """Authenticate and start a session, or raise AuthenticationError."""
        now = self.clock()
        user = self.users.get_by_email(email)
        if user is None:
            self.hasher.verify_dummy(password)
            raise AuthenticationError(MSG_INVALID)
        if user.locked_until is not None and user.locked_until > now:
            raise AuthenticationError(MSG_LOCKED)
        if user.status == UserStatus.ACTIVE and self._access_ended(user, now):
            user.status = UserStatus.INACTIVE  # FR-USR-11
            self.audit.record(None, "DEACTIVATE", "User", user.id,
                              {"status": "ACTIVE"}, {"status": "INACTIVE"})
            self.users.commit()
        if user.status != UserStatus.ACTIVE:
            self.hasher.verify_dummy(password)
            raise AuthenticationError(MSG_INVALID)
        if not self.hasher.verify(password, user.password_hash):
            self._register_failure(user, now)
            raise AuthenticationError(MSG_INVALID)

        user.failed_attempts = 0
        user.locked_until = None
        user.last_login_at = now
        token = self.tokens.new_token()
        self.sessions.add(UserSession(
            token_hash=self.tokens.digest(token), user_id=user.id,
            created_at=now, last_seen_at=now,
        ))
        self.audit.record(user, "LOGIN", "User", user.id)
        return LoginResult(token=token, user=user)

    def authenticate(self, token: str | None) -> User:
        """Return the user for a live session and refresh its idle timer."""
        if not token:
            raise AuthenticationError(MSG_LOGIN_REQUIRED)
        session = self.sessions.get_by_digest(self.tokens.digest(token))
        if session is None or session.revoked:
            raise AuthenticationError(MSG_LOGIN_REQUIRED)
        now = self.clock()
        idle = timedelta(minutes=self.settings.session_timeout_minutes)
        if now - session.last_seen_at >= idle:
            session.revoked = True
            self.sessions.commit()  # keep the revocation although the request fails
            raise AuthenticationError(MSG_EXPIRED)
        user = self.users.get_or_raise(session.user_id)
        if user.status != UserStatus.ACTIVE:
            raise AuthenticationError(MSG_LOGIN_REQUIRED)
        session.last_seen_at = now
        return user

    def logout(self, token: str, user: User) -> None:
        """End the session behind this token."""
        session = self.sessions.get_by_digest(self.tokens.digest(token))
        if session is not None:
            session.revoked = True
        self.audit.record(user, "LOGOUT", "User", user.id)

    def _register_failure(self, user: User, now: datetime) -> None:
        """Count a failed attempt; lock on the 5th (FR-USR-07). Saved even though the request fails."""
        user.failed_attempts += 1
        if user.failed_attempts >= self.settings.max_failed_logins:
            user.locked_until = now + timedelta(minutes=self.settings.lockout_minutes)
            user.failed_attempts = 0
        self.users.commit()

    @staticmethod
    def _access_ended(user: User, now: datetime) -> bool:
        return user.access_end_date is not None and now.date() > user.access_end_date


class UserManager:
    """Account administration (US-USR-02..05)."""

    def __init__(
        self,
        users: UserRepository,
        sessions: SessionRepository,
        hasher: PasswordHasher,
        audit: AuditLog,
        clock: Clock,
    ) -> None:
        self.users = users
        self.sessions = sessions
        self.hasher = hasher
        self.audit = audit
        self.clock = clock

    def create_user(self, actor: User | None, data: UserCreate) -> User:
        """Create an active account with a temporary password (BR-USR-04, BR-USR-03)."""
        if actor is not None:
            AccessControl.require_role(actor, Role.ADMIN)
        return self._create(actor, data.full_name, str(data.email), data.school_id,
                            data.role, data.access_end_date, data.temporary_password)

    def seed_admin(self, full_name: str, email: str, school_id: str, password: str) -> User | None:
        """Create the first Admin when no user exists yet; otherwise do nothing."""
        if self.users.list():
            return None
        user = self._create(None, full_name, email, school_id, Role.ADMIN, None, password)
        user.must_change_password = True
        return user

    def list_users(self, actor: User, role: Role | None = None,
                   status: UserStatus | None = None) -> list[User]:
        """List users filtered by role and status (Admin only, FR-USR-10)."""
        AccessControl.require_role(actor, Role.ADMIN)
        return self.users.search(role, status)

    def get_user(self, actor: User, user_id: int) -> User:
        """Fetch one user (Admin only)."""
        AccessControl.require_role(actor, Role.ADMIN)
        return self.users.get_or_raise(user_id)

    def update_user(self, actor: User, user_id: int, role: Role | None,
                    status: UserStatus | None) -> User:
        """Change role and/or status, keeping one active Admin (BR-USR-06)."""
        AccessControl.require_role(actor, Role.ADMIN)
        user = self.users.get_or_raise(user_id)
        new_role = role or user.role
        new_status = status or user.status
        old = {"role": user.role.value, "status": user.status.value}
        was_active_admin = user.role == Role.ADMIN and user.status == UserStatus.ACTIVE
        stays_active_admin = new_role == Role.ADMIN and new_status == UserStatus.ACTIVE
        if was_active_admin and not stays_active_admin and self.users.count_active_admins() <= 1:
            raise ConflictError(MSG_LAST_ADMIN)
        user.role = new_role
        user.status = new_status
        if new_status != UserStatus.ACTIVE:
            self.sessions.revoke_for_user(user.id)
        self.users.flush()
        self.audit.record(actor, "UPDATE", "User", user.id, old,
                          {"role": user.role.value, "status": user.status.value})
        return user

    def reset_password(self, actor: User, user_id: int, temporary_password: str) -> User:
        """Set a temporary password that must be changed at next login (FR-USR-09)."""
        AccessControl.require_role(actor, Role.ADMIN)
        user = self.users.get_or_raise(user_id)
        check_password_rule(temporary_password)
        user.password_hash = self.hasher.hash(temporary_password)
        user.must_change_password = True
        user.failed_attempts = 0
        user.locked_until = None
        self.sessions.revoke_for_user(user.id)
        self.users.flush()
        self.audit.record(actor, "RESET_PASSWORD", "User", user.id)
        return user

    def change_own_password(self, user: User, current_password: str, new_password: str) -> None:
        """Change the caller's own password (FR-USR-08)."""
        if not self.hasher.verify(current_password, user.password_hash):
            raise ValidationRuleError(MSG_WRONG_CURRENT)
        check_password_rule(new_password)
        user.password_hash = self.hasher.hash(new_password)
        user.must_change_password = False
        self.users.flush()
        self.audit.record(user, "CHANGE_PASSWORD", "User", user.id)

    def _create(self, actor: User | None, full_name: str, email: str, school_id: str,
                role: Role, access_end_date, password: str) -> User:
        email = email.strip().lower()
        school_id = school_id.strip()
        if self.users.get_by_email(email) or self.users.get_by_school_id(school_id):
            raise ConflictError(MSG_DUPLICATE)
        check_password_rule(password)
        user = self.users.add(User(
            full_name=full_name.strip(), email=email, school_id=school_id, role=role,
            status=UserStatus.ACTIVE, password_hash=self.hasher.hash(password),
            must_change_password=True, access_end_date=access_end_date,
            created_at=self.clock(),
        ))
        self.audit.record(actor, "CREATE", "User", user.id, None, {
            "email": user.email, "school_id": user.school_id, "role": role.value,
        })
        return user
