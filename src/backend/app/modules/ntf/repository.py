"""NTF storage."""

from datetime import date, datetime, time

from sqlalchemy import select

from app.modules.ntf.models import EmailStatus, EmailWebhookEvent, Notification
from app.shared.repository import BaseRepository


class NotificationRepository(BaseRepository[Notification]):
    """Notification queries."""

    model = Notification
    not_found_message = "Notification not found."

    def list_for_user(self, user_id: int, unread_only: bool = False) -> list[Notification]:
        """A user's notifications, newest first."""
        stmt = select(Notification).where(Notification.recipient_id == user_id)
        if unread_only:
            stmt = stmt.where(Notification.read_at.is_(None))
        return list(self.session.scalars(stmt.order_by(Notification.created_at.desc(), Notification.id.desc())))

    def get_by_message_id(self, message_id: str) -> Notification | None:
        """The notification whose email the provider knows by this id."""
        return self.session.scalars(
            select(Notification).where(Notification.email_message_id == message_id)).first()

    def deliveries(self, status: EmailStatus | None = None, recipient_id: int | None = None,
                   date_from: date | None = None, date_to: date | None = None) -> list[Notification]:
        """Notifications filtered for the email delivery log, newest first."""
        stmt = select(Notification)
        if status is not None:
            stmt = stmt.where(Notification.email_status == status)
        if recipient_id is not None:
            stmt = stmt.where(Notification.recipient_id == recipient_id)
        if date_from is not None:
            stmt = stmt.where(Notification.created_at >= datetime.combine(date_from, time.min))
        if date_to is not None:
            stmt = stmt.where(Notification.created_at <= datetime.combine(date_to, time.max))
        return list(self.session.scalars(stmt.order_by(Notification.created_at.desc(), Notification.id.desc())))

    def webhook_seen(self, svix_id: str) -> bool:
        """True when this webhook delivery was already processed."""
        return self.session.scalars(
            select(EmailWebhookEvent.id).where(EmailWebhookEvent.svix_id == svix_id)).first() is not None

    def add_webhook_event(self, event: EmailWebhookEvent) -> EmailWebhookEvent:
        """Remember a processed webhook delivery."""
        self.session.add(event)
        self.session.flush()
        return event
