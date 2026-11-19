"""ORD entity: Order and its status transitions (SP7 §1)."""

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.exceptions import ConflictError, ValidationRuleError

MSG_QUANTITY = "Quantity must be a positive whole number."


class OrderStatus(str, enum.Enum):
    """Order life cycle: Requested -> Ordered -> (Partially) Arrived, or Cancelled."""

    REQUESTED = "REQUESTED"
    ORDERED = "ORDERED"
    PARTIALLY_ARRIVED = "PARTIALLY_ARRIVED"
    ARRIVED = "ARRIVED"
    CANCELLED = "CANCELLED"


OPEN_STATUSES = (OrderStatus.REQUESTED, OrderStatus.ORDERED, OrderStatus.PARTIALLY_ARRIVED)


class Order(Base):
    """An order for one consumable. Orders are never deleted (US-ORD-05)."""

    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(Integer, index=True)
    item_name: Mapped[str] = mapped_column(String(200), index=True)  # snapshot, for search
    quantity_ordered: Mapped[int] = mapped_column(Integer)
    quantity_received: Mapped[int] = mapped_column(Integer, default=0)
    vendor: Mapped[str] = mapped_column(String(150), default="")
    status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus), default=OrderStatus.REQUESTED)
    requested_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)  # None = system
    received_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    requested_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    ordered_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    arrived_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    def is_open(self) -> bool:
        """Requested, Ordered or Partially Arrived."""
        return self.status in OPEN_STATUSES

    @property
    def remaining_quantity(self) -> int:
        """Quantity still to arrive."""
        return self.quantity_ordered - self.quantity_received

    def mark_ordered(self, now: datetime) -> None:
        """Requested -> Ordered."""
        if self.status != OrderStatus.REQUESTED:
            raise ConflictError(f"Order is {self._label()} and cannot be placed.")
        self.status = OrderStatus.ORDERED
        self.ordered_at = now

    def receive(self, quantity: int, user_id: int, now: datetime) -> None:
        """Ordered / Partially Arrived -> Partially Arrived or Arrived."""
        if self.status not in (OrderStatus.ORDERED, OrderStatus.PARTIALLY_ARRIVED):
            raise ConflictError(f"Order is {self._label()} and cannot receive stock.")
        if not isinstance(quantity, int) or quantity <= 0:
            raise ValidationRuleError(MSG_QUANTITY)
        if quantity > self.remaining_quantity:
            raise ValidationRuleError(
                f"Quantity exceeds the {self.remaining_quantity} still expected on this order.")
        self.quantity_received += quantity
        self.received_by = user_id
        self.status = (OrderStatus.ARRIVED if self.remaining_quantity == 0
                       else OrderStatus.PARTIALLY_ARRIVED)
        self.arrived_at = now

    def cancel(self) -> None:
        """Requested / Ordered -> Cancelled."""
        if self.status not in (OrderStatus.REQUESTED, OrderStatus.ORDERED):
            raise ConflictError(f"Order is {self._label()} and cannot be cancelled.")
        self.status = OrderStatus.CANCELLED

    def _label(self) -> str:
        return self.status.value.replace("_", " ").title()
