"""NotificationService: Observer of domain events (US-NTF-01..07)."""

from datetime import date
from enum import Enum

from app.core.clock import Clock
from app.core.exceptions import NotFoundError, ValidationRuleError
from app.modules.ntf.channels import EmailChannel
from app.modules.ntf.models import EmailStatus, Notification
from app.modules.ntf.ports import (
    NoProjectMembership,
    NoScheduledWork,
    ProjectMembership,
    ScheduledWork,
    ScheduledWorkSource,
)
from app.modules.ntf.repository import NotificationRepository
from app.modules.usr.models import Role, User, UserStatus
from app.modules.usr.repository import UserRepository
from app.shared.audit import AuditLog
from app.shared.events import DomainEvent, EventType

PROJECT_EVENTS = {EventType.PROJECT_CREATED, EventType.PROJECT_UPDATED, EventType.PROJECT_MEMBER_ADDED}
ADMIN_EVENTS = {EventType.ISSUE_REPORTED, EventType.REPEAT_PROBLEM, EventType.LOW_STOCK,
                EventType.ORDER_ARRIVED, EventType.MONTHLY_SUMMARY}
MSG_NO_RECIPIENTS = "At least one staff member is required."


class ShiftName(str, Enum):
    """Supported shifts (roster source is still an open decision, so the caller supplies it)."""

    MORNING = "MORNING"
    AFTERNOON = "AFTERNOON"
    EVENING = "EVENING"


class NotificationService:
    """Creates, routes and delivers notifications; implements EventObserver and StockObserver."""

    def __init__(self, notifications: NotificationRepository, users: UserRepository,
                 email: EmailChannel, audit: AuditLog, clock: Clock,
                 membership: ProjectMembership | None = None,
                 work: ScheduledWorkSource | None = None) -> None:
        self.notifications = notifications
        self.users = users
        self.email = email
        self.audit = audit
        self.clock = clock
        self.membership = membership or NoProjectMembership()
        self.work = work or NoScheduledWork()

    # ---- Observer entry points -------------------------------------------

    def handle(self, event: DomainEvent) -> list[Notification]:
        """EventObserver: one notification per resolved recipient (NTF-FR-01/02)."""
        return [
            self._create(user, event.event_type, event.message, event.related_type,
                         event.related_id, event.project_id, event.actor_id)
            for user in self._resolve_recipients(event)
        ]

    def on_low_stock(self, asset_id: int, available_quantity: int) -> list[Notification]:
        """StockObserver: tell the Admins an item is low (SP5)."""
        return self.handle(DomainEvent(
            EventType.LOW_STOCK,
            f"Low stock: item {asset_id} has {available_quantity} left.",
            related_type="Asset", related_id=asset_id,
        ))

    def notify(self, recipient: User, message: str, event_type: EventType = EventType.GENERAL,
               related_type: str | None = None, related_id: int | None = None) -> Notification:
        """Direct entry point (SP5 ``notify``): one notification for one user."""
        return self._create(recipient, event_type, message, related_type, related_id, None, None)

    # ---- Shift summary (FR-NTF-03) ---------------------------------------

    def send_shift_summary(self, shift: ShiftName, shift_date: date,
                           roster_user_ids: list[int]) -> list[Notification]:
        """Notify each rostered user of their unfinished work due on/before the shift date."""
        if not roster_user_ids:
            raise ValidationRuleError(MSG_NO_RECIPIENTS)
        created = []
        for user in self._active_users(dict.fromkeys(roster_user_ids)):
            tasks = self.work.open_work_for_user(user.id, shift_date)
            created.append(self._create(
                user, EventType.SHIFT_SUMMARY, self._summary_text(shift, shift_date, tasks),
                "Shift", None, None, None))
        return created

    @staticmethod
    def _summary_text(shift: ShiftName, shift_date: date, tasks: list[ScheduledWork]) -> str:
        head = f"{shift.value.title()} shift summary for {shift_date.isoformat()}"
        if not tasks:
            return f"{head}: no work scheduled."
        lines = [
            f"- #{t.id} {t.title} (due {t.due_date.isoformat()}"
            f"{', overdue' if t.due_date < shift_date else ''})"
            for t in tasks
        ]
        return f"{head}: {len(tasks)} task(s).\n" + "\n".join(lines)

    # ---- Reading (US-NTF-04/05) ------------------------------------------

    def list_for_user(self, user: User, unread_only: bool = False) -> list[Notification]:
        """The user's own notifications."""
        return self.notifications.list_for_user(user.id, unread_only)

    def get_for_user(self, user: User, notification_id: int) -> Notification:
        """One of the user's notifications; someone else's looks like not found."""
        notification = self.notifications.get_or_raise(notification_id)
        if notification.recipient_id != user.id:
            raise NotFoundError(self.notifications.not_found_message)
        return notification

    def set_read(self, user: User, notification_id: int, read: bool) -> Notification:
        """Mark one notification read or unread and audit it (NFR-NTF-01)."""
        notification = self.get_for_user(user, notification_id)
        old = {"read": notification.is_read}
        notification.read_at = self.clock() if read else None
        self.notifications.flush()
        self.audit.record(user, "READ" if read else "UNREAD", "Notification", notification.id,
                          old, {"read": read})
        return notification

    # ---- internals --------------------------------------------------------

    def _resolve_recipients(self, event: DomainEvent) -> list[User]:
        if event.recipient_ids:
            ids: list[int] = list(event.recipient_ids)
        elif event.event_type in PROJECT_EVENTS and event.project_id is not None:
            ids = self.membership.member_ids(event.project_id)  # members only (BR-16)
        elif event.event_type in ADMIN_EVENTS:
            ids = [u.id for u in self.users.search(Role.ADMIN, UserStatus.ACTIVE)]
        else:
            ids = []
        return self._active_users(i for i in ids if i != event.actor_id)

    def _active_users(self, ids) -> list[User]:
        users = (self.users.get(i) for i in dict.fromkeys(ids))
        return [u for u in users if u is not None and u.status == UserStatus.ACTIVE]

    def _create(self, recipient: User, event_type: EventType, message: str,
                related_type: str | None, related_id: int | None, project_id: int | None,
                actor_id: int | None) -> Notification:
        notification = self.notifications.add(Notification(
            recipient_id=recipient.id, event_type=event_type, message=message,
            related_type=related_type, related_id=related_id, project_id=project_id,
            triggered_by=actor_id, created_at=self.clock(),
        ))
        self._deliver_email(notification, recipient)
        self.audit.record(actor_id, "CREATE", "Notification", notification.id, None, {
            "recipient_id": recipient.id, "event_type": event_type.value,
            "related_type": related_type, "related_id": related_id,
            "email_status": notification.email_status.value,
        })
        return notification

    def _deliver_email(self, notification: Notification, recipient: User) -> None:
        """Send the email copy; a failure is recorded, never raised (FR-NTF-07)."""
        try:
            self.email.send(recipient.email, f"IT Inventory Tracker: {notification.event_type.value}",
                            notification.message)
            notification.email_status = EmailStatus.SENT
        except Exception as exc:  # noqa: BLE001 - delivery failure must not drop the notification
            notification.email_status = EmailStatus.FAILED
            notification.email_error = str(exc)[:255] or exc.__class__.__name__
        self.notifications.flush()
