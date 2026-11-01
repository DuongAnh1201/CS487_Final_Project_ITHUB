# SP5 – Object Design (UML): Orders and Reports & Audit

**Designer:** Duong Anh Nguyen (Tom)

## Orders (ORD)

![Orders class diagram](ORD-classes.png)

```mermaid
classDiagram
    direction LR

    class Order {
        -orderId : int
        -item : Item
        -quantityOrdered : int
        -quantityReceived : int
        -vendor : str
        -requestedBy : User
        -receivedBy : User
        -requestedAt : datetime
        -orderedAt : datetime
        -arrivedAt : datetime
        -status : OrderStatus
        +markOrdered() void
        +receive(quantity: int, user: User) void
        +cancel() void
        +isOpen() bool
        +remainingQuantity() int
        +getStatus() OrderStatus
    }

    class OrderStatus {
        <<enumeration>>
        REQUESTED
        ORDERED
        PARTIALLY_ARRIVED
        ARRIVED
        CANCELLED
    }

    class OrderManager {
        -orders : List~Order~
        -assetManager : AssetManager
        -notificationService : NotificationService
        -auditLog : AuditLog
        +createOrder(item: Item, quantity: int, vendor: str, user: User) Order
        +placeOrder(orderId: int, user: User) void
        +receiveOrder(orderId: int, quantity: int, user: User) void
        +cancelOrder(orderId: int, user: User) void
        +findOrder(orderId: int) Order
        +searchOrders(status: OrderStatus, item: Item, dateFrom: date, dateTo: date) List~Order~
        +hasOpenOrder(item: Item) bool
        +onLowStock(item: Item) void
    }

    class StockObserver {
        <<interface>>
        +onLowStock(item: Item) void
    }

    class StockMonitor {
        -observers : List~StockObserver~
        +attach(observer: StockObserver) void
        +detach(observer: StockObserver) void
        +checkStock(item: Item) void
        -notifyLowStock(item: Item) void
    }

    class Item {
        <<from Assets page>>
    }
    class User {
        <<from Login and Users page>>
    }
    class AssetManager {
        <<from Assets page>>
        +addStock(item: Item, quantity: int) void
    }
    class NotificationService {
        <<from Notifications page>>
    }
    class AuditLog {
        <<from Reports and Audit page>>
    }

    Order "*" --> "1" Item : orders
    Order "*" --> "1" User : requestedBy
    Order "*" --> "0..1" User : receivedBy
    Order --> OrderStatus : has
    OrderManager "1" o-- "*" Order : manages
    OrderManager ..|> StockObserver : implements
    StockMonitor "1" o-- "*" StockObserver : notifies
    StockMonitor ..> Item : watches quantity
    OrderManager ..> AssetManager : adds received stock
    OrderManager ..> NotificationService : order arrived
    OrderManager ..> AuditLog : logs changes
```

## Reports & Audit (RPT)

![Reports and Audit class diagram](RPT-classes.png)

```mermaid
classDiagram
    direction TB

    class Report {
        <<abstract>>
        #reportId : int
        #title : str
        #author : User
        #project : Project
        #reviewers : List~User~
        #status : ReportStatus
        #createdAt : datetime
        +submit() void
        +review(newStatus: ReportStatus, reviewer: User, comment: str) void
        +canBeReviewed() bool
        +generateContent()* str
    }

    class DailyReport {
        -template : ReportTemplate
        -shift : str
        -checklistAnswers : dict
        +answer(itemName: str, value: str) void
        +generateContent() str
    }

    class MonthlySummaryReport {
        -month : int
        -year : int
        -reports : List~Report~
        -orders : List~Order~
        +generateContent() str
    }

    class ReportTemplate {
        -templateId : int
        -name : str
        -checklistItems : List~str~
        +createReport(author: User, shift: str) DailyReport
    }

    class ReportStatus {
        <<enumeration>>
        SUBMITTED
        REVIEWED
        REJECTED
        PASSED
    }

    class ReportManager {
        -reports : List~Report~
        -templates : List~ReportTemplate~
        -notificationService : NotificationService
        -auditLog : AuditLog
        +createReport(template: ReportTemplate, author: User, project: Project) Report
        +submitReport(reportId: int, reviewers: List~User~) void
        +reviewReport(reportId: int, status: ReportStatus, reviewer: User, comment: str) void
        +findReport(reportId: int) Report
        +searchReports(status: ReportStatus, project: Project, author: User, dateFrom: date, dateTo: date) List~Report~
        +groupByProject(project: Project) List~Report~
        +getReportsForMonth(month: int, year: int) List~Report~
    }

    class SummaryGenerator {
        -reportManager : ReportManager
        -orderManager : OrderManager
        -notificationService : NotificationService
        +isMonthEnd(day: date) bool
        +generateMonthlySummary(month: int, year: int) MonthlySummaryReport
    }

    class AuditRecord {
        -recordId : int
        -user : User
        -action : str
        -entityType : str
        -entityId : int
        -oldValue : str
        -newValue : str
        -timestamp : datetime
        -status : str
        +describe() str
    }

    class AuditLog {
        -records : List~AuditRecord~
        +record(user: User, action: str, entityType: str, entityId: int, oldValue: str, newValue: str) AuditRecord
        +search(user: User, entityType: str, action: str, dateFrom: date, dateTo: date) List~AuditRecord~
    }

    class User {
        <<from Login and Users page>>
    }
    class Project {
        <<from Projects page>>
    }
    class Order {
        <<from Orders page>>
    }
    class OrderManager {
        <<from Orders page>>
    }
    class NotificationService {
        <<from Notifications page>>
    }

    Report <|-- DailyReport
    Report <|-- MonthlySummaryReport
    Report --> ReportStatus : has
    Report "*" --> "1" User : author
    Report "*" --> "1..*" User : reviewers
    Report "*" --> "0..1" Project : belongs to
    ReportTemplate "1" ..> "*" DailyReport : creates
    MonthlySummaryReport "1" o-- "*" Report : summarizes
    MonthlySummaryReport "1" o-- "*" Order : summarizes
    ReportManager "1" o-- "*" Report : manages
    ReportManager "1" o-- "*" ReportTemplate : manages
    SummaryGenerator ..> MonthlySummaryReport : creates
    SummaryGenerator ..> ReportManager : reads reports
    SummaryGenerator ..> OrderManager : reads orders
    ReportManager ..> NotificationService : notifies reviewers
    SummaryGenerator ..> NotificationService : sends summary
    ReportManager ..> AuditLog : logs changes
    AuditLog "1" *-- "*" AuditRecord : contains
    AuditRecord "*" --> "1" User : madeBy
```

## Object-oriented principles

| Principle | Where it appears |
|---|---|
| **Encapsulation** | All attributes are private (`-`). An `Order` changes status only through `markOrdered()`, `receive()`, and `cancel()`, which enforce the allowed transitions. Audit records can only be added through `AuditLog.record()`; there is no delete method. |
| **Abstraction** | `Report` is abstract, and `StockObserver` is an interface. Managers expose simple operations such as `receiveOrder()` and hide the steps behind them. |
| **Inheritance** | `DailyReport` and `MonthlySummaryReport` extend `Report` and reuse its ID, author, status, and review logic. |
| **Polymorphism** | Each report subclass implements `generateContent()` differently. `StockMonitor` calls `onLowStock()` on any `StockObserver` without knowing its concrete class. |

## Design patterns

| Pattern | Classes | Purpose |
|---|---|---|
| **Observer** | `StockMonitor` (subject), `StockObserver` (interface), `OrderManager` (observer) | When stock falls below the threshold, every registered observer is told. Other observers, such as the Notification Service, can be added without changing `StockMonitor`. |
| **Factory method** | `ReportTemplate.createReport()` | Creates a `DailyReport` already filled with the template's checklist. |
| **Controller** | `OrderManager`, `ReportManager` | Each handles the use cases of its page and delegates to domain objects. |

## Relationship notation

| Symbol | Meaning | Example |
|---|---|---|
| Solid arrow | Association | `Order` → `Item` |
| Hollow diamond | Aggregation (parts can exist alone) | `OrderManager` ◇— `Order` |
| Filled diamond | Composition (parts live only inside the whole) | `AuditLog` ◆— `AuditRecord` |
| Hollow triangle | Inheritance | `DailyReport` → `Report` |
| Dashed hollow triangle | Implements an interface | `OrderManager` ⇢ `StockObserver` |
| Dashed arrow | Dependency (uses) | `OrderManager` ⇢ `AssetManager` |

Classes marked «from … page» belong to other team members; only their name, and any method this page calls, is shown here.
