"""NTF email through Resend: channel, factory, admin API, retry, signed webhook (issue #76, NTF-FR-08, BR-12).

The Resend SDK is never called: ResendEmailChannel takes an injected sender, and one test patches the SDK itself.
"""

import base64
import json
from datetime import datetime, timedelta, timezone

import pytest
from svix.webhooks import Webhook

from app.core.config import Settings
from app.modules.ntf.channels import (
    EmailChannelFactory,
    LoggingEmailChannel,
    ResendEmailChannel,
)
from app.modules.ntf.models import EmailStatus, EmailWebhookEvent, Notification
from app.shared.audit import AuditRecord
from app.modules.ntf.emails import EmailComposer
from app.shared.events import EventType

SECRET = "whsec_" + base64.b64encode(b"test-webhook-secret-bytes").decode()
API_KEY = "re_test_key_do_not_leak"


class FakeResend:
    """Stands in for ``resend.Emails.send``."""

    def __init__(self) -> None:
        self.calls: list[dict] = []
        self.error: Exception | None = None

    def __call__(self, params: dict) -> dict:
        if self.error:
            raise self.error
        self.calls.append(params)
        return {"id": f"re-{len(self.calls)}"}


def with_(settings: Settings, **changes) -> Settings:
    """A copy of the settings with some fields changed (validated, so secrets stay SecretStr)."""
    return Settings(**{**settings.model_dump(), **changes})


@pytest.fixture
def settings(settings: Settings) -> Settings:
    return with_(settings, resend_api_key=API_KEY, email_from="IT Inventory Tracker <noreply@example.edu>",
                 resend_webhook_secret=SECRET, app_base_url="https://app.example.edu",
                 session_timeout_minutes=10**6)  # tests move the clock by days


@pytest.fixture
def resend(app, settings) -> FakeResend:
    fake = FakeResend()
    app.state.email_channel = ResendEmailChannel(API_KEY, settings.email_from, "help@example.edu", sender=fake)
    return fake


@pytest.fixture
def no_email(app) -> None:
    """Email not configured: the app falls back to the logging channel."""
    app.state.email_channel = LoggingEmailChannel()


@pytest.fixture
def sa_id(client, admin_headers, sa_headers, db) -> int:
    """The SA's id; the welcome notification from creating the account is cleared first."""
    db.query(Notification).filter_by(event_type=EventType.ACCOUNT_CREATED).delete()
    db.commit()
    return client.get("/auth/me", headers=sa_headers).json()["id"]


def notify(client, admin_headers, sa_id) -> int:
    response = client.post("/notifications/shift-summary", headers=admin_headers,
                           json={"shift": "MORNING", "shift_date": "2026-01-05", "user_ids": [sa_id]})
    assert response.status_code == 201, response.text
    return response.json()[0]["id"]


def post_webhook(client, event: dict, msg_id: str = "msg_1", when: datetime | None = None, secret: str = SECRET):
    body = json.dumps(event)
    stamp = when or datetime.now(timezone.utc)
    signature = Webhook(secret).sign(msg_id, stamp, body)
    return client.post("/webhooks/resend", content=body, headers={
        "svix-id": msg_id, "svix-timestamp": str(int(stamp.timestamp())), "svix-signature": signature,
        "content-type": "application/json"})


# ---- channel and factory --------------------------------------------------------------------------------------------

def test_resend_channel_sends_text_and_html_and_returns_the_message_id():
    fake = FakeResend()
    channel = ResendEmailChannel(API_KEY, "App <noreply@example.edu>", "help@example.edu", sender=fake)
    assert channel.send("sa@sfbu.edu", "Subject", "Hello <b>", "<p>Hello</p>") == "re-1"
    assert fake.calls == [{"from": "App <noreply@example.edu>", "to": ["sa@sfbu.edu"], "subject": "Subject",
                           "text": "Hello <b>", "html": "<p>Hello</p>", "reply_to": "help@example.edu"}]


def test_resend_channel_uses_the_sdk_with_its_own_key(monkeypatch):
    import resend
    seen = {}

    def fake_send(params):
        seen["key"] = resend.api_key
        return {"id": "sdk-1"}

    monkeypatch.setattr(resend.Emails, "send", staticmethod(fake_send))
    assert ResendEmailChannel(API_KEY, "a@example.edu").send("b@sfbu.edu", "s", "b") == "sdk-1"
    assert seen["key"] == API_KEY


def test_factory_picks_resend_only_when_key_and_sender_are_set(settings):
    assert isinstance(EmailChannelFactory.from_settings(settings), ResendEmailChannel)
    assert settings.email_enabled
    for missing in ("resend_api_key", "email_from"):
        off = with_(settings, **{missing: None})
        assert not off.email_enabled
        assert isinstance(EmailChannelFactory.from_settings(off), LoggingEmailChannel)


def test_html_escapes_the_message_and_links_to_the_record():
    email = EmailComposer().compose(EventType.GENERAL, "<script>x</script>\nline two",
                                    record_url="https://app.example.edu/orders/7")
    assert "<script>x" not in email.html and "&lt;script&gt;" in email.html
    assert 'href="https://app.example.edu/orders/7"' in email.html and "Open in IT HUB" in email.html


def test_notification_email_has_text_html_and_link(client, admin_headers, sa_id, resend, db):
    client.post("/notifications/shift-summary", headers=admin_headers,
                json={"shift": "MORNING", "shift_date": "2026-01-05", "user_ids": [sa_id]})
    call = resend.calls[0]
    assert call["to"] == ["sa@sfbu.edu"] and "shift summary" in call["text"]
    assert call["subject"] == "Your open tasks for the Morning shift, Jan 5, 2026" and "Shift summary" in call["html"]


def test_success_stores_message_id_and_sent(client, admin_headers, sa_id, resend, db):
    note_id = notify(client, admin_headers, sa_id)
    note = db.get(Notification, note_id)
    assert (note.email_status, note.email_message_id, note.email_attempts) == (EmailStatus.SENT, "re-1", 1)
    assert note.email_sent_at is not None


def test_logging_channel_marks_notifications_skipped(no_email, client, admin_headers, sa_id, db):
    note = db.get(Notification, notify(client, admin_headers, sa_id))
    assert (note.email_status, note.email_message_id) == (EmailStatus.SKIPPED, None)


def test_provider_error_marks_failed_and_keeps_the_in_app_notification(client, admin_headers, sa_headers, sa_id, resend):
    resend.error = RuntimeError("provider down")
    note_id = notify(client, admin_headers, sa_id)
    mine = client.get(f"/notifications/{note_id}", headers=sa_headers).json()
    assert mine["email_status"] == "FAILED" and mine["email_attempts"] == 1
    row = client.get("/notifications/email/deliveries?status=FAILED", headers=admin_headers).json()[0]
    assert row["error"] == "provider down" and row["id"] == note_id


# ---- admin API ------------------------------------------------------------------------------------------------------

def test_config_route_hides_the_key(client, admin_headers, resend):
    response = client.get("/notifications/email/config", headers=admin_headers)
    assert response.json() == {"enabled": True, "provider": "resend",
                               "from_address": "IT Inventory Tracker <noreply@example.edu>", "webhook_enabled": True}
    assert API_KEY not in response.text and SECRET not in response.text


def test_config_route_reports_logging_when_unconfigured(no_email, client, admin_headers):
    assert client.get("/notifications/email/config", headers=admin_headers).json() == {
        "enabled": False, "provider": "log", "from_address": None, "webhook_enabled": True}


def test_email_admin_routes_are_admin_only(client, sa_headers, sa_id):
    for method, path in (("get", "/notifications/email/config"), ("post", "/notifications/email/test"),
                         ("get", "/notifications/email/deliveries")):
        assert client.request(method, path, headers=sa_headers).status_code == 403, path


def test_test_email_defaults_to_me_and_is_audited(client, admin_headers, resend, db):
    response = client.post("/notifications/email/test", headers=admin_headers, json={})
    assert response.json() == {"status": "SENT", "message_id": "re-1"}
    assert resend.calls[0]["to"] == ["admin@sfbu.edu"]
    assert client.post("/notifications/email/test", headers=admin_headers, json={"to": "x@sfbu.edu"}).status_code == 200
    assert db.query(AuditRecord).filter_by(action="EMAIL_TEST").count() == 2


def test_test_email_is_503_when_disabled(no_email, client, admin_headers):
    response = client.post("/notifications/email/test", headers=admin_headers, json={})
    assert (response.status_code, response.json()) == (503, {"detail": "Email sending is not configured."})


def test_test_email_provider_error_is_502_without_details(client, admin_headers, resend):
    resend.error = RuntimeError("secret provider detail")
    response = client.post("/notifications/email/test", headers=admin_headers, json={})
    assert response.status_code == 502 and "secret" not in response.text


def test_deliveries_filter_by_status_recipient_and_date(client, admin_headers, sa_id, resend, clock):
    notify(client, admin_headers, sa_id)
    clock.advance(days=3)
    resend.error = RuntimeError("down")
    failed = notify(client, admin_headers, sa_id)
    rows = client.get("/notifications/email/deliveries", headers=admin_headers).json()
    assert [r["id"] for r in rows][0] == failed and len(rows) == 2
    only = client.get("/notifications/email/deliveries?status=SENT", headers=admin_headers).json()
    assert len(only) == 1 and only[0]["attempts"] == 1 and only[0]["sent_at"]
    assert len(client.get(f"/notifications/email/deliveries?recipient_id={sa_id}", headers=admin_headers).json()) == 2
    assert len(client.get("/notifications/email/deliveries?recipient_id=999", headers=admin_headers).json()) == 0
    assert len(client.get("/notifications/email/deliveries?date_from=2026-01-07", headers=admin_headers).json()) == 1
    assert len(client.get("/notifications/email/deliveries?date_to=2026-01-05", headers=admin_headers).json()) == 1


# ---- retry ----------------------------------------------------------------------------------------------------------

def test_owner_can_retry_a_failed_email_and_it_is_audited(client, admin_headers, sa_headers, sa_id, resend, db):
    resend.error = RuntimeError("down")
    note_id = notify(client, admin_headers, sa_id)
    resend.error = None
    response = client.post(f"/notifications/{note_id}/email/retry", headers=sa_headers)
    assert response.status_code == 200
    assert (response.json()["email_status"], response.json()["email_attempts"]) == ("SENT", 2)
    assert db.query(AuditRecord).filter_by(action="EMAIL_RETRY", entity_id=str(note_id)).count() == 1


def test_admin_can_retry_but_other_users_cannot(client, admin_headers, sa_headers, sa_id, resend):
    resend.error = RuntimeError("down")
    note_id = notify(client, admin_headers, sa_id)
    resend.error = None
    other = client.post("/users", headers=admin_headers, json={
        "full_name": "Other Sa", "email": "o@sfbu.edu", "school_id": "SA-002", "role": "STUDENT_ASSISTANT",
        "temporary_password": "TempOther123"}).status_code
    assert other == 201
    token = client.post("/auth/login", json={"email": "o@sfbu.edu", "password": "TempOther123"}).json()["access_token"]
    stranger = {"Authorization": f"Bearer {token}"}
    assert client.post(f"/notifications/{note_id}/email/retry", headers=stranger).status_code in (403, 404)
    assert client.post(f"/notifications/{note_id}/email/retry", headers=admin_headers).status_code == 200


def test_only_failed_or_bounced_emails_can_be_retried(client, admin_headers, sa_headers, sa_id, resend):
    note_id = notify(client, admin_headers, sa_id)  # SENT
    response = client.post(f"/notifications/{note_id}/email/retry", headers=sa_headers)
    assert (response.status_code, response.json()["detail"]) == (409, "Only a failed or bounced email can be retried.")


def test_retry_stops_after_three_attempts(client, admin_headers, sa_headers, sa_id, resend):
    resend.error = RuntimeError("down")
    note_id = notify(client, admin_headers, sa_id)
    for _ in range(2):
        assert client.post(f"/notifications/{note_id}/email/retry", headers=sa_headers).json()["email_status"] == "FAILED"
    response = client.post(f"/notifications/{note_id}/email/retry", headers=sa_headers)
    assert response.status_code == 409 and "maximum" in response.json()["detail"]


# ---- webhook --------------------------------------------------------------------------------------------------------

def event(kind: str, email_id: str = "re-1") -> dict:
    return {"type": kind, "created_at": "2026-01-05T09:00:00Z", "data": {"email_id": email_id}}


@pytest.mark.parametrize("kind,status", [("email.delivered", "DELIVERED"), ("email.bounced", "BOUNCED"),
                                         ("email.complained", "COMPLAINED")])
def test_webhook_maps_events_onto_the_notification(client, admin_headers, sa_headers, sa_id, resend, db, kind, status):
    note_id = notify(client, admin_headers, sa_id)
    assert post_webhook(client, event(kind)).status_code == 200
    assert client.get(f"/notifications/{note_id}", headers=sa_headers).json()["email_status"] == status
    audit = db.query(AuditRecord).filter_by(action="EMAIL_EVENT").one()
    assert audit.actor_id is None


def test_delivery_delayed_keeps_the_status(client, admin_headers, sa_headers, sa_id, resend):
    note_id = notify(client, admin_headers, sa_id)
    assert post_webhook(client, event("email.delivery_delayed")).status_code == 200
    assert client.get(f"/notifications/{note_id}", headers=sa_headers).json()["email_status"] == "SENT"


def test_a_bounced_email_can_be_retried(client, admin_headers, sa_headers, sa_id, resend):
    note_id = notify(client, admin_headers, sa_id)
    post_webhook(client, event("email.bounced"))
    assert client.post(f"/notifications/{note_id}/email/retry", headers=sa_headers).json()["email_status"] == "SENT"


def test_webhook_rejects_a_bad_signature(client, admin_headers, sa_id, resend):
    other = "whsec_" + base64.b64encode(b"another-secret-bytes!").decode()
    assert post_webhook(client, event("email.delivered"), secret=other).status_code == 401
    assert client.post("/webhooks/resend", content="{}", headers={"svix-id": "x"}).status_code == 401


def test_webhook_rejects_a_stale_signature(client, admin_headers, sa_id, resend):
    old = datetime.now(timezone.utc) - timedelta(minutes=30)
    assert post_webhook(client, event("email.delivered"), when=old).status_code == 401


def test_webhook_is_503_without_a_secret(client, app, settings):
    app.state.settings = with_(settings, resend_webhook_secret=None)
    assert post_webhook(client, event("email.delivered")).status_code == 503


def test_webhook_is_idempotent_on_the_svix_id(client, admin_headers, sa_headers, sa_id, resend, db):
    note_id = notify(client, admin_headers, sa_id)
    assert post_webhook(client, event("email.bounced"), msg_id="same").status_code == 200
    client.post(f"/notifications/{note_id}/email/retry", headers=sa_headers)  # back to SENT
    assert post_webhook(client, event("email.bounced"), msg_id="same").status_code == 200  # replay ignored
    assert client.get(f"/notifications/{note_id}", headers=sa_headers).json()["email_status"] == "SENT"
    assert db.query(EmailWebhookEvent).count() == 1
    assert db.query(AuditRecord).filter_by(action="EMAIL_EVENT").count() == 1


def test_webhook_ignores_unknown_emails(client, resend, db):
    assert post_webhook(client, event("email.delivered", "nope")).status_code == 200
    assert db.query(EmailWebhookEvent).count() == 0


def test_email_links_open_the_record_page_of_the_served_frontend():
    from types import SimpleNamespace

    from app.modules.ntf.service import NotificationService

    service = SimpleNamespace(app_base_url="http://127.0.0.1:8000/app")
    order = SimpleNamespace(related_type="Order", related_id=7)
    unknown = SimpleNamespace(related_type="Something", related_id=3)
    task = SimpleNamespace(related_type="Task", related_id=4)
    none = SimpleNamespace(related_type=None, related_id=None)
    assert NotificationService._link(service, order) == "http://127.0.0.1:8000/app/orders.html?id=7"
    assert NotificationService._link(service, unknown) == "http://127.0.0.1:8000/app/notifications.html?id=3"
    assert NotificationService._link(service, task) == "http://127.0.0.1:8000/app/projects.html?task=4"
    assert NotificationService._link(service, none) is None
