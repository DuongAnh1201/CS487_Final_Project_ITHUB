Main user role:
The Assets & Lending page as long as the Login & Users page have the following users

Admin user: The IT Supervisor (IT specialists, IT lead, IT manager) who manages accounts and item retirement that a Student Assistant can not handle.
Student Assistant: The lower role that handles daily work: registering items, lending and returning items, issuing supplies. Everything that a student assistant can do also can be done by Admin user.

## User Stories with Guidelines

### Assets & Lending:

| ID User Stories | ID Requirements | User Story | Invest Quality | Priority |
|---|---|---|---|---|
| US-AST-01 | FR-AST-01, FR-AST-02 | As the student assistant, I need to register a new item with a unique asset tag and its details, so that IT knows what equipment it owns and where it is | Independent | Must have |
| US-AST-02 | FR-AST-03 | As the student assistant, I need to edit an item's details, so that the inventory stays accurate when an item moves or was entered wrong | Independent | Must have |
| US-AST-03 | FR-AST-04 | As the student assistant, I need the system to allow me to search and filter items by tag, serial, model, category, location and status, so I can find an item quickly | Independent | Must have |
| US-AST-04 | FR-AST-06 | As the student assistant, I need to record supplies going in and out by quantity, so I always know how many we have | Negotiable | Must have |
| US-AST-05 | FR-AST-08 | As the student assistant, I need to lend out an item and record the borrower, due date and condition, so every lent item can be tracked and returned on time | Valuable | Must have |
| US-AST-06 | FR-AST-09 | As the student assistant, I need to record when an item is returned and its condition, so the loan is closed and the item status is correct | Testable | Must have |
| US-AST-07 | FR-AST-10 | As the admin user, I need to see all overdue loans, so I can follow up on late items | Valuable | Must have |
| US-AST-08 | FR-AST-12 | As the student assistant, I need to mark an item as Lost or Damaged with a description, so nobody lends it out and IT knows it needs attention | Independent | Must have |
| US-AST-09 | FR-AST-13 | As the admin user, I need to retire an item with a reason and date, so old equipment leaves active inventory but its history is kept | Independent | Must have |

### Login & Users:

| ID User Stories | ID Requirements | User Story | Invest Quality | Priority |
|---|---|---|---|---|
| US-USR-01 | FR-USR-01, FR-USR-02 | As the student assistant, I need to log in with my school email and password and log out when I'm done, so only I can act under my account | Testable | Must have |
| US-USR-02 | FR-USR-03 | As the admin user, I need to create accounts for new student assistants, so each person has their own login | Independent | Must have |
| US-USR-03 | FR-USR-04 | As the admin user, I need to change a user's role and deactivate or reactivate their account, so people who leave lose access while their records stay | Independent | Must have |
| US-USR-04 | FR-USR-05 | As the admin user, I need admin-only actions blocked for student assistants, so only I can manage accounts and retire items | Valuable | Must have |
| US-USR-05 | FR-USR-06 | As the admin user, I need every create, update and status change saved with who did it and when, so I can trace any record back to a person | Valuable | Must have |

Note: Loan rules: students can borrow up to 2 items for 7 days, faculty/staff 30 days, and anyone with an overdue item is blocked from borrowing. Password rule: at least 10 characters with letters and digits.

---

## Detailed User Stories (Template)

### EP-AST-01 – Inventory Records

#### US-AST-01 – Register a new item

| Field | Value |
|---|---|
| **Story ID** | US-AST-01 |
| **Title** | Register a new item |
| **Epic** | EP-AST-01 Inventory Records |
| **User Role** | Student Assistant |
| **User Story** | As a Student Assistant, I want to register a new hardware item with its asset tag and details, so that the IT department knows what equipment it owns and where it is. |
| **Priority** | Must |
| **Related Requirement** | FR-AST-01, FR-AST-02, BR-AST-01, NFR-AST-03 |
| **Preconditions** | SA is logged in. The item's category and location exist. |
| **Dependencies** | US-USR-01 |
| **Notes** | Use case: UC-AST-01. Estimate: 3 story points. Classes: `Item`, `Category`, `Location`. Status defaults to Available. |

**Acceptance Criteria**
1. Given the SA fills in asset tag, serial number, model, manufacturer, category, location, purchase date, warranty end date and notes, when they save, then the item is stored with status **Available** and appears in inventory search.
2. Given an item with tag `SFBU-00123` exists, when the SA registers another item with `SFBU-00123`, then the save is rejected with "Asset tag already exists".
3. Given a **Retired** item has tag `SFBU-00050`, when the SA registers a new item with `SFBU-00050`, then the save is rejected (tags are never reused).
4. Given a required field (asset tag, serial number, category, location) is empty, when the SA saves, then an inline error appears next to that field and nothing is saved.
5. Given the item is saved, when anyone views the item, then it shows which SA added it and when.

#### US-AST-02 – Edit item details

| Field | Value |
|---|---|
| **Story ID** | US-AST-02 |
| **Title** | Edit item details |
| **Epic** | EP-AST-01 Inventory Records |
| **User Role** | Student Assistant |
| **User Story** | As a Student Assistant, I want to update an item's details, so that the inventory stays accurate when an item moves or a record was entered wrong. |
| **Priority** | Must |
| **Related Requirement** | FR-AST-03, BR-AST-01, BR-AST-08 |
| **Preconditions** | SA is logged in. The item exists and is not Retired. |
| **Dependencies** | US-AST-01 |
| **Notes** | Use case: UC-AST-02. Estimate: 2 story points. Classes: `Item`. Status changes go through the lending, incident and retire stories, not this edit form. |

**Acceptance Criteria**
1. Given an Available item, when the SA changes its location and saves, then the new location is shown on the item and in search results.
2. Given the SA changes the asset tag to one that already exists, when they save, then the save is rejected with "Asset tag already exists".
3. Given a **Retired** item, when the SA opens it, then all fields are read-only and there is no Save button.
4. Given the edit is saved, when anyone views the item, then it shows which SA last changed it and when.

#### US-AST-03 – Search and filter inventory

| Field | Value |
|---|---|
| **Story ID** | US-AST-03 |
| **Title** | Search and filter inventory |
| **Epic** | EP-AST-01 Inventory Records |
| **User Role** | Student Assistant, Admin |
| **User Story** | As a Student Assistant, I want to search and filter items by tag, serial, model, category, location and status, so that I can find a specific item or see what is available quickly. |
| **Priority** | Must |
| **Related Requirement** | FR-AST-04 |
| **Preconditions** | User is logged in. Inventory has items. |
| **Dependencies** | US-AST-01 |
| **Notes** | Use case: UC-AST-03. Estimate: 3 story points. Classes: `Item`. |

**Acceptance Criteria**
1. Given an item with serial `5CG1234XYZ`, when the user searches `5CG1234`, then that item is in the results.
2. Given the user filters Category = Laptop and Status = Available, when results load, then only Available laptops are listed.
3. Given no item matches, when the search runs, then the page shows "No items found" instead of an empty table.

---

### EP-AST-02 – Consumable Stock

#### US-AST-04 – Issue and restock consumables

| Field | Value |
|---|---|
| **Story ID** | US-AST-04 |
| **Title** | Issue and restock consumables |
| **Epic** | EP-AST-02 Consumable Stock |
| **User Role** | Student Assistant |
| **User Story** | As a Student Assistant, I want to record supplies going in and out by quantity, so that we always know how many cables, adapters and toner we have. |
| **Priority** | Must |
| **Related Requirement** | FR-AST-06, BR-AST-06, BR-AST-07 |
| **Preconditions** | SA is logged in. The consumable exists. |
| **Dependencies** | US-USR-01 |
| **Notes** | Use case: UC-AST-07. Estimate: 3 story points. Classes: `Consumable`, `StockTransaction`. Consumables are issued, never lent or returned. |

**Acceptance Criteria**
1. Given HDMI cables have quantity 20, when the SA issues 3 to "Room 204", then quantity becomes 17 and the record shows the quantity, recipient, SA and time.
2. Given quantity 17, when the SA restocks 10, then quantity becomes 27 and the restock is recorded.
3. Given quantity 2, when the SA tries to issue 5, then the action is rejected with "Not enough stock" and quantity stays 2.
4. Given a consumable, when the SA opens it, then there is no Lend Out option.

---

### EP-AST-03 – Lending

#### US-AST-05 – Lend out an item

| Field | Value |
|---|---|
| **Story ID** | US-AST-05 |
| **Title** | Lend out an item |
| **Epic** | EP-AST-03 Lending |
| **User Role** | Student Assistant |
| **User Story** | As a Student Assistant, I want to check out an item to a borrower and record who has it and when it is due, so that every lent item can be tracked and returned on time. |
| **Priority** | Must |
| **Related Requirement** | FR-AST-08, BR-AST-02, BR-AST-03, BR-AST-04, BR-AST-05 |
| **Preconditions** | SA is logged in. Item exists. |
| **Dependencies** | US-AST-01, US-USR-01 |
| **Notes** | Use case: UC-AST-04. Estimate: 8 story points. Classes: `Loan`, `Borrower`, `Item`. Borrowers don't log in; the SA records the loan for them. |

**Acceptance Criteria**
1. Given an Available item and an eligible student, when the SA enters the asset tag, borrower school ID, name, email, type and condition out and confirms, then a loan is created with due date = today + 7 days, the item becomes **On Loan**, and the loan shows which SA processed it.
2. Given an eligible faculty or staff borrower, when the loan is created, then the default due date is today + 30 days.
3. Given the item is On Loan, Damaged, Lost or Retired, when the SA enters its tag, then checkout is blocked and the item's current status is shown.
4. Given the borrower has an overdue loan, when the SA tries to check out to them, then checkout is blocked and the overdue item is listed.
5. Given a student already holds 2 items, when the SA tries to lend a third, then checkout is blocked with "Borrowing limit reached".
6. Given the SA sets a due date beyond the maximum loan length for the borrower type, then the date is rejected.

#### US-AST-06 – Record an item return

| Field | Value |
|---|---|
| **Story ID** | US-AST-06 |
| **Title** | Record an item return |
| **Epic** | EP-AST-03 Lending |
| **User Role** | Student Assistant |
| **User Story** | As a Student Assistant, I want to record when a lent item comes back and its condition, so that the loan is closed and the item's status is correct. |
| **Priority** | Must |
| **Related Requirement** | FR-AST-09, BR-AST-09 |
| **Preconditions** | SA is logged in. The item has an open loan. |
| **Dependencies** | US-AST-05 |
| **Notes** | Use case: UC-AST-05. Estimate: 3 story points. Classes: `Loan`, `Item`. Loan records are kept, never deleted (NFR-AST-04). |

**Acceptance Criteria**
1. Given an open loan, when the SA records the return with condition **Good**, then the loan is closed with today's return date and the item becomes **Available**.
2. Given an open loan, when the SA records condition **Damaged** with a note, then the loan is closed and the item becomes **Damaged**, not Available.
3. Given the return is saved, then the loan shows which SA received it and when.
4. Given an item with no open loan, when the SA tries to return it, then the system shows "No open loan for this item".

#### US-AST-07 – View overdue loans

| Field | Value |
|---|---|
| **Story ID** | US-AST-07 |
| **Title** | View overdue loans |
| **Epic** | EP-AST-03 Lending |
| **User Role** | Student Assistant, Admin |
| **User Story** | As the IT Supervisor, I want to see which loans are overdue, so that I can follow up on late items. |
| **Priority** | Must |
| **Related Requirement** | FR-AST-10 |
| **Preconditions** | User is logged in. |
| **Dependencies** | US-AST-05, US-AST-06 |
| **Notes** | Use case: UC-AST-06. Estimate: 2 story points. Classes: `Loan`, `Borrower`. Sending overdue reminders is owned by the Notifications page. |

**Acceptance Criteria**
1. Given a loan due yesterday that is not returned, when the user opens Overdue Loans, then it is listed with borrower name, contact, item, due date and days overdue.
2. Given a loan due today, when the user opens Overdue Loans, then it is **not** listed.
3. Given a returned loan, then it never appears in Overdue Loans.

---

### EP-AST-04 – Item Lifecycle

#### US-AST-08 – Report an item lost or damaged

| Field | Value |
|---|---|
| **Story ID** | US-AST-08 |
| **Title** | Report an item lost or damaged |
| **Epic** | EP-AST-04 Item Lifecycle |
| **User Role** | Student Assistant |
| **User Story** | As a Student Assistant, I want to mark an item as Lost or Damaged with a description, so that nobody lends it out and IT knows it needs attention. |
| **Priority** | Must |
| **Related Requirement** | FR-AST-12, BR-AST-02 |
| **Preconditions** | SA is logged in. Item exists and is not Retired. |
| **Dependencies** | US-AST-01 |
| **Notes** | Use case: UC-AST-08. Estimate: 3 story points. Classes: `ItemIncident`, `Item`, `Loan`. |

**Acceptance Criteria**
1. Given an Available item, when the SA reports it **Damaged** with a description and date, then the item becomes Damaged and the report shows which SA filed it and when.
2. Given an item On Loan, when the SA reports it **Lost**, then the item becomes Lost and its open loan is marked Lost.
3. Given the description is empty, when the SA submits, then an inline error asks for a description.
4. Given an item is Lost or Damaged, when an SA tries to lend it, then checkout is blocked.

#### US-AST-09 – Retire an item

| Field | Value |
|---|---|
| **Story ID** | US-AST-09 |
| **Title** | Retire an item |
| **Epic** | EP-AST-04 Item Lifecycle |
| **User Role** | Admin |
| **User Story** | As the IT Supervisor, I want to retire an item with a reason and date, so that disposed or obsolete equipment leaves active inventory but its history is kept. |
| **Priority** | Must |
| **Related Requirement** | FR-AST-13, BR-AST-01, BR-AST-08, NFR-AST-04 |
| **Preconditions** | Admin is logged in. Item has no open loan. |
| **Dependencies** | US-USR-04 |
| **Notes** | Use case: UC-AST-09. Estimate: 2 story points. Classes: `ItemIncident`, `Item`. |

**Acceptance Criteria**
1. Given an Available or Damaged item, when the Admin retires it with a reason and date, then its status becomes **Retired** and the reason and date are saved.
2. Given an item with an open loan, when the Admin tries to retire it, then the action is blocked until the item is returned.
3. Given a Retired item, then it is read-only, cannot be lent, and its loan history is still viewable.
4. Given an SA is logged in, then the Retire option is not available to them.

---

### EP-USR-01 – Authentication

#### US-USR-01 – Log in and log out

| Field | Value |
|---|---|
| **Story ID** | US-USR-01 |
| **Title** | Log in and log out |
| **Epic** | EP-USR-01 Authentication |
| **User Role** | Student Assistant, Admin |
| **User Story** | As a Student Assistant, I want to log in with my school email and password and log out when I'm done, so that only I can act under my account. |
| **Priority** | Must |
| **Related Requirement** | FR-USR-01, FR-USR-02, BR-USR-07, NFR-USR-01 |
| **Preconditions** | User has an active account. |
| **Dependencies** | US-USR-02 |
| **Notes** | Use case: UC-USR-01, UC-USR-02. Estimate: 3 story points. Classes: `User`. |

**Acceptance Criteria**
1. Given an active user with correct credentials, when they log in, then they reach the dashboard for their role.
2. Given a wrong password or unknown email, when they log in, then they see "Invalid email or password" (same message for both) and they stay on the login page.
3. Given a deactivated account, when the user enters correct credentials, then login is refused.
4. Given a logged-in user, when they click Log out, then they return to the login page and pressing Back does not show any inventory pages.

---

### EP-USR-02 – Account Administration

#### US-USR-02 – Create a user account

| Field | Value |
|---|---|
| **Story ID** | US-USR-02 |
| **Title** | Create a user account |
| **Epic** | EP-USR-02 Account Administration |
| **User Role** | Admin |
| **User Story** | As the IT Supervisor, I want to create accounts for new student assistants, so that each person who works the desk has their own login. |
| **Priority** | Must |
| **Related Requirement** | FR-USR-03, BR-USR-01, BR-USR-03, BR-USR-04 |
| **Preconditions** | Admin is logged in. |
| **Dependencies** | US-USR-01 |
| **Notes** | Use case: UC-USR-03. Estimate: 3 story points. Classes: `User`, `Role`. |

**Acceptance Criteria**
1. Given the Admin enters full name, school email, school ID, role, a password and an optional access end date, when they save, then an **Active** account is created.
2. Given an account with that school email or school ID already exists, then the save is rejected (one account per person).
3. Given the password is under 10 characters or lacks both letters and digits, then it is rejected with the password rule shown.
4. Given an SA is logged in, then they cannot open the Create User page.

#### US-USR-03 – Change a user's role or status

| Field | Value |
|---|---|
| **Story ID** | US-USR-03 |
| **Title** | Change a user's role or status |
| **Epic** | EP-USR-02 Account Administration |
| **User Role** | Admin |
| **User Story** | As the IT Supervisor, I want to change a user's role and deactivate or reactivate their account, so that people who leave lose access while their past actions stay on record. |
| **Priority** | Must |
| **Related Requirement** | FR-USR-04, BR-USR-02, BR-USR-05, BR-USR-06 |
| **Preconditions** | Admin is logged in. Target account exists. |
| **Dependencies** | US-USR-02 |
| **Notes** | Use case: UC-USR-04. Estimate: 3 story points. Classes: `User`. There is no delete; accounts are only deactivated. |

**Acceptance Criteria**
1. Given an active SA, when the Admin deactivates them, then the account becomes **Inactive** and that user cannot log in.
2. Given an inactive account, when the Admin reactivates it, then the user can log in again.
3. Given only one active Admin exists, when anyone tries to deactivate or demote that Admin, then the action is blocked with "At least one active Admin is required".
4. Given a deactivated user, then records they created still show their name.
5. Given the user management page, then there is no Delete option.

---

### EP-USR-03 – Access Control & Accountability

#### US-USR-04 – Restrict actions by role

| Field | Value |
|---|---|
| **Story ID** | US-USR-04 |
| **Title** | Restrict actions by role |
| **Epic** | EP-USR-03 Access Control & Accountability |
| **User Role** | Admin |
| **User Story** | As the IT Supervisor, I want admin-only actions blocked for student assistants, so that only I can manage accounts and retire items. |
| **Priority** | Must |
| **Related Requirement** | FR-USR-05, BR-USR-01, BR-AST-08 |
| **Preconditions** | Roles Admin and Student Assistant exist. |
| **Dependencies** | US-USR-01 |
| **Notes** | Use case: UC-USR-01. Estimate: 3 story points. Classes: `User`, `Role`. Admin-only: create users, change roles, deactivate accounts, retire items. |

**Acceptance Criteria**
1. Given an SA is logged in, then admin-only menu items are hidden.
2. Given an SA tries to open an admin-only page by any route, then they see an access-denied message and nothing changes.
3. Given an Admin is logged in, then they can do every SA action plus the admin-only actions.
4. Given a user's role is changed, then the new permissions apply from their next action.

#### US-USR-05 – Tie every change to the user who made it

| Field | Value |
|---|---|
| **Story ID** | US-USR-05 |
| **Title** | Tie every change to the user who made it |
| **Epic** | EP-USR-03 Access Control & Accountability |
| **User Role** | Admin |
| **User Story** | As the IT Supervisor, I want every create, update and status change recorded with who did it and when, so that I can trace any record back to a person. |
| **Priority** | Must |
| **Related Requirement** | FR-USR-06, BR-USR-04 |
| **Preconditions** | User is logged in. |
| **Dependencies** | US-USR-01 |
| **Notes** | Use case: All AST and USR use cases. Estimate: 5 story points. Classes: `AuditLogEntry`, `User`. Viewing and filtering the full audit log belongs to the Reports & Audit page. |

**Acceptance Criteria**
1. Given an SA creates, edits, lends, returns or reports an item, then the change is recorded with their name, what they did, which record, and when.
2. Given an Admin changes a user's role or status, then that change is recorded the same way.
3. Given any item, when the Admin opens its history, then each change shows who made it and when.
4. Given an action fails validation, then nothing is recorded.

---

## Story Refinement Check

| Step | How it was applied |
|---|---|
| Clear role, goal and benefit | Every story uses "As a … I want … so that …" with a real role (SA or Admin). |
| One main goal | Each story covers one user goal. FR-AST-01/02 and FR-USR-01/02 were merged because they belong to the same action. |
| Business rules in criteria | Loan limits, loan lengths, overdue block and password rules are acceptance criteria, not notes. |
| Measurable criteria | Every criterion is Given/When/Then with concrete values. |
| Dependencies stated | Each story lists the stories it needs first. |
| Priority assigned | Only Must Have stories are included. Should/Could requirements are left for a later version. |
| Effort estimated | Every story has a story-point estimate in Notes (1 point ≈ half a day). Total: 46 points. |
| Linked to use case and requirement | Every story names its SP2 use case in Notes and its FRs in Related Requirement. |

## INVEST Checklist

| Story | I | N | V | E | S | T | Note |
|---|---|---|---|---|---|---|---|
| US-AST-01 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | |
| US-AST-02 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | |
| US-AST-03 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | |
| US-AST-04 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | |
| US-AST-05 | ~ | ✓ | ✓ | ✓ | ~ | ✓ | Largest story; can split into "checkout" and "eligibility checks". |
| US-AST-06 | ~ | ✓ | ✓ | ✓ | ✓ | ✓ | Needs US-AST-05. |
| US-AST-07 | ~ | ✓ | ✓ | ✓ | ✓ | ✓ | Needs loan data. |
| US-AST-08 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | |
| US-AST-09 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | |
| US-USR-01 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | |
| US-USR-02 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | |
| US-USR-03 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | |
| US-USR-04 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | |
| US-USR-05 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | |

✓ = met · ~ = met with a noted dependency or size risk

## Definition of Done

A user story is complete when:
- The required functionality has been implemented.
- The code follows the project's object-oriented design.
- Input validation has been added: invalid input shows an inline error and saves nothing.
- Every acceptance criterion has been tested, including a failing case for each business rule (loan limits, overdue block, password rules).
- The change is recorded with the user and time (US-USR-05).
- An SA cannot reach admin-only features by any route.
- Related classes and UML diagrams are updated if necessary.
- The feature does not introduce known errors.
- The project team and supervisor accept the result.
