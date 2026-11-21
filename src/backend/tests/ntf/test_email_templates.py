"""Branded email templates (#108): every designed email is sent with all its values, through the real flows."""

import pytest

from app.modules.ntf.channels import EmailChannel
from app.modules.ntf.emails import COMMON_VARIABLES, SAMPLE_DETAILS, TEMPLATES, EmailComposer
from app.modules.ntf.models import EmailStatus, Notification
from app.shared.events import EventType
from tests.test_e2e import install_desktop, make_location, ok

BASE = "https://ithub.example.edu/app"


class CapturingEmail(EmailChannel):
    """Records every email the app sends."""

    real = True

    def __init__(self) -> None:
        self.sent: list[dict] = []

    def send(self, to_address: str, subject: str, body: str, html: str | None = None) -> str | None:
        self.sent.append({"to": to_address, "subject": subject, "text": body, "html": html or ""})
        return f"msg-{len(self.sent)}"

    def to(self, address: str) -> list[dict]:
        return [m for m in self.sent if m["to"] == address]


@pytest.fixture
def settings(settings):
    """Shared settings with a public frontend address, so links and the logo are absolute."""
    return settings.model_copy(update={"app_base_url": BASE})


@pytest.fixture
def mail(app) -> CapturingEmail:
    channel = CapturingEmail()
    app.state.email_channel = channel
    return channel


def ids(client, admin_headers, sa_headers) -> dict[str, int]:
    return {"admin": client.get("/auth/me", headers=admin_headers).json()["id"],
            "sa": client.get("/auth/me", headers=sa_headers).json()["id"]}


def assert_branded(email: dict) -> None:
    """Designed layout, nothing left unrendered, logo served by the frontend."""
    html = email["html"]
    assert "{{" not in html and "{%" not in html
    assert f'src="{BASE}/assets/brand/it-hub-logo-email.png"' in html
    assert "<title>" in html and "IT HUB &middot; SFBU IT Department" in html


# ---- the templates themselves ---------------------------------------------------------------------------------

@pytest.mark.parametrize("event_type", list(TEMPLATES), ids=lambda e: e.value)
def test_every_designed_email_renders_its_sample(event_type):
    composer = EmailComposer(BASE)
    template = TEMPLATES[event_type]
    needed = template.variables(composer.environment) - COMMON_VARIABLES - {template.link_variable}
    assert needed - set(template.extra_links or {}) <= set(SAMPLE_DETAILS[event_type])
    email = composer.preview(event_type)
    assert not email.subject.startswith("IT HUB:")  # the designed email, not the general one
    assert_branded({"subject": email.subject, "html": email.html})


def test_values_are_escaped():
    details = {**SAMPLE_DETAILS[EventType.TASK_ASSIGNED], "task_title": "<img src=x onerror=alert(1)>"}
    email = EmailComposer(BASE).compose(EventType.TASK_ASSIGNED, "x", details)
    assert "<img src=x" not in email.html and "&lt;img src=x" in email.html


def test_an_event_without_its_details_uses_the_general_design():
    email = EmailComposer(BASE).compose(EventType.TASK_ASSIGNED, "You were assigned task #3: Image PCs",
                                        {}, f"{BASE}/projects.html?task=3")
    assert email.subject == "IT HUB: You were assigned task #3: Image PCs"
    assert "Open in IT HUB" in email.html and f"{BASE}/projects.html?task=3" in email.text


def test_admin_can_list_and_preview_the_designs(client, admin_headers, sa_headers):
    listed = ok(client.get("/notifications/email/templates", headers=admin_headers))
    assert {t["template"] for t in listed} == {t.file for t in TEMPLATES.values()}
    page = client.get("/notifications/email/templates/TASK_ASSIGNED/preview", headers=admin_headers)
    assert page.status_code == 200 and page.headers["content-type"].startswith("text/html")
    assert "Morgan Lee assigned you a task" in page.text
    general = client.get("/notifications/email/templates/PROJECT_UPDATED/preview", headers=admin_headers)
    assert general.status_code == 200 and "Open in IT HUB" not in general.text
    assert client.get("/notifications/email/templates", headers=sa_headers).status_code == 403


# ---- each real flow sends its designed email ------------------------------------------------------------------

def test_welcome_email_never_contains_the_temporary_password(client, admin_headers, mail):
    ok(client.post("/users", headers=admin_headers, json={
        "full_name": "Pat Nguyen", "email": "pat@sfbu.edu", "school_id": "SA-777",
        "role": "STUDENT_ASSISTANT", "temporary_password": "TempPat12345", "access_end_date": "2027-05-31"}), 201)
    (email,) = mail.to("pat@sfbu.edu")
    assert email["subject"] == "Welcome to IT HUB"
    assert "Welcome to IT HUB, Pat" in email["html"] and "May 31, 2027" in email["html"]
    assert f'href="{BASE}/login.html"' in email["html"]
    assert "TempPat12345" not in email["html"] + email["text"]
    assert_branded(email)


def test_password_reset_email(client, admin_headers, sa_headers, mail):
    sa = ids(client, admin_headers, sa_headers)["sa"]
    ok(client.post(f"/users/{sa}/reset-password", headers=admin_headers, json={"temporary_password": "ResetPass123"}))
    (email,) = mail.to("sa@sfbu.edu")
    assert email["subject"] == "Your IT HUB password was reset"
    assert "admin@sfbu.edu" in email["html"] and "ResetPass123" not in email["html"] + email["text"]


def test_task_assigned_email(client, admin_headers, sa_headers, mail):
    sa = ids(client, admin_headers, sa_headers)["sa"]
    project = ok(client.post("/projects", headers=admin_headers, json={
        "name": "Lab refresh", "description": "", "start_date": "2026-02-01", "due_date": "2026-03-01",
        "status": "ACTIVE"}), 201)
    task = ok(client.post("/tasks", headers=admin_headers, json={
        "title": "Image PCs", "description": "Room 204", "project_id": project["id"], "priority": "HIGH",
        "due_date": "2026-02-10"}), 201)
    ok(client.put(f"/tasks/{task['id']}/assignees", headers=admin_headers, json={"user_ids": [sa]}))
    (email,) = [m for m in mail.to("sa@sfbu.edu") if "assigned you" in m["subject"]]
    assert email["subject"] == "System Administrator assigned you: Image PCs"
    for text in ("Lab refresh", "High", "Feb 10, 2026", "Room 204", f"{BASE}/projects.html?task={task['id']}"):
        assert text in email["html"]
    assert_branded(email)


def test_issue_reported_email_tells_admins_what_changed(client, admin_headers, sa_headers, mail):
    room, equipment, item = install_desktop(client, admin_headers, sa_headers)
    issue = ok(client.post("/issues", headers=sa_headers, json={
        "classroom_id": room["id"], "room_equipment_id": equipment["id"], "category": "HARDWARE",
        "severity": "HIGH", "description": "Will not boot", "reporter_name": "Dr. Lee",
        "reporter_type": "FACULTY"}), 201)
    (email,) = mail.to("admin@sfbu.edu")
    assert email["subject"] == f"High issue in Main 101: {issue['issue_id']}"
    for text in ("Will not boot", "Dr. Lee (Faculty)", f"Desktop #{item['id']}",
                 "The reported item is now marked Faulty."):
        assert text in email["html"]


def test_low_stock_email_names_the_order_it_created(client, admin_headers, sa_headers, mail):
    category = ok(client.post("/ast/categories", headers=admin_headers, json={"name": "Cables", "is_consumable": True}), 201)
    location = make_location(client, admin_headers)
    supply = ok(client.post("/ast/consumables", headers=sa_headers, json={
        "name": "HDMI cable", "category_id": category["id"], "location_id": location["id"],
        "reorder_threshold": 5, "unit": "pcs"}), 201)
    ok(client.post(f"/ast/consumables/{supply['id']}/stock-in", headers=sa_headers, json={"quantity": 10}))
    ok(client.post(f"/ast/consumables/{supply['id']}/stock-out", headers=sa_headers,
                   json={"quantity": 6, "issued_to": "Room 101"}))
    (order,) = ok(client.get("/orders", headers=sa_headers))
    (email,) = mail.to("admin@sfbu.edu")
    assert email["subject"] == f"Stock low: HDMI cable · order #{order['id']} created"
    for text in ("4 pcs", "5 pcs", f"#{order['id']} · 6 pcs", "Main 101", "created an order automatically",
                 f"{BASE}/orders.html?id={order['id']}"):
        assert text in email["html"]

    # a later low-stock movement while that order is open says so instead
    ok(client.post(f"/ast/consumables/{supply['id']}/stock-out", headers=sa_headers,
                   json={"quantity": 1, "issued_to": "Room 102"}))
    assert "An order for this item is already open." not in mail.to("admin@sfbu.edu")[-1]["html"]
    assert "created an order automatically" in mail.to("admin@sfbu.edu")[-1]["html"]  # still the IT HUB order


def test_order_arrived_email_for_a_partial_and_a_full_delivery(client, admin_headers, sa_headers, mail):
    category = ok(client.post("/ast/categories", headers=admin_headers, json={"name": "Toner", "is_consumable": True}), 201)
    location = make_location(client, admin_headers)
    supply = ok(client.post("/ast/consumables", headers=sa_headers, json={
        "name": "Toner", "category_id": category["id"], "location_id": location["id"], "reorder_threshold": 0}), 201)
    order = ok(client.post("/orders", headers=sa_headers, json={"item_id": supply["id"], "quantity": 5, "vendor": "Acme"}), 201)
    ok(client.post(f"/orders/{order['id']}/place", headers=admin_headers))
    ok(client.post(f"/orders/{order['id']}/receive", headers=admin_headers, json={"quantity": 2}))
    ok(client.post(f"/orders/{order['id']}/receive", headers=admin_headers, json={"quantity": 3}))
    partial, full = mail.to("sa@sfbu.edu")
    assert partial["subject"] == f"Part of order #{order['id']} has arrived"
    assert "2 of 5 have been received so far" in partial["html"]
    assert full["subject"] == f"Order #{order['id']} has arrived"
    assert "Everything you requested has been received" in full["html"] and "Acme" in full["html"]


def test_report_reviewed_email(client, admin_headers, sa_headers, mail):
    admin = ids(client, admin_headers, sa_headers)["admin"]
    report = ok(client.post("/reports", headers=sa_headers, json={"title": "Lab check", "description": "All good"}), 201)
    ok(client.post(f"/reports/{report['id']}/submit", headers=sa_headers, json={"reviewer_ids": [admin]}))
    ok(client.post(f"/reports/{report['id']}/review", headers=admin_headers,
                   json={"status": "REJECTED", "comment": "Add the room numbers."}))
    (email,) = [m for m in mail.to("sa@sfbu.edu") if "reviewed" in m["subject"]]
    assert email["subject"] == f"System Administrator reviewed #{report['id']}: Rejected"
    assert "Add the room numbers." in email["html"] and "submit it again" in email["html"]


def test_shift_summary_email_lists_the_tasks(client, admin_headers, sa_headers, mail):
    sa = ids(client, admin_headers, sa_headers)["sa"]
    task = ok(client.post("/tasks", headers=admin_headers, json={
        "title": "Check speakers", "priority": "LOW", "due_date": "2026-01-04"}), 201)
    ok(client.put(f"/tasks/{task['id']}/assignees", headers=admin_headers, json={"user_ids": [sa]}))
    ok(client.post("/notifications/shift-summary", headers=admin_headers,
                   json={"shift": "EVENING", "shift_date": "2026-01-05", "user_ids": [sa]}), 201)
    (email,) = [m for m in mail.to("sa@sfbu.edu") if "shift" in m["subject"]]
    assert email["subject"] == "Your open tasks for the Evening shift, Jan 5, 2026"
    for text in ("1 open task<", "Check speakers", "Standalone task", "Overdue since Jan 4, 2026", "Low",
                 "sent by System Administrator"):
        assert text in email["html"]


def test_a_retried_email_keeps_its_design(client, admin_headers, sa_headers, mail, db):
    sa = ids(client, admin_headers, sa_headers)["sa"]
    ok(client.post("/notifications/shift-summary", headers=admin_headers,
                   json={"shift": "MORNING", "shift_date": "2026-01-05", "user_ids": [sa]}), 201)
    note = db.query(Notification).filter_by(event_type=EventType.SHIFT_SUMMARY).one()
    assert note.details["shift"] == "Morning"  # stored for retries
    note.email_status = EmailStatus.FAILED
    db.commit()
    ok(client.post(f"/notifications/{note.id}/email/retry", headers=sa_headers))
    assert mail.sent[-1]["subject"] == "Your open tasks for the Morning shift, Jan 5, 2026"
