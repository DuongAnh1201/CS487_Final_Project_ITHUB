"""AST managers enforce merged FR-AST-01–14 and BR-01–11/18."""

from datetime import timedelta
from typing import Any, Protocol
from uuid import uuid4

from sqlalchemy.exc import IntegrityError

from app.core.clock import Clock
from app.core.exceptions import (
    ConflictError,
    PermissionDeniedError,
    ValidationRuleError,
)
from app.modules.ast import schemas as s
from app.modules.ast.models import (
    Borrower,
    BorrowerType,
    Category,
    Consumable,
    IncidentType,
    Item,
    ItemCondition,
    ItemIncident,
    ItemStatus,
    Loan,
    LoanStatus,
    Location,
    StockTransaction,
    TransactionType,
)
from app.modules.ast.monitor import StockMonitor
from app.modules.ast.repository import (
    BorrowerRepository,
    CategoryRepository,
    ConsumableRepository,
    IncidentRepository,
    ItemRepository,
    LoanRepository,
    LocationRepository,
    StockTransactionRepository,
)
from app.modules.usr.models import Role, User
from app.shared.audit import AuditLog
from app.shared.events import DomainEvent, EventPublisher, EventType


class ChangeRecorder:
    """Audit snapshots in the caller's transaction (BR-03)."""

    def __init__(
        self, audit: AuditLog, clock: Clock, publisher: EventPublisher
    ) -> None:
        self.audit, self.clock, self.publisher = audit, clock, publisher

    def record(
        self,
        actor: User,
        action: str,
        entity: Any,
        schema: type[s.Read],
        old: dict[str, Any] | None = None,
    ) -> None:
        """Serialize before/after values; dates and enums become JSON values."""
        new = schema.model_validate(entity).model_dump(mode="json")
        self.audit.record(actor, action, type(entity).__name__, entity.id, old, new)


class StockManager(ChangeRecorder):
    """Stock-in/out keeps quantities nonnegative (US-AST-04, BR-11)."""

    def __init__(
        self,
        stock: ConsumableRepository,
        transactions: StockTransactionRepository,
        audit: AuditLog,
        clock: Clock,
        publisher: EventPublisher,
        monitor: StockMonitor,
    ) -> None:
        super().__init__(audit, clock, publisher)
        self.stock, self.transactions, self.monitor = stock, transactions, monitor

    def change(
        self, item_id: int, data: s.StockChange, actor: User, kind: TransactionType
    ) -> Consumable:
        """Save movement, quantity and audit before checking low stock."""
        if type(data.quantity) is not int or data.quantity <= 0:
            raise ValidationRuleError("Quantity must be a positive whole number.")
        if kind == TransactionType.OUT and not data.issued_to:
            raise ValidationRuleError("Issued to is required.")
        item = self.stock.get_or_raise(item_id)
        if item.status == ItemStatus.RETIRED:
            raise ConflictError("Retired items are read-only.")
        old = s.ConsumableRead.model_validate(item).model_dump(mode="json")
        delta = data.quantity if kind == TransactionType.IN else -data.quantity
        if not self.stock.adjust(item_id, delta):
            raise ValidationRuleError("Not enough stock.")
        transaction = self.transactions.add(
            StockTransaction(
                consumable_id=item_id,
                type=kind,
                quantity=data.quantity,
                issued_to=data.issued_to,
                performed_by=actor.id,
                timestamp=self.clock(),
                note=data.note,
            )
        )
        item.updated_by, item.updated_at = actor.id, self.clock()
        self.stock.flush()
        self.record(actor, "stock_change", item, s.ConsumableRead, old)
        self.record(actor, "create", transaction, s.StockTransactionRead)
        self.monitor.check_stock(item.id, item.quantity_on_hand, item.reorder_threshold)
        return item

    def history(self, item_id: int) -> list[StockTransaction]:
        """Stock movement history for an existing consumable."""
        self.stock.get_or_raise(item_id)
        return self.transactions.for_consumable(item_id)

    def stock_in(self, item_id: int, data: s.StockChange, actor: User) -> Consumable:
        """Record received stock."""
        return self.change(item_id, data, actor, TransactionType.IN)

    def stock_out(self, item_id: int, data: s.StockChange, actor: User) -> Consumable:
        """Issue supplies; they are never lent or returned."""
        return self.change(item_id, data, actor, TransactionType.OUT)


class RetirementObserver(Protocol):
    """CLS supplies transactional equipment removal on retirement (BR-18)."""

    def on_item_retired(self, item_id: int) -> None:
        """Remove installed equipment and recalculate room condition."""


class AssetManager(ChangeRecorder):
    """Equipment lifecycle and cross-page inventory gateway (US-AST-01–03/10/11)."""

    def __init__(
        self,
        items: ItemRepository,
        categories: CategoryRepository,
        locations: LocationRepository,
        consumables: ConsumableRepository,
        incidents: IncidentRepository,
        stock: StockManager,
        audit: AuditLog,
        clock: Clock,
        publisher: EventPublisher,
        retirement_observers: tuple[RetirementObserver, ...] = (),
    ) -> None:
        super().__init__(audit, clock, publisher)
        self.items, self.categories, self.locations = items, categories, locations
        self.consumables, self.incidents, self.stock = consumables, incidents, stock
        self.retirement_observers = retirement_observers

    def list_categories(self) -> list[Category]:
        """Inventory category lookup."""
        return self.categories.list()

    def list_locations(self) -> list[Location]:
        """Locations shared with CLS."""
        return self.locations.list()

    def list_consumables(self) -> list[Consumable]:
        """Stock levels available for ordering."""
        return self.consumables.list()

    def get_item(self, item_id: int) -> Item:
        """Equipment lookup for Lending/CLS/ISS."""
        return self.items.get_or_raise(item_id)

    def get_location(self, location_id: int) -> Location:
        """Location lookup shared with CLS."""
        return self.locations.get_or_raise(location_id)

    def get_consumable(self, item_id: int) -> Consumable:
        """ORD gateway: name, quantity_on_hand and reorder_threshold."""
        return self.consumables.get_or_raise(item_id)

    def add_stock(self, item_id: int, quantity: int, actor: User) -> int:
        """ORD receipt adds stock in its existing transaction (FR-AST-13)."""
        return self.stock.stock_in(
            item_id, s.StockChange(quantity=quantity), actor
        ).quantity_on_hand

    def writable(self, item: Item) -> None:
        """Retired equipment is read-only (BR-07)."""
        if item.status == ItemStatus.RETIRED:
            raise ConflictError("Retired items are read-only.")

    def validate_details(self, values: dict[str, Any]) -> None:
        """Validate category/location references and warranty dates."""
        self.categories.get_or_raise(values["category_id"])
        self.locations.get_or_raise(values["location_id"])
        if (
            values["purchase_date"]
            and values["warranty_end_date"]
            and values["warranty_end_date"] < values["purchase_date"]
        ):
            raise ValidationRuleError(
                "Warranty end date cannot be earlier than the purchase date."
            )

    def unique_tag(self, tag: str, item_id: int | None = None) -> None:
        """Include retired records (BR-01, FR-AST-02)."""
        other = self.items.by_tag(tag)
        if other and other.id != item_id:
            raise ConflictError("Asset tag already exists.")

    def register(self, data: s.ItemCreate, actor: User) -> Item:
        """Register as Available, atomically with audit (US-AST-01)."""
        values = data.model_dump()
        self.validate_details(values)
        self.unique_tag(data.asset_tag)
        item = Item(
            **values,
            status=ItemStatus.AVAILABLE,
            created_by=actor.id,
            updated_by=actor.id,
            created_at=self.clock(),
            updated_at=self.clock(),
        )
        try:
            self.items.add(item)
        except IntegrityError as exc:
            raise ConflictError("Asset tag already exists.") from exc
        self.record(actor, "create", item, s.ItemRead)
        return item

    def edit(self, item_id: int, data: s.ItemUpdate, actor: User) -> Item:
        """Update descriptive fields without bypassing lifecycle rules (US-AST-02)."""
        item = self.get_item(item_id)
        self.writable(item)
        old = s.ItemRead.model_validate(item).model_dump(mode="json")
        changes = data.model_dump(exclude_unset=True)
        for key, value in changes.items():
            if value is None and key not in {"purchase_date", "warranty_end_date"}:
                raise ValidationRuleError(
                    f"{key.replace('_', ' ').capitalize()} is required."
                )
        values = {**old, **changes}
        # Use typed dates, not JSON audit dates.
        values["purchase_date"] = changes.get("purchase_date", item.purchase_date)
        values["warranty_end_date"] = changes.get(
            "warranty_end_date", item.warranty_end_date
        )
        self.validate_details(values)
        self.unique_tag(values["asset_tag"], item.id)
        for key, value in changes.items():
            setattr(item, key, value)
        item.updated_by, item.updated_at = actor.id, self.clock()
        try:
            self.items.flush()
        except IntegrityError as exc:
            raise ConflictError("Asset tag already exists.") from exc
        self.record(actor, "update", item, s.ItemRead, old)
        return item

    def search(self, **filters: object) -> list[Item]:
        """Apply all inventory filters together (FR-AST-04)."""
        return self.items.search(**filters)

    def set_status(self, item: Item, status: ItemStatus, actor: User) -> None:
        """Owned status transition, audited in the enclosing operation."""
        self.writable(item)
        old = s.ItemRead.model_validate(item).model_dump(mode="json")
        item.status, item.updated_by, item.updated_at = status, actor.id, self.clock()
        self.items.flush()
        self.record(actor, "status_change", item, s.ItemRead, old)

    def incident(
        self, item_id: int, data: s.IncidentCreate, actor: User, retiring: bool = False
    ) -> ItemIncident:
        """Record lifecycle reason and status together (US-AST-10/11)."""
        item = self.get_item(item_id)
        self.writable(item)
        if data.type == IncidentType.RETIRED and not retiring:
            raise ValidationRuleError("Use the retirement operation.")
        if not data.description.strip():
            raise ValidationRuleError("Description is required.")
        incident = self.incidents.add(
            ItemIncident(
                item_id=item_id,
                type=data.type,
                description=data.description,
                date=data.date or self.clock().date(),
                reported_by=actor.id,
                timestamp=self.clock(),
            )
        )
        self.set_status(item, ItemStatus(data.type.value), actor)
        self.record(actor, "create", incident, s.IncidentRead)
        self.publisher.publish(
            DomainEvent(
                EventType.GENERAL,
                f"Item {item.asset_tag}: {data.type.value}.",
                actor_id=actor.id,
                related_type="Item",
                related_id=item.id,
            )
        )
        return incident

    def retire(self, item_id: int, data: s.RetireRequest, actor: User) -> ItemIncident:
        """Admin-only retirement invokes CLS removal in the same transaction (BR-18)."""
        if actor.role != Role.ADMIN:
            raise PermissionDeniedError("Access denied.")
        incident = self.incident(
            item_id,
            s.IncidentCreate(
                type=IncidentType.RETIRED, description=data.reason, date=data.date
            ),
            actor,
            retiring=True,
        )
        for observer in self.retirement_observers:
            observer.on_item_retired(item_id)
        return incident

    def create_category(self, data: s.CategoryCreate, actor: User) -> Category:
        """Admin lookup provisioning."""
        if actor.role != Role.ADMIN:
            raise PermissionDeniedError("Access denied.")
        try:
            category = self.categories.add(Category(**data.model_dump()))
        except IntegrityError as exc:
            raise ConflictError("Category already exists.") from exc
        self.record(actor, "create", category, s.CategoryRead)
        return category

    def create_location(self, data: s.LocationCreate, actor: User) -> Location:
        """Provision a shared location."""
        location = self.locations.add(Location(**data.model_dump()))
        self.record(actor, "create", location, s.LocationRead)
        return location

    def create_consumable(self, data: s.ConsumableCreate, actor: User) -> Consumable:
        """Provision zero stock; all quantity increases have movements."""
        category = self.categories.get_or_raise(data.category_id)
        self.get_location(data.location_id)
        if not category.is_consumable:
            raise ValidationRuleError("Category must be consumable.")
        item = self.consumables.add(
            Consumable(
                **data.model_dump(),
                quantity_on_hand=0,
                asset_tag="SUP-" + uuid4().hex,
                serial_number="",
                model=data.name,
                manufacturer="",
                status=ItemStatus.AVAILABLE,
                created_by=actor.id,
                updated_by=actor.id,
                created_at=self.clock(),
                updated_at=self.clock(),
            )
        )
        self.record(actor, "create", item, s.ConsumableRead)
        return item


class LendingManager(ChangeRecorder):
    """Checkout/return/extension policies (US-AST-05–09, BR-07–11)."""

    def __init__(
        self,
        loans: LoanRepository,
        borrowers: BorrowerRepository,
        assets: AssetManager,
        audit: AuditLog,
        clock: Clock,
        publisher: EventPublisher,
    ) -> None:
        super().__init__(audit, clock, publisher)
        self.loans, self.borrowers, self.assets = loans, borrowers, assets

    def list_borrowers(self) -> list[Borrower]:
        """Known borrower identities."""
        return self.borrowers.list()

    def create_borrower(self, data: s.BorrowerCreate, actor: User) -> Borrower:
        """Persist a borrower without creating an account."""
        if self.borrowers.by_school_id(data.school_id):
            raise ConflictError("Borrower school ID already exists.")
        borrower = self.borrowers.add(Borrower(**data.model_dump()))
        self.record(actor, "create", borrower, s.BorrowerRead)
        return borrower

    def lend(self, data: s.LoanCreate, actor: User) -> Loan:
        """Check eligibility before saving loan and status together (BR-07–09)."""
        item = self.assets.get_item(data.item_id)
        self.assets.writable(item)
        if (
            isinstance(item, Consumable)
            or self.assets.categories.get_or_raise(item.category_id).is_consumable
        ):
            raise ValidationRuleError("Consumables are issued, not lent.")
        if not item.can_be_lent():
            raise ConflictError(f"Item is {item.status.value} and cannot be lent.")
        borrower = self.borrowers.get_or_raise(data.borrower_id)
        active = self.loans.open_for_borrower(borrower.id)
        for loan in self.loans.overdue(self.clock().date()):
            if loan.borrower_id == borrower.id:
                tag = self.assets.get_item(loan.item_id).asset_tag
                raise ConflictError(f"Borrower has an overdue item: {tag}.")
        if borrower.type == BorrowerType.STUDENT and len(active) >= 2:
            raise ConflictError("Borrowing limit reached.")
        checkout = data.checkout_date or self.clock().date()
        maximum = 7 if borrower.type == BorrowerType.STUDENT else 30
        due = data.due_date or checkout + timedelta(days=maximum)
        if not checkout < due <= checkout + timedelta(days=maximum):
            raise ValidationRuleError(
                f"Due date must be within {maximum} days of checkout."
            )
        loan = Loan(
            **{
                **data.model_dump(exclude={"checkout_date", "due_date"}),
                "checkout_date": checkout,
                "due_date": due,
            },
            checked_out_by=actor.id,
            status=LoanStatus.OPEN,
            extended=False,
        )
        try:
            self.loans.add(loan)
        except IntegrityError as exc:
            raise ConflictError("Item is On Loan and cannot be lent.") from exc
        self.assets.set_status(item, ItemStatus.ON_LOAN, actor)
        self.record(actor, "lend", loan, s.LoanRead)
        return loan

    def return_item(self, item_id: int, data: s.LoanReturn, actor: User) -> Loan:
        """Preserve history and damaged state (US-AST-06, BR-10)."""
        item = self.assets.get_item(item_id)
        self.assets.writable(item)
        loan = self.loans.open_for_item(item_id)
        if loan is None:
            raise ConflictError("No open loan for this item.")
        returned = data.return_date or self.clock().date()
        if returned < loan.checkout_date:
            raise ValidationRuleError(
                "Return date cannot be earlier than the checkout date."
            )
        old = s.LoanRead.model_validate(loan).model_dump(mode="json")
        loan.return_date, loan.condition_in, loan.received_by = (
            returned,
            data.condition_in,
            actor.id,
        )
        loan.status, loan.notes = LoanStatus.RETURNED, data.notes
        self.assets.set_status(
            item,
            ItemStatus.DAMAGED
            if data.condition_in in {ItemCondition.POOR, ItemCondition.DAMAGED}
            else ItemStatus.AVAILABLE,
            actor,
        )
        self.loans.flush()
        self.record(actor, "return", loan, s.LoanRead, old)
        return loan

    def extend(self, loan_id: int, data: s.LoanExtend, actor: User) -> Loan:
        """One extension, at most seven additional days (BR-08)."""
        loan = self.loans.get_or_raise(loan_id)
        self.assets.writable(self.assets.get_item(loan.item_id))
        if loan.status != LoanStatus.OPEN:
            raise ConflictError("No open loan for this item.")
        if loan.extended:
            raise ConflictError("This loan has already been extended.")
        if not loan.due_date < data.due_date <= loan.due_date + timedelta(days=7):
            raise ValidationRuleError("Due date must be within 7 days of checkout.")
        old = s.LoanRead.model_validate(loan).model_dump(mode="json")
        loan.due_date, loan.extended, loan.extended_by = data.due_date, True, actor.id
        self.loans.flush()
        self.record(actor, "extend", loan, s.LoanRead, old)
        return loan

    def overdue(self) -> list[s.OverdueRead]:
        """Include contact and days late; due today is excluded (US-AST-08)."""
        return [
            s.OverdueRead(
                loan=s.LoanRead.model_validate(loan),
                borrower=s.BorrowerRead.model_validate(
                    self.borrowers.get_or_raise(loan.borrower_id)
                ),
                item=s.ItemRead.model_validate(self.assets.get_item(loan.item_id)),
                days_overdue=(self.clock().date() - loan.due_date).days,
            )
            for loan in self.loans.overdue(self.clock().date())
        ]

    def history(
        self, item_id: int | None = None, borrower_id: int | None = None
    ) -> list[Loan]:
        """Retired item loans remain visible (US-AST-09)."""
        if item_id is not None:
            self.assets.get_item(item_id)
        if borrower_id is not None:
            self.borrowers.get_or_raise(borrower_id)
        return self.loans.history(item_id, borrower_id)
