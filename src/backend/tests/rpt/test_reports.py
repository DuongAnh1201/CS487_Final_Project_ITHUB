"""RPT: US-RPT-01..06, FR-RPT-01..09, BR-RPT-01..03."""

from datetime import datetime

import pytest
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError
from app.modules.ntf.models import Notification
from app.modules.rpt.models import DailyReport, MonthlySummaryReport, Report
from app.shared.audit import AuditLog, AuditRecord
from app.shared.events import EventType


@pytest.fixture
def ids(client, admin_headers, sa_headers) -> dict[str, int]:
    return {"admin": client.get("/auth/me", headers=admin_headers).json()["id"],
            "sa": client.get("/auth/me", headers=sa_headers).json()["id"]}


def make_report(client, headers, **extra) -> dict:
    r = client.post("/reports", headers=headers, json={"title": "Lab check", "description": "All good", **extra})
    assert r.status_code == 201, r.text
    return r.json()


def submit(client, headers, report_id, reviewer_ids):
    return client.post(f"/reports/{report_id}/submit", headers=headers, json={"reviewer_ids": reviewer_ids})


def review(client, headers, report_id, status, comment=""):
    return client.post(f"/reports/{report_id}/review", headers=headers, json={"status": status, "comment": comment})


# ---- create (US-RPT-01) and the abstract Report ----------------------------------------------

def test_create_report_starts_as_draft(client, sa_headers, ids):
    r = make_report(client, sa_headers, project_id=7)
    assert (r["status"], r["author_id"], r["project_id"], r["report_type"]) == ("DRAFT", ids["sa"], 7, "DAILY")
    assert r["content"] == "All good"
    assert client.get(f"/reports/{r['id']}", headers=sa_headers).json()["id"] == r["id"]


def test_title_is_required_without_a_template(client, sa_headers):
    r = client.post("/reports", headers=sa_headers, json={"description": "x"})
    assert (r.status_code, r.json()["detail"]) == (422, "Title is required.")
    assert client.get("/reports/99", headers=sa_headers).json()["detail"] == "Report not found."


def test_report_base_class_is_abstract():
    with pytest.raises(NotImplementedError):
        Report.generate_content(DailyReport())


def test_template_method_render_uses_the_subclass_body():
    from app.modules.rpt.models import ReportStatus
    report = DailyReport(title="T", status=ReportStatus.DRAFT, description="body", checklist_answers={"A": "ok", "B": ""})
    assert report.render() == "T [DRAFT]\nbody\n- A: ok\n- B: (not answered)"


# ---- templates (US-RPT-05) ----------------------------------------------------------------------

def test_default_morning_template_is_provided(client, sa_headers):
    names = [t["name"] for t in client.get("/report-templates", headers=sa_headers).json()]
    assert names == ["Morning checklist"]


def test_report_from_template_prefills_the_checklist(client, sa_headers):
    tpl = client.post("/report-templates", headers=sa_headers, json={
        "name": "Evening", "checklist_items": ["Doors locked", "Lights off"]}).json()
    r = client.post("/reports", headers=sa_headers, json={"template_id": tpl["id"], "shift": "EVENING"}).json()
    assert r["title"].startswith("Evening - ") and r["shift"] == "EVENING"
    assert r["checklist_answers"] == {"Doors locked": "", "Lights off": ""}
    done = client.put(f"/reports/{r['id']}/answers", headers=sa_headers, json={"answers": {"Doors locked": "yes"}})
    assert done.json()["checklist_answers"]["Doors locked"] == "yes"
    assert "- Doors locked: yes" in done.json()["content"] and "(not answered)" in done.json()["content"]
    bad = client.put(f"/reports/{r['id']}/answers", headers=sa_headers, json={"answers": {"Nope": "x"}})
    assert (bad.status_code, bad.json()["detail"]) == (422, "Unknown checklist item: Nope.")


def test_template_changes_do_not_alter_existing_reports(client, sa_headers):
    tpl = client.get("/report-templates", headers=sa_headers).json()[0]
    r = client.post("/reports", headers=sa_headers, json={"template_id": tpl["id"]}).json()
    client.put(f"/report-templates/{tpl['id']}", headers=sa_headers,
               json={"name": "Morning checklist", "checklist_items": ["Only this"]})
    assert list(client.get(f"/reports/{r['id']}", headers=sa_headers).json()["checklist_answers"]) == tpl["checklist_items"]


def test_template_names_are_unique(client, sa_headers):
    r = client.post("/report-templates", headers=sa_headers, json={"name": "Morning checklist", "checklist_items": ["x"]})
    assert (r.status_code, r.json()["detail"]) == (409, "A template with this name already exists.")
    assert client.post("/reports", headers=sa_headers, json={"template_id": 99}).json()["detail"] == "Template not found."


# ---- submit / review workflow (SP7 §3, FR-RPT-03/04) -----------------------------------------------

def test_submit_notifies_reviewers(client, sa_headers, admin_headers, ids, db):
    r = make_report(client, sa_headers)
    s = submit(client, sa_headers, r["id"], [ids["admin"]]).json()
    assert (s["status"], s["reviewer_ids"], s["submitted_at"] is not None) == ("SUBMITTED", [ids["admin"]], True)
    notes = db.query(Notification).filter_by(event_type=EventType.REPORT_SUBMITTED).all()
    assert [(n.recipient_id, n.related_id) for n in notes] == [(ids["admin"], r["id"])]


def test_submit_needs_a_reviewer_and_a_draft(client, sa_headers, ids):
    r = make_report(client, sa_headers)
    none = submit(client, sa_headers, r["id"], [])
    assert (none.status_code, none.json()["detail"]) == (422, "At least one reviewer is required.")
    assert submit(client, sa_headers, r["id"], [999]).json()["detail"] == "User not found."
    submit(client, sa_headers, r["id"], [ids["admin"]])
    again = submit(client, sa_headers, r["id"], [ids["admin"]])
    assert (again.status_code, again.json()["detail"]) == (409, "Only draft or reviewed reports can be submitted.")


def test_review_sets_status_and_notifies_the_author(client, sa_headers, admin_headers, ids, db):
    r = make_report(client, sa_headers)
    submit(client, sa_headers, r["id"], [ids["admin"]])
    done = review(client, admin_headers, r["id"], "PASSED").json()
    assert done["status"] == "PASSED"
    notes = db.query(Notification).filter_by(event_type=EventType.REPORT_REVIEWED).all()
    assert [(n.recipient_id, n.message) for n in notes] == [(ids["sa"], f"Report #{r['id']} is now PASSED.")]
    audit = db.query(AuditRecord).filter_by(action="REVIEW").one()
    assert (audit.old_value["status"], audit.new_value["status"], audit.actor_id) == ("SUBMITTED", "PASSED", ids["admin"])


def test_review_rules(client, sa_headers, admin_headers, ids):
    r = make_report(client, sa_headers)
    early = review(client, admin_headers, r["id"], "PASSED")
    assert (early.status_code, early.json()["detail"]) == (409, "Only submitted reports can be reviewed.")
    submit(client, sa_headers, r["id"], [ids["admin"]])
    stranger = review(client, sa_headers, r["id"], "PASSED")
    assert (stranger.status_code, stranger.json()["detail"]) == (403, "Only an assigned reviewer can review this report.")
    for status in ("REJECTED", "REVIEWED"):
        needs = review(client, admin_headers, r["id"], status)
        assert (needs.status_code, needs.json()["detail"]) == (422, "A comment is required.")
    assert review(client, admin_headers, r["id"], "SUBMITTED").status_code == 422
    assert review(client, admin_headers, r["id"], "REJECTED", "Missing photos").json()["status"] == "REJECTED"
    final = review(client, admin_headers, r["id"], "PASSED")
    assert final.status_code == 409  # Rejected is final


def test_reviewed_report_can_be_edited_and_resubmitted(client, sa_headers, admin_headers, ids):
    r = make_report(client, sa_headers)
    submit(client, sa_headers, r["id"], [ids["admin"]])
    assert client.patch(f"/reports/{r['id']}", headers=sa_headers, json={"title": "Nope"}).json()["detail"] == "Submitted reports cannot be edited."
    review(client, admin_headers, r["id"], "REVIEWED", "Please add the printer count")
    assert client.patch(f"/reports/{r['id']}", headers=sa_headers, json={"description": "Added"}).status_code == 200
    again = submit(client, sa_headers, r["id"], [])  # keeps the earlier reviewers
    assert (again.json()["status"], again.json()["reviewer_ids"]) == ("SUBMITTED", [ids["admin"]])


def test_history_records_every_status_change(client, sa_headers, admin_headers, ids, clock):
    r = make_report(client, sa_headers)
    submit(client, sa_headers, r["id"], [ids["admin"]])
    clock.advance(hours=2)
    review(client, admin_headers, r["id"], "REVIEWED", "Add details")
    history = client.get(f"/reports/{r['id']}/history", headers=sa_headers).json()
    assert [(h["old_status"], h["new_status"], h["changed_by"]) for h in history] == [
        (None, "DRAFT", ids["sa"]), ("DRAFT", "SUBMITTED", ids["sa"]), ("SUBMITTED", "REVIEWED", ids["admin"])]
    assert history[2]["comment"] == "Add details" and history[2]["changed_at"] > history[1]["changed_at"]


# ---- search and grouping (US-RPT-02, FR-RPT-08) --------------------------------------------------------

def test_search_and_filter_reports(client, sa_headers, admin_headers, ids):
    a = make_report(client, sa_headers, title="Printer audit", project_id=1)
    b = make_report(client, admin_headers, title="Network check", project_id=2)
    submit(client, sa_headers, a["id"], [ids["admin"]])
    found = lambda qs: [r["id"] for r in client.get("/reports" + qs, headers=sa_headers).json()]
    assert found("?q=printer") == [a["id"]] and found(f"?q={b['id']}") == [b["id"]]
    assert found("?status=SUBMITTED") == [a["id"]] and found("?project_id=2") == [b["id"]]
    assert found(f"?author_id={ids['admin']}") == [b["id"]]
    assert found("?q=printer&project_id=2") == []
    assert found("?date_from=2026-01-05&date_to=2026-01-05") == [a["id"], b["id"]]
    assert found("?date_from=2026-02-01") == []


def test_reports_grouped_by_project_with_unlinked_last(client, sa_headers):
    make_report(client, sa_headers, title="Loose")
    p2 = make_report(client, sa_headers, title="P2", project_id=2)
    p1 = make_report(client, sa_headers, title="P1", project_id=1)
    groups = client.get("/reports/by-project", headers=sa_headers).json()
    assert [(g["project_id"], [r["id"] for r in g["reports"]]) for g in groups] == [
        (1, [p1["id"]]), (2, [p2["id"]]), (None, [groups[2]["reports"][0]["id"]])]
    assert groups[2]["reports"][0]["title"] == "Loose"


# ---- monthly summary (US-RPT, FR-RPT-07, BR-RPT-01) ----------------------------------------------------

def test_monthly_summary_only_at_month_end(client, admin_headers, sa_headers, clock, ids, db):
    make_report(client, sa_headers)  # Jan 5
    early = client.post("/reports/monthly-summary", headers=admin_headers, json={"month": 1, "year": 2026})
    assert (early.status_code, early.json()["detail"]) == (422, "The monthly summary can only be generated at the end of the month.")
    clock.advance(days=26)  # Jan 31
    r = client.post("/reports/monthly-summary", headers=admin_headers, json={"month": 1, "year": 2026})
    assert r.status_code == 201, r.text
    body = r.json()
    assert (body["report_type"], body["status"], body["author_id"], body["reviewer_ids"]) == (
        "MONTHLY_SUMMARY", "SUBMITTED", None, [ids["admin"]])
    assert "Reports (1): DRAFT: 1" in body["content"] and "Orders (0): none" in body["content"]
    dup = client.post("/reports/monthly-summary", headers=admin_headers, json={"month": 1, "year": 2026})
    assert (dup.status_code, dup.json()["detail"]) == (409, "The monthly summary for this month already exists.")
    notes = db.query(Notification).filter_by(event_type=EventType.MONTHLY_SUMMARY).all()
    assert [n.recipient_id for n in notes] == []  # the actor is the only Admin and is not notified of own action
    assert db.query(MonthlySummaryReport).count() == 1


def test_monthly_summary_counts_orders_and_reaches_other_admins(client, admin_headers, sa_headers, clock, ids, db):
    from app.modules.ord.models import Order, OrderStatus
    client.patch(f"/users/{ids['sa']}", headers=admin_headers, json={"role": "ADMIN"})
    db.add_all([Order(item_id=1, item_name="x", quantity_ordered=1, status=OrderStatus.ARRIVED, requested_at=datetime(2026, 1, 9)),
                Order(item_id=2, item_name="y", quantity_ordered=1, status=OrderStatus.ORDERED, requested_at=datetime(2026, 1, 10)),
                Order(item_id=3, item_name="z", quantity_ordered=1, status=OrderStatus.ORDERED, requested_at=datetime(2026, 2, 1))])
    db.commit()
    clock.advance(days=40)
    r = client.post("/reports/monthly-summary", headers=admin_headers, json={"month": 1, "year": 2026}).json()
    assert "Orders (2): ARRIVED: 1, ORDERED: 1" in r["content"]
    assert sorted(r["reviewer_ids"]) == sorted(ids.values())
    notes = db.query(Notification).filter_by(event_type=EventType.MONTHLY_SUMMARY).all()
    assert [n.recipient_id for n in notes] == [ids["sa"]]


def test_is_month_end():
    from datetime import date
    from app.modules.rpt.service import SummaryGenerator
    assert SummaryGenerator.is_month_end(date(2026, 2, 28)) and not SummaryGenerator.is_month_end(date(2026, 2, 27))
    assert SummaryGenerator.is_month_end(date(2028, 2, 29))


# ---- audit log (FR-RPT-06/08/09, BR-RPT-03, UC-RPT-04) --------------------------------------------------

def test_audit_search_and_filters(client, sa_headers, admin_headers, ids, clock):
    make_report(client, sa_headers)
    clock.advance(days=3)
    r2 = make_report(client, sa_headers, title="Later")
    submit(client, sa_headers, r2["id"], [ids["admin"]])
    audit = lambda qs: client.get("/audit" + qs, headers=admin_headers).json()
    assert {a["entity_type"] for a in audit("?entity_type=Report")} == {"Report"}
    assert [a["action"] for a in audit(f"?entity_type=Report&entity_id={r2['id']}")] == ["SUBMIT", "CREATE"]  # newest first
    assert all(a["actor_id"] == ids["sa"] for a in audit(f"?user_id={ids['sa']}&entity_type=Report"))
    assert [a["action"] for a in audit("?action=submit")] == ["SUBMIT"]
    jan8 = audit("?date_from=2026-01-08&date_to=2026-01-08&entity_type=Report")
    assert {a["entity_id"] for a in jan8} == {str(r2["id"])}
    assert audit("?date_to=2026-01-01") == []
    assert len(audit("?limit=2")) == 2 and audit("?limit=2&offset=1")[0]["id"] == audit("")[1]["id"]


def test_every_audit_record_has_a_unique_id_and_a_status(client, sa_headers):
    make_report(client, sa_headers)
    records = client.get("/audit", headers=sa_headers).json()
    assert len({r["id"] for r in records}) == len(records) and all(r["status"] == "SUCCESS" for r in records)
    one = client.get(f"/audit/{records[0]['id']}", headers=sa_headers)
    assert one.status_code == 200 and one.json()["id"] == records[0]["id"]
    assert client.get("/audit/99999", headers=sa_headers).json()["detail"] == "Audit record not found."


def test_audit_records_cannot_be_changed_or_removed(client, sa_headers, db: Session):
    make_report(client, sa_headers)
    record = db.query(AuditRecord).first()
    record.action = "TAMPERED"
    with pytest.raises(ConflictError, match="cannot be changed or removed"):
        db.flush()
    db.rollback()
    db.delete(db.query(AuditRecord).first())
    with pytest.raises(ConflictError):
        db.flush()
    db.rollback()
    assert client.delete("/audit/1", headers=sa_headers).status_code == 405
    assert client.put("/audit/1", headers=sa_headers).status_code == 405


def test_audit_describe_and_requires_login(client, db: Session):
    AuditLog(db).record(None, "TEST", "Thing", 5)
    assert "system: TEST Thing 5" in db.query(AuditRecord).filter_by(action="TEST").one().describe()
    assert client.get("/audit").status_code == 401
    db.rollback()
