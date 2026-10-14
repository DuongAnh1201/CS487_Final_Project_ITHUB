1. Main user role:

The Order page as long as the Report and Audit have the following users

- `Admin user`: The admin mentions about the ***IT specialists, IT lead and IT manager*** who manage some important things that Student Assistant can not handle.
- `Student Assistant`: The lower role that can handle basic work, can not work with higher credential work. Everything that a student assistant can do also can be done by Admin user.

1. User Stories with Guidlines

- Order:  

ID User Stories|ID Requirements | User Story | Invest Quality | Priority |
|---|---|---|---|---|
|US-ORD-01 | FR-ORD-01 | As the **student assistant**, I need to check the order of the inventory, I need the system to flag need order whenever that item is almost out of stock so that I don't need to manually keep check it | Negotiable | Must have |
|US-ORD-02| FR-ORD-02 | As the **student assistant**, I need to have a summarized order table , showing **all order status**, so I can easier keep track of the orders | Independent | Must have |
|US-ORD-03 | FR-ORD-03 | As the **student assistant**, I need the system to auto update the quantity whenever a **new order status** has been changed to arrived, so I do not need to manually update it | Negotiable | Must have |
|US-ORD-04 | FR-ORD-04 | As the **student assistant**, I need the system allow to **search** for orders and **filter** orders, so it would be easier to look for specific orders | Independent | Must have |
|US-ORD-05 | FR-ORD-05 | As the **student assistant**, I need the system control each order by a unique ID, and never be removed, **only filter by status** | Independent | Must have |
|US-RPT-01 | FR-RPT-01 | As the **student assistant**, I need the system to allow me create new reports, so everyone can be in the same conversation by checking the report | Independent | Must have |
|US-RPT-02 | FR-RPT-02 | As the **admin user**, I need the system to group the reports by project, so it is more convenient for me to check the reports by project (be able to link to project) | Negotiable | Must have |
|US-RPT-03 | FR-RPT-03| As the **admin user**, I need the system to notice the assigned when a report is submitted, and also notice the reporter the status whether it's changed | Independent | Must have
|US-RPT-04 | FR-RPT-04| As the **admin user**, I need the **report status** can be changed (Submitted, Reviewed, Rejected, Passed) | Independent | Must have 
|US-RPT-05 | FR-RPT-05| As the **admin user**, the system should provide common templates, auto create report template for daily task (e.g. Morning checklist) | Independent | Must have
|US-RPT-06 | FR-RPT-06| As the **admin user** I need the system to keep the report history| Independent | Must have
|US-RPT-06 | FR-RPT-08| As the **admin user** I need the system to be able to search and filter the report, handle by unique ID so I can easier searching it in the future | Independent | Must have
|US-RPT-07 | NFR-RPT-01 | As the **student assistant**, I need the system to be easy to use and understand, also visualized | Negotiable | Must have |
|US-RPT-08 | NFR-RPT-02 | As the **admin user**, I need the system to store all the data within its own database, and data shall remain available to retrive even after the ticket/ order is closed | Independent | Must have |

- **Note:** "Almost out of stock" means the quantity of an item is less than a threshold. The item is then automatically added to an order, and a notification is sent through Gmail and on the Notification page.


