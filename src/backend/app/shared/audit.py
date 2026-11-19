"""Shared audit log (FR-USR-06). RPT adds querying and reports on top of this."""

from datetime import datetime
from typing import Any, Protocol

from sqlalchemy import JSON, DateTime, Integer, String
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.core.clock import Clock, utc_now
from app.core.database import Base


class HasId(Protocol):
    """Anything with an integer ``id`` (a User, usually)."""

    id: int


class AuditRecord(Base):
    """One immutable audit entry."""

    __tablename__ = "audit_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, index=True)
    actor_id: Mapped[int | None] = mapped_column(Integer, index=True, nullable=True)
    action: Mapped[str] = mapped_column(String(50), index=True)
    entity_type: Mapped[str] = mapped_column(String(50), index=True)
    entity_id: Mapped[str] = mapped_column(String(50))
    old_value: Mapped[Any] = mapped_column(JSON, nullable=True)
    new_value: Mapped[Any] = mapped_column(JSON, nullable=True)


class AuditLog:
    """Writes audit records in the caller's transaction (same commit as the change)."""

    def __init__(self, session: Session, clock: Clock = utc_now) -> None:
        self.session = session
        self.clock = clock

    def record(
        self,
        actor: HasId | int | None,
        action: str,
        entity_type: str,
        entity_id: int | str,
        old_value: dict[str, Any] | None = None,
        new_value: dict[str, Any] | None = None,
    ) -> AuditRecord:
        """Add an entry; ``actor`` is the acting user (or user id), or None for system actions."""
        entry = AuditRecord(
            timestamp=self.clock(),
            actor_id=actor if isinstance(actor, int) or actor is None else actor.id,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id),
            old_value=old_value,
            new_value=new_value,
        )
        self.session.add(entry)
        self.session.flush()
        return entry
