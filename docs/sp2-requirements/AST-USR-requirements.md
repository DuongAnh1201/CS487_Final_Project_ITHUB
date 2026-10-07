# SP2 – Requirements: Assets & Lending (AST), Login & Users (USR)

**Owner:** Zafar Azatov · **Issue:** #3 (parent #2) · **Milestone:** SP2 – Requirements Collection

---

## 1. Stakeholders & Actors

| Code | Stakeholder | Role in these pages |
|---|---|---|
| ITS | IT Supervisor | Admin user. Creates accounts, retires items, sets lending policy |
| SA | Student Assistant | Daily user. Registers items, lends/returns items, issues supplies |
| BOR | Borrower (student, faculty, staff) | Borrows items. Not a system user; SA records loans for them |
| TEAM | Project team | Builds and tests the system |
| INS | Course instructor | Reviews requirements |

**Actors:** IT Supervisor (Admin), Student Assistant. Admin can do everything an SA can.

## 2. Gathering Questions

### Assets & Lending

**Item records**
1. What is recorded per item (asset tag, serial, model, manufacturer, location, purchase date, warranty)?
2. What item types exist (desktops, laptops, monitors, network devices, peripherals, supplies)?
3. Who assigns asset tags? Are they printed labels, barcodes, or QR codes?
4. Are asset tags ever reused after an item is retired?
5. How are locations described (building + room, closet, rack, desk)?
6. Is there existing data (Excel/CSV) that must be imported?
7. Do we need to track who an item is permanently assigned to (e.g. a staff laptop), separate from loans?

**Consumables**
8. Are cables, toner, adapters tracked by quantity instead of individually?
9. When stock is low, who should be told and at what threshold?
10. Is issuing a consumable recorded against a person or department?

**Lending**
11. How are items lent out today (paper sign-out sheet, spreadsheet, email)?
12. Who can borrow: students, faculty, staff, guests?
13. Default and maximum loan length for each borrower type? Can loans be extended?
14. Is there a limit on how many items one borrower holds at once?
15. What is recorded at checkout and return (borrower ID, contact, dates, condition, who processed it)?
16. What happens when an item is returned late? Is the borrower blocked from borrowing again?
17. Do borrowers sign anything (agreement, acknowledgement)?
18. Can items be reserved in advance?

**Lost, damaged, retired**
19. What is the process when an item is reported lost or damaged? Who approves?
20. Who can retire an item, and what happens to its history?
21. Are retired items disposed, recycled, or kept? Is the disposal date recorded?

### Login & Users

22. What information does a user account need (name, school email, school ID, role)?
23. Who creates accounts? Can users self-register?
24. What roles exist and what can each do?
25. How do users log in: username + password, school email, school ID, SSO?
26. Password rules: length, complexity, expiry?
27. Lockout after failed attempts? How many, and for how long?
28. How are forgotten passwords handled?
29. What happens to SA accounts when they graduate or leave the job?
30. Must every change be tied to the logged-in user? Is shared login ever allowed?
31. Should sessions time out after inactivity? How long?

## 3. Assumptions (confirm with IT Supervisor)

- A-01: Borrowers do not log in; SAs record loans for them.
- A-02: Two roles this semester: **Admin** (IT Supervisor) and **Student Assistant**.
- A-03: Default loan length is 7 days for students, 30 days for faculty/staff.
- A-04: Login uses school email + password (Can do the SSO by using Google Firebase).
- A-05: The audit log storage is shared with the Reports & Audit page (RPT).

---

## 4. Functional Requirements

Priority: **M** = Must Have · **S** = Should Have · **C** = Could Have · **W** = Will Not Have (this semester)

### Assets & Lending

| ID | Requirement | Priority |
|---|---|---|
| FR-AST-01 | The system shall let an SA register an item with asset tag, serial number, model, manufacturer, category, location, status, purchase date, warranty end date, and notes. | M |
| FR-AST-02 | The system shall reject an item whose asset tag already exists. | M |
| FR-AST-03 | The system shall let an SA edit an item's details. | M |
| FR-AST-04 | The system shall let users search and filter items by asset tag, serial number, model, category, location, and status. | M |
| FR-AST-05 | The system shall let the Admin manage item categories (e.g. Desktop, Laptop, Monitor, Network Device, Peripheral, Supply). | S |
| FR-AST-06 | The system shall track consumables by quantity, recording each stock-in and stock-out. | M |
| FR-AST-07 | The system shall flag a consumable when its quantity falls at or below its reorder threshold. | S |
| FR-AST-08 | The system shall let an SA lend out an item, recording borrower name, school ID, email, borrower type, checkout date, due date, condition out, and the SA who processed it. | M |
| FR-AST-09 | The system shall let an SA record a return, capturing return date, condition in, notes, and the SA who received it. | M |
| FR-AST-10 | The system shall list all overdue loans (due date passed, not returned). | M |
| FR-AST-11 | The system shall show loan history per item and per borrower. | S |
| FR-AST-12 | The system shall let an SA report an item as Lost or Damaged with a description and date. | M |
| FR-AST-13 | The system shall let the Admin retire an item with a reason and date. | M |
| FR-AST-14 | The system shall let an SA extend a loan's due date once, within the maximum loan length. | S |
| FR-AST-15 | The system shall export the filtered inventory list to CSV. | S |
| FR-AST-16 | The system shall import items from a CSV file, reporting rows that fail validation. | C |
| FR-AST-17 | The system shall generate a printable QR/barcode label for an asset tag. | C |
| FR-AST-18 | Item reservations in advance. | W |
| FR-AST-19 | Photo attachments for items. | W |
| FR-AST-20 | The system should be auto updated the quantity when an order is set to received | M |
| FR-AST-21 | The system should be auto flag and send notification when quantity of an item is under the threshold| M |
### Login & Users

| ID | Requirement | Priority |
|---|---|---|
| FR-USR-01 | The system shall authenticate users with school email and password. | M |
| FR-USR-02 | The system shall let a logged-in user log out. | M |
| FR-USR-03 | The system shall let the Admin create user accounts with full name, school email, school ID, role, and optional access end date. | M |
| FR-USR-04 | The system shall let the Admin change a user's role and deactivate or reactivate an account. | M |
| FR-USR-05 | The system shall restrict actions by role (Admin, Student Assistant) (This is created in advanced). | M |
| FR-USR-06 | The system shall record the logged-in user and timestamp on every create, update, and status change. | M |
| FR-USR-07 | The system shall lock an account for 15 minutes after 5 consecutive failed login attempts. | S |
| FR-USR-08 | The system shall let a user change their own password. | S |
| FR-USR-09 | The system shall let the Admin reset a user's password to a temporary one that must be changed at next login. | S |
| FR-USR-10 | The system shall list users with filters by role and status. | S |
| FR-USR-11 | The system shall automatically deactivate an account after its access end date. | C |
| FR-USR-12 | Single sign-on with the school identity provider. | W |

## 5. Non-Functional Requirements

| ID | Category | Requirement | Priority |
|---|---|---|---|
| NFR-AST-01 | Performance | Inventory search returns results within 2 seconds for up to 5,000 items. | S |
| NFR-AST-02 | Usability | An SA can complete a checkout in under 1 minute and no more than 3 screens. | S |
| NFR-AST-03 | Usability | Required fields show clear inline error messages on invalid input. | M |
| NFR-AST-04 | Reliability | Item and loan records are never hard-deleted; history is kept at least 3 years. | M |
| NFR-AST-05 | Compatibility | Pages work on current Chrome, Edge, Firefox, Safari at widths ≥ 768 px. | S |
| NFR-USR-01 | Security | Passwords are stored only as salted hashes (bcrypt or Argon2). | M |
| NFR-USR-03 | Security | Sessions expire after 30 minutes of inactivity. | S |
| NFR-USR-04 | Security | Login errors do not reveal whether the email exists. | S |
| NFR-USR-05 | Performance | Login completes within 2 seconds under normal load. | S |

## 6. Business Rules

| ID | Rule |
|---|---|
| BR-AST-01 | Asset tags are unique and never reused, even after retirement. |
| BR-AST-02 | Only items with status **Available** can be lent out. |
| BR-AST-03 | Default loan length: 7 days (students), 30 days (faculty/staff). Max one extension of 7 days. |
| BR-AST-04 | A student borrower may hold at most 2 items at a time. |
| BR-AST-05 | A borrower with an overdue item cannot borrow until it is returned. |
| BR-AST-06 | Consumables are issued, not lent; they are not returned. |
| BR-AST-07 | Consumable quantity cannot go below zero. |
| BR-AST-08 | Only the Admin can retire an item. Retired items are read-only and cannot be lent. |
| BR-AST-09 | An item returned in damaged condition is set to **Damaged**, not Available. |
| BR-USR-01 | Only the Admin creates accounts, assigns roles, and deactivates accounts. |
| BR-USR-02 | Accounts are deactivated, never deleted, so past actions stay attributable. |
| BR-USR-03 | Passwords are at least 10 characters and contain letters and digits. |
| BR-USR-04 | One account per person; shared accounts are not allowed. |
| BR-USR-05 | An SA's account is deactivated within 1 business day of leaving the job. |
| BR-USR-06 | At least one active Admin account must always exist. |
| BR-USR-07 | Deactivated or locked accounts cannot log in. |

---

## 7. Main Use Cases

| ID | Use Case | Primary Actor | Result |
|---|---|---|---|
| UC-AST-01 | Register Item | SA | Item saved with status Available |
| UC-AST-02 | Update Item | SA | Item details updated |
| UC-AST-03 | Search Inventory | SA / Admin | Matching items listed |
| UC-AST-04 | Lend Out Item | SA | Open loan created; item status On Loan |
| UC-AST-05 | Return Item | SA | Loan closed; item Available or Damaged |
| UC-AST-06 | View Overdue Loans | SA / Admin | Overdue loans listed |
| UC-AST-07 | Issue / Restock Consumable | SA | Stock quantity updated |
| UC-AST-08 | Report Lost or Damaged Item | SA | Item status Lost/Damaged with incident record |
| UC-AST-09 | Retire Item | Admin | Item status Retired, read-only |
| UC-AST-10 | Keep track the quantity of items| SA | Quantity of items can be updated |
| UC-USR-01 | Log In | SA / Admin | Authenticated session started |
| UC-USR-02 | Log Out | SA / Admin | Session ended |
| UC-USR-03 | Create User Account | Admin | New active account |
| UC-USR-04 | Deactivate User Account | Admin | Account inactive; cannot log in |
| UC-USR-05 | Reset User Password | Admin | Temporary password set |
| UC-USR-06 | Change Own Password | SA / Admin | Password updated |

## 8. Use-Case Specifications

### UC-AST-04 – Lend Out Item

| Field | Description |
|---|---|
| **Primary actor** | Student Assistant |
| **Stakeholders** | Borrower (gets item), IT Supervisor (tracks equipment) |
| **Preconditions** | SA is logged in. Item exists and is Available. |
| **Trigger** | A borrower asks to borrow an item at the IT desk. |
| **Postconditions** | Loan is Open with a due date; item status is On Loan; action logged with SA and timestamp. |

**Main flow**
1. SA opens *Lend Out Item*.
2. SA scans or enters the asset tag.
3. System shows the item and confirms it is Available.
4. SA enters borrower school ID.
5. System loads the borrower if known, otherwise SA enters name, email, and borrower type.
6. System checks borrower eligibility (no overdue items, under item limit).
7. System proposes a due date based on borrower type.
8. SA records condition out (Good / Fair / Poor + notes) and confirms.
9. System creates the loan, sets item to On Loan, logs the action, and shows a confirmation.

**Alternate flows**
- 3a. Item is not Available → system shows its current status and stops.
- 5a. New borrower → system saves the borrower record with the loan.
- 7a. SA changes the due date → system accepts it only within the maximum loan length (BR-AST-03).

**Exception flows**
- 2a. Asset tag not found → system shows "Item not found"; SA re-enters or cancels.
- 6a. Borrower has an overdue item → system blocks the loan and lists the overdue item (BR-AST-05).
- 6b. Student already holds 2 items → system blocks the loan (BR-AST-04).
- 9a. Save fails → no loan is created and the item stays Available.

**Related:** FR-AST-08, FR-AST-10, BR-AST-02–05, FR-USR-06

### UC-USR-01 – Log In

| Field | Description |
|---|---|
| **Primary actor** | Student Assistant or Admin |
| **Preconditions** | User has an active account. |
| **Postconditions** | Authenticated session started; last login time recorded. |

**Main flow**
1. User opens the login page.
2. User enters school email and password.
3. System verifies the credentials against the stored hash.
4. System resets the failed-attempt count, records last login, and opens the dashboard for the user's role.

**Alternate flows**
- 4a. Temporary password → system requires a new password before continuing (FR-USR-09).

**Exception flows**
- 3a. Wrong email or password → system shows a generic "Invalid email or password" and increments the failed count (NFR-USR-04).
- 3b. 5th consecutive failure → account locked for 15 minutes (FR-USR-07).
- 3c. Account deactivated or locked → login refused (BR-USR-07).

**Related:** FR-USR-01, FR-USR-07, NFR-USR-01, NFR-USR-03, NFR-USR-04

---

## 9. Acceptance Criteria

**FR-AST-02 – Unique asset tag**
- Given an item with tag `SFBU-00123` exists, when an SA registers another item with `SFBU-00123`, then the system rejects it and shows "Asset tag already exists".
- Given a retired item with tag `SFBU-00050`, when an SA registers a new item with `SFBU-00050`, then it is rejected (BR-AST-01).

**FR-AST-08 – Lend out item**
- Given an Available item and an eligible student, when the SA completes checkout, then a loan is created with due date = today + 7 days, the item becomes On Loan, and the SA's ID is stored on the loan.
- Given an item On Loan, when an SA tries to lend it, then the system blocks the checkout and shows its current status.
- Given a borrower with an overdue loan, when an SA tries to lend them an item, then the checkout is blocked.

**FR-AST-09 – Return item**
- Given an open loan, when the SA records the return in Good condition, then the loan is closed with the return date and the item becomes Available.
- Given an open loan, when the SA records condition Poor/Damaged, then the item becomes Damaged (BR-AST-09).

**FR-USR-01 – Log in**
- Given an active user with correct credentials, when they log in, then they reach the dashboard for their role.
- Given a wrong password, when they log in, then they see "Invalid email or password" and no session is created.
- Given a deactivated account, when the user enters correct credentials, then login is refused.

**FR-USR-06 – Changes tied to user**
- Given an SA is logged in, when they create, edit, lend, or return an item, then the record stores their user ID and a timestamp.
- Given any change, when the Admin views the item history, then the user who made each change is shown.

---

## 10. Proposed Classes

| Class | Attributes |
|---|---|
| **Item** | itemId, assetTag, serialNumber, model, manufacturer, category: Category, location: Location, status: ItemStatus, purchaseDate, warrantyEndDate, notes, createdBy: User, createdAt, updatedBy: User, updatedAt |
| **Category** | categoryId, name, isConsumable |
| **Location** | locationId, building, room, description |
| **Consumable** | consumableId, name, category: Category, location: Location, quantityOnHand, reorderThreshold, unit |
| **StockTransaction** | transactionId, consumable: Consumable, type (IN/OUT), quantity, issuedTo, performedBy: User, timestamp, note |
| **Borrower** | borrowerId, schoolId, fullName, email, type (STUDENT/FACULTY/STAFF), department |
| **Loan** | loanId, item: Item, borrower: Borrower, checkoutDate, dueDate, conditionOut, checkedOutBy: User, returnDate, conditionIn, receivedBy: User, extended: boolean, status (OPEN/RETURNED/LOST), notes |
| **ItemIncident** | incidentId, item: Item, type (LOST/DAMAGED/RETIRED), description, reportedBy: User, timestamp |
| **User** | userId, fullName, email, schoolId, passwordHash, role: Role, status (ACTIVE/INACTIVE), failedLoginCount, lockedUntil, mustChangePassword, accessEndDate, lastLoginAt, createdBy: User, createdAt |
| **AuditLogEntry** | entryId, user: User, action, entityType, entityId, timestamp, details *(shared with RPT)* |

**Enums:** `ItemStatus` = AVAILABLE, ON_LOAN, DAMAGED, LOST, RETIRED · `Role` = ADMIN, STUDENT_ASSISTANT

**Relationships:** Item 1–* Loan · Borrower 1–* Loan · Item 1–* ItemIncident · Category 1–* Item · Location 1–* Item · Consumable 1–* StockTransaction · User 1–* AuditLogEntry

---

## 11. Traceability Matrix

| Requirement | Stakeholder | Use Case | Class | Test Case |
|---|---|---|---|---|
| FR-AST-01 | SA, ITS | UC-AST-01 | Item, Category, Location | TC-AST-01 |
| FR-AST-02 | ITS | UC-AST-01 | Item | TC-AST-02 |
| FR-AST-03 | SA | UC-AST-02 | Item | TC-AST-03 |
| FR-AST-04 | SA, ITS | UC-AST-03 | Item | TC-AST-04 |
| FR-AST-05 | ITS | UC-AST-01 | Category | TC-AST-05 |
| FR-AST-06 | SA, ITS | UC-AST-07 | Consumable, StockTransaction | TC-AST-06 |
| FR-AST-07 | ITS | UC-AST-07 | Consumable | TC-AST-07 |
| FR-AST-08 | SA, BOR | UC-AST-04 | Loan, Borrower, Item | TC-AST-08 |
| FR-AST-09 | SA, BOR | UC-AST-05 | Loan, Item | TC-AST-09 |
| FR-AST-10 | ITS, SA | UC-AST-06 | Loan | TC-AST-10 |
| FR-AST-11 | ITS | UC-AST-03 | Loan, Borrower | TC-AST-11 |
| FR-AST-12 | SA, ITS | UC-AST-08 | ItemIncident, Item | TC-AST-12 |
| FR-AST-13 | ITS | UC-AST-09 | ItemIncident, Item | TC-AST-13 |
| FR-AST-14 | SA, BOR | UC-AST-04 | Loan | TC-AST-14 |
| FR-AST-15 | ITS | UC-AST-03 | Item | TC-AST-15 |
| FR-AST-16 | ITS | UC-AST-01 | Item | TC-AST-16 |
| FR-AST-17 | SA | UC-AST-01 | Item | TC-AST-17 |
| FR-USR-01 | SA, ITS | UC-USR-01 | User | TC-USR-01 |
| FR-USR-02 | SA, ITS | UC-USR-02 | User | TC-USR-02 |
| FR-USR-03 | ITS | UC-USR-03 | User | TC-USR-03 |
| FR-USR-04 | ITS | UC-USR-04 | User | TC-USR-04 |
| FR-USR-05 | ITS | UC-USR-01 | User, Role | TC-USR-05 |
| FR-USR-06 | ITS, INS | all UCs | AuditLogEntry, User | TC-USR-06 |
| FR-USR-07 | ITS | UC-USR-01 | User | TC-USR-07 |
| FR-USR-08 | SA, ITS | UC-USR-06 | User | TC-USR-08 |
| FR-USR-09 | ITS | UC-USR-05 | User | TC-USR-09 |
| FR-USR-10 | ITS | UC-USR-04 | User | TC-USR-10 |
| FR-USR-11 | ITS | UC-USR-04 | User | TC-USR-11 |
| NFR-AST-01 | SA | UC-AST-03 | Item | TC-AST-N01 |
| NFR-AST-02 | SA | UC-AST-04 | Loan | TC-AST-N02 |
| NFR-AST-03 | SA | UC-AST-01, 04 | Item, Loan | TC-AST-N03 |
| NFR-AST-04 | ITS | UC-AST-05, 09 | Item, Loan | TC-AST-N04 |
| NFR-AST-05 | SA | all AST UCs | — | TC-AST-N05 |
| NFR-USR-01 | ITS, TEAM | UC-USR-01, 03 | User | TC-USR-N01 |
| NFR-USR-02 | ITS, TEAM | UC-USR-01 | — | TC-USR-N02 |
| NFR-USR-03 | ITS | UC-USR-01 | User | TC-USR-N03 |
| NFR-USR-04 | ITS | UC-USR-01 | User | TC-USR-N04 |
| NFR-USR-05 | SA | UC-USR-01 | User | TC-USR-N05 |
| BR-AST-01 | ITS | UC-AST-01 | Item | TC-AST-02 |
| BR-AST-02 | ITS | UC-AST-04 | Item, Loan | TC-AST-08 |
| BR-AST-03 | ITS, BOR | UC-AST-04 | Loan, Borrower | TC-AST-08, TC-AST-14 |
| BR-AST-04 | ITS | UC-AST-04 | Loan, Borrower | TC-AST-B04 |
| BR-AST-05 | ITS | UC-AST-04 | Loan | TC-AST-B05 |
| BR-AST-06 | ITS | UC-AST-07 | StockTransaction | TC-AST-06 |
| BR-AST-07 | ITS | UC-AST-07 | Consumable | TC-AST-B07 |
| BR-AST-08 | ITS | UC-AST-09 | Item | TC-AST-13 |
| BR-AST-09 | ITS | UC-AST-05 | Item, Loan | TC-AST-09 |
| BR-USR-01 | ITS | UC-USR-03, 04 | User | TC-USR-05 |
| BR-USR-02 | ITS, INS | UC-USR-04 | User | TC-USR-04 |
| BR-USR-03 | ITS | UC-USR-03, 06 | User | TC-USR-B03 |
| BR-USR-04 | ITS | UC-USR-03 | User | TC-USR-03 |
| BR-USR-05 | ITS | UC-USR-04 | User | TC-USR-11 |
| BR-USR-06 | ITS | UC-USR-04 | User | TC-USR-B06 |
| BR-USR-07 | ITS | UC-USR-01 | User | TC-USR-01 |

---

## 12. Validation Checklist

| Criterion | How it was applied | Result / changes |
|---|---|---|
| **Correct** | Each requirement maps to a gathering question and a stakeholder need. | Assumptions A-01–A-05 to be confirmed by IT Supervisor. |
| **Complete** | Every use case has at least one FR; every FR has a use case, class, and test case. | Added FR-AST-14 (loan extension) after spec review. |
| **Clear** | One "shall" statement per requirement; vague words ("fast", "easy") replaced by numbers. | NFR-AST-01/02, NFR-USR-05 given measurable limits. |
| **Consistent** | Checked FRs against BRs and between AST/USR. | Lockout values match in FR-USR-07 and UC-USR-01; loan lengths match in BR-AST-03 and UC-AST-04. |
| **Testable** | Every requirement has a test case ID; Must-Haves have Given/When/Then criteria. | All rows in §11 have a TC. |
| **Feasible** | Scope fits one semester and the team's stack. | SSO (FR-USR-12), reservations (FR-AST-18), photos (FR-AST-19) set to Will Not Have. |
| **In scope** | Kept to AST and USR pages. | Audit log viewing left to RPT; notifications for overdue loans left to NTF. |

---

## 13. Diagrams

- Use case diagram: [`ast-usr-usecases.puml`](ast-usr-usecases.puml) → `ast-usr-usecases.png`
- Class diagram: [`ast-usr-classes.puml`](ast-usr-classes.puml) → `ast-usr-classes.png`
