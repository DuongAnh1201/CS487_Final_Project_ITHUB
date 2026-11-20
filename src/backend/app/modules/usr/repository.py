"""USR storage."""

from sqlalchemy import func, select, update

from app.modules.usr.models import Role, User, UserSession, UserStatus
from app.shared.repository import BaseRepository


class UserRepository(BaseRepository[User]):
    """User queries."""

    model = User
    not_found_message = "User not found."

    def get_by_email(self, email: str) -> User | None:
        """Find a user by email (case-insensitive)."""
        return self.session.scalar(select(User).where(User.email == email.strip().lower()))

    def get_by_school_id(self, school_id: str) -> User | None:
        """Find a user by school ID."""
        return self.session.scalar(select(User).where(User.school_id == school_id))

    def count_active_admins(self) -> int:
        """Number of active Admin accounts (BR-USR-06)."""
        return self.session.scalar(
            select(func.count()).select_from(User).where(
                User.role == Role.ADMIN, User.status == UserStatus.ACTIVE
            )
        ) or 0

    def directory(self, name_contains: str | None = None) -> list[User]:
        """Active users ordered by name, optionally filtered by part of the name."""
        stmt = select(User).where(User.status == UserStatus.ACTIVE).order_by(User.full_name, User.id)
        if name_contains:
            stmt = stmt.where(User.full_name.ilike(f"%{name_contains}%"))
        return list(self.session.scalars(stmt))

    def search(self, role: Role | None = None, status: UserStatus | None = None) -> list[User]:
        """List users filtered by role and/or status (FR-USR-10)."""
        stmt = select(User).order_by(User.id)
        if role is not None:
            stmt = stmt.where(User.role == role)
        if status is not None:
            stmt = stmt.where(User.status == status)
        return list(self.session.scalars(stmt))


class SessionRepository(BaseRepository[UserSession]):
    """Login session queries."""

    model = UserSession

    def get_by_digest(self, digest: str) -> UserSession | None:
        """Find a session by its stored token digest."""
        return self.session.scalar(select(UserSession).where(UserSession.token_hash == digest))

    def revoke_for_user(self, user_id: int) -> None:
        """End every session of a user."""
        self.session.execute(
            update(UserSession).where(UserSession.user_id == user_id).values(revoked=True)
        )
