"""NTF: observer routing, read state, email channel, shift summary (US-NTF-01..07)."""

from datetime import date, datetime

import pytest
from sqlalchemy.orm import Session

from app.modules.ntf.models import EmailStatus, Notification
from app.modules.ntf.ports import ScheduledWork
from app.modules.ntf.service import ShiftName
from app.shared.audit import AuditRecord
from app.shared.events import DomainEvent, EventPublisher, EventType


def test_event_creates_one_notification_per_recipient(publisher, db: Session, user_ids, email):
    publisher.publish(DomainEvent(
        EventType.TASK_ASSIGNED, "You were assigned task #3", actor_id=user_ids["admin"],
        recipient_ids=(user_ids["sa"],), related_type="Task", related_id=3))
    note = db.query(Notification).one()
    assert (note.recipient_id, note.event_type, note.related_type, note.related_id) == (
        user_ids["sa"], EventType.TASK_ASSIGNED, "Task", 3)
    assert note.read_at is None and note.is_read is False
    assert email.sent[0][0] == "sa@sfbu.edu"


def test_actor_is_not_notified_of_own_action(publisher, db: Session, user_ids):
    publisher.publish(DomainEvent(EventType.TASK_ASSIGNED, "x", actor_id=user_ids["sa"],
                                  recipient_ids=(user_ids["sa"],)))
    assert db.query(Notification).count() == 0


def test_issue_events_go_to_active_admins(publisher, db: Session, user_ids):
    publisher.publish(DomainEvent(EventType.ISSUE_REPORTED, "Issue #1 reported",
                                  actor_id=user_ids["sa"], related_type="Issue", related_id=1))
    assert [n.recipient_id for n in db.query(Notification)] == [user_ids["admin"]]


def test_order_arrived_and_low_stock_reach_admins(publisher, service, db: Session, user_ids):
    publisher.publish(DomainEvent(EventType.ORDER_ARRIVED, "Order 7 arrived", related_type="Order",
                                  related_id=7))
    service.on_low_stock(asset_id=4, available_quantity=1)
    kinds = sorted(n.event_type.value for n in db.query(Notification))
    assert kinds == ["LOW_STOCK", "ORDER_ARRIVED"]


def test_event_without_recipients_creates_nothing(publisher, db: Session, user_ids):
    publisher.publish(DomainEvent(EventType.GENERAL, "hello"))
    assert db.query(Notification).count() == 0


def test_email_failure_keeps_in_app_notification(publisher, db: Session, user_ids, email):
    email.fail = True
    publisher.publish(DomainEvent(EventType.GENERAL, "hi", recipient_ids=(user_ids["sa"],)))
    note = db.query(Notification).one()
    assert note.email_status == EmailStatus.FAILED and "SMTP down" in note.email_error


def test_failing_observer_does_not_undo_callers_change(db: Session, user_ids):
    class Boom:
        def handle(self, event):
            db.add(Notification(recipient_id=user_ids["sa"], event_type=EventType.GENERAL,
                                message="half", created_at=None))  # invalid row
            db.flush()

    pub = EventPublisher(db)
    pub.subscribe(Boom())
    db.add(AuditRecord(timestamp=datetime(2026, 1, 1), action="KEEP",
                       entity_type="T", entity_id="1"))
    db.flush()
    pub.publish(DomainEvent(EventType.GENERAL, "x"))
    assert db.query(AuditRecord).filter_by(action="KEEP").count() == 1
    assert db.query(Notification).count() == 0


def test_subscription_by_event_type(db: Session, user_ids):
    seen = []

    class Spy:
        def handle(self, event):
            seen.append(event.event_type)

    pub = EventPublisher(db)
    pub.subscribe(Spy(), [EventType.ORDER_ARRIVED])
    pub.publish(DomainEvent(EventType.GENERAL, "x"))
    pub.publish(DomainEvent(EventType.ORDER_ARRIVED, "y"))
    assert seen == [EventType.ORDER_ARRIVED]


def test_list_only_my_notifications_and_read_state(client, publisher, db, user_ids, admin_headers,
                                                   sa_headers):
    publisher.publish(DomainEvent(EventType.GENERAL, "for sa", recipient_ids=(user_ids["sa"],)))
    publisher.publish(DomainEvent(EventType.GENERAL, "for admin", recipient_ids=(user_ids["admin"],)))
    db.commit()
    mine = client.get("/notifications", headers=sa_headers).json()
    assert [n["message"] for n in mine] == ["for sa"] and mine[0]["is_read"] is False
    nid = mine[0]["id"]
    assert client.patch(f"/notifications/{nid}", headers=sa_headers, json={"read": True}).json()["is_read"]
    assert client.get("/notifications?unread_only=true", headers=sa_headers).json() == []
    assert client.patch(f"/notifications/{nid}", headers=sa_headers, json={"read": False}).json()["read_at"] is None
    actions = [a.action for a in db.query(AuditRecord).filter(AuditRecord.entity_type == "Notification")]
    assert {"CREATE", "READ", "UNREAD"} <= set(actions)


def test_cannot_read_or_change_someone_elses_notification(client, publisher, db, user_ids, admin_headers,
                                                          sa_headers):
    publisher.publish(DomainEvent(EventType.GENERAL, "for admin", recipient_ids=(user_ids["admin"],)))
    db.commit()
    nid = db.query(Notification).one().id
    for r in (client.get(f"/notifications/{nid}", headers=sa_headers),
              client.patch(f"/notifications/{nid}", headers=sa_headers, json={"read": True})):
        assert (r.status_code, r.json()["detail"]) == (404, "Notification not found.")


def test_notifications_require_login(client):
    assert client.get("/notifications").status_code == 401


class FakeMembership:
    def __init__(self, members: dict[int, list[int]]) -> None:
        self.members = members

    def member_ids(self, project_id: int) -> list[int]:
        return self.members.get(project_id, [])


class FakeWork:
    def __init__(self, items: dict[int, list[ScheduledWork]]) -> None:
        self.items = items

    def open_work_for_user(self, user_id: int, due_on_or_before: date) -> list[ScheduledWork]:
        return self.items.get(user_id, [])


def test_project_events_reach_members_only(db: Session, service, user_ids):
    service.membership = FakeMembership({1: [user_ids["sa"]], 2: [user_ids["admin"]]})
    pub = EventPublisher(db)
    pub.subscribe(service)
    pub.publish(DomainEvent(EventType.PROJECT_UPDATED, "Project 1 updated", actor_id=user_ids["admin"],
                            related_type="Project", related_id=1, project_id=1))
    notes = db.query(Notification).all()
    assert [(n.recipient_id, n.project_id) for n in notes] == [(user_ids["sa"], 1)]


def test_project_event_without_membership_source_notifies_nobody(publisher, db: Session, user_ids):
    publisher.publish(DomainEvent(EventType.PROJECT_CREATED, "x", project_id=9))
    assert db.query(Notification).count() == 0


def test_shift_summary_goes_to_roster_only_and_lists_work(db: Session, service, user_ids):
    service.work = FakeWork({user_ids["sa"]: [
        ScheduledWork(3, "Check lab PCs", date(2026, 1, 5)),
        ScheduledWork(4, "Image laptops", date(2026, 1, 2))]})
    created = service.send_shift_summary(ShiftName.MORNING, date(2026, 1, 5), [user_ids["sa"]])
    assert [n.recipient_id for n in created] == [user_ids["sa"]]
    note = created[0]
    assert note.event_type == EventType.SHIFT_SUMMARY
    assert "Morning shift summary for 2026-01-05" in note.message
    assert "#3 Check lab PCs (due 2026-01-05)" in note.message
    assert "#4 Image laptops (due 2026-01-02, overdue)" in note.message
    assert db.query(Notification).filter_by(recipient_id=user_ids["admin"]).count() == 0


def test_shift_summary_endpoint_with_no_work(client, user_ids, sa_headers):
    r = client.post("/notifications/shift-summary", headers=sa_headers, json={
        "shift": "MORNING", "shift_date": "2026-01-05", "user_ids": [user_ids["sa"]]})
    assert r.status_code == 201
    assert r.json()[0]["message"].endswith("no work scheduled.")
    assert client.post("/notifications/shift-summary", headers=sa_headers, json={
        "shift": "MORNING", "shift_date": "2026-01-05", "user_ids": []}).status_code == 422
