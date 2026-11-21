"""AST storage operations; managers never execute SQL (Repository pattern)."""

from datetime import date

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.modules.ast.models import (
    Borrower,
    Category,
    Consumable,
    Item,
    ItemIncident,
    Loan,
    LoanStatus,
    Location,
    StockTransaction,
)
from app.shared.events import StockObserver
from app.shared.repository import BaseRepository


class ItemRepository(BaseRepository[Item]):
    """Equipment lookup and conjunctive inventory search (FR-AST-04)."""

    model = Item
    not_found_message = "Item not found."

    def by_tag(self, tag: str) -> Item | None:
        """Include retired tags in uniqueness checks (BR-01)."""
        return self.session.scalar(select(Item).where(Item.asset_tag == tag))

    def search(self, **filters: object) -> list[Item]:
        """All supplied filters must match; text filters use literal substrings."""
        query = select(Item)
        for key, value in filters.items():
            if value is not None:
                column = getattr(Item, key)
                query = query.where(
                    column.icontains(value, autoescape=True)  # case-insensitive on SQLite and PostgreSQL
                    if key in {"asset_tag", "serial_number", "model"}
                    else column == value
                )
        return list(self.session.scalars(query.order_by(Item.id)))


class CategoryRepository(BaseRepository[Category]):
    """Category lookup."""

    model = Category
    not_found_message = "Category not found."


class LocationRepository(BaseRepository[Location]):
    """Shared location lookup."""

    model = Location
    not_found_message = "Location not found."


class ConsumableRepository(BaseRepository[Consumable]):
    """Guard stock decrements atomically (BR-11)."""

    model = Consumable
    not_found_message = "Consumable not found."

    def adjust(self, entity_id: int, delta: int) -> bool:
        """Prevent concurrent issues from taking stock below zero."""
        result = self.session.execute(
            update(Consumable)
            .where(Consumable.id == entity_id, Consumable.quantity_on_hand + delta >= 0)
            .values(quantity_on_hand=Consumable.quantity_on_hand + delta)
        )
        self.session.flush()
        return result.rowcount == 1


class StockTransactionRepository(BaseRepository[StockTransaction]):
    """Retained stock history."""

    model = StockTransaction

    def for_consumable(self, entity_id: int) -> list[StockTransaction]:
        """List movements chronologically."""
        return list(
            self.session.scalars(
                select(StockTransaction)
                .where(StockTransaction.consumable_id == entity_id)
                .order_by(StockTransaction.id)
            )
        )


class BorrowerRepository(BaseRepository[Borrower]):
    """Stable borrower identity by school ID."""

    model = Borrower
    not_found_message = "Borrower not found."

    def by_school_id(self, school_id: str) -> Borrower | None:
        """Find the existing borrower."""
        return self.session.scalar(
            select(Borrower).where(Borrower.school_id == school_id)
        )


class LoanRepository(BaseRepository[Loan]):
    """Open loans and retained history (US-AST-05–09)."""

    model = Loan
    not_found_message = "Loan not found."

    def open_for_item(self, item_id: int) -> Loan | None:
        """Find an open checkout."""
        return self.session.scalar(
            select(Loan).where(Loan.item_id == item_id, Loan.status == LoanStatus.OPEN)
        )

    def history(
        self, item_id: int | None = None, borrower_id: int | None = None
    ) -> list[Loan]:
        """Filter past and current loans by either identity."""
        query = select(Loan)
        if item_id is not None:
            query = query.where(Loan.item_id == item_id)
        if borrower_id is not None:
            query = query.where(Loan.borrower_id == borrower_id)
        return list(self.session.scalars(query.order_by(Loan.id)))

    def open_for_borrower(self, borrower_id: int) -> list[Loan]:
        """Loans counted by borrower eligibility checks."""
        return [
            loan
            for loan in self.history(borrower_id=borrower_id)
            if loan.status == LoanStatus.OPEN
        ]

    def overdue(self, today: date) -> list[Loan]:
        """Due today is not overdue; unreturned lost loans remain overdue."""
        return list(
            self.session.scalars(
                select(Loan)
                .where(Loan.return_date.is_(None), Loan.due_date < today)
                .order_by(Loan.due_date, Loan.id)
            )
        )


class IncidentRepository(BaseRepository[ItemIncident]):
    """Retained lifecycle records."""

    model = ItemIncident


class ObserverRepository:
    """Isolate observer persistence without exposing SQL to managers."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def notify(self, observer: StockObserver, asset_id: int, quantity: int) -> None:
        """Roll back only a failing observer's writes."""
        with self.session.begin_nested():
            observer.on_low_stock(asset_id, quantity)
