"""Validated AST REST bodies (US-AST-01–11, SP4 §11.1)."""

from __future__ import annotations

import re
from datetime import date as Date
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from app.core.exceptions import ValidationRuleError
from app.modules.ast.models import (
    BorrowerType,
    IncidentType,
    ItemCondition,
    ItemStatus,
    LoanStatus,
    TransactionType,
)


class Input(BaseModel):
    """Reject unknown fields and use the SP4 format messages."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @model_validator(mode="before")
    @classmethod
    def validate_formats(cls, data: Any) -> Any:
        """Required fields and dates match SP4 §11.1."""
        if isinstance(data, dict):
            for name, field in cls.model_fields.items():
                value = data.get(name)
                if (field.is_required() and (name not in data or value is None)) or (
                    isinstance(value, str) and not value.strip() and field.is_required()
                ):
                    raise ValidationRuleError(
                        f"{name.replace('_', ' ').capitalize()} is required."
                    )
                if name.endswith("_date") or name == "date":
                    if value is not None and isinstance(value, str):
                        try:
                            if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
                                raise ValueError
                            Date.fromisoformat(value)
                        except ValueError:
                            raise ValidationRuleError(
                                "Enter a valid date (YYYY-MM-DD)."
                            )
        return data


class Read(BaseModel):
    """Responses are serialized explicitly from domain records."""

    model_config = ConfigDict(from_attributes=True)


class CategoryCreate(Input):
    """Category lookup creation."""

    name: str = Field(min_length=1, max_length=120)
    is_consumable: bool = False


class CategoryRead(Read, CategoryCreate):
    """Category lookup."""

    id: int


class LocationCreate(Input):
    """Location shared with CLS."""

    building: str = Field(min_length=1, max_length=120)
    room: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=1000)


class LocationRead(Read, LocationCreate):
    """Location lookup."""

    id: int


class ItemCreate(Input):
    """Register equipment as Available (FR-AST-01/02)."""

    asset_tag: str = Field(min_length=1, max_length=100)
    serial_number: str = Field(min_length=1, max_length=120)
    model: str = Field(min_length=1, max_length=120)
    manufacturer: str = Field(min_length=1, max_length=120)
    category_id: int = Field(gt=0)
    location_id: int = Field(gt=0)
    purchase_date: Date | None = None
    warranty_end_date: Date | None = None
    notes: str = Field(default="", max_length=4000)


class ItemUpdate(Input):
    """Descriptive edits only; status follows lifecycle operations (US-AST-02)."""

    asset_tag: str | None = Field(default=None, min_length=1, max_length=100)
    serial_number: str | None = Field(default=None, min_length=1, max_length=120)
    model: str | None = Field(default=None, min_length=1, max_length=120)
    manufacturer: str | None = Field(default=None, min_length=1, max_length=120)
    category_id: int | None = Field(default=None, gt=0)
    location_id: int | None = Field(default=None, gt=0)
    purchase_date: Date | None = None
    warranty_end_date: Date | None = None
    notes: str | None = Field(default=None, max_length=4000)


class ItemRead(Read, ItemCreate):
    """Equipment public record."""

    id: int
    serial_number: str
    manufacturer: str
    status: ItemStatus
    created_by: int
    updated_by: int
    created_at: datetime
    updated_at: datetime


class ConsumableCreate(Input):
    """Create supplies with zero opening stock; stock-in records additions."""

    name: str = Field(min_length=1, max_length=120)
    category_id: int = Field(gt=0)
    location_id: int = Field(gt=0)
    reorder_threshold: int = Field(default=0, ge=0, strict=True)
    unit: str = Field(default="each", min_length=1, max_length=50)


class ConsumableRead(ItemRead):
    """Consumable stock level."""

    id: int
    quantity_on_hand: int
    name: str
    reorder_threshold: int
    unit: str


class StockChange(Input):
    """Positive whole quantity (BR-11)."""

    quantity: int
    issued_to: str | None = Field(default=None, max_length=255)
    note: str = Field(default="", max_length=4000)

    @model_validator(mode="before")
    @classmethod
    def positive_whole(cls, data: Any) -> Any:
        """Do not coerce fractions, strings or booleans into quantities."""
        if isinstance(data, dict) and (
            type(data.get("quantity")) is not int or data["quantity"] <= 0
        ):
            raise ValidationRuleError("Quantity must be a positive whole number.")
        return data


class StockTransactionRead(Read):
    """Retained movement history."""

    id: int
    consumable_id: int
    type: TransactionType
    quantity: int
    issued_to: str | None
    performed_by: int
    timestamp: datetime
    note: str


class BorrowerCreate(Input):
    """Borrower identity; borrowers never authenticate."""

    school_id: str = Field(min_length=1, max_length=50)
    full_name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    type: BorrowerType
    department: str = Field(default="", max_length=120)


class BorrowerRead(Read, BorrowerCreate):
    """Borrower identity."""

    id: int


class LoanCreate(Input):
    """Checkout request (US-AST-05)."""

    item_id: int = Field(gt=0)
    borrower_id: int = Field(gt=0)
    checkout_date: Date | None = None
    due_date: Date | None = None
    condition_out: ItemCondition
    notes: str = Field(default="", max_length=4000)


class LoanReturn(Input):
    """Return request (US-AST-06)."""

    return_date: Date | None = None
    condition_in: ItemCondition
    notes: str = Field(default="", max_length=4000)


class LoanExtend(Input):
    """One extension of at most seven days (BR-08)."""

    due_date: Date


class LoanRead(Read):
    """Current or historical loan."""

    id: int
    item_id: int
    borrower_id: int
    checkout_date: Date
    due_date: Date
    condition_out: ItemCondition
    checked_out_by: int
    return_date: Date | None
    condition_in: ItemCondition | None
    received_by: int | None
    extended: bool
    extended_by: int | None
    status: LoanStatus
    notes: str


class OverdueRead(Read):
    """Overdue row includes borrower contact and equipment (US-AST-08)."""

    loan: LoanRead
    borrower: BorrowerRead
    item: ItemRead
    days_overdue: int


class IncidentCreate(Input):
    """Lost or damaged incident (US-AST-10)."""

    type: IncidentType
    description: str = Field(min_length=1, max_length=4000)
    date: Date | None = None


class RetireRequest(Input):
    """Admin retirement reason (US-AST-11)."""

    reason: str = Field(min_length=1, max_length=4000)
    date: Date | None = None


class IncidentRead(Read):
    """Retained lifecycle incident."""

    id: int
    item_id: int
    type: IncidentType
    description: str
    date: Date
    reported_by: int
    timestamp: datetime
