Main user role:
The Assets & Lending page as long as the Login & Users page have the following users

Admin user: The IT Supervisor (IT specialists, IT lead, IT manager) who manages accounts, categories and item retirement that a Student Assistant can not handle.
Student Assistant: The lower role that handles daily work: registering items, lending and returning items, issuing supplies. Everything that a student assistant can do also can be done by Admin user.

## User Stories with Guidelines

### Assets & Lending:

| ID User Stories | ID Requirements | User Story | Invest Quality | Priority |
|---|---|---|---|---|
| US-AST-01 | FR-AST-01, FR-AST-02 | As the student assistant, I need to register a new item with a unique asset tag and its details, so that IT knows what equipment it owns and where it is | Independent | Must have |
| US-AST-02 | FR-AST-03 | As the student assistant, I need to edit an item's details, so that the inventory stays accurate when an item moves or was entered wrong | Independent | Must have |
| US-AST-03 | FR-AST-04 | As the student assistant, I need the system to allow me to search and filter items by tag, serial, model, category, location and status, so I can find an item quickly | Independent | Must have |
| US-AST-04 | FR-AST-05 | As the admin user, I need to add and rename item categories, so that every item is grouped the same way | Independent | Should have |
| US-AST-05 | FR-AST-06, FR-AST-07 | As the student assistant, I need to record supplies going in and out by quantity and see a low-stock flag, so I know when to reorder | Negotiable | Must have |
| US-AST-06 | FR-AST-08 | As the student assistant, I need to lend out an item and record the borrower, due date and condition, so every lent item can be tracked and returned on time | Valuable | Must have |
| US-AST-07 | FR-AST-09 | As the student assistant, I need to record when an item is returned and its condition, so the loan is closed and the item status is correct | Testable | Must have |
| US-AST-08 | FR-AST-10, FR-AST-11 | As the admin user, I need to see overdue loans and the loan history of an item or borrower, so I can follow up on late items | Valuable | Must have |
| US-AST-09 | FR-AST-14 | As the student assistant, I need to extend a loan's due date once, so a borrower can keep an item longer without re-borrowing it | Small | Should have |
| US-AST-10 | FR-AST-12 | As the student assistant, I need to mark an item as Lost or Damaged with a description, so nobody lends it out and IT knows it needs attention | Independent | Must have |
| US-AST-11 | FR-AST-13 | As the admin user, I need to retire an item with a reason and date, so old equipment leaves active inventory but its history is kept | Independent | Must have |

### Login & Users:

| ID User Stories | ID Requirements | User Story | Invest Quality | Priority |
|---|---|---|---|---|
| US-USR-01 | FR-USR-01, FR-USR-02, FR-USR-07 | As the student assistant, I need to log in with my school email and password and log out when I'm done, and the account should lock after too many failed tries, so only I can act under my account | Testable | Must have |
| US-USR-02 | FR-USR-03 | As the admin user, I need to create accounts for new student assistants, so each person has their own login | Independent | Must have |
| US-USR-03 | FR-USR-04 | As the admin user, I need to change a user's role and deactivate or reactivate their account, so people who leave lose access while their records stay | Independent | Must have |
| US-USR-04 | FR-USR-05 | As the admin user, I need admin-only actions blocked for student assistants, so only I can manage accounts, categories and retirements | Valuable | Must have |
| US-USR-05 | FR-USR-06 | As the admin user, I need every create, update and status change saved with who did it and when, so I can trace any record back to a person | Valuable | Must have |
| US-USR-06 | FR-USR-08 | As the student assistant, I need to change my own password, so I can keep my account secure | Small | Should have |
| US-USR-07 | FR-USR-09 | As the admin user, I need to reset a user's forgotten password to a temporary one, so they can log back in and must set a new one | Negotiable | Should have |

Note: Loan rules: students can borrow up to 2 items for 7 days, faculty/staff 30 days, one 7-day extension, and anyone with an overdue item is blocked from borrowing. Login rules: the account locks for 15 minutes after 5 failed tries, and passwords are at least 10 characters with letters and digits.

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
| **Dependencies** | US-USR-01 (login), US-AST-04 (categories) |
| **Notes** | Classes: `Item`, `Category`, `Location`. Status defaults to Available. |

**Acceptance Criteria**
1. Given the SA fills in asset tag, serial number, model, manufacturer, category, location, purchase date, warranty end date and notes, when they save, then the item is stored with status **Available** and appears in inventory search.
2. Given an item with tag `SFBU-00123` exists, when the SA registers another item with `SFBU-00123`, then the save is rejected with "Asset tag already exists".
3. Given a **Retired** item has tag `SFBU-00050`, when the SA registers a new item with `SFBU-00050`, then the save is rejected (tags are never reused).
4. Given a required field (asset tag, serial number, category, location) is empty, when the SA saves, then an inline error appears next to that field and nothing is saved.
5. Given the item is saved, then the record stores the SA's user ID and a timestamp.

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
| **Notes** | Classes: `Item`. Status changes go through lending, incident and retire stories, not this edit form. |

**Acceptance Criteria**
1. Given an Available item, when the SA changes its location and saves, then the new location is shown on the item and in search results.
2. Given the SA changes the asset tag to one that already exists, when they save, then the save is rejected with "Asset tag already exists".
3. Given a **Retired** item, when the SA opens it, then all fields are read-only and there is no Save button.
4. Given the edit is saved, then `updatedBy` and `updatedAt` hold the SA's user ID and the time of the change.

#### US-AST-03 – Search and filter inventory

| Field | Value |
|---|---|
| **Story ID** | US-AST-03 |
| **Title** | Search and filter inventory |
| **Epic** | EP-AST-01 Inventory Records |
| **User Role** | Student Assistant, Admin |
| **User Story** | As a Student Assistant, I want to search and filter items by tag, serial, model, category, location and status, so that I can find a specific item or see what is available quickly. |
| **Priority** | Must |
| **Related Requirement** | FR-AST-04, NFR-AST-01 |
| **Preconditions** | User is logged in. Inventory has items. |
| **Dependencies** | US-AST-01 |
| **Notes** | Classes: `Item`. CSV export (FR-AST-15) is a later Could/Should item. |

**Acceptance Criteria**
1. Given an item with serial `5CG1234XYZ`, when the user searches `5CG1234`, then that item is in the results.
2. Given the user filters Category = Laptop and Status = Available, when results load, then only Available laptops are listed.
3. Given no item matches, when the search runs, then the page shows "No items found" instead of an empty table.
4. Given 5,000 items in the database, when the user runs a search, then results appear within 2 seconds.

#### US-AST-04 – Manage item categories

| Field | Value |
|---|---|
| **Story ID** | US-AST-04 |
| **Title** | Manage item categories |
| **Epic** | EP-AST-01 Inventory Records |
| **User Role** | Admin |
| **User Story** | As the IT Supervisor, I want to add and rename item categories, so that every item is grouped consistently (Desktop, Laptop, Monitor, Network Device, Peripheral, Supply). |
| **Priority** | Should |
| **Related Requirement** | FR-AST-05 |
| **Preconditions** | Admin is logged in. |
| **Dependencies** | US-USR-04 (role restriction) |
| **Notes** | Classes: `Category` (`isConsumable` marks supply categories). |

**Acceptance Criteria**
1. Given the Admin adds category "Docking Station", when they save, then it appears in the category list on the Register Item form.
2. Given a category named "Laptop" exists, when the Admin adds another "Laptop", then the save is rejected with "Category already exists".
3. Given a category is used by at least one item, when the Admin tries to delete it, then the delete is blocked and the item count is shown.
4. Given an SA is logged in, when they open category management, then they get an access-denied message.

---

### EP-AST-02 – Consumable Stock

#### US-AST-05 – Issue and restock consumables

| Field | Value |
|---|---|
| **Story ID** | US-AST-05 |
| **Title** | Issue and restock consumables |
| **Epic** | EP-AST-02 Consumable Stock |
| **User Role** | Student Assistant |
| **User Story** | As a Student Assistant, I want to record supplies going in and out by quantity, so that we know how many cables, adapters and toner we have and when to reorder. |
| **Priority** | Must |
| **Related Requirement** | FR-AST-06, FR-AST-07, BR-AST-06, BR-AST-07 |
| **Preconditions** | SA is logged in. The consumable exists with a reorder threshold. |
| **Dependencies** | US-AST-04 |
| **Notes** | Classes: `Consumable`, `StockTransaction`. Consumables are issued, never lent or returned. Low-stock alerts to people are owned by the Notifications page. |

**Acceptance Criteria**
1. Given HDMI cables have quantity 20, when the SA issues 3 to "Room 204", then quantity becomes 17 and an OUT transaction stores the quantity, recipient, SA and timestamp.
2. Given quantity 17, when the SA restocks 10, then quantity becomes 27 and an IN transaction is stored.
3. Given quantity 2, when the SA tries to issue 5, then the action is rejected with "Not enough stock" and quantity stays 2.
4. Given a reorder threshold of 5, when quantity drops to 5 or below, then the consumable shows a **Low stock** flag in the list.
5. Given a consumable, when the SA opens it, then there is no Lend Out option.

---

### EP-AST-03 – Lending

#### US-AST-06 – Lend out an item

| Field | Value |
|---|---|
| **Story ID** | US-AST-06 |
| **Title** | Lend out an item |
| **Epic** | EP-AST-03 Lending |
| **User Role** | Student Assistant |
| **User Story** | As a Student Assistant, I want to check out an item to a borrower and record who has it and when it is due, so that every lent item can be tracked and returned on time. |
| **Priority** | Must |
| **Related Requirement** | FR-AST-08, BR-AST-02, BR-AST-03, BR-AST-04, BR-AST-05, NFR-AST-02 |
| **Preconditions** | SA is logged in. Item exists. |
| **Dependencies** | US-AST-01, US-USR-01 |
| **Notes** | Classes: `Loan`, `Borrower`, `Item`. Based on UC-AST-04. Borrowers don't log in; the SA records the loan for them. |

**Acceptance Criteria**
1. Given an Available item and an eligible student, when the SA enters the asset tag, borrower school ID, name, email, type and condition out and confirms, then a loan is created with due date = today + 7 days, the item becomes **On Loan**, and the SA's ID is stored on the loan.
2. Given an eligible faculty or staff borrower, when the loan is created, then the default due date is today + 30 days.
3. Given the item is On Loan, Damaged, Lost or Retired, when the SA enters its tag, then checkout is blocked and the item's current status is shown.
4. Given the borrower has an overdue loan, when the SA tries to check out to them, then checkout is blocked and the overdue item is listed.
5. Given a student already holds 2 items, when the SA tries to lend a third, then checkout is blocked with "Borrowing limit reached".
6. Given the SA sets a due date beyond the maximum loan length for the borrower type, then the date is rejected.
7. Given a returning borrower's school ID, when entered, then their saved name, email and type are filled in.
8. Given a trained SA, the full checkout takes under 1 minute and no more than 3 screens.

#### US-AST-07 – Record an item return

| Field | Value |
|---|---|
| **Story ID** | US-AST-07 |
| **Title** | Record an item return |
| **Epic** | EP-AST-03 Lending |
| **User Role** | Student Assistant |
| **User Story** | As a Student Assistant, I want to record when a lent item comes back and its condition, so that the loan is closed and the item's status is correct. |
| **Priority** | Must |
| **Related Requirement** | FR-AST-09, BR-AST-09 |
| **Preconditions** | SA is logged in. The item has an open loan. |
| **Dependencies** | US-AST-06 |
| **Notes** | Classes: `Loan`, `Item`. Loan records are kept, never deleted (NFR-AST-04). |

**Acceptance Criteria**
1. Given an open loan, when the SA records the return with condition **Good**, then the loan is closed with today's return date and the item becomes **Available**.
2. Given an open loan, when the SA records condition **Damaged** with a note, then the loan is closed and the item becomes **Damaged**, not Available.
3. Given the return is saved, then the loan stores the SA who received it and the timestamp.
4. Given an item with no open loan, when the SA tries to return it, then the system shows "No open loan for this item".

#### US-AST-08 – View overdue loans and loan history

| Field | Value |
|---|---|
| **Story ID** | US-AST-08 |
| **Title** | View overdue loans and loan history |
| **Epic** | EP-AST-03 Lending |
| **User Role** | Student Assistant, Admin |
| **User Story** | As the IT Supervisor, I want to see which loans are overdue and the loan history of an item or borrower, so that I can follow up on late items and see who had an item last. |
| **Priority** | Must |
| **Related Requirement** | FR-AST-10 (M), FR-AST-11 (S) |
| **Preconditions** | User is logged in. |
| **Dependencies** | US-AST-06, US-AST-07 |
| **Notes** | Classes: `Loan`, `Borrower`. Sending overdue reminders is owned by the Notifications page. |

**Acceptance Criteria**
1. Given a loan due yesterday that is not returned, when the user opens Overdue Loans, then it is listed with borrower name, contact, item, due date and days overdue.
2. Given a loan due today, when the user opens Overdue Loans, then it is **not** listed.
3. Given a returned loan, then it never appears in Overdue Loans.
4. Given an item with 3 past loans, when the user opens its history, then all 3 loans appear newest first with borrower, dates and conditions.
5. Given a borrower school ID, when the user opens their history, then all their loans, open and closed, are listed.

#### US-AST-09 – Extend a loan

| Field | Value |
|---|---|
| **Story ID** | US-AST-09 |
| **Title** | Extend a loan |
| **Epic** | EP-AST-03 Lending |
| **User Role** | Student Assistant |
| **User Story** | As a Student Assistant, I want to extend a borrower's due date once, so that they can keep an item a little longer without returning and re-borrowing it. |
| **Priority** | Should |
| **Related Requirement** | FR-AST-14, BR-AST-03 |
| **Preconditions** | SA is logged in. The loan is open and not yet extended. |
| **Dependencies** | US-AST-06 |
| **Notes** | Classes: `Loan` (`extended` flag). |

**Acceptance Criteria**
1. Given an open, unextended loan, when the SA extends it, then the due date moves forward by up to 7 days and the loan is marked extended.
2. Given a loan already extended once, when the SA tries again, then the action is blocked with "Loan already extended".
3. Given the SA enters an extension longer than 7 days, then it is rejected.
4. Given the extension is saved, then the SA and timestamp are recorded on the loan.

---

### EP-AST-04 – Item Lifecycle

#### US-AST-10 – Report an item lost or damaged

| Field | Value |
|---|---|
| **Story ID** | US-AST-10 |
| **Title** | Report an item lost or damaged |
| **Epic** | EP-AST-04 Item Lifecycle |
| **User Role** | Student Assistant |
| **User Story** | As a Student Assistant, I want to mark an item as Lost or Damaged with a description, so that nobody lends it out and IT knows it needs attention. |
| **Priority** | Must |
| **Related Requirement** | FR-AST-12, BR-AST-02 |
| **Preconditions** | SA is logged in. Item exists and is not Retired. |
| **Dependencies** | US-AST-01 |
| **Notes** | Classes: `ItemIncident`, `Item`, `Loan`. |

**Acceptance Criteria**
1. Given an Available item, when the SA reports it **Damaged** with a description and date, then the item becomes Damaged and an incident record is saved with the SA and timestamp.
2. Given an item On Loan, when the SA reports it **Lost**, then the item becomes Lost and its open loan is marked Lost.
3. Given the description is empty, when the SA submits, then an inline error asks for a description.
4. Given an item is Lost or Damaged, when an SA tries to lend it, then checkout is blocked.

#### US-AST-11 – Retire an item

| Field | Value |
|---|---|
| **Story ID** | US-AST-11 |
| **Title** | Retire an item |
| **Epic** | EP-AST-04 Item Lifecycle |
| **User Role** | Admin |
| **User Story** | As the IT Supervisor, I want to retire an item with a reason and date, so that disposed or obsolete equipment leaves active inventory but its history is kept. |
| **Priority** | Must |
| **Related Requirement** | FR-AST-13, BR-AST-01, BR-AST-08, NFR-AST-04 |
| **Preconditions** | Admin is logged in. Item has no open loan. |
| **Dependencies** | US-USR-04 |
| **Notes** | Classes: `ItemIncident` (type RETIRED), `Item`. |

**Acceptance Criteria**
1. Given an Available or Damaged item, when the Admin retires it with a reason and date, then its status becomes **Retired** and an incident record is saved.
2. Given an item with an open loan, when the Admin tries to retire it, then the action is blocked until the item is returned.
3. Given a Retired item, then it is read-only, cannot be lent, and its loan history is still viewable.
4. Given an SA is logged in, then the Retire option is not shown and a direct request is denied.

---

### EP-USR-01 – Authentication

#### US-USR-01 – Log in and log out securely

| Field | Value |
|---|---|
| **Story ID** | US-USR-01 |
| **Title** | Log in and log out securely |
| **Epic** | EP-USR-01 Authentication |
| **User Role** | Student Assistant, Admin |
| **User Story** | As a Student Assistant, I want to log in with my school email and password and log out when I'm done, so that only I can act under my account. |
| **Priority** | Must |
| **Related Requirement** | FR-USR-01 (M), FR-USR-02 (M), FR-USR-07 (S), BR-USR-07, NFR-USR-01, NFR-USR-03, NFR-USR-04 |
| **Preconditions** | User has an active account. |
| **Dependencies** | US-USR-02 |
| **Notes** | Classes: `User` (`failedLoginCount`, `lockedUntil`, `lastLoginAt`). Based on UC-USR-01. |

**Acceptance Criteria**
1. Given an active user with correct credentials, when they log in, then they reach the dashboard for their role and `lastLoginAt` is updated.
2. Given a wrong password or unknown email, when they log in, then they see "Invalid email or password" (same message for both) and no session is created.
3. Given 4 failed attempts in a row, when the 5th attempt fails, then the account is locked for 15 minutes, even if the next attempt uses the right password.
4. Given a locked account, when 15 minutes pass, then the user can log in again and the failed count resets.
5. Given a successful login, then the failed count resets to 0.
6. Given a deactivated account, when the user enters correct credentials, then login is refused.
7. Given a logged-in user, when they click Log out, then the session ends and the browser Back button does not show protected pages.
8. Given 30 minutes of inactivity, then the session expires and the user is sent to the login page.

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
| **Notes** | Classes: `User`, `Role`. New accounts get a temporary password that must be changed at first login. |

**Acceptance Criteria**
1. Given the Admin enters full name, school email, school ID, role and an optional access end date, when they save, then an **Active** account is created.
2. Given an account with that school email or school ID already exists, then the save is rejected (one account per person).
3. Given the initial password is under 10 characters or lacks both letters and digits, then it is rejected with the password rule shown.
4. Given the new user logs in the first time, then they must set a new password before continuing.
5. Given an SA is logged in, then they cannot open the Create User page.

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
| **Notes** | Classes: `User`. There is no delete; accounts are only deactivated. |

**Acceptance Criteria**
1. Given an active SA, when the Admin deactivates them, then the account becomes **Inactive** and that user cannot log in.
2. Given the user is logged in when deactivated, then their next request ends the session.
3. Given an inactive account, when the Admin reactivates it, then the user can log in again.
4. Given only one active Admin exists, when anyone tries to deactivate or demote that Admin, then the action is blocked with "At least one active Admin is required".
5. Given a deactivated user, then records they created still show their name.
6. Given the user management page, then there is no Delete option.

#### US-USR-07 – Reset a user's password

| Field | Value |
|---|---|
| **Story ID** | US-USR-07 |
| **Title** | Reset a user's password |
| **Epic** | EP-USR-02 Account Administration |
| **User Role** | Admin |
| **User Story** | As the IT Supervisor, I want to reset a user's forgotten password to a temporary one, so that they can get back in without me knowing their real password. |
| **Priority** | Should |
| **Related Requirement** | FR-USR-09, BR-USR-03 |
| **Preconditions** | Admin is logged in. Target account is Active. |
| **Dependencies** | US-USR-02 |
| **Notes** | Classes: `User` (`mustChangePassword`). |

**Acceptance Criteria**
1. Given an active user, when the Admin resets their password, then a temporary password that meets the password rules is shown once to the Admin.
2. Given the user logs in with the temporary password, then they must set a new password before reaching any other page.
3. Given the reset, then the user's old password no longer works.
4. Given a locked account, when the Admin resets the password, then the lock is cleared.

---

### EP-USR-03 – Access Control & Accountability

#### US-USR-04 – Restrict actions by role

| Field | Value |
|---|---|
| **Story ID** | US-USR-04 |
| **Title** | Restrict actions by role |
| **Epic** | EP-USR-03 Access Control & Accountability |
| **User Role** | Admin |
| **User Story** | As the IT Supervisor, I want admin-only actions blocked for student assistants, so that only I can manage accounts, categories and retirements. |
| **Priority** | Must |
| **Related Requirement** | FR-USR-05, BR-USR-01, BR-AST-08 |
| **Preconditions** | Roles Admin and Student Assistant exist. |
| **Dependencies** | US-USR-01 |
| **Notes** | Classes: `User`, `Role`. Admin-only: create/deactivate users, change roles, reset passwords, manage categories, retire items. |

**Acceptance Criteria**
1. Given an SA is logged in, then admin-only menu items are hidden.
2. Given an SA sends a direct request to an admin-only action (e.g. by URL), then the server returns access denied and nothing changes.
3. Given an Admin is logged in, then they can do every SA action plus the admin-only actions.
4. Given a user's role is changed, then the new permissions apply from their next request.

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
| **Notes** | Classes: `AuditLogEntry`, `User`. Viewing and filtering the full audit log belongs to the Reports & Audit page. |

**Acceptance Criteria**
1. Given an SA creates, edits, lends, returns or reports an item, then an audit entry stores their user ID, the action, the record and a timestamp.
2. Given an Admin changes a user's role or status, then an audit entry records it.
3. Given any item, when the Admin opens its history, then each change shows who made it and when.
4. Given an action fails validation, then no audit entry is created.

---

### EP-USR-04 – Self-Service

#### US-USR-06 – Change my own password

| Field | Value |
|---|---|
| **Story ID** | US-USR-06 |
| **Title** | Change my own password |
| **Epic** | EP-USR-04 Self-Service |
| **User Role** | Student Assistant, Admin |
| **User Story** | As a Student Assistant, I want to change my own password, so that I can keep my account secure. |
| **Priority** | Should |
| **Related Requirement** | FR-USR-08, BR-USR-03, NFR-USR-01 |
| **Preconditions** | User is logged in. |
| **Dependencies** | US-USR-01 |
| **Notes** | Classes: `User`. |

**Acceptance Criteria**
1. Given the user enters the correct current password and a valid new one twice, when they save, then the password is changed and stored only as a salted hash.
2. Given the current password is wrong, then the change is rejected.
3. Given the new password is under 10 characters or lacks letters and digits, then it is rejected with the rule shown.
4. Given the two new-password fields don't match, then an inline error is shown.
5. Given the change succeeds, then the old password no longer works.

---

## 4. Story Refinement Check

| Step | How it was applied |
|---|---|
| Clear role, goal and benefit | Every story uses "As a … I want … so that …" with a real role (SA or Admin). |
| Linked to requirements | Every Must/Should FR in scope maps to a story (§5). |
| Business rules in criteria | Loan limits, overdue block, loan lengths, extension limit, lockout and password rules are acceptance criteria, not notes. |
| Right size | Related small FRs were merged (FR-AST-01/02, 06/07, 10/11; FR-USR-01/02/07). Each story fits one sprint. |
| Dependencies stated | Each story lists the stories it needs first. |
| Testable | Every criterion is Given/When/Then with concrete values. |
| Scope | Only AST and USR pages; notifications and the audit report are left to their own pages. |

## 5. Requirement Coverage

| Requirement | Priority | Story |
|---|---|---|
| FR-AST-01, FR-AST-02 | M | US-AST-01 |
| FR-AST-03 | M | US-AST-02 |
| FR-AST-04 | M | US-AST-03 |
| FR-AST-05 | S | US-AST-04 |
| FR-AST-06, FR-AST-07 | M, S | US-AST-05 |
| FR-AST-08 | M | US-AST-06 |
| FR-AST-09 | M | US-AST-07 |
| FR-AST-10, FR-AST-11 | M, S | US-AST-08 |
| FR-AST-12 | M | US-AST-10 |
| FR-AST-13 | M | US-AST-11 |
| FR-AST-14 | S | US-AST-09 |
| FR-USR-01, FR-USR-02, FR-USR-07 | M, M, S | US-USR-01 |
| FR-USR-03 | M | US-USR-02 |
| FR-USR-04 | M | US-USR-03 |
| FR-USR-05 | M | US-USR-04 |
| FR-USR-06 | M | US-USR-05 |
| FR-USR-08 | S | US-USR-06 |
| FR-USR-09 | S | US-USR-07 |

## 6. INVEST Checklist

| Story | I | N | V | E | S | T | Note |
|---|---|---|---|---|---|---|---|
| US-AST-01 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | |
| US-AST-02 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | |
| US-AST-03 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | |
| US-AST-04 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | |
| US-AST-05 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | |
| US-AST-06 | ~ | ✓ | ✓ | ✓ | ~ | ✓ | Largest story; split into "checkout" and "eligibility checks" if it doesn't fit a sprint. |
| US-AST-07 | ~ | ✓ | ✓ | ✓ | ✓ | ✓ | Needs US-AST-06. |
| US-AST-08 | ~ | ✓ | ✓ | ✓ | ✓ | ✓ | Needs loan data. |
| US-AST-09 | ~ | ✓ | ✓ | ✓ | ✓ | ✓ | Needs US-AST-06. |
| US-AST-10 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | |
| US-AST-11 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | |
| US-USR-01 | ✓ | ✓ | ✓ | ✓ | ~ | ✓ | Lockout can be split out if needed. |
| US-USR-02 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | |
| US-USR-03 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | |
| US-USR-04 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | |
| US-USR-05 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | |
| US-USR-06 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | |
| US-USR-07 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | |

✓ = met · ~ = met with a noted dependency or size risk

## 7. Definition of Done

A story is done when:
- Every acceptance criterion passes as a test case.
- Business-rule criteria (limits, blocks, lockout, password rules) have a passing negative test.
- Invalid input shows an inline error and saves nothing.
- The change is recorded with user and timestamp (US-USR-05).
- Role restrictions are enforced on the server, not only hidden in the UI.
- Code is reviewed and merged by PR.
