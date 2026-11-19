"""NTF routes: /notifications."""

from fastapi import APIRouter, Depends

from app.core.deps import get_current_user, get_notification_service
from app.modules.ntf.models import Notification
from app.modules.ntf.schemas import NotificationRead, ReadStateUpdate, ShiftSummaryRequest
from app.modules.ntf.service import NotificationService
from app.modules.usr.models import User

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationRead])
def list_notifications(
    unread_only: bool = False,
    user: User = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
) -> list[Notification]:
    """My notifications, newest first (FR-NTF-04)."""
    return service.list_for_user(user, unread_only)


@router.post("/shift-summary", response_model=list[NotificationRead], status_code=201)
def send_shift_summary(
    body: ShiftSummaryRequest,
    user: User = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
) -> list[Notification]:
    """Send each rostered user their shift work summary (FR-NTF-03)."""
    return service.send_shift_summary(body.shift, body.shift_date, body.user_ids)


@router.get("/{notification_id}", response_model=NotificationRead)
def get_notification(
    notification_id: int,
    user: User = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
) -> Notification:
    """One of my notifications (FR-NTF-08)."""
    return service.get_for_user(user, notification_id)


@router.patch("/{notification_id}", response_model=NotificationRead)
def set_read_state(
    notification_id: int,
    body: ReadStateUpdate,
    user: User = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
) -> Notification:
    """Mark one of my notifications read or unread (FR-NTF-05)."""
    return service.set_read(user, notification_id, body.read)
