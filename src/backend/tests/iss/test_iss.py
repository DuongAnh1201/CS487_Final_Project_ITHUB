"""Issue workflows, roles, history, atomicity and Observer integration (US-ISS-01–07)."""

from datetime import timedelta
import pytest
from sqlalchemy import func, select
from app.core.deps import get_audit_log, get_event_publisher
from app.core.exceptions import ValidationRuleError
from app.modules.cls.models import EquipmentCondition, RoomEquipment
from app.modules.iss.models import Issue, IssueStatus, IssueUpdate
from app.shared.audit import AuditLog, AuditRecord
from app.shared.events import EventPublisher


def report(client, headers, room, equipment=None, **changes):
    payload = dict(
        classroom_id=room["id"],
        category="HARDWARE",
        severity="MEDIUM",
        description="PC does not boot",
        reporter_name="Student Reporter",
        reporter_type="STUDENT",
    )
    if equipment:
        payload["room_equipment_id"] = equipment["id"]
    response = client.post("/issues", headers=headers, json=payload | changes)
    assert response.status_code == 201, response.text
    return response.json()


def transition(client, headers, issue, status, **changes):
    response = client.post(
        f"/issues/{issue['id']}/status",
        headers=headers,
        json={"status": status, "version": issue["version"]} | changes,
    )
    assert response.status_code == 200, response.text
    return response.json()


def started(client, admin_headers, sa_headers, issue):
    user_id = client.get("/auth/me", headers=sa_headers).json()["id"]
    issue = transition(client, admin_headers, issue, "ASSIGNED", assignee_id=user_id)
    return transition(client, sa_headers, issue, "IN_PROGRESS")


@pytest.mark.parametrize(
    "severity, days", [("CRITICAL", 1), ("HIGH", 3), ("MEDIUM", 7), ("LOW", 14)]
)
def test_report_targets_notifications(
    client, sa_headers, admin_headers, room, equipment, clock, severity, days
):
    """FR-ISS-01–03, BR-21/22: reporter metadata, target date, OPEN and Admin event."""
    issue = report(client, sa_headers, room, equipment, severity=severity)
    assert issue["status"] == "OPEN"
    assert issue["target_date"] == (clock().date() + timedelta(days=days)).isoformat()
    assert issue["created_at"] == clock().isoformat()
    assert issue["issue_id"].startswith("ISS-")
    assert issue["reporter_name"] == "Student Reporter"
    assert (
        client.get(f"/classrooms/{room['id']}/equipment", headers=sa_headers).json()[0][
            "condition"
        ]
        == "FAULTY"
    )
    notices = client.get("/notifications", headers=admin_headers)
    assert notices.status_code == 200, notices.text
    assert "ISSUE_REPORTED" in str(notices.json())


def test_report_validation_and_effect_selection(client, sa_headers, room, equipment):
    """BR-21, DD-ISS-01: validate installation and apply only matching effects."""
    base = dict(
        classroom_id=room["id"],
        category="OTHER",
        severity="LOW",
        description=" ",
        reporter_name="N",
        reporter_type="STAFF",
    )
    assert client.post("/issues", headers=sa_headers, json=base).status_code == 422
    assert (
        client.post(
            "/issues",
            headers=sa_headers,
            json=base | {"description": "Broken", "room_equipment_id": 999},
        ).status_code
        == 404
    )
    report(client, sa_headers, room, equipment, category="SOFTWARE")
    assert (
        client.get(f"/classrooms/{room['id']}/equipment", headers=sa_headers).json()[0][
            "condition"
        ]
        == "WORKING"
    )
    other = report(client, sa_headers, room, severity="CRITICAL", category="NETWORK")
    assert (
        client.get(f"/classrooms/{room['id']}", headers=sa_headers).json()["status"]
        == "CLOSED"
    )
    duplicates = client.get(
        "/issues/possible-duplicates",
        headers=sa_headers,
        params={"classroom_id": room["id"], "category": "NETWORK"},
    ).json()
    assert [issue["id"] for issue in duplicates] == [other["id"]]


def test_full_lifecycle_history_comments_permissions(
    client, sa_headers, admin_headers, room, equipment, db
):
    """BR-23, US-ISS-03/04/05/07: role restrictions, notes, finality and retained history."""
    issue = report(client, sa_headers, room, equipment)
    url = f"/issues/{issue['id']}"
    assert (
        client.post(
            url + "/status", headers=sa_headers, json={"status": "CLOSED", "version": 1}
        ).json()["detail"]
        == "This status change is not allowed."
    )
    assert (
        client.post(
            url + "/status",
            headers=sa_headers,
            json={"status": "ASSIGNED", "version": 1, "assignee_id": 1},
        ).json()["detail"]
        == "Not allowed for your role."
    )
    assert (
        client.post(
            url + "/status",
            headers=admin_headers,
            json={"status": "ASSIGNED", "version": 1},
        ).status_code
        == 422
    )
    issue = started(client, admin_headers, sa_headers, issue)
    assert (
        client.get(f"/classrooms/{room['id']}/equipment", headers=sa_headers).json()[0][
            "condition"
        ]
        == "UNDER_REPAIR"
    )
    assert (
        client.post(
            url + "/resolve",
            headers=sa_headers,
            json={"notes": " ", "version": issue["version"]},
        ).json()["detail"]
        == "Resolution notes are required."
    )
    assert (
        client.post(
            url + "/comments",
            headers=sa_headers,
            json={"text": "", "version": issue["version"]},
        ).json()["detail"]
        == "Comment cannot be empty."
    )
    issue = client.post(
        url + "/comments",
        headers=sa_headers,
        json={"text": "Replaced cable", "version": issue["version"]},
    ).json()
    resolved = client.post(
        url + "/resolve",
        headers=sa_headers,
        json={"notes": "Replaced PSU", "version": issue["version"]},
    )
    assert resolved.status_code == 200, resolved.text
    issue = resolved.json()
    assert (
        issue["resolution_notes"] == "Replaced PSU"
        and issue["resolved_by"]
        and issue["resolved_at"]
    )
    assert (
        client.get(f"/classrooms/{room['id']}/equipment", headers=sa_headers).json()[0][
            "condition"
        ]
        == "WORKING"
    )
    assert (
        client.post(
            url + "/status",
            headers=sa_headers,
            json={"status": "CLOSED", "version": issue["version"]},
        ).status_code
        == 403
    )
    issue = transition(client, sa_headers, issue, "IN_PROGRESS")
    issue = transition(client, sa_headers, issue, "RESOLVED", note="Verified")
    issue = transition(client, admin_headers, issue, "CLOSED")
    assert (
        client.post(
            url + "/comments",
            headers=sa_headers,
            json={"text": "late", "version": issue["version"]},
        ).json()["detail"]
        == "This issue is closed. Comments are not allowed."
    )
    history = client.get(url + "/history", headers=admin_headers).json()
    assert [h["new_status"] for h in history] == [
        "ASSIGNED",
        "IN_PROGRESS",
        None,
        "RESOLVED",
        "IN_PROGRESS",
        "RESOLVED",
        "CLOSED",
    ]
    assert all(h["user_id"] and h["timestamp"] for h in history)
    saved = db.get(IssueUpdate, history[0]["id"])
    saved.comment = "Tampered"
    with pytest.raises(ValidationRuleError, match="Issue history cannot be changed"):
        db.flush()
    db.rollback()
    assert client.delete(url, headers=admin_headers).status_code == 405


def test_other_unresolved_issue_prevents_working(
    client, sa_headers, admin_headers, room, equipment
):
    """FR-ISS-09: restore chosen condition only after the last unresolved problem."""
    first = report(client, sa_headers, room, equipment)
    second = report(client, sa_headers, room, equipment)
    first = started(client, admin_headers, sa_headers, first)
    first = transition(client, sa_headers, first, "RESOLVED", note="Fixed one")
    assert (
        client.get(f"/classrooms/{room['id']}/equipment", headers=sa_headers).json()[0][
            "condition"
        ]
        == "UNDER_REPAIR"
    )
    second = started(client, admin_headers, sa_headers, second)
    response = client.post(
        f"/issues/{second['id']}/resolve",
        headers=sa_headers,
        json={
            "notes": "Unrepairable",
            "version": second["version"],
            "new_condition": "OUT_OF_SERVICE",
        },
    )
    assert response.status_code == 200, response.text
    assert (
        client.get(f"/classrooms/{room['id']}/equipment", headers=sa_headers).json()[0][
            "condition"
        ]
        == "OUT_OF_SERVICE"
    )


def test_critical_closure_manual_override_and_other_issues(
    client, admin_headers, sa_headers, room
):
    """DD-CLS-02/DD-ISS-01: no premature reopening with another Critical issue or manual closure."""
    first = report(client, sa_headers, room, severity="CRITICAL", category="NETWORK")
    second = report(
        client, sa_headers, room, severity="CRITICAL", category="ROOM_FACILITY"
    )
    first = started(client, admin_headers, sa_headers, first)
    transition(client, sa_headers, first, "RESOLVED", note="Network restored")
    url = f"/classrooms/{room['id']}"
    assert client.get(url, headers=sa_headers).json()["status"] == "CLOSED"
    client.post(
        url + "/closure",
        headers=admin_headers,
        json={"closed": True, "reason": "Painting"},
    )
    second = started(client, admin_headers, sa_headers, second)
    transition(client, sa_headers, second, "RESOLVED", note="Fixed")
    assert client.get(url, headers=sa_headers).json()["closed_reason"] == "Painting"
    client.post(url + "/closure", headers=admin_headers, json={"closed": False})
    assert client.get(url, headers=sa_headers).json()["status"] == "AVAILABLE"


def test_duplicate_chains_repeat_threshold_once(
    client, sa_headers, admin_headers, room, db
):
    """FR-ISS-08, US-ISS-06: canonical original, report four threshold, one notification."""
    original = report(client, sa_headers, room)
    duplicate = report(client, sa_headers, room)
    url = f"/issues/{duplicate['id']}/duplicate"
    assert (
        client.post(
            url, headers=sa_headers, json={"original_id": duplicate["id"], "version": 1}
        ).status_code
        == 422
    )
    assert (
        client.post(
            url, headers=sa_headers, json={"original_id": 999, "version": 1}
        ).status_code
        == 422
    )
    response = client.post(
        url, headers=sa_headers, json={"original_id": original["id"], "version": 1}
    )
    assert response.status_code == 200, response.text
    for index in range(3):
        child = report(client, sa_headers, room)
        result = client.post(
            f"/issues/{child['id']}/duplicate",
            headers=sa_headers,
            json={"original_id": duplicate["id"], "version": 1},
        )
        assert result.status_code == 200, result.text
        assert result.json()["duplicate_of_id"] == original["id"]
        flagged = client.get(f"/issues/{original['id']}", headers=sa_headers).json()[
            "is_repeat_problem"
        ]
        assert flagged is (index >= 1)
    events = list(
        db.scalars(select(AuditRecord).where(AuditRecord.action == "REPEAT_PROBLEM"))
    )
    assert len(events) == 1
    notices = client.get("/notifications", headers=admin_headers).json()
    assert str(notices).count("'event_type': 'REPEAT_PROBLEM'") == 1


def test_reject_permissions_and_reason(client, sa_headers, admin_headers, room):
    """BR-23: reject is Admin-only and requires a reason."""
    issue = report(client, sa_headers, room)
    url = f"/issues/{issue['id']}/status"
    data = {"status": "REJECTED", "version": issue["version"]}
    assert (
        client.post(
            url, headers=sa_headers, json=data | {"note": "Invalid"}
        ).status_code
        == 403
    )
    assert (
        client.post(url, headers=admin_headers, json=data).json()["detail"]
        == "Give a reason for rejecting this issue."
    )
    rejected = transition(
        client, admin_headers, issue, "REJECTED", note="No problem found"
    )
    assert (
        client.post(
            url,
            headers=admin_headers,
            json={
                "status": "ASSIGNED",
                "version": rejected["version"],
                "assignee_id": 1,
            },
        ).status_code
        == 422
    )


def test_issue_search_overdue_and_stale_edit(
    client, sa_headers, room, equipment, clock, db
):
    """FR-ISS-04, BR-22: combined SQL filters, bounded paging, overdue and version conflict."""
    issue = report(client, sa_headers, room, equipment, severity="HIGH")
    saved = db.get(Issue, issue["id"])
    saved.target_date = clock().date() - timedelta(days=1)
    db.commit()
    criteria = {
        "status": "OPEN",
        "classroom_id": room["id"],
        "item_id": 1,
        "category": "HARDWARE",
        "severity": "HIGH",
        "date_from": clock().date().isoformat(),
        "date_to": clock().date().isoformat(),
    }
    result = client.get("/issues", headers=sa_headers, params=criteria).json()
    assert result["total"] == 1 and result["items"][0]["is_overdue"] is True
    assert (
        client.get(
            "/issues", headers=sa_headers, params=criteria | {"severity": "LOW"}
        ).json()["total"]
        == 0
    )
    assert (
        client.get("/issues", headers=sa_headers, params={"page_size": 51}).status_code
        == 422
    )
    assert (
        client.get(
            "/issues",
            headers=sa_headers,
            params={"date_from": "2026-02-01", "date_to": "2026-01-01"},
        ).status_code
        == 422
    )
    stale = client.post(
        f"/issues/{issue['id']}/comments",
        headers=sa_headers,
        json={"text": "Stale", "version": 1},
    )
    assert stale.status_code == 409


def test_report_and_equipment_rollback_on_audit_failure(
    client, sa_headers, room, equipment, app, db
):
    """NFR-ISS-05: failed audit rolls back issue, equipment and audit together."""

    class FailingAudit(AuditLog):
        def record(
            self, actor, action, entity_type, entity_id, old_value=None, new_value=None
        ):
            if action == "CREATE" and entity_type == "Issue":
                raise ValidationRuleError("Injected audit failure")
            return super().record(
                actor, action, entity_type, entity_id, old_value, new_value
            )

    from app.core.database import get_db
    from app.core.deps import get_clock
    from fastapi import Depends

    def failing_audit(session=Depends(get_db), clock=Depends(get_clock)):
        return FailingAudit(session, clock)

    app.dependency_overrides[get_audit_log] = failing_audit
    response = client.post(
        "/issues",
        headers=sa_headers,
        json={
            "classroom_id": room["id"],
            "room_equipment_id": equipment["id"],
            "category": "HARDWARE",
            "severity": "MEDIUM",
            "description": "Broken",
            "reporter_name": "Name",
            "reporter_type": "STUDENT",
        },
    )
    assert response.status_code == 422
    db.expire_all()
    assert db.scalar(select(func.count()).select_from(Issue)) == 0
    assert (
        db.get(RoomEquipment, equipment["id"]).condition == EquipmentCondition.WORKING
    )
    assert (
        db.scalar(
            select(func.count())
            .select_from(AuditRecord)
            .where(AuditRecord.action == "CONDITION")
        )
        == 0
    )


def test_observer_failure_does_not_undo_report(
    client, sa_headers, room, equipment, app, db
):
    """US-NTF-01/NFR-ISS-05: Observer savepoints protect the saved business change."""

    class BrokenObserver:
        def handle(self, event):
            raise RuntimeError("Notification unavailable")

    from fastapi import Depends
    from app.core.database import get_db

    def publisher(session=Depends(get_db)):
        result = EventPublisher(session)
        result.subscribe(BrokenObserver())
        return result

    app.dependency_overrides[get_event_publisher] = publisher
    issue = report(client, sa_headers, room, equipment)
    db.expire_all()
    assert db.get(Issue, issue["id"]) is not None
    assert db.get(RoomEquipment, equipment["id"]).condition == EquipmentCondition.FAULTY


def test_moved_item_resolution_checks_all_installations(
    client, sa_headers, admin_headers, room, equipment, assets
):
    """FR-ISS-09/BR-18: moves retain issues and unresolved guards for the same AST item."""
    original = report(client, sa_headers, room, equipment)
    target = client.post(
        "/classrooms",
        headers=admin_headers,
        json={"location_id": 2, "capacity": 10, "room_type": "COMPUTER_LAB"},
    ).json()
    current = client.get(
        f"/classrooms/{room['id']}/equipment", headers=sa_headers
    ).json()[0]
    moved = client.post(
        f"/classroom-equipment/{current['id']}/move",
        headers=sa_headers,
        json={"to_classroom_id": target["id"], "version": current["version"]},
    ).json()
    candidates = client.get(
        "/issues/possible-duplicates",
        headers=sa_headers,
        params={
            "classroom_id": target["id"],
            "room_equipment_id": moved["id"],
            "category": "HARDWARE",
        },
    ).json()
    assert [candidate["id"] for candidate in candidates] == [original["id"]]
    newer = report(client, sa_headers, target, moved)
    original = started(client, admin_headers, sa_headers, original)
    newer = started(client, admin_headers, sa_headers, newer)
    transition(client, sa_headers, newer, "RESOLVED", note="One fix")
    assert (
        client.get(f"/classrooms/{target['id']}/equipment", headers=sa_headers).json()[
            0
        ]["condition"]
        == "UNDER_REPAIR"
    )
    transition(client, sa_headers, original, "RESOLVED", note="Last fix")
    assert (
        client.get(f"/classrooms/{target['id']}/equipment", headers=sa_headers).json()[
            0
        ]["condition"]
        == "WORKING"
    )


def test_resolution_failure_rolls_back_history_and_condition(
    client, sa_headers, admin_headers, room, equipment, app, db
):
    """NFR-ISS-05: resolution status/history/equipment roll back when its final audit fails."""
    issue = started(
        client, admin_headers, sa_headers, report(client, sa_headers, room, equipment)
    )
    before = db.scalar(select(func.count()).select_from(IssueUpdate))

    class FailingAudit(AuditLog):
        def record(
            self, actor, action, entity_type, entity_id, old_value=None, new_value=None
        ):
            if action == "STATUS":
                raise ValidationRuleError("Injected audit failure")
            return super().record(
                actor, action, entity_type, entity_id, old_value, new_value
            )

    from app.core.database import get_db
    from app.core.deps import get_clock
    from fastapi import Depends

    def audit(session=Depends(get_db), clock=Depends(get_clock)):
        return FailingAudit(session, clock)

    app.dependency_overrides[get_audit_log] = audit
    response = client.post(
        f"/issues/{issue['id']}/resolve",
        headers=sa_headers,
        json={"notes": "Fixed", "version": issue["version"]},
    )
    assert response.status_code == 422
    db.expire_all()
    assert db.get(Issue, issue["id"]).status == IssueStatus.IN_PROGRESS
    assert (
        db.get(RoomEquipment, equipment["id"]).condition
        == EquipmentCondition.UNDER_REPAIR
    )
    assert db.scalar(select(func.count()).select_from(IssueUpdate)) == before


@pytest.mark.parametrize("initial", list(IssueStatus))
@pytest.mark.parametrize("target", list(IssueStatus))
def test_state_machine_matrix(initial, target, clock):
    """BR-23: exercise all 49 transition pairs against the approved state diagram."""
    from app.modules.usr.models import User, Role
    from app.modules.iss.models import Severity, ReporterType, IssueCategory

    permitted = {
        "OPEN": {"ASSIGNED", "REJECTED", "DUPLICATE"},
        "ASSIGNED": {"IN_PROGRESS", "REJECTED", "DUPLICATE"},
        "IN_PROGRESS": {"RESOLVED"},
        "RESOLVED": {"IN_PROGRESS", "CLOSED"},
    }
    user = User(id=1, role=Role.ADMIN)
    issue = Issue(
        id=1,
        classroom_id=1,
        category=IssueCategory.OTHER,
        severity=Severity.LOW,
        status=initial,
        description="Problem",
        reporter_name="Reporter",
        reporter_type=ReporterType.STAFF,
        created_by=1,
        created_at=clock(),
        target_date=clock().date(),
    )
    if target.value in permitted.get(initial.value, set()):
        issue.change_status(
            target, user, clock(), "Reason", assignee_id=1, original_id=2
        )
        assert issue.status == target and len(issue.history) == 1
    else:
        with pytest.raises(
            ValidationRuleError, match="This status change is not allowed."
        ):
            issue.change_status(
                target, user, clock(), "Reason", assignee_id=1, original_id=2
            )
        assert issue.status == initial and issue.history == []


def test_issue_list_5000_records_is_paged_within_two_seconds(
    client, sa_headers, room, equipment, db, clock
):
    """NFR-ISS-02: real authenticated API query against 5,000 issues, fifty per page."""
    from time import perf_counter
    from sqlalchemy import insert
    from app.modules.iss.models import IssueCategory, Severity, ReporterType

    user_id = client.get("/auth/me", headers=sa_headers).json()["id"]
    rows = [
        dict(
            classroom_id=room["id"],
            room_equipment_id=equipment["id"],
            category=IssueCategory.HARDWARE,
            severity=Severity.MEDIUM,
            description=f"Problem {i}",
            status=IssueStatus.OPEN,
            reporter_name="Reporter",
            reporter_type=ReporterType.STUDENT,
            created_by=user_id,
            created_at=clock(),
            target_date=clock().date() + timedelta(days=7),
        )
        for i in range(5000)
    ]
    db.execute(insert(Issue), rows)
    db.commit()
    start = perf_counter()
    response = client.get(
        "/issues",
        headers=sa_headers,
        params={"status": "OPEN", "classroom_id": room["id"], "item_id": 1},
    )
    duration = perf_counter() - start
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["total"] == 5000 and len(result["items"]) == 50
    assert duration < 2.0
