"""USR business rules: AccessControl, AuthService and UserManager (SP4 §9.3, §11)."""

import logging
import re
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta

from app.core.clock import Clock
from app.core.config import Settings
from app.core.exceptions import (
    AuthenticationError,
    ConflictError,
    PermissionDeniedError,
    ServiceUnavailableError,
    ValidationRuleError,
)
from app.core.security import PasswordHasher, TokenService
from app.modules.usr.google import GoogleTokenError, GoogleTokenVerifier
from app.modules.usr.models import Role, User, UserSession, UserStatus
from app.modules.usr.repository import SessionRepository, UserRepository
from app.modules.usr.schemas import UserCreate
from app.shared.audit import AuditLog
from app.shared.events import DomainEvent, EventPublisher, EventType
from app.shared.formatting import human_date, human_datetime

MSG_INVALID = "Invalid email or password."
MSG_LOCKED = "Account locked. Try again in 15 minutes."
MSG_EXPIRED = "Session expired. Please log in again."
MSG_LOGIN_REQUIRED = "Please log in to continue."
logger = logging.getLogger(__name__)

MSG_DENIED = "Access denied."
MSG_DUPLICATE = "An account with this email or school ID already exists."
MSG_PASSWORD_RULE = "Password must be at least 10 characters and include letters and digits."
MSG_LAST_ADMIN = "At least one active Admin is required."
MSG_PASSWORD_CHANGE_REQUIRED = "Password change required."
MSG_WRONG_CURRENT = "Current password is incorrect."
MSG_GOOGLE_OFF = "Google sign-in is not configured."


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
    must_change_password: bool = False


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
        google: GoogleTokenVerifier | None = None,
    ) -> None:
        self.users = users
        self.sessions = sessions
        self.hasher = hasher
        self.tokens = tokens
        self.audit = audit
        self.settings = settings
        self.clock = clock
        self.google = google

    def login(self, email: str, password: str) -> LoginResult:
        """Authenticate and start a session, or raise AuthenticationError."""
        now = self.clock()
        user = self.users.get_by_email(email)
        if user is None:
            self.hasher.verify_dummy(password)
            raise AuthenticationError(MSG_INVALID)
        self._guard_account(user, now, password)
        if not self.hasher.verify(password, user.password_hash):
            self._register_failure(user, now)
            raise AuthenticationError(MSG_INVALID)
        user.failed_attempts = 0
        user.locked_until = None
        return self._start_session(user, now, "password", user.must_change_password)

    def login_with_google(self, id_token: str) -> LoginResult:
        """Sign in an existing user with a Google ID token; never creates accounts."""
        if self.google is None or not self.settings.google_enabled:
            raise ServiceUnavailableError(MSG_GOOGLE_OFF)
        try:
            identity = self.google.verify(id_token)
        except GoogleTokenError:
            raise AuthenticationError(MSG_INVALID) from None
        if not identity.is_acceptable(self.settings.google_hosted_domain):
            raise AuthenticationError(MSG_INVALID)
        user = self.users.get_by_email(identity.email)
        if user is None:
            raise AuthenticationError(MSG_INVALID)
        now = self.clock()
        self._guard_account(user, now)
        if user.google_sub is not None and user.google_sub != identity.sub:
            raise AuthenticationError(MSG_INVALID)
        user.google_sub = identity.sub
        return self._start_session(user, now, "google", False)

    def authenticate(self, token: str | None) -> User:
        """Return the user for a live session and refresh its idle timer."""
        return self.authenticate_session(token)[0]

    def authenticate_session(self, token: str | None) -> tuple[User, UserSession]:
        """Like ``authenticate`` but also returns the session (to know how it was started)."""
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
        return user, session

    def logout(self, token: str, user: User) -> None:
        """End the session behind this token."""
        session = self.sessions.get_by_digest(self.tokens.digest(token))
        if session is not None:
            session.revoked = True
        self.audit.record(user, "LOGOUT", "User", user.id)

    def _guard_account(self, user: User, now: datetime, password: str | None = None) -> None:
        """Refuse locked, ended-access and deactivated accounts (BR-USR-07, FR-USR-11)."""
        if user.locked_until is not None and user.locked_until > now:
            raise AuthenticationError(MSG_LOCKED)
        if user.status == UserStatus.ACTIVE and self._access_ended(user, now):
            user.status = UserStatus.INACTIVE
            self.audit.record(None, "DEACTIVATE", "User", user.id,
                              {"status": "ACTIVE"}, {"status": "INACTIVE"})
            self.users.commit()
        if user.status != UserStatus.ACTIVE:
            if password is not None:
                self.hasher.verify_dummy(password)
            raise AuthenticationError(MSG_INVALID)

    def _start_session(self, user: User, now: datetime, method: str,
                       must_change_password: bool) -> LoginResult:
        """Create the session and the LOGIN audit entry (shared by every login method)."""
        user.last_login_at = now
        token = self.tokens.new_token()
        self.sessions.add(UserSession(
            token_hash=self.tokens.digest(token), user_id=user.id,
            created_at=now, last_seen_at=now, auth_method=method,
        ))
        self.audit.record(user, "LOGIN", "User", user.id, None, {"method": method})
        return LoginResult(token=token, user=user, must_change_password=must_change_password)

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
        publisher: EventPublisher | None = None,
    ) -> None:
        self.users = users
        self.sessions = sessions
        self.hasher = hasher
        self.audit = audit
        self.clock = clock
        self.publisher = publisher

    def create_user(self, actor: User | None, data: UserCreate) -> User:
        """Create an active account with a temporary password (BR-USR-04, BR-USR-03).

        The new user gets a welcome notification and email; the temporary password is never sent.
        """
        if actor is not None:
            AccessControl.require_role(actor, Role.ADMIN)
        user = self._create(actor, data.full_name, str(data.email), data.school_id,
                            data.role, data.access_end_date, data.temporary_password)
        if actor is not None:
            self._tell(user, actor, EventType.ACCOUNT_CREATED,
                       f"Welcome to IT HUB. {actor.full_name} created your account.", {
                           "first_name": user.full_name.split()[0], "email": user.email,
                           "role": "Admin" if user.role == Role.ADMIN else "Student Assistant",
                           "access_end": human_date(user.access_end_date, "No end date"),
                           "admin_name": actor.full_name,
                       })
        return user

    def seed_admin(self, full_name: str, email: str, school_id: str,
                   password: str | None = None) -> User | None:
        """Create the first Admin when no user exists yet; otherwise do nothing.

        Without a configured password a random temporary one is generated and logged once.
        Either way it must be changed at first password login.
        """
        if self.users.list():
            return None
        if password is None:
            password = self._random_password()
            logger.warning("Initial admin password: %s", password)
        user = self._create(None, full_name, email, school_id, Role.ADMIN, None, password)
        user.must_change_password = True
        return user

    def list_users(self, actor: User, role: Role | None = None,
                   status: UserStatus | None = None) -> list[User]:
        """List users filtered by role and status (Admin only, FR-USR-10)."""
        AccessControl.require_role(actor, Role.ADMIN)
        return self.users.search(role, status)

    def staff_directory(self, q: str | None = None) -> list[User]:
        """Active staff for member, assignee, reviewer and recipient pickers (any logged-in user)."""
        return self.users.directory(q.strip() if q else None)

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
        self._tell(user, actor, EventType.PASSWORD_RESET,
                   f"{actor.full_name} reset your IT HUB password. Sign in with the new temporary password.", {
                       "admin_name": actor.full_name, "reset_at": human_datetime(self.clock()),
                       "support_contact": f"{actor.full_name} ({actor.email})",
                   })
        return user

    def _tell(self, user: User, actor: User, event_type: EventType, message: str,
              details: dict[str, str]) -> None:
        """Notify the account owner (NTF skips it when owners act on their own account)."""
        if self.publisher is not None:
            self.publisher.publish(DomainEvent(event_type, message, actor_id=actor.id,
                                               recipient_ids=(user.id,), details=details))

    def change_own_password(self, user: User, current_password: str, new_password: str) -> None:
        """Change the caller's own password (FR-USR-08)."""
        if not self.hasher.verify(current_password, user.password_hash):
            raise ValidationRuleError(MSG_WRONG_CURRENT)
        check_password_rule(new_password)
        user.password_hash = self.hasher.hash(new_password)
        user.must_change_password = False
        self.users.flush()
        self.audit.record(user, "CHANGE_PASSWORD", "User", user.id)

    @staticmethod
    def _random_password() -> str:
        """A random temporary password that satisfies the password rule (BR-USR-03)."""
        while True:
            candidate = secrets.token_urlsafe(16)
            if re.search(r"[A-Za-z]", candidate) and re.search(r"\d", candidate):
                return candidate

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
