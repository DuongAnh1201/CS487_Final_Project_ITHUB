"""AST persistent records (FR-AST-01–12, BR-01/02/07–11)."""

from datetime import date, datetime
from enum import Enum as PyEnum

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ItemStatus(str, PyEnum):
    """Equipment lifecycle states (BR-07)."""

    AVAILABLE = "Available"
    ON_LOAN = "On Loan"
    LOST = "Lost"
    DAMAGED = "Damaged"
    RETIRED = "Retired"


class BorrowerType(str, PyEnum):
    """Borrower policy categories (BR-08/09)."""

    STUDENT = "STUDENT"
    FACULTY = "FACULTY"
    STAFF = "STAFF"


class ItemCondition(str, PyEnum):
    """Checkout and return conditions (BR-10)."""

    GOOD = "Good"
    FAIR = "Fair"
    POOR = "Poor"
    DAMAGED = "Damaged"


class LoanStatus(str, PyEnum):
    """Historical loan states; loans are never deleted."""

    OPEN = "OPEN"
    RETURNED = "RETURNED"
    LOST = "LOST"


class TransactionType(str, PyEnum):
    """Consumables are issued or restocked (BR-11)."""

    IN = "IN"
    OUT = "OUT"


class IncidentType(str, PyEnum):
    """Recorded lifecycle changes."""

    LOST = "Lost"
    DAMAGED = "Damaged"
    RETIRED = "Retired"


class Category(Base):
    """Inventory category and consumable flag."""

    __tablename__ = "ast_categories"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    is_consumable: Mapped[bool] = mapped_column(Boolean, default=False)


class Location(Base):
    """Shared building/room lookup for CLS."""

    __tablename__ = "ast_locations"
    id: Mapped[int] = mapped_column(primary_key=True)
    building: Mapped[str] = mapped_column(String(120))
    room: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(String(1000), default="")


class Item(Base):
    """Individually tagged equipment; tags are never reused (BR-01)."""

    __tablename__ = "ast_items"
    kind: Mapped[str] = mapped_column(String(30), default="item")
    __mapper_args__ = {"polymorphic_on": kind, "polymorphic_identity": "item"}
    id: Mapped[int] = mapped_column(primary_key=True)
    asset_tag: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    serial_number: Mapped[str] = mapped_column(String(120), index=True)
    model: Mapped[str] = mapped_column(String(120), index=True)
    manufacturer: Mapped[str] = mapped_column(String(120))
    category_id: Mapped[int] = mapped_column(
        ForeignKey("ast_categories.id"), index=True
    )
    location_id: Mapped[int] = mapped_column(ForeignKey("ast_locations.id"), index=True)
    status: Mapped[ItemStatus] = mapped_column(Enum(ItemStatus), index=True)
    purchase_date: Mapped[date | None] = mapped_column(Date)
    warranty_end_date: Mapped[date | None] = mapped_column(Date)
    notes: Mapped[str] = mapped_column(String(4000), default="")
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    updated_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime)
    updated_at: Mapped[datetime] = mapped_column(DateTime)

    def can_be_lent(self) -> bool:
        """SP5 polymorphic lending policy (BR-07)."""
        return self.status == ItemStatus.AVAILABLE


class Consumable(Item):
    """Quantity-tracked supplies (US-AST-04)."""

    __tablename__ = "ast_consumables"
    __table_args__ = (
        CheckConstraint("quantity_on_hand >= 0"),
        CheckConstraint("reorder_threshold >= 0"),
    )
    __mapper_args__ = {"polymorphic_identity": "consumable"}
    id: Mapped[int] = mapped_column(ForeignKey("ast_items.id"), primary_key=True)

    def can_be_lent(self) -> bool:
        """Supplies are issued, never lent (BR-11)."""
        return False

    @property
    def quantity(self) -> int:
        """ORD stock-level port alias."""
        return self.quantity_on_hand

    name: Mapped[str] = mapped_column(String(120))
    quantity_on_hand: Mapped[int] = mapped_column(default=0)
    reorder_threshold: Mapped[int] = mapped_column(default=0)
    unit: Mapped[str] = mapped_column(String(50), default="each")


class StockTransaction(Base):
    """Immutable stock movement with operator and recipient (BR-03/11)."""

    __tablename__ = "ast_stock_transactions"
    __table_args__ = (CheckConstraint("quantity > 0"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    consumable_id: Mapped[int] = mapped_column(
        ForeignKey("ast_consumables.id"), index=True
    )
    type: Mapped[TransactionType] = mapped_column(Enum(TransactionType))
    quantity: Mapped[int]
    issued_to: Mapped[str | None] = mapped_column(String(255))
    performed_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    timestamp: Mapped[datetime] = mapped_column(DateTime)
    note: Mapped[str] = mapped_column(String(4000), default="")


class Borrower(Base):
    """A borrower does not have a login (US-AST-05)."""

    __tablename__ = "ast_borrowers"
    id: Mapped[int] = mapped_column(primary_key=True)
    school_id: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255))
    type: Mapped[BorrowerType] = mapped_column(Enum(BorrowerType))
    department: Mapped[str] = mapped_column(String(120), default="")


class Loan(Base):
    """Retained lending history with one active loan per item (BR-07–10)."""

    __tablename__ = "ast_loans"
    __table_args__ = (
        Index(
            "ast_one_open_loan",
            "item_id",
            unique=True,
            # Partial index: at most one OPEN loan per item; returned loans stay as history.
            sqlite_where=text("status = 'OPEN'"),
            postgresql_where=text("status = 'OPEN'"),
        ),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("ast_items.id"), index=True)
    borrower_id: Mapped[int] = mapped_column(ForeignKey("ast_borrowers.id"), index=True)
    checkout_date: Mapped[date] = mapped_column(Date)
    due_date: Mapped[date] = mapped_column(Date, index=True)
    condition_out: Mapped[ItemCondition] = mapped_column(Enum(ItemCondition))
    checked_out_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    return_date: Mapped[date | None] = mapped_column(Date)
    condition_in: Mapped[ItemCondition | None] = mapped_column(Enum(ItemCondition))
    received_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    extended: Mapped[bool] = mapped_column(Boolean, default=False)
    extended_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    status: Mapped[LoanStatus] = mapped_column(
        Enum(LoanStatus), default=LoanStatus.OPEN
    )
    notes: Mapped[str] = mapped_column(String(4000), default="")


class ItemIncident(Base):
    """Lost/damaged/retirement reason and actor (US-AST-10/11)."""

    __tablename__ = "ast_item_incidents"
    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("ast_items.id"), index=True)
    type: Mapped[IncidentType] = mapped_column(Enum(IncidentType))
    description: Mapped[str] = mapped_column(String(4000))
    date: Mapped[date] = mapped_column(Date)
    reported_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    timestamp: Mapped[datetime] = mapped_column(DateTime)
