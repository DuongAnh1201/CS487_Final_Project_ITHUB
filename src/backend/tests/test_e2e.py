"""End-to-end smoke flows across pages (issue #65), using the real wiring from app.integration."""

import re

import pytest

PUBLIC = {("GET", "/health"), ("POST", "/auth/login"), ("POST", "/auth/google"), ("GET", "/auth/config")}
# Verified by its signature instead of a login (see tests/ntf/test_email.py).
SIGNED_WEBHOOKS = {("POST", "/webhooks/resend")}


@pytest.fixture
def ids(client, admin_headers, sa_headers) -> dict[str, int]:
    return {"admin": client.get("/auth/me", headers=admin_headers).json()["id"],
            "sa": client.get("/auth/me", headers=sa_headers).json()["id"]}


def ok(response, status=None):
    assert response.status_code == (status or response.status_code) and response.status_code < 300, response.text
    return response.json()


def notifications(client, headers, event_type=None) -> list[dict]:
    found = ok(client.get("/notifications", headers=headers))
    return [n for n in found if event_type is None or n["event_type"] == event_type]


def make_location(client, headers, room="101") -> dict:
    return ok(client.post("/ast/locations", headers=headers, json={"building": "Main", "room": room}), 201)


def install_desktop(client, admin, sa, tag="PC-1"):
    """A classroom with one installed desktop; returns (classroom, equipment, item)."""
    category = ok(client.post("/ast/categories", headers=admin, json={"name": "Desktop"}), 201)
    location = make_location(client, admin)
    item = ok(client.post("/ast/items", headers=sa, json={
        "asset_tag": tag, "serial_number": "S1", "model": "OptiPlex", "manufacturer": "Dell",
        "category_id": category["id"], "location_id": location["id"]}), 201)
    room = ok(client.post("/classrooms", headers=admin, json={
        "location_id": location["id"], "capacity": 30, "room_type": "COMPUTER_LAB"}), 201)
    equipment = ok(client.post(f"/classrooms/{room['id']}/equipment", headers=sa, json={"item_id": item["id"]}), 201)
    return room, equipment, item


# ---- flow 1: consumable -> low stock -> automatic order -> receive -> stock + notifications ----------

def test_low_stock_creates_an_order_and_receiving_it_restocks(client, admin_headers, sa_headers, ids):
    category = ok(client.post("/ast/categories", headers=admin_headers, json={"name": "Cables", "is_consumable": True}), 201)
    location = make_location(client, admin_headers)
    supply = ok(client.post("/ast/consumables", headers=sa_headers, json={
        "name": "HDMI cable", "category_id": category["id"], "location_id": location["id"],
        "reorder_threshold": 5, "unit": "each"}), 201)
    ok(client.post(f"/ast/consumables/{supply['id']}/stock-in", headers=sa_headers, json={"quantity": 10}))
    assert ok(client.get("/orders", headers=sa_headers)) == []  # 10 is above the threshold

    ok(client.post(f"/ast/consumables/{supply['id']}/stock-out", headers=sa_headers,
                   json={"quantity": 6, "issued_to": "Room 101"}))
    (order,) = ok(client.get("/orders", headers=sa_headers))
    assert (order["status"], order["item_id"], order["item_name"], order["requested_by"]) == (
        "REQUESTED", supply["id"], "HDMI cable", None)
    assert order["quantity_ordered"] == 6  # back up to twice the threshold (4 on hand + 6 = 10)
    assert [n["related_id"] for n in notifications(client, admin_headers, "LOW_STOCK")] == [supply["id"]]

    # a further stock-out while the order is open must not create a second order (BR-ORD-01)
    ok(client.post(f"/ast/consumables/{supply['id']}/stock-out", headers=sa_headers,
                   json={"quantity": 1, "issued_to": "Room 102"}))
    assert len(ok(client.get("/orders", headers=sa_headers))) == 1

    ok(client.post(f"/orders/{order['id']}/place", headers=sa_headers))
    received = ok(client.post(f"/orders/{order['id']}/receive", headers=sa_headers, json={"quantity": 6}))
    assert (received["status"], received["remaining_quantity"]) == ("ARRIVED", 0)
    stock = ok(client.get(f"/ast/consumables/{supply['id']}", headers=sa_headers))
    assert stock["quantity_on_hand"] == 9  # 10 - 6 - 1 + 6
    arrived = notifications(client, admin_headers, "ORDER_ARRIVED")
    assert [(n["related_type"], n["related_id"]) for n in arrived] == [("Order", order["id"])]
    audit = ok(client.get("/audit?entity_type=Order", headers=admin_headers))
    assert {"CREATE", "PLACE", "RECEIVE"} <= {a["action"] for a in audit}


def test_receiving_an_order_through_orders_adds_stock_in_assets(client, admin_headers, sa_headers):
    category = ok(client.post("/ast/categories", headers=admin_headers, json={"name": "Toner", "is_consumable": True}), 201)
    location = make_location(client, admin_headers)
    supply = ok(client.post("/ast/consumables", headers=sa_headers, json={
        "name": "Toner", "category_id": category["id"], "location_id": location["id"], "reorder_threshold": 2}), 201)
    order = ok(client.post("/orders", headers=sa_headers, json={"item_id": supply["id"], "quantity": 5, "vendor": "Acme"}), 201)
    ok(client.post(f"/orders/{order['id']}/place", headers=sa_headers))
    ok(client.post(f"/orders/{order['id']}/receive", headers=sa_headers, json={"quantity": 2}))
    assert ok(client.get(f"/ast/consumables/{supply['id']}", headers=sa_headers))["quantity_on_hand"] == 2
    movements = ok(client.get(f"/ast/consumables/{supply['id']}/transactions", headers=sa_headers))
    assert [m["quantity"] for m in movements] == [2]


# ---- flow 2: issue -> equipment faulty -> admin notified -> resolve -----------------------------------

def test_issue_marks_equipment_faulty_notifies_admin_and_resolves(client, admin_headers, sa_headers, ids):
    room, equipment, _ = install_desktop(client, admin_headers, sa_headers)
    assert ok(client.get(f"/classrooms/{room['id']}", headers=sa_headers))["status"] == "AVAILABLE"

    issue = ok(client.post("/issues", headers=sa_headers, json={
        "classroom_id": room["id"], "room_equipment_id": equipment["id"], "category": "HARDWARE",
        "severity": "HIGH", "description": "Will not boot", "reporter_name": "Dr. Lee",
        "reporter_type": "FACULTY"}), 201)
    installed = ok(client.get(f"/classrooms/{room['id']}/equipment", headers=sa_headers))
    assert installed[0]["condition"] == "FAULTY"
    assert ok(client.get(f"/classrooms/{room['id']}", headers=sa_headers))["status"] != "AVAILABLE"
    reported = notifications(client, admin_headers, "ISSUE_REPORTED")
    assert [(n["related_type"], n["related_id"]) for n in reported] == [("Issue", issue["id"])]
    assert notifications(client, sa_headers, "ISSUE_REPORTED") == []  # the reporter is not told about their own report

    step = ok(client.post(f"/issues/{issue['id']}/status", headers=admin_headers, json={
        "status": "ASSIGNED", "version": issue["version"], "assignee_id": ids["sa"]}))
    step = ok(client.post(f"/issues/{issue['id']}/status", headers=sa_headers, json={
        "status": "IN_PROGRESS", "version": step["version"]}))
    done = ok(client.post(f"/issues/{issue['id']}/resolve", headers=sa_headers, json={
        "notes": "Replaced the PSU", "new_condition": "WORKING", "version": step["version"]}))
    assert done["status"] == "RESOLVED"
    assert ok(client.get(f"/classrooms/{room['id']}/equipment", headers=sa_headers))[0]["condition"] == "WORKING"
    assert ok(client.get(f"/classrooms/{room['id']}", headers=sa_headers))["status"] == "AVAILABLE"
    history = ok(client.get(f"/issues/{issue['id']}/history", headers=sa_headers))
    assert len(history) >= 3


def test_only_admin_can_assign_an_issue(client, admin_headers, sa_headers, ids):
    room, _, _ = install_desktop(client, admin_headers, sa_headers)
    issue = ok(client.post("/issues", headers=sa_headers, json={
        "classroom_id": room["id"], "category": "SOFTWARE", "severity": "LOW", "description": "Slow",
        "reporter_name": "Dr. Lee", "reporter_type": "FACULTY"}), 201)
    denied = client.post(f"/issues/{issue['id']}/status", headers=sa_headers, json={
        "status": "ASSIGNED", "version": issue["version"], "assignee_id": ids["sa"]})
    assert (denied.status_code, denied.json()["detail"]) == (403, "Not allowed for your role.")


# ---- flow 3: retiring equipment removes it from its classroom (BR-18) ---------------------------------

def test_retiring_an_item_removes_it_from_its_classroom(client, admin_headers, sa_headers):
    room, _, item = install_desktop(client, admin_headers, sa_headers)
    assert len(ok(client.get(f"/classrooms/{room['id']}/equipment", headers=sa_headers))) == 1
    denied = client.post(f"/ast/items/{item['id']}/retire", headers=sa_headers, json={"reason": "End of life"})
    assert denied.status_code == 403
    ok(client.post(f"/ast/items/{item['id']}/retire", headers=admin_headers, json={"reason": "End of life"}))
    assert ok(client.get(f"/classrooms/{room['id']}/equipment", headers=sa_headers)) == []
    assert ok(client.get(f"/ast/items/{item['id']}", headers=sa_headers))["status"] == "Retired"


def test_equipment_installed_in_a_classroom_cannot_be_lent(client, admin_headers, sa_headers):
    _, _, item = install_desktop(client, admin_headers, sa_headers)
    borrower = ok(client.post("/ast/borrowers", headers=sa_headers, json={
        "school_id": "S-1", "full_name": "Alex", "email": "alex@sfbu.edu", "type": "STUDENT"}), 201)
    lend = client.post("/ast/loans", headers=sa_headers, json={
        "item_id": item["id"], "borrower_id": borrower["id"], "condition_out": "Good"})
    assert (lend.status_code, lend.json()["detail"]) == (
        409, "Item is installed in a classroom and cannot be lent.")


def test_equipment_can_be_lent_again_once_removed_from_the_classroom(client, admin_headers, sa_headers):
    room, equipment, item = install_desktop(client, admin_headers, sa_headers)
    borrower = ok(client.post("/ast/borrowers", headers=sa_headers, json={
        "school_id": "S-2", "full_name": "Sam", "email": "sam@sfbu.edu", "type": "STUDENT"}), 201)
    ok(client.post(f"/classroom-equipment/{equipment['id']}/remove", headers=sa_headers,
                   json={"version": equipment["version"]}))
    loan = client.post("/ast/loans", headers=sa_headers, json={
        "item_id": item["id"], "borrower_id": borrower["id"], "condition_out": "Good"})
    assert loan.status_code == 201, loan.text


def test_classroom_equipment_must_exist_in_assets(client, admin_headers, sa_headers):
    location = make_location(client, admin_headers)
    room = ok(client.post("/classrooms", headers=admin_headers, json={
        "location_id": location["id"], "capacity": 20, "room_type": "LECTURE"}), 201)
    missing = client.post(f"/classrooms/{room['id']}/equipment", headers=sa_headers, json={"item_id": 999})
    assert missing.status_code == 404
    unknown_location = client.post("/classrooms", headers=admin_headers, json={
        "location_id": 999, "capacity": 20, "room_type": "LECTURE"})
    assert unknown_location.status_code == 404


# ---- flow 4: project from template -> assign -> notification ---------------------------------------------

def test_project_from_template_assign_and_notify(client, admin_headers, sa_headers, ids):
    template = ok(client.post("/templates", headers=admin_headers, json={
        "name": "Semester setup", "tasks": [{"title": "Inventory check", "relative_due_days": 3},
                                            {"title": "Update images"}]}), 201)
    project = ok(client.post("/projects/from-template", headers=admin_headers, json={
        "template_id": template["id"], "name": "Fall setup", "start_date": "2026-08-10"}), 201)
    assert project["total_tasks"] == 2
    task = project["tasks"][0]
    ok(client.put(f"/tasks/{task['id']}/assignees", headers=admin_headers, json={"user_ids": [ids["sa"]]}))
    assigned = notifications(client, sa_headers, "TASK_ASSIGNED")
    assert [(n["related_type"], n["related_id"]) for n in assigned] == [("Task", task["id"])]
    assert ids["sa"] in ok(client.get(f"/projects/{project['id']}/members", headers=admin_headers))
    ok(client.put(f"/tasks/{task['id']}/status", headers=sa_headers, json={"status": "COMPLETE"}))
    assert ok(client.get(f"/projects/{project['id']}", headers=sa_headers))["progress"] == 50.0


# ---- flow 5: report review across notifications and audit ---------------------------------------------------

def test_report_review_notifies_author_and_is_audited(client, admin_headers, sa_headers, ids):
    template = ok(client.get("/report-templates", headers=sa_headers))[0]
    report = ok(client.post("/reports", headers=sa_headers, json={"template_id": template["id"], "shift": "MORNING"}), 201)
    ok(client.post(f"/reports/{report['id']}/submit", headers=sa_headers, json={"reviewer_ids": [ids["admin"]]}))
    assert [n["related_id"] for n in notifications(client, admin_headers, "REPORT_SUBMITTED")] == [report["id"]]
    ok(client.post(f"/reports/{report['id']}/review", headers=admin_headers, json={"status": "PASSED"}))
    assert [n["related_id"] for n in notifications(client, sa_headers, "REPORT_REVIEWED")] == [report["id"]]
    actions = {a["action"] for a in ok(client.get(f"/audit?entity_type=Report&entity_id={report['id']}", headers=admin_headers))}
    assert {"CREATE", "SUBMIT", "REVIEW"} <= actions


def test_changes_across_pages_share_one_audit_log(client, admin_headers, sa_headers):
    install_desktop(client, admin_headers, sa_headers)
    seen = {(a["entity_type"], a["action"].upper()) for a in ok(client.get("/audit?limit=500", headers=admin_headers))}
    assert {("Category", "CREATE"), ("Location", "CREATE"), ("Item", "CREATE"), ("Classroom", "CREATE"),
            ("RoomEquipment", "INSTALL"), ("User", "CREATE")} <= seen


# ---- auth is required everywhere except the public routes ----------------------------------------------------------

def concrete(path: str) -> str:
    return re.sub(r"\{[^}]+\}", "1", path)


def test_every_route_requires_login_except_the_public_ones(client):
    spec = client.get("/openapi.json").json()
    checked = []
    for path, operations in spec["paths"].items():
        for method in operations:
            if (method.upper(), path) in PUBLIC | SIGNED_WEBHOOKS:
                continue
            response = client.request(method.upper(), concrete(path))
            assert response.status_code == 401, f"{method.upper()} {path} answered {response.status_code}"
            assert response.json()["detail"] in ("Please log in to continue.",), (method, path)
            checked.append((method, path))
    assert len(checked) > 100  # the whole API was covered, not a handful


def test_public_routes_work_without_a_token(client):
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/auth/config").status_code == 200
    assert client.post("/auth/login", json={"email": "x@sfbu.edu", "password": "nope"}).status_code == 401
    assert client.post("/auth/google", json={"id_token": "x"}).status_code == 503


def test_a_bad_token_is_rejected_everywhere(client):
    headers = {"Authorization": "Bearer not-a-real-token"}
    for path in ("/ast/items", "/classrooms", "/issues", "/orders", "/reports", "/projects", "/audit", "/users"):
        assert client.get(path, headers=headers).status_code == 401, path
