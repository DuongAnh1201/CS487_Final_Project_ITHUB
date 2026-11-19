"""ORD: US-ORD-01..05, FR-ORD-01..06, BR-ORD-01, SP7 order states."""

from dataclasses import dataclass

import pytest

from app.core.exceptions import NotFoundError
from app.modules.ntf.models import Notification
from app.modules.ord.models import Order
from app.shared.audit import AuditRecord
from app.shared.events import EventType


@dataclass
class FakeConsumable:
    id: int
    name: str
    quantity_on_hand: int
    reorder_threshold: int


class FakeStock:
    """Stands in for AssetManager: get_consumable / add_stock."""

    def __init__(self) -> None:
        self.items = {1: FakeConsumable(1, "HDMI cable", 2, 5), 2: FakeConsumable(2, "Toner", 9, 3)}
        self.added: list[tuple[int, int, int]] = []

    def get_consumable(self, item_id: int) -> FakeConsumable:
        if item_id not in self.items:
            raise NotFoundError("Item not found.")
        return self.items[item_id]

    def add_stock(self, item_id: int, quantity: int, actor) -> int:
        self.items[item_id].quantity_on_hand += quantity
        self.added.append((item_id, quantity, actor.id))
        return self.items[item_id].quantity_on_hand


@pytest.fixture
def stock(app) -> FakeStock:
    fake = FakeStock()
    app.state.stock_gateway = fake
    return fake


def new_order(client, headers, item_id=1, quantity=10, vendor="Acme") -> dict:
    r = client.post("/orders", headers=headers, json={"item_id": item_id, "quantity": quantity, "vendor": vendor})
    assert r.status_code == 201, r.text
    return r.json()


def place(client, headers, order_id):
    return client.post(f"/orders/{order_id}/place", headers=headers)


def receive(client, headers, order_id, quantity):
    return client.post(f"/orders/{order_id}/receive", headers=headers, json={"quantity": quantity})


# ---- create / BR-ORD-01 ---------------------------------------------------------------

def test_create_order_starts_requested(client, sa_headers, stock):
    order = new_order(client, sa_headers)
    assert (order["status"], order["quantity_ordered"], order["remaining_quantity"], order["item_name"]) == (
        "REQUESTED", 10, 10, "HDMI cable")
    assert client.get(f"/orders/{order['id']}", headers=sa_headers).json()["id"] == order["id"]


def test_item_cannot_have_two_open_orders(client, sa_headers, stock):
    first = new_order(client, sa_headers)
    dup = client.post("/orders", headers=sa_headers, json={"item_id": 1, "quantity": 3})
    assert (dup.status_code, dup.json()["detail"]) == (409, "This item already has an open order.")
    client.post(f"/orders/{first['id']}/cancel", headers=sa_headers)
    assert client.post("/orders", headers=sa_headers, json={"item_id": 1, "quantity": 3}).status_code == 201


def test_order_validation(client, sa_headers, stock):
    assert client.post("/orders", headers=sa_headers, json={"item_id": 1, "quantity": 0}).status_code == 422
    assert client.post("/orders", headers=sa_headers, json={"item_id": 1, "quantity": -4}).status_code == 422
    missing = client.post("/orders", headers=sa_headers, json={"item_id": 99, "quantity": 1})
    assert (missing.status_code, missing.json()["detail"]) == (404, "Item not found.")
    assert client.get("/orders/99", headers=sa_headers).json()["detail"] == "Order not found."


def test_orders_require_login(client):
    assert client.get("/orders").status_code == 401


# ---- state transitions (SP7) -----------------------------------------------------------

def test_place_then_cancel_rules(client, sa_headers, stock):
    order = new_order(client, sa_headers)
    assert receive(client, sa_headers, order["id"], 1).json()["detail"] == "Order is Requested and cannot receive stock."
    assert place(client, sa_headers, order["id"]).json()["status"] == "ORDERED"
    again = place(client, sa_headers, order["id"])
    assert (again.status_code, again.json()["detail"]) == (409, "Order is Ordered and cannot be placed.")
    cancelled = client.post(f"/orders/{order['id']}/cancel", headers=sa_headers)
    assert cancelled.json()["status"] == "CANCELLED"
    assert client.post(f"/orders/{order['id']}/cancel", headers=sa_headers).status_code == 409
    assert client.get(f"/orders/{order['id']}", headers=sa_headers).status_code == 200  # never removed
    assert client.delete(f"/orders/{order['id']}", headers=sa_headers).status_code == 405


def test_partial_then_full_receive_adds_stock_exactly(client, sa_headers, stock):
    order = new_order(client, sa_headers, quantity=10)
    place(client, sa_headers, order["id"])
    part = receive(client, sa_headers, order["id"], 4).json()
    assert (part["status"], part["quantity_received"], part["remaining_quantity"]) == ("PARTIALLY_ARRIVED", 4, 6)
    assert stock.items[1].quantity_on_hand == 6
    assert client.post(f"/orders/{order['id']}/cancel", headers=sa_headers).status_code == 409
    done = receive(client, sa_headers, order["id"], 6).json()
    assert (done["status"], done["arrived_at"] is not None) == ("ARRIVED", True)
    assert stock.items[1].quantity_on_hand == 12
    assert sum(q for _, q, _ in stock.added) == 10


def test_receive_cannot_double_count(client, sa_headers, stock):
    order = new_order(client, sa_headers, quantity=5)
    place(client, sa_headers, order["id"])
    receive(client, sa_headers, order["id"], 5)
    again = receive(client, sa_headers, order["id"], 5)
    assert (again.status_code, again.json()["detail"]) == (409, "Order is Arrived and cannot receive stock.")
    assert stock.items[1].quantity_on_hand == 7  # added once


def test_receive_quantity_rules(client, sa_headers, stock):
    order = new_order(client, sa_headers, quantity=5)
    place(client, sa_headers, order["id"])
    assert receive(client, sa_headers, order["id"], 0).status_code == 422
    assert receive(client, sa_headers, order["id"], -2).status_code == 422
    over = receive(client, sa_headers, order["id"], 6)
    assert (over.status_code, over.json()["detail"]) == (
        422, "Quantity exceeds the 5 still expected on this order.")
    assert stock.added == []


# ---- notification + audit ------------------------------------------------------------------

def test_arrival_notifies_requester_and_audits(client, admin_headers, sa_headers, stock, db):
    order = new_order(client, sa_headers, quantity=3)
    place(client, admin_headers, order["id"])
    receive(client, admin_headers, order["id"], 3)
    notes = db.query(Notification).filter_by(event_type=EventType.ORDER_ARRIVED).all()
    sa_id = client.get("/auth/me", headers=sa_headers).json()["id"]
    assert [(n.recipient_id, n.related_type, n.related_id) for n in notes] == [(sa_id, "Order", order["id"])]
    actions = [a.action for a in db.query(AuditRecord).filter_by(entity_type="Order").order_by(AuditRecord.id)]
    assert actions == ["CREATE", "PLACE", "RECEIVE"]
    receive_audit = db.query(AuditRecord).filter_by(action="RECEIVE").one()
    assert receive_audit.old_value["status"] == "ORDERED" and receive_audit.new_value["status"] == "ARRIVED"
    assert receive_audit.new_value["quantity_on_hand"] == 5


def test_failed_stock_in_rolls_the_receive_back(client, sa_headers, stock, db):
    order = new_order(client, sa_headers, quantity=5)
    place(client, sa_headers, order["id"])
    stock.add_stock = lambda *a, **k: (_ for _ in ()).throw(NotFoundError("Item not found."))
    assert receive(client, sa_headers, order["id"], 2).status_code == 404
    db.expire_all()
    stored = db.get(Order, order["id"])
    assert (stored.status.value, stored.quantity_received) == ("ORDERED", 0)


# ---- low-stock observer (FR-ORD-01) --------------------------------------------------------

def test_low_stock_creates_one_requested_order(app, client, admin_headers, stock, db):
    from app.modules.ord.repository import OrderRepository
    from app.modules.ord.service import OrderManager
    from app.shared.audit import AuditLog
    from app.shared.events import EventPublisher

    manager = OrderManager(OrderRepository(db), stock, AuditLog(db, app.state.clock),
                           EventPublisher(db), app.state.clock)
    order = manager.on_low_stock(asset_id=1, available_quantity=2)  # threshold 5 -> order up to 10
    assert (order.status.value, order.quantity_ordered, order.requested_by) == ("REQUESTED", 8, None)
    assert manager.on_low_stock(asset_id=1, available_quantity=1) is None  # BR-ORD-01
    assert db.query(Order).count() == 1
    audit = db.query(AuditRecord).filter_by(entity_type="Order", action="CREATE").one()
    assert audit.actor_id is None and audit.new_value["source"] == "low_stock"
    db.rollback()


# ---- search / summary (US-ORD-02, US-ORD-04) ---------------------------------------------------

def test_search_filter_and_summary(client, sa_headers, stock):
    a = new_order(client, sa_headers, item_id=1)
    b = new_order(client, sa_headers, item_id=2, quantity=4)
    place(client, sa_headers, b["id"])
    ids = lambda qs: [o["id"] for o in client.get("/orders" + qs, headers=sa_headers).json()]
    assert ids("") == [a["id"], b["id"]]
    assert ids("?q=toner") == [b["id"]]
    assert ids(f"?q={a['id']}") == [a["id"]]
    assert ids("?status=ORDERED") == [b["id"]]
    assert ids("?q=toner&status=REQUESTED") == []
    assert ids("?date_from=2026-01-05&date_to=2026-01-05") == [a["id"], b["id"]]
    assert ids("?date_to=2026-01-04") == []
    summary = client.get("/orders/summary", headers=sa_headers).json()
    assert summary == {"total": 2, "by_status": {"REQUESTED": 1, "ORDERED": 1}}


def test_without_the_assets_page_wired_items_are_not_found(client, sa_headers):
    r = client.post("/orders", headers=sa_headers, json={"item_id": 1, "quantity": 1})
    assert (r.status_code, r.json()["detail"]) == (404, "Item not found.")


def test_for_session_builds_a_manager_on_an_existing_gateway(app, client, admin_headers, stock, db):
    """The Assets page attaches this as a StockObserver using its own AssetManager."""
    from app.modules.ord.service import OrderManager
    from app.shared.audit import AuditLog
    from app.shared.events import EventPublisher

    manager = OrderManager.for_session(db, stock, AuditLog(db, app.state.clock),
                                       EventPublisher(db), app.state.clock)
    assert manager.stock is stock
    assert manager.on_low_stock(asset_id=2, available_quantity=1).item_name == "Toner"
    db.rollback()
