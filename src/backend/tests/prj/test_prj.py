"""PRJ: US-PRJ-01..07, BR-13..15, NFR-PRJ-01, plus the NTF hooks (US-NTF-01/06)."""

from datetime import datetime

import pytest
from sqlalchemy.orm import Session

from app.modules.ntf.models import Notification
from app.modules.prj.models import Project, Task, TaskAssignment
from app.shared.audit import AuditRecord
from app.shared.events import EventType

PROJECT = {"name": "Lab refresh", "description": "Replace PCs", "start_date": "2026-02-01",
           "due_date": "2026-03-01", "status": "ACTIVE"}


@pytest.fixture
def ids(client, admin_headers, sa_headers) -> dict[str, int]:
    return {"admin": client.get("/auth/me", headers=admin_headers).json()["id"],
            "sa": client.get("/auth/me", headers=sa_headers).json()["id"]}


def make_project(client, headers, **extra) -> dict:
    r = client.post("/projects", headers=headers, json={**PROJECT, **extra})
    assert r.status_code == 201, r.text
    return r.json()


def make_task(client, headers, **extra) -> dict:
    r = client.post("/tasks", headers=headers, json={"title": "Image PCs", **extra})
    assert r.status_code == 201, r.text
    return r.json()


# ---- projects (US-PRJ-01) ----------------------------------------------------

def test_create_project_and_find_by_id(client, admin_headers, ids):
    created = make_project(client, admin_headers)
    assert created["status"] == "ACTIVE" and created["total_tasks"] == 0
    got = client.get(f"/projects/{created['id']}", headers=admin_headers).json()
    assert got["name"] == "Lab refresh" and got["tasks"] == []
    assert client.get(f"/projects/{created['id']}/members", headers=admin_headers).json() == [ids["admin"]]


def test_project_validation_and_missing(client, admin_headers):
    bad = client.post("/projects", headers=admin_headers, json={**PROJECT, "name": ""})
    assert bad.status_code == 422
    dates = client.post("/projects", headers=admin_headers,
                        json={**PROJECT, "due_date": "2026-01-01"})
    assert (dates.status_code, dates.json()["detail"]) == (
        422, "Due date cannot be earlier than the start date.")
    missing = client.get("/projects/999", headers=admin_headers)
    assert (missing.status_code, missing.json()["detail"]) == (404, "Project not found.")


def test_update_project_and_audit(client, admin_headers, db: Session):
    p = make_project(client, admin_headers)
    r = client.patch(f"/projects/{p['id']}", headers=admin_headers, json={"name": "Renamed"})
    assert r.json()["name"] == "Renamed"
    audit = db.query(AuditRecord).filter_by(action="UPDATE", entity_type="Project").one()
    assert audit.old_value["name"] == "Lab refresh" and audit.new_value["name"] == "Renamed"


def test_endpoints_require_login(client):
    for path in ("/projects", "/tasks", "/templates"):
        assert client.get(path).status_code == 401


# ---- templates and create-from-template (US-PRJ-02, BR-13) ------------------

TEMPLATE = {"name": "Semester setup", "description": "Recurring", "tasks": [
    {"title": "Inventory check", "relative_due_days": 3, "default_priority": "HIGH"},
    {"title": "Update images"},
    {"title": "Report to supervisor", "description": "Email summary"}]}


def test_project_from_template_copies_tasks_independently(client, admin_headers):
    tpl = client.post("/templates", headers=admin_headers, json=TEMPLATE).json()
    r = client.post("/projects/from-template", headers=admin_headers, json={
        "template_id": tpl["id"], "name": "Fall setup", "start_date": "2026-08-10"})
    assert r.status_code == 201, r.text
    project = r.json()
    assert project["template_id"] == tpl["id"] and project["total_tasks"] == 3
    first = project["tasks"][0]
    assert (first["title"], first["priority"], first["due_date"]) == ("Inventory check", "HIGH", "2026-08-13")
    assert project["tasks"][1]["due_date"] is None

    client.patch(f"/tasks/{first['id']}", headers=admin_headers, json={"title": "Edited copy"})
    stored = client.get(f"/templates/{tpl['id']}", headers=admin_headers).json()
    assert [t["title"] for t in stored["tasks"]][0] == "Inventory check"  # editing a copy leaves the template
    client.put(f"/templates/{tpl['id']}", headers=admin_headers,
               json={"name": "Semester setup v2", "tasks": [{"title": "Only one"}]})
    assert client.get(f"/tasks/{first['id']}", headers=admin_headers).json()["title"] == "Edited copy"
    assert client.get(f"/projects/{project['id']}", headers=admin_headers).json()["total_tasks"] == 3
    again = client.post("/projects/from-template", headers=admin_headers, json={
        "template_id": tpl["id"], "name": "Second", "start_date": "2026-09-01"}).json()
    assert [t["title"] for t in again["tasks"]] == ["Only one"]


def test_from_template_is_all_or_nothing(client, admin_headers, db: Session):
    tpl = client.post("/templates", headers=admin_headers, json=TEMPLATE).json()
    r = client.post("/projects/from-template", headers=admin_headers, json={
        "template_id": tpl["id"], "name": "Broken", "start_date": "2026-08-10", "member_ids": [9999]})
    assert r.status_code == 404
    assert db.query(Project).count() == 0 and db.query(Task).count() == 0


def test_from_template_unknown_template_and_invalid_details(client, admin_headers):
    r = client.post("/projects/from-template", headers=admin_headers,
                    json={"template_id": 99, "name": "x", "start_date": "2026-08-10"})
    assert (r.status_code, r.json()["detail"]) == (404, "Template not found.")
    tpl = client.post("/templates", headers=admin_headers, json=TEMPLATE).json()
    r = client.post("/projects/from-template", headers=admin_headers, json={
        "template_id": tpl["id"], "name": "x", "start_date": "2026-08-10", "due_date": "2026-08-01"})
    assert r.status_code == 422
    assert client.get("/projects", headers=admin_headers).json() == []


def test_template_needs_at_least_one_task(client, admin_headers):
    assert client.post("/templates", headers=admin_headers,
                       json={"name": "Empty", "tasks": []}).status_code == 422


# ---- tasks (US-PRJ-03, BR-14) -------------------------------------------------

def test_standalone_task_can_be_linked_to_a_project_later_but_only_once(client, admin_headers):
    p1, p2 = make_project(client, admin_headers), make_project(client, admin_headers, name="Other")
    task = make_task(client, admin_headers)
    assert task["project_id"] is None and task["status"] == "TODO"
    linked = client.patch(f"/tasks/{task['id']}", headers=admin_headers, json={"project_id": p1["id"]})
    assert linked.json()["project_id"] == p1["id"]
    again = client.patch(f"/tasks/{task['id']}", headers=admin_headers, json={"project_id": p2["id"]})
    assert (again.status_code, again.json()["detail"]) == (409, "Task already belongs to a project.")


def test_task_validation(client, admin_headers):
    assert client.post("/tasks", headers=admin_headers, json={"title": ""}).status_code == 422
    r = client.post("/tasks", headers=admin_headers, json={"title": "x", "project_id": 99})
    assert (r.status_code, r.json()["detail"]) == (404, "Project not found.")
    assert client.get("/tasks/99", headers=admin_headers).json()["detail"] == "Task not found."


# ---- assignment, history, hand-off (US-PRJ-04, US-PRJ-07) -----------------------

def test_assign_notifies_new_assignee_only_and_audits(client, admin_headers, sa_headers, ids, db):
    task = make_task(client, admin_headers)
    r = client.put(f"/tasks/{task['id']}/assignees", headers=admin_headers,
                   json={"user_ids": [ids["sa"], ids["admin"]]})
    assert sorted(r.json()["assignee_ids"]) == sorted(ids.values())
    notes = db.query(Notification).filter_by(event_type=EventType.TASK_ASSIGNED).all()
    assert [(n.recipient_id, n.related_type, n.related_id) for n in notes] == [(ids["sa"], "Task", task["id"])]
    audit = db.query(AuditRecord).filter_by(action="ASSIGN", entity_type="Task").one()
    assert audit.old_value == {"assignee_ids": []} and audit.actor_id == ids["admin"]


def test_assignee_must_exist_and_be_active(client, admin_headers, sa_headers, ids):
    task = make_task(client, admin_headers)
    missing = client.put(f"/tasks/{task['id']}/assignees", headers=admin_headers, json={"user_ids": [999]})
    assert (missing.status_code, missing.json()["detail"]) == (404, "User not found.")
    client.patch(f"/users/{ids['sa']}", headers=admin_headers, json={"status": "INACTIVE"})
    inactive = client.put(f"/tasks/{task['id']}/assignees", headers=admin_headers,
                          json={"user_ids": [ids["sa"]]})
    assert (inactive.status_code, inactive.json()["detail"]) == (422, "Assignee must be an active user.")
    assert client.put(f"/tasks/{task['id']}/assignees", headers=admin_headers,
                      json={"user_ids": []}).status_code == 422


def test_reassign_keeps_status_and_history(client, admin_headers, sa_headers, ids):
    task = make_task(client, admin_headers, assignee_ids=[ids["admin"]])
    client.put(f"/tasks/{task['id']}/status", headers=admin_headers, json={"status": "IN_PROGRESS"})
    r = client.put(f"/tasks/{task['id']}/assignees", headers=admin_headers, json={"user_ids": [ids["sa"]]})
    assert r.json()["assignee_ids"] == [ids["sa"]] and r.json()["status"] == "IN_PROGRESS"
    history = client.get(f"/tasks/{task['id']}/assignments", headers=admin_headers).json()
    assert [(h["user_id"], h["active"]) for h in history] == [(ids["admin"], False), (ids["sa"], True)]
    assert history[0]["ended_by"] == ids["admin"]


def test_handoff_unfinished_task_keeps_status_and_history(client, admin_headers, sa_headers, ids, db):
    task = make_task(client, admin_headers, assignee_ids=[ids["admin"]], status="IN_PROGRESS")
    r = client.post(f"/tasks/{task['id']}/handoff", headers=admin_headers, json={"to_user_id": ids["sa"]})
    assert r.status_code == 200
    assert (r.json()["status"], r.json()["assignee_ids"]) == ("IN_PROGRESS", [ids["sa"]])
    assert db.query(TaskAssignment).filter_by(task_id=task["id"]).count() == 2
    assert db.query(AuditRecord).filter_by(action="HANDOFF").count() == 1
    assert db.query(Notification).filter_by(recipient_id=ids["sa"]).count() == 1
    same = client.post(f"/tasks/{task['id']}/handoff", headers=admin_headers, json={"to_user_id": ids["sa"]})
    assert (same.status_code, same.json()["detail"]) == (409, "Task is already assigned to this user.")


def test_cannot_hand_off_a_finished_task(client, admin_headers, ids):
    task = make_task(client, admin_headers, assignee_ids=[ids["admin"]], status="COMPLETE")
    r = client.post(f"/tasks/{task['id']}/handoff", headers=admin_headers, json={"to_user_id": ids["sa"]})
    assert (r.status_code, r.json()["detail"]) == (422, "Only unfinished tasks can be handed off.")


# ---- status and project completion (US-PRJ-05, BR-15) -------------------------------

def test_progress_and_completion_rule(client, admin_headers):
    p = make_project(client, admin_headers)
    t1 = make_task(client, admin_headers, project_id=p["id"])
    t2 = make_task(client, admin_headers, project_id=p["id"], title="Second")
    client.put(f"/tasks/{t1['id']}/status", headers=admin_headers, json={"status": "COMPLETE"})
    detail = client.get(f"/projects/{p['id']}", headers=admin_headers).json()
    assert (detail["completed_tasks"], detail["total_tasks"], detail["progress"]) == (1, 2, 50.0)
    blocked = client.patch(f"/projects/{p['id']}", headers=admin_headers, json={"status": "COMPLETED"})
    assert (blocked.status_code, blocked.json()["detail"]) == (
        422, "A project can be completed only when all its tasks are Complete.")
    client.put(f"/tasks/{t2['id']}/status", headers=admin_headers, json={"status": "COMPLETE"})
    done = client.patch(f"/projects/{p['id']}", headers=admin_headers, json={"status": "COMPLETED"})
    assert done.json()["status"] == "COMPLETED" and done.json()["progress"] == 100.0


def test_reopening_a_task_reopens_a_completed_project(client, admin_headers):
    p = make_project(client, admin_headers)
    t = make_task(client, admin_headers, project_id=p["id"], status="COMPLETE")
    client.patch(f"/projects/{p['id']}", headers=admin_headers, json={"status": "COMPLETED"})
    client.put(f"/tasks/{t['id']}/status", headers=admin_headers, json={"status": "IN_PROGRESS"})
    assert client.get(f"/projects/{p['id']}", headers=admin_headers).json()["status"] == "ACTIVE"


def test_status_change_is_audited_with_old_and_new(client, admin_headers, ids, db):
    t = make_task(client, admin_headers)
    client.put(f"/tasks/{t['id']}/status", headers=admin_headers, json={"status": "IN_PROGRESS"})
    a = db.query(AuditRecord).filter_by(action="STATUS_CHANGE").one()
    assert (a.old_value, a.new_value, a.actor_id) == (
        {"status": "TODO"}, {"status": "IN_PROGRESS"}, ids["admin"])


# ---- search (US-PRJ-06) -------------------------------------------------------------------

def test_search_and_filter_tasks(client, admin_headers, ids):
    p = make_project(client, admin_headers)
    make_task(client, admin_headers, title="Replace projector bulb", due_date="2026-02-10",
              assignee_ids=[ids["admin"]], project_id=p["id"])
    make_task(client, admin_headers, title="Image laptops", due_date="2026-03-10", status="IN_PROGRESS")
    titles = lambda qs: [t["title"] for t in client.get("/tasks" + qs, headers=admin_headers).json()]
    assert titles("?q=projector") == ["Replace projector bulb"]
    assert titles("?status=IN_PROGRESS") == ["Image laptops"]
    assert titles(f"?assignee_id={ids['admin']}") == ["Replace projector bulb"]
    assert titles("?due_before=2026-02-28") == ["Replace projector bulb"]
    assert titles("?due_after=2026-02-28") == ["Image laptops"]
    assert titles(f"?project_id={p['id']}&status=TODO") == ["Replace projector bulb"]
    assert titles("?q=projector&status=IN_PROGRESS") == []


def test_search_and_filter_projects(client, admin_headers, ids):
    p = make_project(client, admin_headers)
    make_project(client, admin_headers, name="Network upgrade", status="PLANNED", due_date="2026-06-01")
    make_task(client, admin_headers, project_id=p["id"], assignee_ids=[ids["admin"]])
    names = lambda qs: [x["name"] for x in client.get("/projects" + qs, headers=admin_headers).json()]
    assert names("?q=network") == ["Network upgrade"]
    assert names("?status=ACTIVE") == ["Lab refresh"]
    assert names(f"?assignee_id={ids['admin']}") == ["Lab refresh"]
    assert names("?due_after=2026-05-01") == ["Network upgrade"]


# ---- notifications from PRJ (US-NTF-06, US-NTF-01, FR-NTF-03) --------------------------------

def notes_for(db: Session, user_id: int, kind: EventType) -> list[Notification]:
    return db.query(Notification).filter_by(recipient_id=user_id, event_type=kind).all()


def test_project_events_notify_members_only(client, admin_headers, sa_headers, ids, db):
    p = make_project(client, admin_headers, member_ids=[ids["sa"]])
    assert [n.project_id for n in notes_for(db, ids["sa"], EventType.PROJECT_CREATED)] == [p["id"]]
    client.patch(f"/projects/{p['id']}", headers=admin_headers, json={"description": "new text"})
    assert len(notes_for(db, ids["sa"], EventType.PROJECT_UPDATED)) == 1
    assert notes_for(db, ids["admin"], EventType.PROJECT_UPDATED) == []  # actor not notified
    other = make_project(client, admin_headers, name="Private")  # SA is not a member
    client.patch(f"/projects/{other['id']}", headers=admin_headers, json={"description": "x"})
    assert len(notes_for(db, ids["sa"], EventType.PROJECT_UPDATED)) == 1


def test_adding_a_member_notifies_members(client, admin_headers, sa_headers, ids, db):
    p = make_project(client, admin_headers)
    r = client.post(f"/projects/{p['id']}/members", headers=admin_headers, json={"user_id": ids["sa"]})
    assert sorted(r.json()) == sorted(ids.values())
    assert len(notes_for(db, ids["sa"], EventType.PROJECT_MEMBER_ADDED)) == 1
    dup = client.post(f"/projects/{p['id']}/members", headers=admin_headers, json={"user_id": ids["sa"]})
    assert (dup.status_code, dup.json()["detail"]) == (409, "User is already a project member.")


def test_assigning_a_project_task_makes_the_assignee_a_member(client, admin_headers, sa_headers, ids):
    p = make_project(client, admin_headers)
    t = make_task(client, admin_headers, project_id=p["id"])
    client.put(f"/tasks/{t['id']}/assignees", headers=admin_headers, json={"user_ids": [ids["sa"]]})
    assert ids["sa"] in client.get(f"/projects/{p['id']}/members", headers=admin_headers).json()


def test_shift_summary_lists_assigned_open_tasks(client, admin_headers, sa_headers, ids):
    make_task(client, admin_headers, title="Check lab PCs", due_date="2026-01-05", assignee_ids=[ids["sa"]])
    make_task(client, admin_headers, title="Late job", due_date="2026-01-01", assignee_ids=[ids["sa"]])
    make_task(client, admin_headers, title="Done job", due_date="2026-01-05", status="COMPLETE",
              assignee_ids=[ids["sa"]])
    make_task(client, admin_headers, title="Admin only", due_date="2026-01-05", assignee_ids=[ids["admin"]])
    r = client.post("/notifications/shift-summary", headers=admin_headers, json={
        "shift": "MORNING", "shift_date": "2026-01-05", "user_ids": [ids["sa"]]})
    msg = r.json()[0]["message"]
    assert "Check lab PCs" in msg and "Late job (due 2026-01-01, overdue)" in msg
    assert "Done job" not in msg and "Admin only" not in msg
