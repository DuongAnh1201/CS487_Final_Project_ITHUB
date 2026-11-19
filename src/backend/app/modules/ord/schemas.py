"""ORD request and response models."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.modules.ord.models import OrderStatus


class OrderCreate(BaseModel):
    """New order for a consumable (US-ORD-01 manual path)."""

    item_id: int
    quantity: int = Field(gt=0, description="Quantity must be a positive whole number.")
    vendor: str = Field(default="", max_length=150)


class ReceiveRequest(BaseModel):
    """Quantity that arrived (UC-ORD-03)."""

    quantity: int = Field(gt=0, description="Quantity must be a positive whole number.")


class OrderRead(BaseModel):
    """An order."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    item_id: int
    item_name: str
    quantity_ordered: int
    quantity_received: int
    remaining_quantity: int
    vendor: str
    status: OrderStatus
    requested_by: int | None
    received_by: int | None
    requested_at: datetime
    ordered_at: datetime | None
    arrived_at: datetime | None


class OrderSummary(BaseModel):
    """Counts of orders by status (FR-ORD-04)."""

    total: int
    by_status: dict[str, int]

