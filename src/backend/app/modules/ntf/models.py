"""NTF entity: Notification."""

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.shared.events import EventType


class EmailStatus(str, enum.Enum):
    """Result of the email copy (FR-NTF-07)."""

    PENDING = "PENDING"
    SENT = "SENT"
    DELIVERED = "DELIVERED"
    BOUNCED = "BOUNCED"
    COMPLAINED = "COMPLAINED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"  # no email provider configured


class Notification(Base):
    """One in-app message for one recipient, linked to one triggering event (BR-16)."""

    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    recipient_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    event_type: Mapped[EventType] = mapped_column(Enum(EventType))
    message: Mapped[str] = mapped_column(Text)
    related_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    related_id: Mapped[int | None] = mapped_column(nullable=True)
    project_id: Mapped[int | None] = mapped_column(nullable=True)
    triggered_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime)
    read_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    email_status: Mapped[EmailStatus] = mapped_column(Enum(EmailStatus), default=EmailStatus.PENDING)
    email_error: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email_message_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    email_sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    email_attempts: Mapped[int] = mapped_column(default=0)

    @property
    def is_read(self) -> bool:
        """Read when ``read_at`` is set."""
        return self.read_at is not None


class EmailWebhookEvent(Base):
    """A processed provider webhook delivery (``svix-id``), kept so replays are ignored."""

    __tablename__ = "email_webhook_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    svix_id: Mapped[str] = mapped_column(String(100), unique=True)
    event_type: Mapped[str] = mapped_column(String(50))
    notification_id: Mapped[int | None] = mapped_column(ForeignKey("notifications.id"), nullable=True)
    received_at: Mapped[datetime] = mapped_column(DateTime)
