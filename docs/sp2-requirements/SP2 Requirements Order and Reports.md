# SP2 Requirements – Orders and Reports

**Date:** Oct 6, 2026
**Designer:** Duong Anh Nguyen (Tom)
**Pages:** Orders (`ORD`) and Reports & Audit (`RPT`)

---

## 1. Stakeholders

| Actor | Use cases |
|---|---|
| IT administrators | Review reports, approve orders, monitor audits and monthly summaries |
| IT student assistants | Create daily reports, track orders, update order status when items arrive |
| People recorded in the system who do not use it | Faculty and staff who appear in records (for example, as requesters or room users) but never log in |

## 2. Requirement-Gathering Methods

- **Document review:** examine existing forms, tickets, and documents used for reports and orders.
- **Questionnaires:** collect common needs for a tracking system from IT department staff.
- **Use-case discussions:** describe typical interactions between users and the system.

## 3. Questions

### Reports & Audit
- What statuses can a report have?
- What components does a report contain, and which reports are required?
- Why do we need each report?
- What format should reports use? Should they be editable after submission?
- What is the next step after a report is received?

### Orders
- What statuses can an order have?
- When an order arrives, what is the next step?
- When should an order be flagged? What event triggers an automatic order?

## 4. Functional Requirements

### Reports & Audit

| ID | Requirement | Priority |
|---|---|---|
| FR-RPT-01 | The system shall allow users to create new reports. | Must Have |
| FR-RPT-02 | The system shall allow users to group reports by project. | Should Have |
| FR-RPT-03 | The system shall notify the assigned reviewers when a report is submitted. | Must Have |
| FR-RPT-04 | The system shall allow users to change a report's status (Submitted, Reviewed, Rejected, Passed). | Must Have |
| FR-RPT-05 | The system shall provide templates for daily reports, such as the morning report completed by the student assistant on the morning shift. | Should Have |
| FR-RPT-06 | The system shall keep an audit record of all tracked activities, including tasks, orders, and their progress, not only reports. | Must Have |
| FR-RPT-07 | The system shall automatically send a monthly summary report. | Should Have |
| FR-RPT-08 | The system shall allow users to search and filter reports and audit records. | Must Have |
| FR-RPT-09 | The system shall assign a unique ID to every report and audit record. | Must Have |

### Orders

| ID | Requirement | Priority |
|---|---|---|
| FR-ORD-01 | The system shall link orders to the inventory and automatically flag items that are almost out of stock. | Must Have |
| FR-ORD-02 | The system shall track every order and its status. | Must Have |
| FR-ORD-03 | When an order's status changes to Arrived, the system shall automatically add the received quantity to the inventory. | Must Have |
| FR-ORD-04 | The system shall automatically summarize orders. | Should Have |
| FR-ORD-05 | The system shall allow users to search and filter orders. | Must Have |
| FR-ORD-06 | The system shall assign a unique ID to every order. | Must Have |

> **Note:** "Almost out of stock" means the quantity of an item is less than a threshold. The item is then automatically added to an order, and a notification is sent through Gmail and on the Notifications page.

## 5. Non-Functional Requirements

These apply to both pages.

| ID | Requirement | Priority |
|---|---|---|
| NFR-RPT-01 | The system shall be easy to use and understand. | Must Have |
| NFR-RPT-02 | The system shall store all data within its own database, and the data shall remain available after the program is closed. | Must Have |
| NFR-RPT-03 | The system shall display a clear error message for invalid input. | Must Have |
| NFR-RPT-04 | The design shall follow object-oriented principles. | Must Have |

## 6. Business Rules

| ID | Business rule |
|---|---|
| BR-ORD-01 | An item cannot have more than one open order at the same time. |
| BR-RPT-01 | The monthly summary is sent only at the end of each month. |
| BR-RPT-02 | Only IT administrators and IT student assistants can add, update, or modify reports and orders. |
| BR-RPT-03 | Every audit record has a status, and audit records are never removed from the system. |

## 7. Main Use Cases

| ID | Use case | Primary actor | Result |
|---|---|---|---|
| UC-ORD-01 | Create Order | IT student assistant | A new order is recorded with status Requested |
| UC-ORD-02 | Update Order Status | IT student assistant | The order moves to its next status |
| UC-ORD-03 | Receive Order | IT student assistant | The order is marked Arrived and the inventory quantity increases |
| UC-ORD-04 | Flag Low Stock | System | Items almost out of stock are flagged for ordering |
| UC-RPT-01 | Create Report | IT student assistant | A new report is saved, optionally from a daily template |
| UC-RPT-02 | Review Report | IT administrator | The report status changes to Reviewed, Rejected, or Passed |
| UC-RPT-03 | Send Monthly Summary | System | A summary of reports and orders is sent at month end |
| UC-RPT-04 | View Audit History | IT administrator or student assistant | Audit records matching the search or filter are displayed |

## 8. Use-Case Specification: Receive Order

**Use case ID:** UC-ORD-03
**Primary actor:** IT student assistant
**Precondition:** The user is logged in, and the order exists with status Ordered.

**Main flow:**
1. The user opens the Orders page and searches for the order by ID or item.
2. The system displays the order details: item, quantity ordered, vendor, and status.
3. The user selects "Receive Order."
4. The user enters the quantity received.
5. The system validates the quantity.
6. The system changes the order status to Arrived and records the arrival date and the user.
7. The system adds the received quantity to the item's stock in the inventory.
8. The system clears the item's low-stock flag if the new quantity is above the threshold.
9. The system creates an audit record of the change.
10. The system displays a confirmation message.

**Alternative flows:**
- **1a.** The order ID does not exist: the system displays an error.
- **2a.** The order status is not Ordered (for example, already Arrived or Cancelled): the system rejects the action and shows the current status.
- **4a.** The quantity received is less than the quantity ordered: the system records a partial delivery, adds the received quantity, and keeps the order open for the rest.
- **5a.** The quantity is invalid (zero, negative, or not a number): the system displays an error and asks again.

**Postcondition:**
- The order status is Arrived (or Partially Arrived).
- The inventory quantity is updated.
- An audit record of the change is saved.

## 9. Proposed Object-Oriented Classes

| Class | Main responsibilities |
|---|---|
| Order | Store item, quantity ordered and received, vendor, requester, dates, and status |
| OrderStatus (enum) | Requested, Ordered, Partially Arrived, Arrived, Cancelled |
| OrderService | Create orders, update status, receive orders, summarize orders, prevent duplicate open orders |
| StockMonitor | Watch inventory quantities and flag items that fall below their threshold |
| Report (abstract) | Common report data: ID, title, author, project, status, created date |
| DailyReport | A report filled in by a student assistant, such as the morning report |
| MonthlySummaryReport | A report generated by the system at month end from reports and orders |
| ReportTemplate | A reusable checklist used to create daily reports |
| ReportStatus (enum) | Submitted, Reviewed, Rejected, Passed |
| ReportService | Create, group, review, and search reports; send the monthly summary |
| AuditRecord | Store one change: ID, user, action, entity, old and new values, timestamp, status |
| AuditLog | Add and search audit records; never delete them |

**Possible relationships:**
- An `Order` refers to one inventory item (owned by the Assets page).
- `OrderService` manages many `Order` objects and updates the inventory when an order arrives.
- `StockMonitor` observes inventory items and notifies `OrderService` when stock is low (Observer pattern).
- `DailyReport` and `MonthlySummaryReport` extend `Report` (inheritance and polymorphism).
- A `DailyReport` is created from one `ReportTemplate`.
- A `Report` belongs to one project and has one or more reviewers.
- `AuditLog` contains many `AuditRecord` objects; `OrderService` and `ReportService` write to it on every change.

## 10. Acceptance Criteria

### Requirement: Receive an order (FR-ORD-03)
The requirement is accepted when:
- An order with status Ordered can be selected.
- Entering the quantity received changes the status to Arrived.
- The item's inventory quantity increases by exactly the quantity received.
- A partial delivery keeps the order open with status Partially Arrived.
- Invalid quantities (zero, negative, non-numeric) are rejected with an error message.
- An audit record is created for the change.

### Requirement: Flag low stock (FR-ORD-01)
The requirement is accepted when:
- An item whose quantity falls below its threshold is flagged.
- An item that already has an open order is not flagged for a second order (BR-ORD-01).
- The flag is cleared when stock rises above the threshold.

### Requirement: Change a report's status (FR-RPT-04)
The requirement is accepted when:
- A reviewer can set a submitted report to Reviewed, Rejected, or Passed.
- The new status is saved and shown on the report.
- The report's author is notified of the change.
- An audit record is created with the old and new status.

### Requirement: Send the monthly summary (FR-RPT-07)
The requirement is accepted when:
- The summary is generated only at the end of the month (BR-RPT-01).
- It includes that month's reports, orders, and their statuses.
- It is delivered to IT administrators.

### Requirement: Keep audit records (FR-RPT-06)
The requirement is accepted when:
- Every change to a report or order creates an audit record.
- Each audit record has an ID, user, timestamp, and status.
- No user can delete an audit record (BR-RPT-03).

## 11. Out-of-Scope Requirements

The following are excluded from this version of the Orders and Reports pages:
- Online payment or vendor invoicing
- Placing orders directly with vendors or through vendor portals (the system only flags and tracks orders)
- Budget and accounting management
- Email or SMS delivery of notifications and summaries (delivered inside the system only)
- Barcode or RFID scanning when receiving orders
- Editing or deleting audit records
- Mobile application

## 12. Requirement Traceability

Each requirement is linked to its stakeholder, use case, class or component, and test case.

### Functional requirements

| Requirement | Stakeholder | Use case | Class / component | Test case |
|---|---|---|---|---|
| FR-RPT-01 | IT student assistant | UC-RPT-01 | Report, DailyReport, ReportService | TC-RPT-01: Create a blank report and a report from a template |
| FR-RPT-02 | IT student assistant | UC-RPT-01 | Report, ReportService | TC-RPT-02: Assign a report to a project and list reports by project |
| FR-RPT-03 | IT administrator | UC-RPT-01 | ReportService, notification service (Notifications page) | TC-RPT-03: Submitting a report notifies each assigned reviewer |
| FR-RPT-04 | IT administrator | UC-RPT-02 | Report, ReportStatus, ReportService | TC-RPT-04: Change status to Reviewed, Rejected, and Passed |
| FR-RPT-05 | IT student assistant | UC-RPT-01 | ReportTemplate, DailyReport | TC-RPT-05: Create the morning report from its template |
| FR-RPT-06 | IT administrator | UC-RPT-04 | AuditRecord, AuditLog | TC-RPT-06: Changes to reports, orders, and tasks create audit records |
| FR-RPT-07 | IT administrator | UC-RPT-03 | MonthlySummaryReport, ReportService | TC-RPT-07: Month-end summary contains that month's reports and orders |
| FR-RPT-08 | IT administrator, IT student assistant | UC-RPT-04 | ReportService, AuditLog | TC-RPT-08: Search and filter reports and audit records |
| FR-RPT-09 | IT administrator, IT student assistant | UC-RPT-01, UC-RPT-04 | Report, AuditRecord | TC-RPT-09: New reports and audit records receive unique IDs |
| FR-ORD-01 | IT student assistant | UC-ORD-04 | StockMonitor, OrderService | TC-ORD-01: Item below threshold is flagged; flag clears above threshold |
| FR-ORD-02 | IT student assistant | UC-ORD-01, UC-ORD-02 | Order, OrderStatus, OrderService | TC-ORD-02: Order moves through each status in order |
| FR-ORD-03 | IT student assistant | UC-ORD-03 | Order, OrderService, AuditLog | TC-ORD-03: Full and partial delivery update inventory correctly |
| FR-ORD-04 | IT administrator | UC-RPT-03 | OrderService, MonthlySummaryReport | TC-ORD-04: Order summary totals match recorded orders |
| FR-ORD-05 | IT administrator, IT student assistant | UC-ORD-03 | OrderService | TC-ORD-05: Search orders by ID, item, and status |
| FR-ORD-06 | IT administrator, IT student assistant | UC-ORD-01 | Order | TC-ORD-06: New orders receive unique IDs |

### Non-functional requirements

| Requirement | Stakeholder | Use case | Class / component | Test case |
|---|---|---|---|---|
| NFR-RPT-01 | IT administrator, IT student assistant | All | User interface | TC-NFR-01: New user completes "Receive Order" without help |
| NFR-RPT-02 | IT administrator, IT student assistant | All | Database / repository layer | TC-NFR-02: Data is still present after the program restarts |
| NFR-RPT-03 | IT administrator, IT student assistant | UC-ORD-03 (5a), UC-RPT-01 | User interface, input validation in services | TC-NFR-03: Invalid input shows a clear error message |
| NFR-RPT-04 | Project team, instructor | All | All classes | TC-NFR-04: Design review against the class diagram |

### Business rules

| Rule | Stakeholder | Use case | Class / component | Test case |
|---|---|---|---|---|
| BR-ORD-01 | IT student assistant | UC-ORD-01, UC-ORD-04 | OrderService | TC-ORD-07: Second open order for the same item is rejected |
| BR-RPT-01 | IT administrator | UC-RPT-03 | ReportService | TC-RPT-10: Summary is not sent before month end |
| BR-RPT-02 | IT administrator | All | User (Login & Users page), OrderService, ReportService | TC-RPT-11: User without access cannot add or modify reports and orders |
| BR-RPT-03 | IT administrator | UC-RPT-04 | AuditLog | TC-RPT-12: Attempt to delete an audit record is rejected |