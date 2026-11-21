"""Branded notification emails (#108): the designer's HTML templates rendered with Jinja2.

Each event type with its own design maps to an ``EmailTemplate``; every other event uses
``general.html`` in the same style. Publishers put the values a template needs in
``DomainEvent.details`` (stored on the notification, so a retried email looks the same).
Values are HTML-escaped; a missing value shows as a dash instead of failing the email.
"""

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, Undefined, meta, select_autoescape

from app.shared.events import EventType
from app.shared.formatting import label

TEMPLATE_DIR = Path(__file__).resolve().parent / "email_templates"
LOGO_PATH = "assets/brand/it-hub-logo-email.png"  # served with the frontend (PNG: mail apps block SVG)
GENERAL_TEMPLATE = "general.html"
# Frontend page and query parameter that open each kind of record (src/frontend, served at ITHUB_APP_BASE_URL).
RECORD_PAGES = {
    "Order": "orders.html?id=", "Report": "reports.html?id=", "Issue": "issues.html?id=",
    "Project": "projects.html?id=", "Task": "projects.html?task=", "Asset": "inventory.html?id=",
    "Item": "inventory.html?id=", "Classroom": "classrooms.html?id=",
}
# Variables the composer supplies to every template; the rest come from the event's details.
COMMON_VARIABLES = frozenset({"subject", "logo_url", "login_url", "record_url"})


class RecordLinks:
    """Absolute frontend URLs, or None when ``ITHUB_APP_BASE_URL`` is not set."""

    def __init__(self, app_base_url: str) -> None:
        self.base = app_base_url.rstrip("/")

    def record(self, related_type: str | None, related_id: int | None) -> str | None:
        """The page that opens one record; unknown types open the notifications page."""
        if not self.base or not related_type or related_id is None:
            return None
        return f"{self.base}/{RECORD_PAGES.get(related_type, 'notifications.html?id=')}{related_id}"

    def page(self, path: str) -> str | None:
        """A frontend page, e.g. ``login.html``."""
        return f"{self.base}/{path}" if self.base else None


@dataclass(frozen=True)
class EmailTemplate:
    """One designed email: its file, subject line and where the record link goes."""

    file: str
    subject: Callable[[Mapping[str, Any]], str]
    link_variable: str  # the template's button variable that gets the record (or login) link
    extra_links: Mapping[str, str] | None = None  # template variable -> details key holding an Order id

    def variables(self, environment: Environment) -> set[str]:
        """Every variable the template file reads."""
        source = environment.loader.get_source(environment, self.file)[0]
        return meta.find_undeclared_variables(environment.parse(source))


TEMPLATES: dict[EventType, EmailTemplate] = {
    EventType.ACCOUNT_CREATED: EmailTemplate(
        "welcome.html", lambda d: "Welcome to IT HUB", "login_url"),
    EventType.PASSWORD_RESET: EmailTemplate(
        "password-reset.html", lambda d: "Your IT HUB password was reset", "login_url"),
    EventType.TASK_ASSIGNED: EmailTemplate(
        "task-assigned.html", lambda d: f"{d['assigner']} assigned you: {d['task_title']}", "task_url"),
    EventType.ISSUE_REPORTED: EmailTemplate(
        "issue-reported.html", lambda d: f"{d['severity']} issue in {d['room']}: {d['issue_no']}", "issue_url"),
    EventType.LOW_STOCK: EmailTemplate(
        "low-stock.html",
        lambda d: f"Stock low: {d['item_name']}"
                  + (f" · order {d['order_no']} created" if d.get("order_created") else ""),
        "item_url", {"order_url": "order_id"}),
    EventType.ORDER_ARRIVED: EmailTemplate(
        "order-arrived.html",
        lambda d: f"Order {d['order_no']} has arrived" if d.get("complete")
        else f"Part of order {d['order_no']} has arrived", "order_url"),
    EventType.REPORT_REVIEWED: EmailTemplate(
        "report-reviewed.html", lambda d: f"{d['reviewer']} reviewed {d['report_no']}: {d['outcome']}",
        "report_url"),
    EventType.SHIFT_SUMMARY: EmailTemplate(
        "shift-summary.html", lambda d: f"Your open tasks for the {d['shift']} shift, {d['shift_date']}",
        "tasks_url"),
}
# Pages a template's button opens when the event names no record.
PAGE_LINKS = {"login_url": "login.html", "tasks_url": "projects.html"}


@dataclass(frozen=True)
class EmailContent:
    """A ready-to-send email."""

    subject: str
    text: str
    html: str


class DashUndefined(Undefined):
    """A missing value prints as a dash rather than breaking the email."""

    def __str__(self) -> str:
        return "—"


class EmailComposer:
    """Builds the subject, plain text and branded HTML for a notification email."""

    def __init__(self, app_base_url: str = "") -> None:
        self.links = RecordLinks(app_base_url)
        self.environment = Environment(
            loader=FileSystemLoader(TEMPLATE_DIR), autoescape=select_autoescape(["html"]),
            undefined=DashUndefined, keep_trailing_newline=True)
        self._needed: dict[str, set[str]] = {}

    def compose(self, event_type: EventType, message: str, details: Mapping[str, Any] | None = None,
                record_url: str | None = None) -> EmailContent:
        """The email for one notification: its event's design, or the general one."""
        details = dict(details or {})
        template = TEMPLATES.get(event_type)
        if template is None or not self._has_details(template, details):
            return self._general(event_type, message, record_url)
        page = PAGE_LINKS.get(template.link_variable)
        link = record_url or (self.links.page(page) if page else None)
        values = {
            **details,
            "subject": template.subject(details),
            "logo_url": self.links.page(LOGO_PATH),
            "login_url": self.links.page("login.html"),
            "record_url": link,
            template.link_variable: link,
        }
        for variable, key in (template.extra_links or {}).items():
            values[variable] = self.links.record("Order", details.get(key))
        html = self.environment.get_template(template.file).render(values)
        return EmailContent(values["subject"], self._text(message, link), html)

    def _general(self, event_type: EventType, message: str, record_url: str | None) -> EmailContent:
        lines = [line.strip() for line in message.splitlines() if line.strip()] or [label(event_type)]
        subject = f"IT HUB: {lines[0]}"[:150]
        html = self.environment.get_template(GENERAL_TEMPLATE).render(
            subject=subject, logo_url=self.links.page(LOGO_PATH), label=label(event_type),
            heading=lines[0], paragraphs=lines[1:], preheader=lines[0], record_url=record_url,
            reason="You are receiving this because of your work in IT HUB.")
        return EmailContent(subject, self._text(message, record_url), html)

    def _has_details(self, template: EmailTemplate, details: Mapping[str, Any]) -> bool:
        """Designed emails need their event's details; older notifications fall back to general."""
        if template.file not in self._needed:
            self._needed[template.file] = (template.variables(self.environment) - COMMON_VARIABLES
                                           - {template.link_variable} - set(template.extra_links or {}))
        return bool(details) and self._needed[template.file] <= set(details)

    @staticmethod
    def _text(message: str, link: str | None) -> str:
        return f"{message}\n\nOpen in IT HUB: {link}" if link else message

    def preview(self, event_type: EventType) -> EmailContent:
        """The email for ``event_type`` filled with sample values (Admin preview, tests)."""
        sample = dict(SAMPLE_DETAILS[event_type])
        message = sample.pop("_message")
        record = self.links.record(*SAMPLE_RECORDS.get(event_type, (None, None)))
        return self.compose(event_type, message, sample, record)


# Realistic sample values for every designed email (used by the preview route and the tests).
SAMPLE_DETAILS: dict[EventType, dict[str, Any]] = {
    EventType.ACCOUNT_CREATED: {
        "_message": "Welcome to IT HUB. Morgan Lee created your account.",
        "first_name": "Sam", "email": "sam.assistant@sfbu.edu", "role": "Student Assistant",
        "access_end": "May 31, 2027", "admin_name": "Morgan Lee"},
    EventType.PASSWORD_RESET: {
        "_message": "Morgan Lee reset your IT HUB password.",
        "admin_name": "Morgan Lee", "reset_at": "Nov 21, 2026, 9:30 AM UTC",
        "support_contact": "Morgan Lee (morgan.lee@sfbu.edu)"},
    EventType.TASK_ASSIGNED: {
        "_message": "You were assigned task #42: Image lab PCs",
        "assigner": "Morgan Lee", "task_title": "Image lab PCs",
        "task_description": "Re-image the 24 PCs in room 204 with the spring build.",
        "project_name": "Lab refresh", "priority": "High", "due_date": "Nov 25, 2026"},
    EventType.ISSUE_REPORTED: {
        "_message": "Issue ISS-0012 reported: Projector shows no signal",
        "issue_no": "ISS-0012", "severity": "High", "room": "Main 204", "category": "Hardware",
        "description": "Projector shows no signal from the lectern PC.", "item": "Projector #18",
        "reporter": "Dr. Alvarez", "reporter_type": "Faculty",
        "auto_effect": "The reported item is now marked Faulty."},
    EventType.LOW_STOCK: {
        "_message": "Low stock: HDMI cable has 2 left.",
        "item_name": "HDMI cable", "unit": "pcs", "location": "Main 101", "on_hand": 2,
        "threshold": 5, "order_no": "#31", "order_qty": 8, "order_id": 31, "order_created": True},
    EventType.ORDER_ARRIVED: {
        "_message": "Order #31 for HDMI cable arrived: 8 received, 0 still expected.",
        "item_name": "HDMI cable", "order_no": "#31", "qty_ordered": 8, "qty_received": 8,
        "received_at": "Nov 21, 2026, 10:15 AM UTC", "vendor": "CDW", "complete": True},
    EventType.REPORT_REVIEWED: {
        "_message": "Report #7 is now Passed.",
        "reviewer": "Morgan Lee", "report_no": "#7", "outcome": "Passed",
        "report_title": "Evening shift report", "review_comment": "Clear and complete, thank you.",
        "submitted_at": "Nov 20, 2026, 8:40 PM UTC", "next_step": "No action needed. The report is closed."},
    EventType.SHIFT_SUMMARY: {
        "_message": "Morning shift summary for 2026-11-21: 2 task(s).",
        "sender": "Morgan Lee", "shift": "Morning", "shift_date": "Nov 21, 2026",
        "shift_date_long": "Saturday, November 21, 2026", "task_count": 2,
        "tasks": [
            {"title": "Image lab PCs", "project": "Lab refresh", "due": "Due Nov 21, 2026", "priority": "High"},
            {"title": "Check room 110 speakers", "project": "Standalone task", "due": "Overdue since Nov 19, 2026",
             "priority": "Medium"},
        ]},
}
SAMPLE_RECORDS: dict[EventType, tuple[str, int]] = {
    EventType.TASK_ASSIGNED: ("Task", 42), EventType.ISSUE_REPORTED: ("Issue", 12),
    EventType.LOW_STOCK: ("Asset", 9), EventType.ORDER_ARRIVED: ("Order", 31),
    EventType.REPORT_REVIEWED: ("Report", 7),
}
