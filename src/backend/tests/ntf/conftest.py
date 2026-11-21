"""NTF fixtures: build the same publisher/service the app builds per request."""

import pytest
from sqlalchemy.orm import Session

from app.modules.ntf.channels import EmailChannel
from app.modules.ntf.models import Notification
from app.modules.ntf.repository import NotificationRepository
from app.modules.ntf.service import NotificationService
from app.modules.usr.repository import UserRepository
from app.shared.audit import AuditLog
from app.shared.events import EventPublisher, EventType


class RecordingEmail(EmailChannel):
    """Collects emails; raises when ``fail`` is set."""

    def __init__(self) -> None:
        self.sent: list[tuple[str, str, str]] = []
        self.fail = False

    def send(self, to_address: str, subject: str, body: str, html: str | None = None) -> str | None:
        if self.fail:
            raise RuntimeError("SMTP down")
        self.sent.append((to_address, subject, body))
        return f"msg-{len(self.sent)}"


@pytest.fixture
def email() -> RecordingEmail:
    return RecordingEmail()


@pytest.fixture
def service(db: Session, clock, email: RecordingEmail) -> NotificationService:
    return NotificationService(
        NotificationRepository(db), UserRepository(db), email, AuditLog(db, clock), clock)


@pytest.fixture
def publisher(db: Session, service: NotificationService) -> EventPublisher:
    pub = EventPublisher(db)
    pub.subscribe(service)
    return pub


@pytest.fixture
def user_ids(db: Session, admin_headers, sa_headers) -> dict[str, int]:
    """ids of the seeded Admin and the SA; the SA's welcome notification is cleared so tests start empty."""
    db.query(Notification).filter_by(event_type=EventType.ACCOUNT_CREATED).delete()
    db.commit()
    users = UserRepository(db)
    return {"admin": users.get_by_email("admin@sfbu.edu").id, "sa": users.get_by_email("sa@sfbu.edu").id}
