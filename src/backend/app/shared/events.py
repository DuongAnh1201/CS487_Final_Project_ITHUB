"""Observer pattern: pages publish domain events, observers (NTF) react to them.

Pages never import the notification code. They build a ``DomainEvent`` and call
``publisher.publish(event)`` (``deps.get_event_publisher``) after their change is saved.
"""

import logging
from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """Kinds of events that can produce notifications."""

    TASK_ASSIGNED = "TASK_ASSIGNED"
    ISSUE_REPORTED = "ISSUE_REPORTED"
    REPEAT_PROBLEM = "REPEAT_PROBLEM"
    PROJECT_CREATED = "PROJECT_CREATED"
    PROJECT_UPDATED = "PROJECT_UPDATED"
    PROJECT_MEMBER_ADDED = "PROJECT_MEMBER_ADDED"
    ORDER_ARRIVED = "ORDER_ARRIVED"
    REPORT_SUBMITTED = "REPORT_SUBMITTED"
    REPORT_REVIEWED = "REPORT_REVIEWED"
    MONTHLY_SUMMARY = "MONTHLY_SUMMARY"
    LOW_STOCK = "LOW_STOCK"
    SHIFT_SUMMARY = "SHIFT_SUMMARY"
    GENERAL = "GENERAL"
    ACCOUNT_CREATED = "ACCOUNT_CREATED"
    PASSWORD_RESET = "PASSWORD_RESET"


@dataclass(frozen=True)
class DomainEvent:
    """Something that happened and may need to be told to staff.

    ``recipient_ids`` lets the publisher name the recipients. When empty, routing
    depends on the type: project events go to that project's members only (BR-11,
    needs ``project_id``); issue, repeat-problem, low-stock and order events go to
    the active Admins. The acting user is never notified about their own action.
    """

    event_type: EventType
    message: str
    actor_id: int | None = None
    recipient_ids: tuple[int, ...] = ()
    related_type: str | None = None  # e.g. "Task", "Issue", "Project", "Order"
    related_id: int | None = None
    project_id: int | None = None
    # Values the event's email template shows (see app/modules/ntf/emails.py), JSON-safe.
    details: dict[str, Any] = field(default_factory=dict)


class EventObserver(Protocol):
    """Anything that reacts to domain events."""

    def handle(self, event: DomainEvent) -> None:
        """React to one event."""


class StockObserver(Protocol):
    """Low-stock callback used by the Orders ``StockMonitor`` (SP5)."""

    def on_low_stock(self, asset_id: int, available_quantity: int) -> None:
        """Called when an item's stock falls to or below its threshold."""


class EventPublisher:
    """Subject: delivers events to subscribed observers.

    Each observer runs in its own savepoint, so a failing observer never undoes the
    caller's saved change (US-NTF-01).
    """

    def __init__(self, session: Session) -> None:
        self.session = session
        self._observers: list[tuple[EventObserver, frozenset[EventType] | None]] = []

    def subscribe(self, observer: EventObserver, event_types: Iterable[EventType] | None = None) -> None:
        """Register an observer for the given types (all types when omitted)."""
        self._observers.append((observer, frozenset(event_types) if event_types else None))

    def publish(self, event: DomainEvent) -> None:
        """Tell every interested observer about the event."""
        for observer, types in self._observers:
            if types is not None and event.event_type not in types:
                continue
            try:
                with self.session.begin_nested():
                    observer.handle(event)
            except Exception:  # noqa: BLE001 - observers must not break the publisher
                logger.exception("Observer failed for %s", event.event_type)
