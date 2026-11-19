"""ORD storage."""

from datetime import date, datetime, time, timedelta

from sqlalchemy import or_, select

from app.modules.ord.models import OPEN_STATUSES, Order, OrderStatus
from app.shared.repository import BaseRepository


class OrderRepository(BaseRepository[Order]):
    """Order queries."""

    model = Order
    not_found_message = "Order not found."

    def open_order_for_item(self, item_id: int) -> Order | None:
        """The item's open order, if any (BR-ORD-01)."""
        return self.session.scalar(select(Order).where(
            Order.item_id == item_id, Order.status.in_(OPEN_STATUSES)))

    def search(self, q: str | None = None, status: OrderStatus | None = None,
               item_id: int | None = None, date_from: date | None = None,
               date_to: date | None = None) -> list[Order]:
        """Orders matching an id or item name and every filter (FR-ORD-05)."""
        stmt = select(Order).order_by(Order.id)
        if q:
            text = q.strip()
            conditions = [Order.item_name.ilike(f"%{text}%")]
            if text.isdigit():
                conditions.append(Order.id == int(text))
            stmt = stmt.where(or_(*conditions))
        if status is not None:
            stmt = stmt.where(Order.status == status)
        if item_id is not None:
            stmt = stmt.where(Order.item_id == item_id)
        if date_from is not None:
            stmt = stmt.where(Order.requested_at >= datetime.combine(date_from, time.min))
        if date_to is not None:
            stmt = stmt.where(Order.requested_at < datetime.combine(date_to + timedelta(days=1), time.min))
        return list(self.session.scalars(stmt))

    def for_month(self, month: int, year: int) -> list[Order]:
        """Orders requested in the month."""
        start = datetime(year, month, 1)
        end = datetime(year + (month == 12), month % 12 + 1, 1)
        return list(self.session.scalars(
            select(Order).where(Order.requested_at >= start, Order.requested_at < end)))
