"""OrderManager: order rules and the low-stock observer (US-ORD-01..05, SP7 §1)."""

from collections import Counter
from datetime import date

from sqlalchemy.orm import Session

from app.core.clock import Clock
from app.core.exceptions import ConflictError
from app.modules.ord.models import Order, OrderStatus
from app.modules.ord.ports import StockGateway
from app.modules.ord.repository import OrderRepository
from app.modules.usr.models import User
from app.shared.audit import AuditLog
from app.shared.events import DomainEvent, EventPublisher, EventType
from app.shared.formatting import human_datetime

MSG_OPEN_ORDER = "This item already has an open order."


class OrderManager:
    """Creates and tracks orders; implements ``StockObserver`` for low-stock events."""

    def __init__(self, orders: OrderRepository, stock: StockGateway, audit: AuditLog,
                 publisher: EventPublisher, clock: Clock) -> None:
        self.orders = orders
        self.stock = stock
        self.audit = audit
        self.publisher = publisher
        self.clock = clock

    @classmethod
    def for_session(cls, session: Session, stock: StockGateway, audit: AuditLog,
                    publisher: EventPublisher, clock: Clock) -> "OrderManager":
        """Build a manager on an already-built stock gateway (the AssetManager).

        Lets the Assets page attach this as a ``StockObserver`` without depending on ORD's
        repository or on its FastAPI providers.
        """
        return cls(OrderRepository(session), stock, audit, publisher, clock)

    def create_order(self, user: User, item_id: int, quantity: int, vendor: str = "") -> Order:
        """A staff-requested order. One open order per item (BR-ORD-01)."""
        item = self.stock.get_consumable(item_id)
        if self.has_open_order(item.id):
            raise ConflictError(MSG_OPEN_ORDER)
        return self._add_order(user, item.id, item.name, quantity, vendor, "manual")

    def on_low_stock(self, asset_id: int, available_quantity: int) -> Order | None:
        """StockObserver: flag a low item by adding it to an order (FR-ORD-01).

        Skipped when the item already has an open order. The quantity requested brings the
        stock back to twice its threshold (a team decision; SP2 does not fix an amount).
        """
        if self.has_open_order(asset_id):
            return None
        item = self.stock.get_consumable(asset_id)
        quantity = max(2 * item.reorder_threshold - available_quantity, 1)
        return self._add_order(None, item.id, item.name, quantity, "", "low_stock")

    def place_order(self, user: User, order_id: int) -> Order:
        """Requested -> Ordered."""
        order = self.find_order(order_id)
        old = self._state(order)
        order.mark_ordered(self.clock())
        self._save(user, "PLACE", order, old)
        return order

    def receive_order(self, user: User, order_id: int, quantity: int) -> Order:
        """Record a delivery and add it to stock exactly once (FR-ORD-03, US-ORD-03)."""
        order = self.find_order(order_id)
        old = self._state(order)
        order.receive(quantity, user.id, self.clock())
        new_quantity = self.stock.add_stock(order.item_id, quantity, user)
        self._save(user, "RECEIVE", order, old, {"quantity_on_hand": new_quantity})
        done = order.status == OrderStatus.ARRIVED
        self.publisher.publish(DomainEvent(
            EventType.ORDER_ARRIVED,
            f"Order #{order.id} for {order.item_name} "
            f"{'arrived' if done else 'partly arrived'}: {quantity} received, "
            f"{order.remaining_quantity} still expected.",
            actor_id=user.id, recipient_ids=(order.requested_by,) if order.requested_by else (),
            related_type="Order", related_id=order.id,
            details={
                "item_name": order.item_name, "order_no": f"#{order.id}",
                "qty_ordered": order.quantity_ordered, "qty_received": order.quantity_received,
                "received_at": human_datetime(self.clock()), "vendor": order.vendor or "Not set",
                "complete": done,
            }))
        return order

    def cancel_order(self, user: User, order_id: int) -> Order:
        """Requested / Ordered -> Cancelled. The order is kept (US-ORD-05)."""
        order = self.find_order(order_id)
        old = self._state(order)
        order.cancel()
        self._save(user, "CANCEL", order, old)
        return order

    def find_order(self, order_id: int) -> Order:
        """One order by its unique id."""
        return self.orders.get_or_raise(order_id)

    def search_orders(self, q: str | None = None, status: OrderStatus | None = None,
                      item_id: int | None = None, date_from: date | None = None,
                      date_to: date | None = None) -> list[Order]:
        """Search by id or item name and filter by status, item and date (US-ORD-04)."""
        return self.orders.search(q, status, item_id, date_from, date_to)

    def has_open_order(self, item_id: int) -> bool:
        """Whether the item has a Requested, Ordered or Partially Arrived order."""
        return self.orders.open_order_for_item(item_id) is not None

    def summary(self) -> tuple[int, dict[str, int]]:
        """Total orders and counts by status (FR-ORD-04)."""
        counts = Counter(o.status.value for o in self.orders.list())
        return sum(counts.values()), dict(counts)

    # ---- internals ----

    def _add_order(self, user: User | None, item_id: int, item_name: str, quantity: int,
                   vendor: str, source: str) -> Order:
        order = self.orders.add(Order(
            item_id=item_id, item_name=item_name, quantity_ordered=quantity, vendor=vendor.strip(),
            status=OrderStatus.REQUESTED, requested_by=user.id if user else None,
            requested_at=self.clock()))
        self.audit.record(user, "CREATE", "Order", order.id, None, {
            **self._state(order), "item_id": item_id, "quantity_ordered": quantity, "source": source})
        return order

    def _save(self, user: User, action: str, order: Order, old: dict,
              extra: dict | None = None) -> None:
        self.orders.flush()
        self.audit.record(user, action, "Order", order.id, old, {**self._state(order), **(extra or {})})

    @staticmethod
    def _state(order: Order) -> dict:
        return {"status": order.status.value, "quantity_received": order.quantity_received}
