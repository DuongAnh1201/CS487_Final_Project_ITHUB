1. Main user role:

The Order page as long as the Report and Audit have the following users

- `Admin user`: The admin mentions about the ***IT specialists, IT lead and IT manager*** who manage some important things that Student Assistant can not handle.
- `Student Assistant`: The lower role that can handle basic work, can not work with higher credential work. Everything that a student assistant can do also can be done by Admin user.

1. User Stories with Guidlines

- Order:  

ID User Stories|ID Requirements | User Story | Invest Quality | Priority |
|---|---|---|---|---|
|US-ORD-01 | FR-ORD-01 | As the **student assistant**, I need to check the order of the inventory, I need the system to flag need order whenever that item is almost out of stock | Negotiable | Must have |
|US-ORD-02| FR-ORD-02 | As the **student assistant**, I need to have a summarized order table , showing **all order status** | Independent | Must have |
|US-ORD-03 | FR-ORD-03 | As the **student assistant**, I need the system to auto update the quantity whenever a **new order status** has been changed to arrived | Negotiable | Must have |
|US-ORD-04 | FR-ORD-04 | As the **student assistant**, I need the system allow to **search** for orders and **filter** orders | Independent | Must have |
|US-ORD-05 | FR-ORD-05 | As the **student assistant**, I need the system control each order by a unique ID, and never be removed, **only filter by status** | Independent | Must have |

- **Note:** "Almost out of stock" means the quantity of an item is less than a threshold. The item is then automatically added to an order, and a notification is sent through Gmail and on the Notification page.


