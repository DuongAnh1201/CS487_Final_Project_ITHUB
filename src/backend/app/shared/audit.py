"""Shared audit log (FR-USR-06). RPT adds querying and reports on top of this."""

from datetime import date, datetime, time, timedelta
from typing import Any, Protocol

from sqlalchemy import JSON, DateTime, Integer, String, event, select
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.core.clock import Clock, utc_now
from app.core.database import Base
from app.core.exceptions import ConflictError, NotFoundError

MSG_IMMUTABLE = "Audit records cannot be changed or removed."


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
    status: Mapped[str] = mapped_column(String(20), default="SUCCESS")  # BR-RPT-03

    def describe(self) -> str:
        """One-line human description."""
        who = f"user {self.actor_id}" if self.actor_id is not None else "system"
        return f"{self.timestamp.isoformat()} {who}: {self.action} {self.entity_type} {self.entity_id}"


@event.listens_for(AuditRecord, "before_update")
@event.listens_for(AuditRecord, "before_delete")
def _audit_records_are_immutable(*_: Any) -> None:
    """Audit records are never edited or removed (BR-RPT-03)."""
    raise ConflictError(MSG_IMMUTABLE)


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
        status: str = "SUCCESS",
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
            status=status,
        )
        self.session.add(entry)
        self.session.flush()
        return entry

    def get(self, record_id: int) -> AuditRecord:
        """One record by its unique id (FR-RPT-09)."""
        record = self.session.get(AuditRecord, record_id)
        if record is None:
            raise NotFoundError("Audit record not found.")
        return record

    def search(
        self,
        user_id: int | None = None,
        entity_type: str | None = None,
        entity_id: int | str | None = None,
        action: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditRecord]:
        """Records matching every given filter, newest first (FR-RPT-08)."""
        stmt = select(AuditRecord)
        if user_id is not None:
            stmt = stmt.where(AuditRecord.actor_id == user_id)
        if entity_type:
            stmt = stmt.where(AuditRecord.entity_type == entity_type)
        if entity_id is not None:
            stmt = stmt.where(AuditRecord.entity_id == str(entity_id))
        if action:
            stmt = stmt.where(AuditRecord.action == action.upper())
        if date_from is not None:
            stmt = stmt.where(AuditRecord.timestamp >= datetime.combine(date_from, time.min))
        if date_to is not None:
            stmt = stmt.where(AuditRecord.timestamp < datetime.combine(date_to + timedelta(days=1), time.min))
        stmt = stmt.order_by(AuditRecord.timestamp.desc(), AuditRecord.id.desc())
        return list(self.session.scalars(stmt.limit(limit).offset(offset)))
