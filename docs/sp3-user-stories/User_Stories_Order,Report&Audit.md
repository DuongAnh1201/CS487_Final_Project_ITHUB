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

### US-ORD-02: Order Summary Table
As the **student assistant**, I need to have a summarized order table , showing **all order status**, so I can easier keep track of the orders

**Priority:** Must have
**Related Requirement:** FR-ORD-02
**INVEST Quality:** Independent

### US-ORD-03: Auto-Update Quantity on Arrival
As the **student assistant**, I need the system to auto update the quantity whenever a **new order status** has been changed to arrived, so I do not need to manually update it

**Priority:** Must have
**Related Requirement:** FR-ORD-03
**INVEST Quality:** Negotiable

### US-ORD-04: Search and Filter Orders
As the **student assistant**, I need the system allow to **search** for orders and **filter** orders, so it would be easier to look for specific orders

**Priority:** Must have
**Related Requirement:** FR-ORD-04
**INVEST Quality:** Independent

### US-ORD-05: Unique Order ID, No Removal
As the **student assistant**, I need the system control each order by a unique ID, and never be removed, **only filter by status**

**Priority:** Must have
**Related Requirement:** FR-ORD-05
**INVEST Quality:** Independent

## Epic 2: Report Management

### US-RPT-01: Create a Report
As the **student assistant**, I need the system to allow me create new reports, so everyone can be in the same conversation by checking the report

**Priority:** Must have
**Related Requirement:** FR-RPT-01
**INVEST Quality:** Independent

### US-RPT-02: Group Reports by Project
As the **admin user**, I need the system to group the reports by project, so it is more convenient for me to check the reports by project (be able to link to project)

**Priority:** Must have
**Related Requirement:** FR-RPT-02
**INVEST Quality:** Negotiable

### US-RPT-03: Report Notifications
As the **admin user**, I need the system to notice the assigned when a report is submitted, and also notice the reporter the status whether it's changed

**Priority:** Must have
**Related Requirement:** FR-RPT-03
**INVEST Quality:** Independent

### US-RPT-04: Change Report Status
As the **admin user**, I need the **report status** can be changed (Submitted, Reviewed, Rejected, Passed)

**Priority:** Must have
**Related Requirement:** FR-RPT-04
**INVEST Quality:** Independent

### US-RPT-05: Report Templates
As the **admin user**, the system should provide common templates, auto create report template for daily task (e.g. Morning checklist)

**Priority:** Must have
**Related Requirement:** FR-RPT-05
**INVEST Quality:** Independent

### US-RPT-06: Report History
As the **admin user** I need the system to keep the report history

**Priority:** Must have
**Related Requirement:** FR-RPT-06
**INVEST Quality:** Independent

### US-RPT-06: Search and Filter Reports
As the **admin user** I need the system to be able to search and filter the report, handle by unique ID so I can easier searching it in the future

**Priority:** Must have
**Related Requirement:** FR-RPT-08
**INVEST Quality:** Independent

### US-RPT-07: Easy-to-Use, Visual Interface
As the **student assistant**, I need the system to be easy to use and understand, also visualized

**Priority:** Must have
**Related Requirement:** NFR-RPT-01
**INVEST Quality:** Negotiable

### US-RPT-08: Data Storage and Retention
As the **admin user**, I need the system to store all the data within its own database, and data shall remain available to retrive even after the ticket/ order is closed

**Priority:** Must have
**Related Requirement:** NFR-RPT-02
**INVEST Quality:** Independent
