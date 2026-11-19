"""USR entities: User, Role, UserStatus, UserSession."""

import enum
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Role(str, enum.Enum):
    """Account roles (FR-USR-05)."""

    ADMIN = "ADMIN"
    STUDENT_ASSISTANT = "STUDENT_ASSISTANT"


class UserStatus(str, enum.Enum):
    """Accounts are deactivated, never deleted (BR-USR-02)."""

    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class User(Base):
    """A person who can log in."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    school_id: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    role: Mapped[Role] = mapped_column(Enum(Role))
    status: Mapped[UserStatus] = mapped_column(Enum(UserStatus), default=UserStatus.ACTIVE)
    password_hash: Mapped[str] = mapped_column(String(255))
    must_change_password: Mapped[bool] = mapped_column(Boolean, default=False)
    failed_attempts: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    access_end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime)


class UserSession(Base):
    """A login session identified by the keyed hash of an opaque token."""

    __tablename__ = "user_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)
