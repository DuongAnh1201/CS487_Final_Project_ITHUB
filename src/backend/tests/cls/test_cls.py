"""CLS acceptance and boundary tests (BR-18–20, US-CLS-01–08)."""

from datetime import timedelta
import pytest
from sqlalchemy import select
from app.modules.cls.models import Classroom, RoomEquipment, ScheduleEntry
from app.shared.audit import AuditRecord


def meeting(room_id, **changes):
    data = dict(
        classroom_id=room_id,
        course_code="CS487",
        course_title="OOD",
        instructor_name="Prof Smith",
        day_of_week="MON",
        start_time="10:00",
        end_time="11:00",
        term_start="2026-01-01",
        term_end="2026-05-31",
    )
    return data | changes


def test_classroom_permissions_uniqueness_deactivation(
    client, sa_headers, admin_headers, assets, room
):
    """BR-18, US-CLS-01: Admin-only setup, unique location and soft deactivation."""
    payload = {"location_id": 2, "capacity": 20, "room_type": "LECTURE"}
    assert (
        client.post("/classrooms", headers=sa_headers, json=payload).status_code == 403
    )
    duplicate = client.post(
        "/classrooms", headers=admin_headers, json=payload | {"location_id": 1}
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["detail"] == "This room already exists as a classroom."
    assert (
        client.post(
            "/classrooms", headers=admin_headers, json=payload | {"capacity": 0}
        ).status_code
        == 422
    )
    assert (
        client.patch(
            f"/classrooms/{room['id']}",
            headers=admin_headers,
            json={"capacity": 42, "room_type": "LECTURE"},
        ).json()["capacity"]
        == 42
    )
    assert (
        client.post(
            f"/classrooms/{room['id']}/deactivate", headers=admin_headers
        ).json()["is_active"]
        is False
    )
    assert client.get("/classrooms", headers=sa_headers).json() == []
    assert (
        client.get(f"/classrooms/{room['id']}", headers=sa_headers).status_code == 200
    )
    assert (
        client.delete(f"/classrooms/{room['id']}", headers=admin_headers).status_code
        == 405
    )


@pytest.mark.parametrize(
    "item_id, expected", [(4, 422), (5, 409), (6, 409), (999, 404)]
)
def test_install_eligibility(client, sa_headers, room, item_id, expected):
    """DD-CLS-01: only unretired, unloaned Desktops/Monitors can be installed."""
    assert (
        client.post(
            f"/classrooms/{room['id']}/equipment",
            headers=sa_headers,
            json={"item_id": item_id},
        ).status_code
        == expected
    )


def test_status_conditions_and_audit(
    client, sa_headers, admin_headers, room, equipment, db, assets, clock
):
    """FR-CLS-03/04, DD-CLS-02: desktops determine status; reasons and versions are mandatory."""
    url = f"/classroom-equipment/{equipment['id']}/condition"
    assert (
        client.get(f"/classrooms/{room['id']}", headers=sa_headers).json()["status"]
        == "AVAILABLE"
    )
    assert (
        client.post(
            url,
            headers=sa_headers,
            json={"condition": "FAULTY", "reason": " ", "version": 1},
        ).json()["detail"]
        == "Reason is required."
    )
    assert (
        client.post(
            url,
            headers=sa_headers,
            json={"condition": "WORKING", "reason": "Checked", "version": 1},
        ).json()["detail"]
        == "No change."
    )
    changed = client.post(
        url,
        headers=sa_headers,
        json={"condition": "FAULTY", "reason": "No power", "version": 1},
    )
    assert changed.status_code == 200, changed.text
    assert changed.json()["version"] == 2
    assert (
        client.get(f"/classrooms/{room['id']}", headers=sa_headers).json()["status"]
        == "UNUSABLE"
    )
    stale = client.post(
        url,
        headers=sa_headers,
        json={"condition": "WORKING", "reason": "Fixed", "version": 1},
    )
    assert stale.status_code == 409
    assert (
        stale.json()["detail"]
        == "This record was changed by someone else. Reload and try again."
    )
    client.post(
        f"/classrooms/{room['id']}/equipment", headers=sa_headers, json={"item_id": 2}
    )
    assert (
        client.get(f"/classrooms/{room['id']}", headers=sa_headers).json()["status"]
        == "LIMITED"
    )
    monitor = client.post(
        f"/classrooms/{room['id']}/equipment", headers=sa_headers, json={"item_id": 3}
    ).json()
    client.post(
        f"/classroom-equipment/{monitor['id']}/condition",
        headers=sa_headers,
        json={"condition": "MISSING", "reason": "Gone", "version": 1},
    )
    assert (
        client.get(f"/classrooms/{room['id']}", headers=sa_headers).json()["status"]
        == "LIMITED"
    )
    event = db.scalar(
        select(AuditRecord).where(
            AuditRecord.action == "CONDITION",
            AuditRecord.entity_id == str(equipment["id"]),
        )
    )
    assert event.old_value == {"condition": "WORKING"}
    assert event.new_value["reason"] == "No power"
    assert event.timestamp == clock()
    assert assets.items[1].status == "AVAILABLE"
    assert (
        client.post(
            f"/classrooms/{room['id']}/closure",
            headers=sa_headers,
            json={"closed": True, "reason": "Work"},
        ).status_code
        == 403
    )
    assert (
        client.post(
            f"/classrooms/{room['id']}/closure",
            headers=admin_headers,
            json={"closed": True},
        ).status_code
        == 422
    )
    client.post(
        f"/classrooms/{room['id']}/closure",
        headers=admin_headers,
        json={"closed": True, "reason": "Work"},
    )
    assert (
        client.get(f"/classrooms/{room['id']}", headers=sa_headers).json()["status"]
        == "CLOSED"
    )


def test_move_remove_and_deactivation_guards(
    client, sa_headers, admin_headers, room, equipment, assets, db
):
    """BR-18, US-CLS-02: one installation, preserved condition/history, guarded deactivation."""
    assert (
        client.post(
            f"/classrooms/{room['id']}/deactivate", headers=admin_headers
        ).json()["detail"]
        == "Remove the installed equipment first."
    )
    assert (
        client.post(
            f"/classrooms/{room['id']}/equipment",
            headers=sa_headers,
            json={"item_id": 1},
        ).status_code
        == 409
    )
    assert (
        client.post(
            f"/classroom-equipment/{equipment['id']}/move",
            headers=sa_headers,
            json={"to_classroom_id": room["id"], "version": 1},
        ).status_code
        == 422
    )
    target = client.post(
        "/classrooms",
        headers=admin_headers,
        json={"location_id": 2, "capacity": 20, "room_type": "LECTURE"},
    ).json()
    client.post(
        f"/classroom-equipment/{equipment['id']}/condition",
        headers=sa_headers,
        json={"condition": "FAULTY", "reason": "Broken", "version": 1},
    )
    moved = client.post(
        f"/classroom-equipment/{equipment['id']}/move",
        headers=sa_headers,
        json={"to_classroom_id": target["id"], "version": 2},
    )
    assert moved.status_code == 200, moved.text
    moved = moved.json()
    assert moved["condition"] == "FAULTY" and moved["id"] != equipment["id"]
    assert (
        client.get(f"/classrooms/{room['id']}/equipment", headers=sa_headers).json()
        == []
    )
    assert db.get(RoomEquipment, equipment["id"]).removed_at is not None
    assert (
        client.post(
            f"/classroom-equipment/{moved['id']}/remove",
            headers=sa_headers,
            json={"version": moved["version"]},
        ).status_code
        == 200
    )
    assert assets.items[1].status == "AVAILABLE"


def test_checks_complete_and_overdue(client, sa_headers, room, equipment, clock, db):
    """BR-20, US-CLS-04: complete checks clear the overdue flag and retain observations."""
    url = f"/classrooms/{room['id']}"
    assert client.get(url, headers=sa_headers).json()["check_overdue"]
    assert (
        client.post(
            url + "/checks", headers=sa_headers, json={"results": []}
        ).status_code
        == 422
    )
    result = {
        "room_equipment_id": equipment["id"],
        "observed_condition": "FAULTY",
        "comment": "No boot",
        "version": 1,
    }
    assert (
        client.post(
            url + "/checks", headers=sa_headers, json={"results": [result, result]}
        ).status_code
        == 422
    )
    response = client.post(
        url + "/checks",
        headers=sa_headers,
        json={"results": [result], "notes": "Weekly"},
    )
    assert response.status_code == 201, response.text
    assert len(response.json()["results"]) == 1
    assert client.get(url, headers=sa_headers).json()["status"] == "UNUSABLE"
    assert not client.get(url, headers=sa_headers).json()["check_overdue"]
    # Avoid advancing auth sessions; change the check date relative to the injected clock.
    saved = db.get(Classroom, room["id"])
    saved.last_checked_at = clock() - timedelta(days=7)
    db.commit()
    assert not client.get(url, headers=sa_headers).json()["check_overdue"]
    saved.last_checked_at = clock() - timedelta(days=8)
    db.commit()
    assert client.get(url, headers=sa_headers).json()["check_overdue"]


def test_schedule_boundaries_timetable_and_search(
    client, admin_headers, sa_headers, room, assets, db
):
    """BR-19, US-CLS-05/07/08: overlap/edit boundaries, cancellation and AND filters."""
    data = meeting(room["id"])
    assert (
        client.post("/schedule/entries", headers=sa_headers, json=data).status_code
        == 403
    )
    created = client.post("/schedule/entries", headers=admin_headers, json=data)
    assert created.status_code == 201, created.text
    entry = created.json()
    assert (
        client.post(
            f"/classrooms/{room['id']}/deactivate", headers=admin_headers
        ).json()["detail"]
        == "This classroom has future classes."
    )
    overlap = client.post(
        "/schedule/entries", headers=admin_headers, json=data | {"start_time": "10:30"}
    )
    assert overlap.status_code == 409
    assert overlap.json()["detail"] == "Overlaps CS487 on MON 10:00–11:00."
    assert (
        client.put(
            f"/schedule/entries/{entry['id']}", headers=admin_headers, json=data
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/schedule/entries",
            headers=admin_headers,
            json=data | {"start_time": "11:00", "end_time": "12:00"},
        ).status_code
        == 201
    )
    assert (
        client.post(
            "/schedule/entries",
            headers=admin_headers,
            json=data | {"term_start": "2026-06-01", "term_end": "2026-06-30"},
        ).status_code
        == 201
    )
    for change in (
        {"end_time": "09:00"},
        {"term_end": "2025-01-01"},
        {"start_time": "9:00"},
        {"course_code": " "},
    ):
        assert (
            client.post(
                "/schedule/entries", headers=admin_headers, json=data | change
            ).status_code
            == 422
        )
    timetable = client.get(
        f"/classrooms/{room['id']}/timetable",
        headers=sa_headers,
        params={"day": "2026-01-05", "view": "week"},
    ).json()
    assert len(timetable["days"]) == 7
    assert [e["start_time"] for e in timetable["days"][0]["entries"]] == [
        "10:00:00",
        "11:00:00",
    ]
    assert timetable["days"][1]["message"] == "No classes scheduled."
    params = {
        "building": "Main",
        "room_type": "COMPUTER_LAB",
        "min_capacity": 30,
        "status": "AVAILABLE",
        "slot_date": "2026-01-05",
        "start_time": "10:30",
        "end_time": "11:30",
    }
    assert client.get("/classrooms", headers=sa_headers, params=params).json() == []
    assert (
        len(
            client.get(
                "/classrooms",
                headers=sa_headers,
                params=params | {"start_time": "12:00", "end_time": "13:00"},
            ).json()
        )
        == 1
    )
    assert (
        client.get(
            "/classrooms", headers=sa_headers, params={"start_time": "12:00"}
        ).status_code
        == 422
    )
    assert (
        client.get(
            "/classrooms", headers=sa_headers, params={"min_capacity": -1}
        ).status_code
        == 422
    )
    assert (
        client.post(
            f"/schedule/entries/{entry['id']}/cancel", headers=admin_headers
        ).json()["status"]
        == "CANCELLED"
    )
    assert db.get(ScheduleEntry, entry["id"]) is not None
    assert (
        len(
            client.get(
                f"/classrooms/{room['id']}/timetable",
                headers=sa_headers,
                params={"day": "2026-01-05"},
            ).json()["days"][0]["entries"]
        )
        == 1
    )


def test_csv_import_partial_errors(client, admin_headers, sa_headers, room):
    """FR-CLS-06: include accepted-in-file conflicts and unknown/invalid rows."""
    header = "course_code,course_title,instructor,building,room,day,start_time,end_time,term_start,term_end\n"
    content = header + "\n".join(
        [
            "CS487,OOD,Smith,Main,201,Monday,10:00,11:00,2026-01-01,2026-05-31",
            "CS488,Other,Smith,Main,201,MON,10:30,11:30,2026-01-01,2026-05-31",
            "CS489,Other,Smith,Main,999,TUE,10:00,11:00,2026-01-01,2026-05-31",
            "CS490,Other,Smith,Main,201,TUE,25:00,26:00,2026-01-01,2026-05-31",
            "CS491,Other,Smith,Main,201,TUE,12:00,13:00,2026-01-01,2026-05-31",
        ]
    )
    payload = {"file_name": "registrar.csv", "content": content}
    assert (
        client.post("/schedule/imports", headers=sa_headers, json=payload).status_code
        == 403
    )
    response = client.post("/schedule/imports", headers=admin_headers, json=payload)
    assert response.status_code == 201, response.text
    result = response.json()
    assert (result["rows_accepted"], result["rows_rejected"]) == (2, 3)
    assert [r["row"] for r in result["rejected_rows"]] == [3, 4, 5]
    assert "room Main 999 not found." in result["rejected_rows"][1]["reason"]
    assert (
        client.post(
            "/schedule/imports",
            headers=admin_headers,
            json=payload | {"file_name": "bad.txt"},
        ).json()["detail"]
        == "File must be a CSV with the expected columns."
    )
    assert (
        client.post(
            "/schedule/imports",
            headers=admin_headers,
            json=payload | {"content": "wrong,header\n"},
        ).status_code
        == 422
    )


def test_repository_detects_concurrent_equipment_edit(
    client, sa_headers, equipment, app
):
    """US-CLS-03: SQLAlchemy version guards detect a competing committed write."""
    from app.core.exceptions import ConflictError
    from app.modules.cls.repository import RoomEquipmentRepository
    from app.modules.cls.models import EquipmentCondition

    with app.state.database.SessionLocal() as first, app.state.database.SessionLocal() as second:
        winner = RoomEquipmentRepository(first).get_or_raise(equipment["id"])
        stale = RoomEquipmentRepository(second).get_or_raise(equipment["id"])
        winner.condition = EquipmentCondition.FAULTY
        RoomEquipmentRepository(first).flush()
        first.commit()
        stale.condition = EquipmentCondition.MISSING
        with pytest.raises(
            ConflictError, match="This record was changed by someone else"
        ):
            RoomEquipmentRepository(second).flush()
        second.rollback()


def test_schedule_import_audit_failure_rolls_back_all_rows(
    client, admin_headers, room, app, db
):
    """BR-03/19: accepted rows and import record share the audit transaction."""
    from app.core.database import get_db
    from app.core.deps import get_audit_log, get_clock
    from app.core.exceptions import ValidationRuleError
    from app.shared.audit import AuditLog
    from app.modules.cls.models import ScheduleImport
    from fastapi import Depends
    from sqlalchemy import func

    class FailingAudit(AuditLog):
        def record(
            self, actor, action, entity_type, entity_id, old_value=None, new_value=None
        ):
            if action == "IMPORT":
                raise ValidationRuleError("Injected audit failure")
            return super().record(
                actor, action, entity_type, entity_id, old_value, new_value
            )

    def audit(session=Depends(get_db), clock=Depends(get_clock)):
        return FailingAudit(session, clock)

    app.dependency_overrides[get_audit_log] = audit
    content = (
        "course_code,course_title,instructor,building,room,day,start_time,end_time,term_start,term_end\n"
        "CS487,OOD,Smith,Main,201,MON,10:00,11:00,2026-01-01,2026-05-31"
    )
    response = client.post(
        "/schedule/imports",
        headers=admin_headers,
        json={"file_name": "schedule.csv", "content": content},
    )
    assert response.status_code == 422
    assert db.scalar(select(func.count()).select_from(ScheduleEntry)) == 0
    assert db.scalar(select(func.count()).select_from(ScheduleImport)) == 0


def test_import_row_audit_failure_is_not_a_rejected_row(
    client, admin_headers, room, app, db
):
    """BR-03: a row audit failure aborts import instead of leaving a saved rejected row."""
    from app.core.database import get_db
    from app.core.deps import get_audit_log, get_clock
    from app.core.exceptions import ValidationRuleError
    from app.shared.audit import AuditLog
    from app.modules.cls.models import ScheduleImport
    from fastapi import Depends
    from sqlalchemy import func

    class FailingAudit(AuditLog):
        def record(
            self, actor, action, entity_type, entity_id, old_value=None, new_value=None
        ):
            if entity_type == "ScheduleEntry":
                raise ValidationRuleError("Injected row audit failure")
            return super().record(
                actor, action, entity_type, entity_id, old_value, new_value
            )

    def audit(session=Depends(get_db), clock=Depends(get_clock)):
        return FailingAudit(session, clock)

    app.dependency_overrides[get_audit_log] = audit
    content = (
        "course_code,course_title,instructor,building,room,day,start_time,end_time,term_start,term_end\n"
        "CS487,OOD,Smith,Main,201,MON,10:00,11:00,2026-01-01,2026-05-31"
    )
    response = client.post(
        "/schedule/imports",
        headers=admin_headers,
        json={"file_name": "schedule.csv", "content": content},
    )
    assert response.status_code == 422
    assert db.scalar(select(func.count()).select_from(ScheduleEntry)) == 0
    assert db.scalar(select(func.count()).select_from(ScheduleImport)) == 0
