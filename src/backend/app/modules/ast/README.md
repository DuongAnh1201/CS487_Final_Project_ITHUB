AST backend (#55)
=================

The `/ast` JSON routes require an active Admin or Student Assistant session.
Retirement and category creation require Admin. Field and business-rule errors
follow SP4 §11.1. All mutations and audit rows share the `get_db` transaction.

| Resource | Methods and operations |
| --- | --- |
| `/categories` | GET lookup; POST category (`name`, `is_consumable`) |
| `/locations` | GET lookup; POST location (`building`, `room`, `description`) |
| `/items` | POST equipment; GET search by `asset_tag`, `serial_number`, `model`, `category_id`, `location_id`, `status` |
| `/items/{id}` | GET record; PATCH descriptive fields, including warranty/purchase dates |
| `/items/{id}/incidents` | POST `type` Lost/Damaged, `description`, optional `date` |
| `/items/{id}/retire` | POST `reason`, optional `date` (Admin only) |
| `/consumables` | GET supplies; POST `name`, `category_id`, `location_id`, `reorder_threshold`, `unit` |
| `/consumables/{id}` | GET supply stock level |
| `/consumables/{id}/stock-in` | POST positive integer `quantity`, optional `note` |
| `/consumables/{id}/stock-out` | POST positive integer `quantity`, `issued_to`, optional `note` |
| `/consumables/{id}/transactions` | GET retained stock history |
| `/borrowers` | GET lookup; POST `school_id`, `full_name`, `email`, `type`, optional `department` |
| `/loans` | POST checkout; GET history filtered by `item_id` and/or `borrower_id` |
| `/items/{id}/return` | POST `condition_in`, optional `return_date`, `notes` |
| `/loans/{id}/extend` | POST new `due_date` |
| `/overdue` | GET loans with borrower contact, equipment and days overdue |

Equipment registration requires `asset_tag`, `serial_number`, `model`,
`manufacturer`, `category_id` and `location_id`; new equipment is Available.
Optional fields: `purchase_date`, `warranty_end_date`, `notes`. PATCH cannot edit
status. Checkout requires `item_id`, `borrower_id`, `condition_out`; dates and notes
are optional. Borrower types are STUDENT/FACULTY/STAFF. Conditions are
Good/Fair/Poor/Damaged. Dates use YYYY-MM-DD.

Consumable inherits Item through `ast_consumables.id -> ast_items.id`; all item
IDs and asset tags share one namespace. Supplies receive a generated `SUP-...`
asset tag, have zero opening stock, and receive quantity through recorded stock-in.
They are not lendable. An individual registration using a consumable category
is also not lendable (BR-11). Retired stock is read-only.

Integration ports
-----------------

`AssetManager.get_item(item_id)` and `get_location(location_id)` provide CLS/ISS
lookups. `get_consumable(item_id)` returns `Consumable` with `id`, `name`,
`quantity_on_hand`, `reorder_threshold`. `add_stock(item_id, quantity, actor)`
returns the new quantity in ORD's current transaction; it does not commit.

`get_stock_monitor` provides one request-scoped `StockMonitor`, with NTF already
attached. `attach(observer)`, `detach(observer)` and
`check_stock(asset_id, available_quantity, reorder_threshold)` implement the
shared `StockObserver.on_low_stock` contract. Every stock change checks the
threshold after flushing its movement and audit. Each callback runs inside a
savepoint; a failure rolls back the callback and does not undo the stock change.
AST does not publish LOW_STOCK. NTF/ORD own notifications and order creation.

To wire ORD without a cycle, build AssetManager first, build OrderManager with
that instance, then attach OrderManager to `assets.stock.monitor`. Stock write
routes resolve AssetManager so this wiring applies to direct receipts/issues too.
Order attachment belongs in integration #65 once ORD is composed with AST.

`get_retirement_observers` is the injectable CLS port. Attach an implementation
of `RetirementObserver.on_item_retired(item_id)` to remove installed equipment
and recalculate room state (BR-18). Removal failure rolls back the retirement.
The standalone module defaults to no installed-equipment observer; production
composition with CLS is handled by #65.

Tests in `tests/ast/test_ast.py` cover US-AST-01–11, BR-01/03/05/07–11/18,
retired tag reuse, conjunctive search, dates, return conditions, overdue boundaries,
borrower limits, stock quantities, transactional audit rollback and observer
isolation. Cross-page wiring belongs to the integration suite.
