"""NTF routes: /notifications."""

from datetime import date

from fastapi import APIRouter, Body, Depends, Request
from fastapi.responses import HTMLResponse

from app.core.config import Settings
from app.core.deps import (
    get_current_user,
    get_email_channel,
    get_notification_service,
    get_settings,
    require_role,
)
from app.modules.ntf.channels import EmailChannel
from app.modules.ntf.emails import TEMPLATES, EmailComposer
from app.modules.ntf.models import EmailStatus, Notification
from app.modules.ntf.schemas import (
    EmailConfigRead,
    EmailDeliveryRead,
    EmailTemplateRead,
    EmailTestRequest,
    EmailTestResult,
    NotificationRead,
    ReadStateUpdate,
    ShiftSummaryRequest,
    WebhookAck,
)
from app.core.exceptions import ServiceUnavailableError
from app.modules.ntf.service import NotificationService
from app.modules.ntf.webhooks import SvixWebhookVerifier
from app.modules.usr.models import Role, User
from app.shared.events import EventType

router = APIRouter(prefix="/notifications", tags=["notifications"])
webhooks_router = APIRouter(prefix="/webhooks", tags=["webhooks"])
MSG_WEBHOOK_OFF = "Email webhooks are not configured."


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
    return service.send_shift_summary(body.shift, body.shift_date, body.user_ids, sender=user)


@router.get("/email/config", response_model=EmailConfigRead)
def get_email_config(
    admin: User = Depends(require_role(Role.ADMIN)),
    channel: EmailChannel = Depends(get_email_channel),
    settings: Settings = Depends(get_settings),
) -> EmailConfigRead:
    """Admin: how email sending is configured (NTF-FR-08); the API key is never shown."""
    return EmailConfigRead(
        enabled=channel.real, provider=channel.provider,  # type: ignore[arg-type]
        from_address=settings.email_from if channel.real else None,
        webhook_enabled=settings.resend_webhook_secret is not None)


@router.post("/email/test", response_model=EmailTestResult)
def send_test_email(
    body: EmailTestRequest = Body(default_factory=EmailTestRequest),
    admin: User = Depends(require_role(Role.ADMIN)),
    service: NotificationService = Depends(get_notification_service),
) -> EmailTestResult:
    """Admin: send a test email (default: to me) to check the provider setup."""
    status, message_id = service.send_test_email(admin, body.to or admin.email)
    return EmailTestResult(status=status, message_id=message_id)


@router.get("/email/templates", response_model=list[EmailTemplateRead])
def list_email_templates(
    admin: User = Depends(require_role(Role.ADMIN)),
    settings: Settings = Depends(get_settings),
) -> list[EmailTemplateRead]:
    """The designed emails and a sample subject for each (Admin only, #108)."""
    composer = EmailComposer(settings.app_base_url)
    return [EmailTemplateRead(event_type=event, template=template.file, subject=composer.preview(event).subject)
            for event, template in TEMPLATES.items()]


@router.get("/email/templates/{event_type}/preview", response_class=HTMLResponse)
def preview_email_template(
    event_type: EventType,
    admin: User = Depends(require_role(Role.ADMIN)),
    settings: Settings = Depends(get_settings),
) -> HTMLResponse:
    """One email rendered with sample values, to check the design in a browser (Admin only)."""
    composer = EmailComposer(settings.app_base_url)
    if event_type not in TEMPLATES:
        return HTMLResponse(composer.compose(event_type, f"{event_type.value} sample message.").html)
    return HTMLResponse(composer.preview(event_type).html)


@router.get("/email/deliveries", response_model=list[EmailDeliveryRead])
def list_email_deliveries(
    status: EmailStatus | None = None,
    recipient_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    admin: User = Depends(require_role(Role.ADMIN)),
    service: NotificationService = Depends(get_notification_service),
) -> list[Notification]:
    """Admin: email delivery log, newest first."""
    return service.deliveries(status, recipient_id, date_from, date_to)


@router.post("/{notification_id}/email/retry", response_model=NotificationRead)
def retry_email(
    notification_id: int,
    user: User = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
) -> Notification:
    """Re-send a failed or bounced email (owner or Admin, at most 3 attempts)."""
    return service.retry_email(user, notification_id)


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


@webhooks_router.post("/resend", response_model=WebhookAck)
async def resend_webhook(
    request: Request,
    settings: Settings = Depends(get_settings),
    service: NotificationService = Depends(get_notification_service),
) -> WebhookAck:
    """Public, signature-verified: Resend delivery events (delivered, bounced, complained)."""
    if settings.resend_webhook_secret is None:
        raise ServiceUnavailableError(MSG_WEBHOOK_OFF)
    verifier = SvixWebhookVerifier(settings.resend_webhook_secret.get_secret_value())
    payload = verifier.verify(await request.body(), dict(request.headers))
    service.apply_webhook_event(request.headers["svix-id"], payload)
    return WebhookAck()
