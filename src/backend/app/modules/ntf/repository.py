"""NTF storage."""

from sqlalchemy import select

from app.modules.ntf.models import Notification
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
