1. Main user role:

The Order page as long as the Report and Audit have the following users

- `Admin user`: The admin mentions about the ***IT specialists, IT lead and IT manager*** who manage some important things that Student Assistant can not handle.
- `Student Assistant`: The lower role that can handle basic work, can not work with higher credential work. Everything that a student assistant can do also can be done by Admin user.

2. User Stories with Guidlines

## Epic 1: Order Management

### US-ORD-01: Flag Low-Stock Items for Order
As the **student assistant**, I need to check the order of the inventory, I need the system to flag need order whenever that item is almost out of stock so that I don't need to manually keep check it

**Priority:** Must have
**Related Requirement:** FR-ORD-01
**INVEST Quality:** Negotiable

- **Note:** "Almost out of stock" means the quantity of an item is less than a threshold. The item is then automatically added to an order, and a notification is sent through Gmail and on the Notification page.

**Acceptance Criteria:**

- Each inventory item has a low-stock threshold.
- When an item's quantity drops below its threshold, the system flags the item as "Need Order".
- The flagged item is automatically added to an order.
- A notification is sent through Gmail and shown on the Notification page.
- The student assistant does not need to manually check stock levels to find low-stock items.

### US-ORD-02: Order Summary Table
As the **student assistant**, I need to have a summarized order table , showing **all order status**, so I can easier keep track of the orders

**Priority:** Must have
**Related Requirement:** FR-ORD-02
**INVEST Quality:** Independent

**Acceptance Criteria:**

- The Order page displays a summary table of all orders.
- Each row shows the order ID, item(s), quantity, and current order status.
- Orders of every status are included in the table.
- The table updates when an order's status changes.

### US-ORD-03: Auto-Update Quantity on Arrival
As the **student assistant**, I need the system to auto update the quantity whenever a **new order status** has been changed to arrived, so I do not need to manually update it

**Priority:** Must have
**Related Requirement:** FR-ORD-03
**INVEST Quality:** Negotiable

**Acceptance Criteria:**

- When an order's status is changed to "Arrived", the system automatically adds the ordered quantity to the inventory.
- The inventory quantity is updated only once per order, even if the status is saved again, modify using the **unique order ID**.
- The updated quantity is visible on the inventory page right after the status change.
- No manual quantity update is required.

### US-ORD-04: Search and Filter Orders
As the **student assistant**, I need the system allow to **search** for orders and **filter** orders, so it would be easier to look for specific orders

**Priority:** Must have
**Related Requirement:** FR-ORD-04
**INVEST Quality:** Independent

**Acceptance Criteria:**

- The student assistant can search orders by order ID or item name.
- The student assistant can filter orders by status.
- Search and filter can be used together (**Should have**).
- The system shows a "no results" message when nothing matches.

### US-ORD-05: Unique Order ID, No Removal
As the **student assistant**, I need the system control each order by a unique ID, and never be removed, **only filter by status**

**Priority:** Must have
**Related Requirement:** FR-ORD-05
**INVEST Quality:** Independent

**Acceptance Criteria:**

- The system assigns a unique ID to every new order (**Must have**).
- Duplicate order IDs are not allowed (**Must have**).
- There is no option to delete an order (**Add the status as: Not ordered**).
- Closed or completed orders can be hidden or shown only by filtering by status.

## Epic 2: Report Management

### US-RPT-01: Create a Report
As the **student assistant**, I need the system to allow me create new reports, so everyone can be in the same conversation by checking the report

**Priority:** Must have
**Related Requirement:** FR-RPT-01
**INVEST Quality:** Independent

**Acceptance Criteria:**

- The student assistant can create a new report with a title and description.
- The system requires all mandatory fields before submitting.
- The new report is saved with a "Submitted" status.
- The report is visible to other users with access to it.
- A confirmation message is displayed after the report is created.
- Allow to insert images
### US-RPT-02: Group Reports by Project
As the **admin user**, I need the system to group the reports by project, so it is more convenient for me to check the reports by project (be able to link to project or task)

**Priority:** Must have
**Related Requirement:** FR-RPT-02
**INVEST Quality:** Negotiable

**Acceptance Criteria:**

- A report can be linked to a project or a task.
- The admin user can view reports grouped by project.
- Selecting a project shows all reports linked to it.
- Reports not linked to any project are shown in a separate group.

### US-RPT-03: Report Notifications
As the **admin user**, I need the system to notice the assigned when a report is submitted, and also notice the reporter the status whether it's changed

**Priority:** Must have
**Related Requirement:** FR-RPT-03
**INVEST Quality:** Independent

**Acceptance Criteria:**

- When a report is submitted, the assigned user receives a notification (**Should negotiate with notification page**).
- When a report's status changes, the reporter receives a notification.
- The notification includes the report ID and the new status.
- Notifications appear on the Notification page.

### US-RPT-04: Change Report Status
As the **admin user**, I need the **report status** can be changed (Submitted, Reviewed, Rejected, Passed)

**Priority:** Must have
**Related Requirement:** FR-RPT-04
**INVEST Quality:** Independent

**Acceptance Criteria:**

- A report can have one of these statuses: Submitted, Reviewed, Rejected, Passed.
- The admin user can change a report's status.
- The new status is saved and shown on the report.
- A confirmation message is displayed after the status changes.
- After the status is changed, the reported should receive an email
### US-RPT-05: Report Templates
As the **admin user**, the system should provide common templates, auto create report template for daily task (e.g. Morning checklist)

**Priority:** Must have
**Related Requirement:** FR-RPT-05
**INVEST Quality:** Independent

**Acceptance Criteria:**

- The system provides a list of common report templates.
- A user can create a new report from a template, with the template's fields pre-filled.
- The system automatically creates a report from the daily template (e.g. Morning checklist) each day and ask for fulfillment.
- The admin user can create and edit templates.

### US-RPT-06: Report History
As the **admin user** I need the system to keep the report history

**Priority:** Must have
**Related Requirement:** FR-RPT-06
**INVEST Quality:** Independent

**Acceptance Criteria:**

- The system keeps every past report, including closed ones.
- Each status change is recorded with the date, time, and user who made it.
- The admin user can view the history of any report.

### US-RPT-06: Search and Filter Reports
As the **admin user** I need the system to be able to search and filter the report, handle by unique ID so I can easier searching it in the future

**Priority:** Must have
**Related Requirement:** FR-RPT-08
**INVEST Quality:** Independent

**Acceptance Criteria:**

- The system assigns a unique ID to every report.
- The admin user can search reports by report ID or keyword.
- The admin user can filter reports by status, project, or date.
- The system shows a "no results" message when nothing matches.

### US-RPT-07: Easy-to-Use, Visual Interface
As the **student assistant**, I need the system to be easy to use and understand, also visualized

**Priority:** Must have
**Related Requirement:** NFR-RPT-01
**INVEST Quality:** Negotiable

**Acceptance Criteria:**

- Report and order statuses are shown with clear visual indicators (e.g. color labels).
- Main actions (create, search, filter) are reachable from the page without extra navigation.
- A new student assistant can create a report without training.
- Error and confirmation messages are written in plain language.

### US-RPT-08: Data Storage and Retention
As the **admin user**, I need the system to store all the data within its own database, and data shall remain available to retrive even after the ticket/ order is closed

**Priority:** Must have
**Related Requirement:** NFR-RPT-02
**INVEST Quality:** Independent

**Acceptance Criteria:**

- All report and order data is stored in the system's own database.
- Closed reports, tickets, and orders are not deleted from the database.
- Closed records can still be found and opened through search and filter.
