"""AST acceptance and atomicity tests: merged US-AST-01–11, BR-01–11/18."""

from datetime import datetime, timedelta
from unittest.mock import Mock

import pytest
from sqlalchemy import func, select

from app.core.deps import get_audit_log
from app.core.exceptions import ValidationRuleError
from app.modules.ast.models import Item, Loan, StockTransaction
from app.modules.ast.monitor import StockMonitor
from app.modules.ast.repository import ObserverRepository
from app.modules.ast.router import get_retirement_observers, get_stock_monitor
from app.shared.audit import AuditRecord


@pytest.fixture
def inventory(client, admin_headers):
    """Existing category/location precondition for US-AST-01."""
    category = client.post(
        "/ast/categories", headers=admin_headers, json={"name": "Laptop"}
    ).json()["id"]
    supply = client.post(
        "/ast/categories",
        headers=admin_headers,
        json={"name": "Supply", "is_consumable": True},
    ).json()["id"]
    location = client.post(
        "/ast/locations", headers=admin_headers, json={"building": "A", "room": "101"}
    ).json()["id"]
    return {"category_id": category, "location_id": location, "supply": supply}


@pytest.fixture
def item_factory(client, sa_headers, inventory):
    """Register equipment through REST."""

    def create(tag="TAG-1", **changes):
        data = dict(
            asset_tag=tag,
            serial_number="SN-" + tag,
            model="ThinkPad",
            manufacturer="Lenovo",
            category_id=inventory["category_id"],
            location_id=inventory["location_id"],
        )
        data.update(changes)
        response = client.post("/ast/items", headers=sa_headers, json=data)
        assert response.status_code == 201, response.text
        return response.json()

    return create


@pytest.fixture
def borrower_factory(client, sa_headers):
    """Create borrowers without login accounts."""

    def create(kind="STUDENT", school_id="B1"):
        response = client.post(
            "/ast/borrowers",
            headers=sa_headers,
            json={
                "school_id": school_id,
                "full_name": "Alex Borrower",
                "email": "alex@sfbu.edu",
                "type": kind,
            },
        )
        assert response.status_code == 201, response.text
        return response.json()

    return create


@pytest.fixture
def lend(client, sa_headers):
    """Checkout helper retaining the response for rejection assertions."""
    return lambda item, borrower, **changes: client.post(
        "/ast/loans",
        headers=sa_headers,
        json=dict(
            item_id=item["id"],
            borrower_id=borrower["id"],
            condition_out="Good",
            **changes,
        ),
    )


@pytest.fixture
def supply(client, sa_headers, inventory):
    """A zero-stock supply, threshold two."""
    response = client.post(
        "/ast/consumables",
        headers=sa_headers,
        json={
            "name": "Cable",
            "category_id": inventory["supply"],
            "location_id": inventory["location_id"],
            "reorder_threshold": 2,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_register_edit_search_audit(client, sa_headers, item_factory, inventory, db):
    """US-AST-01/02/03, BR-03: status, AND filters, old/new values."""
    item = item_factory()
    assert item["status"] == "Available"
    changed = client.patch(
        f"/ast/items/{item['id']}", headers=sa_headers, json={"model": "T14"}
    ).json()
    assert changed["model"] == "T14"
    query = client.get(
        "/ast/items",
        headers=sa_headers,
        params={"model": "T14", "category_id": inventory["category_id"]},
    )
    assert [x["id"] for x in query.json()] == [item["id"]]
    # Text filters ignore case on SQLite and PostgreSQL alike (#100).
    lower = client.get("/ast/items", headers=sa_headers, params={"model": "t14", "asset_tag": "tag-1"})
    assert [x["id"] for x in lower.json()] == [item["id"]]
    assert (
        client.get(
            "/ast/items",
            headers=sa_headers,
            params={"model": "T14", "asset_tag": "missing"},
        ).json()
        == []
    )
    assert (
        client.get("/ast/items", headers=sa_headers, params={"asset_tag": "%"}).json()
        == []
    )
    audit = db.scalar(
        select(AuditRecord).where(
            AuditRecord.entity_type == "Item", AuditRecord.action == "update"
        )
    )
    assert audit.old_value["model"] == "ThinkPad"
    assert audit.new_value["model"] == "T14"
    assert audit.actor_id == changed["updated_by"]


def test_retire_permissions_history_and_tag_reuse(
    client, sa_headers, admin_headers, item_factory, borrower_factory, lend
):
    """US-AST-11, BR-01/02/05/07: retained history and immutable retired record."""
    item, borrower = item_factory(), borrower_factory()
    loan = lend(item, borrower).json()
    assert (
        client.post(
            f"/ast/items/{item['id']}/return",
            headers=sa_headers,
            json={"condition_in": "Good"},
        ).status_code
        == 200
    )
    url = f"/ast/items/{item['id']}/retire"
    assert (
        client.post(url, headers=sa_headers, json={"reason": "EOL"}).json()["detail"]
        == "Access denied."
    )
    assert (
        client.post(url, headers=admin_headers, json={"reason": "EOL"}).status_code
        == 201
    )
    assert (
        client.patch(
            f"/ast/items/{item['id']}", headers=sa_headers, json={"notes": "x"}
        ).json()["detail"]
        == "Retired items are read-only."
    )
    assert lend(item, borrower).json()["detail"] == "Retired items are read-only."
    assert (
        client.post(
            f"/ast/items/{item['id']}/incidents",
            headers=sa_headers,
            json={"type": "Lost", "description": "x"},
        ).status_code
        == 409
    )
    assert (
        client.post(
            "/ast/items",
            headers=sa_headers,
            json={
                k: v
                for k, v in item.items()
                if k
                in {
                    "asset_tag",
                    "serial_number",
                    "model",
                    "manufacturer",
                    "category_id",
                    "location_id",
                }
            },
        ).json()["detail"]
        == "Asset tag already exists."
    )
    assert (
        client.get(
            "/ast/loans", headers=sa_headers, params={"item_id": item["id"]}
        ).json()[0]["id"]
        == loan["id"]
    )


@pytest.mark.parametrize("kind,days", [("STUDENT", 7), ("FACULTY", 30), ("STAFF", 30)])
def test_default_loan_lengths(kind, days, item_factory, borrower_factory, lend, clock):
    """BR-08: borrower-specific due dates and actor attribution."""
    loan = lend(item_factory(), borrower_factory(kind)).json()
    assert loan["due_date"] == (clock().date() + timedelta(days=days)).isoformat()
    assert loan["checked_out_by"] > 0


@pytest.mark.parametrize(
    "kind,offset", [("STUDENT", 0), ("STUDENT", 8), ("FACULTY", 31), ("STAFF", -1)]
)
def test_invalid_due_date(
    kind, offset, item_factory, borrower_factory, lend, clock, db
):
    """BR-08: no loan/status mutation for an invalid date."""
    item = item_factory()
    response = lend(
        item,
        borrower_factory(kind),
        due_date=(clock().date() + timedelta(days=offset)).isoformat(),
    )
    assert response.status_code == 422
    maximum = 7 if kind == "STUDENT" else 30
    assert (
        response.json()["detail"]
        == f"Due date must be within {maximum} days of checkout."
    )
    assert db.get(Item, item["id"]).status.value == "Available"
    assert db.scalar(select(func.count()).select_from(Loan)) == 0


def test_student_limit_and_double_lending(item_factory, borrower_factory, lend):
    """BR-07/09: one checkout per item, two per student."""
    borrower = borrower_factory()
    one, two, three = item_factory("1"), item_factory("2"), item_factory("3")
    assert lend(one, borrower).status_code == 201
    assert lend(one, borrower).json()["detail"] == "Item is On Loan and cannot be lent."
    assert lend(two, borrower).status_code == 201
    assert lend(three, borrower).json()["detail"] == "Borrowing limit reached."


def test_overdue_today_history_and_block(
    client, sa_headers, item_factory, borrower_factory, lend, clock
):
    """US-AST-08/09, BR-09: due today excluded; returned loan excluded."""
    borrower = borrower_factory()
    item = item_factory("LATE")
    assert (
        lend(
            item,
            borrower,
            checkout_date=(clock().date() - timedelta(days=7)).isoformat(),
            due_date=clock().date().isoformat(),
        ).status_code
        == 201
    )
    assert client.get("/ast/overdue", headers=sa_headers).json() == []
    clock.advance(days=1)
    # Refresh the idle session rather than relying on an expired bearer token.
    from tests.conftest import SA_EMAIL, SA_PASSWORD

    token = client.post(
        "/auth/login", json={"email": SA_EMAIL, "password": SA_PASSWORD}
    ).json()["access_token"]
    headers = {"Authorization": "Bearer " + token}
    overdue = client.get("/ast/overdue", headers=headers).json()
    assert overdue[0]["days_overdue"] == 1
    assert overdue[0]["borrower"]["email"] == "alex@sfbu.edu"
    # Existing helpers use the stale headers; direct calls use the refreshed session.
    other = client.post(
        "/ast/items",
        headers=headers,
        json={
            **{
                k: v
                for k, v in item.items()
                if k
                in {
                    "serial_number",
                    "model",
                    "manufacturer",
                    "category_id",
                    "location_id",
                }
            },
            "asset_tag": "NEW",
        },
    ).json()
    blocked = client.post(
        "/ast/loans",
        headers=headers,
        json={
            "item_id": other["id"],
            "borrower_id": borrower["id"],
            "condition_out": "Good",
        },
    )
    assert blocked.json()["detail"] == "Borrower has an overdue item: LATE."
    assert (
        client.post(
            f"/ast/items/{item['id']}/return",
            headers=headers,
            json={"condition_in": "Good"},
        ).status_code
        == 200
    )
    assert client.get("/ast/overdue", headers=headers).json() == []
    assert (
        len(
            client.get(
                "/ast/loans", headers=headers, params={"borrower_id": borrower["id"]}
            ).json()
        )
        == 1
    )


@pytest.mark.parametrize(
    "condition,status",
    [
        ("Good", "Available"),
        ("Fair", "Available"),
        ("Poor", "Damaged"),
        ("Damaged", "Damaged"),
    ],
)
def test_return_conditions(
    condition, status, client, sa_headers, item_factory, borrower_factory, lend
):
    """BR-10: damaged/poor return never marks equipment Available."""
    item = item_factory()
    assert lend(item, borrower_factory()).status_code == 201
    response = client.post(
        f"/ast/items/{item['id']}/return",
        headers=sa_headers,
        json={"condition_in": condition},
    )
    assert response.json()["status"] == "RETURNED"
    assert response.json()["received_by"] > 0
    assert (
        client.get(f"/ast/items/{item['id']}", headers=sa_headers).json()["status"]
        == status
    )
    assert (
        client.post(
            f"/ast/items/{item['id']}/return",
            headers=sa_headers,
            json={"condition_in": condition},
        ).json()["detail"]
        == "No open loan for this item."
    )


def test_return_date_and_extension(
    client, sa_headers, item_factory, borrower_factory, lend, clock
):
    """US-AST-06/07: return chronology; one extension, up to seven days."""
    item = item_factory()
    loan = lend(item, borrower_factory()).json()
    assert (
        client.post(
            f"/ast/items/{item['id']}/return",
            headers=sa_headers,
            json={
                "condition_in": "Good",
                "return_date": (clock().date() - timedelta(days=1)).isoformat(),
            },
        ).json()["detail"]
        == "Return date cannot be earlier than the checkout date."
    )
    url = f"/ast/loans/{loan['id']}/extend"
    assert (
        client.post(
            url,
            headers=sa_headers,
            json={"due_date": (clock().date() + timedelta(days=15)).isoformat()},
        ).status_code
        == 422
    )
    assert (
        client.post(
            url,
            headers=sa_headers,
            json={"due_date": (clock().date() + timedelta(days=14)).isoformat()},
        ).json()["extended"]
        is True
    )
    assert (
        client.post(
            url,
            headers=sa_headers,
            json={"due_date": (clock().date() + timedelta(days=15)).isoformat()},
        ).json()["detail"]
        == "This loan has already been extended."
    )


@pytest.mark.parametrize("kind", ["Lost", "Damaged"])
def test_incident_and_lending_rejection(
    kind, client, sa_headers, item_factory, borrower_factory, lend
):
    """US-AST-10: incident changes status, retains reason, and blocks lending."""
    item = item_factory()
    url = f"/ast/items/{item['id']}/incidents"
    assert (
        client.post(
            url, headers=sa_headers, json={"type": kind, "description": "   "}
        ).json()["detail"]
        == "Description is required."
    )
    assert (
        client.post(
            url, headers=sa_headers, json={"type": kind, "description": "Found broken"}
        ).json()["description"]
        == "Found broken"
    )
    assert (
        lend(item, borrower_factory()).json()["detail"]
        == f"Item is {kind} and cannot be lent."
    )


@pytest.mark.parametrize("quantity", [0, -1, 1.5, "2", True])
def test_stock_quantity_validation(quantity, client, sa_headers, supply):
    """BR-11: strictly positive whole movements, exact SP4 message."""
    response = client.post(
        f"/ast/consumables/{supply['id']}/stock-in",
        headers=sa_headers,
        json={"quantity": quantity},
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "Quantity must be a positive whole number."


def test_stock_boundaries_history_and_notification(client, sa_headers, supply, db):
    """US-AST-04, BR-11: nonnegative stock and every movement attributed."""
    url = f"/ast/consumables/{supply['id']}"
    assert (
        client.post(url + "/stock-in", headers=sa_headers, json={"quantity": 4}).json()[
            "quantity_on_hand"
        ]
        == 4
    )
    assert (
        client.post(
            url + "/stock-out",
            headers=sa_headers,
            json={"quantity": 5, "issued_to": "IT"},
        ).json()["detail"]
        == "Not enough stock."
    )
    assert (
        client.post(
            url + "/stock-out",
            headers=sa_headers,
            json={"quantity": 4, "issued_to": "IT"},
        ).json()["quantity_on_hand"]
        == 0
    )
    movements = client.get(url + "/transactions", headers=sa_headers).json()
    assert [x["quantity"] for x in movements] == [4, 4]
    assert movements[1]["issued_to"] == "IT"
    assert all(x["performed_by"] > 0 for x in movements)
    from app.modules.ntf.models import Notification

    assert db.scalar(select(func.count()).select_from(Notification)) >= 1


def test_consumable_not_lent(
    client, sa_headers, item_factory, borrower_factory, lend, inventory
):
    """BR-11: even a tagged consumable category cannot be checked out."""
    item = item_factory(category_id=inventory["supply"])
    assert (
        lend(item, borrower_factory()).json()["detail"]
        == "Consumables are issued, not lent."
    )


def test_audit_failure_rolls_back_checkout(
    app, client, sa_headers, item_factory, borrower_factory, lend, db
):
    """BR-03, SP4 §9.1: item/loan/borrower/audit share one transaction."""
    item, borrower = item_factory(), borrower_factory()

    class FailingAudit:
        def record(self, *args, **kwargs):
            raise ValidationRuleError("Could not save. Please try again.")

    app.dependency_overrides[get_audit_log] = lambda: FailingAudit()
    try:
        assert lend(item, borrower).status_code == 422
    finally:
        app.dependency_overrides.clear()
    db.expire_all()
    assert db.get(Item, item["id"]).status.value == "Available"
    assert db.scalar(select(func.count()).select_from(Loan)) == 0


def test_monitor_attach_detach_threshold_and_failure_isolation(db):
    """FR-AST-14: one observer failure does not undo another observer."""
    subject = StockMonitor(ObserverRepository(db))
    bad = Mock()
    bad.on_low_stock.side_effect = RuntimeError("offline")
    good = Mock()
    subject.attach(bad)
    subject.attach(good)
    subject.attach(good)
    subject.check_stock(12, 3, 2)
    good.on_low_stock.assert_not_called()
    subject.check_stock(12, 2, 2)
    good.on_low_stock.assert_called_once_with(12, 2)
    subject.detach(good)
    subject.check_stock(12, 0, 2)
    good.on_low_stock.assert_called_once()


def test_failing_stock_observer_keeps_change(app, db, client, sa_headers, supply):
    """Observer savepoint removes failing writes; stock/audit still commit."""
    # Use the request DB for realistic savepoint behavior.
    from fastapi import Depends

    from app.core.database import get_db

    def monitor_override(session=Depends(get_db)):
        monitor = StockMonitor(ObserverRepository(session))

        class Failing:
            def on_low_stock(self, asset_id, available_quantity):
                session.add(
                    AuditRecord(
                        timestamp=datetime(2026, 1, 1),
                        actor_id=None,
                        action="bad",
                        entity_type="bad",
                        entity_id="bad",
                    )
                )
                session.flush()
                raise RuntimeError("observer failed")

        monitor.attach(Failing())
        return monitor

    app.dependency_overrides[get_stock_monitor] = monitor_override
    try:
        response = client.post(
            f"/ast/consumables/{supply['id']}/stock-in",
            headers=sa_headers,
            json={"quantity": 1},
        )
        assert response.json()["quantity_on_hand"] == 1
    finally:
        app.dependency_overrides.clear()
    assert db.scalar(select(func.count()).select_from(StockTransaction)) == 1
    assert (
        db.scalar(
            select(func.count())
            .select_from(AuditRecord)
            .where(AuditRecord.action == "bad")
        )
        == 0
    )


def test_retirement_callback_atomicity(
    app, client, admin_headers, sa_headers, item_factory
):
    """BR-18: CLS hook runs and a failed removal rolls retirement back."""
    item = item_factory()
    observer = Mock()
    observer.on_item_retired.side_effect = ValidationRuleError("CLS unavailable")
    app.dependency_overrides[get_retirement_observers] = lambda: (observer,)
    try:
        assert (
            client.post(
                f"/ast/items/{item['id']}/retire",
                headers=admin_headers,
                json={"reason": "EOL"},
            ).status_code
            == 422
        )
    finally:
        app.dependency_overrides.clear()
    observer.on_item_retired.assert_called_once_with(item["id"])
    assert (
        client.get(f"/ast/items/{item['id']}", headers=sa_headers).json()["status"]
        == "Available"
    )


def test_format_warranty_duplicates_and_not_found(
    client, sa_headers, item_factory, inventory
):
    """FR-AST-01/02: exact validation messages and no bypass via status edit."""
    item = item_factory()
    other = item_factory("OTHER")
    assert (
        client.patch(
            f"/ast/items/{other['id']}",
            headers=sa_headers,
            json={"asset_tag": item["asset_tag"]},
        ).json()["detail"]
        == "Asset tag already exists."
    )
    assert (
        client.patch(
            f"/ast/items/{item['id']}",
            headers=sa_headers,
            json={"purchase_date": "2026-01-02", "warranty_end_date": "2026-01-01"},
        ).json()["detail"]
        == "Warranty end date cannot be earlier than the purchase date."
    )
    assert (
        client.patch(
            f"/ast/items/{item['id']}",
            headers=sa_headers,
            json={"purchase_date": "bad"},
        ).json()["detail"]
        == "Enter a valid date (YYYY-MM-DD)."
    )
    assert (
        client.patch(
            f"/ast/items/{item['id']}", headers=sa_headers, json={"status": "Available"}
        ).status_code
        == 422
    )
    assert (
        client.get("/ast/items/99999", headers=sa_headers).json()["detail"]
        == "Item not found."
    )
    assert client.get("/ast/items").status_code == 401


def test_consumable_inherits_item_and_retirement_blocks_stock(
    client, sa_headers, admin_headers, supply, borrower_factory, lend
):
    """SP5 inheritance, BR-07/11: supplies share item identity and immutable retirement."""
    assert (
        client.get(f"/ast/items/{supply['id']}", headers=sa_headers).json()["id"]
        == supply["id"]
    )
    assert (
        lend(supply, borrower_factory()).json()["detail"]
        == "Consumables are issued, not lent."
    )
    assert (
        client.get(
            "/ast/items", headers=sa_headers, params={"asset_tag": supply["asset_tag"]}
        ).json()[0]["id"]
        == supply["id"]
    )
    assert (
        client.post(
            f"/ast/items/{supply['id']}/retire",
            headers=admin_headers,
            json={"reason": "Discontinued"},
        ).status_code
        == 201
    )
    assert (
        client.post(
            f"/ast/consumables/{supply['id']}/stock-in",
            headers=sa_headers,
            json={"quantity": 1},
        ).json()["detail"]
        == "Retired items are read-only."
    )


@pytest.mark.parametrize("date_value", ["20260105", "2026-02-30", "not-a-date"])
def test_invalid_date_message(date_value, client, sa_headers, item_factory):
    """SP4 §11.1: malformed/impossible dates use the exact format message."""
    item = item_factory()
    response = client.patch(
        f"/ast/items/{item['id']}",
        headers=sa_headers,
        json={"purchase_date": date_value},
    )
    assert response.json()["detail"] == "Enter a valid date (YYYY-MM-DD)."


def test_status_cannot_be_edited(client, sa_headers, item_factory):
    """US-AST-02: lifecycle status cannot bypass lending and incident managers."""
    item = item_factory()
    assert (
        client.patch(
            f"/ast/items/{item['id']}", headers=sa_headers, json={"status": "On Loan"}
        ).status_code
        == 422
    )
    assert (
        client.patch(
            f"/ast/items/{item['id']}", headers=sa_headers, json={"manufacturer": None}
        ).json()["detail"]
        == "Manufacturer is required."
    )
    assert (
        client.get("/ast/items/99999", headers=sa_headers).json()["detail"]
        == "Item not found."
    )


class FakeLendingGuard:
    """AST test policy emulating installed equipment without importing CLS."""

    def __init__(self, blocked: bool = False) -> None:
        self.blocked = blocked
        self.checked: list[int] = []

    def check_can_lend(self, item_id: int) -> None:
        """DD-CLS-01: reject installed equipment with the specified conflict."""
        from app.core.exceptions import ConflictError

        self.checked.append(item_id)
        if self.blocked:
            raise ConflictError("Item is installed in a classroom and cannot be lent.")


@pytest.mark.parametrize("blocked", [False, True])
def test_lending_guard_policy(blocked, app, item_factory, borrower_factory, lend, db):
    """DD-CLS-01, US-AST-05, BR-03: guard failure cannot create checkout state."""
    from app.modules.ast.router import get_lending_guards

    item, borrower = item_factory(), borrower_factory()
    guard = FakeLendingGuard(blocked)
    audit_count = db.scalar(select(func.count()).select_from(AuditRecord))
    app.dependency_overrides[get_lending_guards] = lambda: (guard,)
    try:
        response = lend(item, borrower)
    finally:
        del app.dependency_overrides[get_lending_guards]
    assert guard.checked == [item["id"]]
    db.expire_all()
    if blocked:
        assert response.status_code == 409
        assert (
            response.json()["detail"]
            == "Item is installed in a classroom and cannot be lent."
        )
        assert db.get(Item, item["id"]).status.value == "Available"
        assert db.scalar(select(func.count()).select_from(Loan)) == 0
        assert db.scalar(select(func.count()).select_from(AuditRecord)) == audit_count
    else:
        assert response.status_code == 201
        assert db.get(Item, item["id"]).status.value == "On Loan"
        assert db.scalar(select(func.count()).select_from(Loan)) == 1


def test_lending_guards_run_in_order_until_rejection(
    app, item_factory, borrower_factory, lend
):
    """DD-CLS-01, US-AST-05: all configured policies must allow checkout."""
    from app.modules.ast.router import get_lending_guards

    item, borrower = item_factory(), borrower_factory()
    allowed, denied, later = (
        FakeLendingGuard(),
        FakeLendingGuard(True),
        FakeLendingGuard(),
    )
    app.dependency_overrides[get_lending_guards] = lambda: (allowed, denied, later)
    try:
        assert lend(item, borrower).status_code == 409
    finally:
        del app.dependency_overrides[get_lending_guards]
    assert allowed.checked == denied.checked == [item["id"]]
    assert later.checked == []
    # The default is optional: removing the guard leaves ordinary AST checkout working.
    assert lend(item, borrower).status_code == 201
