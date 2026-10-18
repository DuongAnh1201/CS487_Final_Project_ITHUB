# SP3 – User Stories: IT Inventory Tracker

**Course:** CS487 – Object-Oriented Design and Analysis  
**Milestone:** SP3 – User Stories (Issue #13)  
**Team:** Duong Anh Nguyen (Tom), Zafar Azatov, Luke Gregory Pamaos, Nusratilloh Soliev  
**Source:** `docs/sp2-requirements/SP2_Requirements_Collection.md` (all requirement, business rule, use case and class IDs below refer to this document)  
**Guidance:** Canvas module *Project Guidance: User Stories* (Sections 2–12)  

## 1. Main User Roles

| Role | Description |
|---|---|
| **Admin** (IT Supervisor) | Full access. Manages user accounts, classrooms, class schedules and lending policy; retires items; assigns, rejects and closes issues; reviews reports, audits and monthly summaries; sets up projects and assigns tasks. The Admin can do everything a Student Assistant can (A-01). |
| **Student Assistant (SA)** | Daily user. Registers, lends and returns items; issues supplies; manages classroom equipment and room checks; records and resolves issues; creates daily reports; tracks and receives orders; works on assigned tasks and reads notifications. |

Borrowers and issue reporters do not log in. They contact IT in person, by email or by phone, and an SA records the loan or issue for them (A-02). On the Projects & Tasks and Notifications pages, the Admin and SA have the same access (A-01, NFR-PRJ-02).

## 2. Conventions

- **Format:** As a [Admin / Student Assistant], I want [goal], so that [benefit].
- **IDs:** `US-<PAGE>-NN`. Priority is copied from the SP2 requirement.
- Every story uses the Section 9 template fields: Story ID, Title, Epic, User Role, User Story, Priority, Related Requirement, Preconditions, Acceptance Criteria, Dependencies, Notes.
- System rules (unique ID, audit log, validation) are in acceptance criteria and the Definition of Done, not separate stories. Class names appear in Notes only.

## 3. Story Summary

| Story ID | Title | Epic | Priority | Requirement(s) | Owner |
|---|---|---|---|---|---|
| US-AST-01 | Register an Item | 1 Inventory Records | Must Have | FR-AST-01, FR-AST-02 | Zafar |
| US-AST-02 | Edit Item Details | 1 Inventory Records | Must Have | FR-AST-03 | Zafar |
| US-AST-03 | Search and Filter Inventory | 1 Inventory Records | Must Have | FR-AST-04 | Zafar |
| US-AST-04 | Track Consumable Stock | 2 Consumable Stock | Must Have | FR-AST-05 | Zafar |
| US-AST-05 | Lend Out an Item | 3 Lending | Must Have | FR-AST-06 | Zafar |
| US-AST-06 | Record an Item Return | 3 Lending | Must Have | FR-AST-07 | Zafar |
| US-AST-07 | Extend a Loan | 3 Lending | Should Have | FR-AST-12 | Zafar |
| US-AST-08 | View Overdue Loans | 3 Lending | Must Have | FR-AST-08 | Zafar |
| US-AST-09 | View Loan History | 3 Lending | Should Have | FR-AST-09 | Zafar |
| US-AST-10 | Report an Item Lost or Damaged | 4 Item Lifecycle | Must Have | FR-AST-10 | Zafar |
| US-AST-11 | Retire an Item | 4 Item Lifecycle | Must Have | FR-AST-11 | Zafar |
| US-USR-01 | Log In and Log Out | 5 Authentication | Must Have | FR-USR-01, FR-USR-02, FR-USR-07 | Zafar |
| US-USR-02 | Change My Own Password | 5 Authentication | Should Have | FR-USR-08 | Zafar |
| US-USR-03 | Reset a User's Password | 5 Authentication | Should Have | FR-USR-09 | Zafar |
| US-USR-04 | Create a User Account | 6 Account Administration | Must Have | FR-USR-03 | Zafar |
| US-USR-05 | Change a User's Role or Status | 6 Account Administration | Must Have | FR-USR-04 | Zafar |
| US-USR-06 | Restrict Actions by Role | 6 Account Administration | Must Have | FR-USR-05 | Zafar |
| US-PRJ-01 | Create a Project | 7 Project and Task Management | Must Have | FR-PRJ-01 | Luke |
| US-PRJ-02 | Create a Project from a Template | 7 Project and Task Management | Must Have | FR-PRJ-02 | Luke |
| US-PRJ-03 | Create a Task | 7 Project and Task Management | Must Have | FR-PRJ-03 | Luke |
| US-PRJ-04 | Assign or Reassign a Task | 7 Project and Task Management | Must Have | FR-PRJ-04 | Luke |
| US-PRJ-05 | Update Task Progress | 7 Project and Task Management | Must Have | FR-PRJ-05 | Luke |
| US-PRJ-06 | Search and Filter Work | 7 Project and Task Management | Should Have | FR-PRJ-06 | Luke |
| US-PRJ-07 | Hand Off an Unfinished Task | 7 Project and Task Management | Must Have | FR-PRJ-07 | Luke |
| US-NTF-01 | Notify Staff About New Work and Issues | 8 Staff Notifications | Must Have | FR-NTF-01 | Luke |
| US-NTF-02 | Route Notifications to the Right Recipients | 8 Staff Notifications | Must Have | FR-NTF-02 | Luke |
| US-NTF-03 | Receive a Shift Summary | 8 Staff Notifications | Must Have | FR-NTF-03 | Luke |
| US-NTF-04 | View My Notifications | 8 Staff Notifications | Must Have | FR-NTF-04, FR-NTF-08 | Luke |
| US-NTF-05 | Mark a Notification Read or Unread | 8 Staff Notifications | Should Have | FR-NTF-05 | Luke |
| US-NTF-06 | Notify Project Members | 8 Staff Notifications | Must Have | FR-NTF-06 | Luke |
| US-NTF-07 | Receive Email Copies of Notifications | 8 Staff Notifications | Must Have | FR-NTF-07 | Luke |
| US-CLS-01 | Manage Classrooms | 9 Classroom Setup | Must Have | FR-CLS-01 | Nusratilloh |
| US-CLS-02 | Move or Remove Installed Equipment | 9 Classroom Setup | Should Have | FR-CLS-02 | Nusratilloh |
| US-CLS-03 | Set Equipment Condition | 9 Classroom Setup | Must Have | FR-CLS-03, FR-CLS-04 | Nusratilloh |
| US-CLS-04 | See Rooms Overdue for a Check | 10 Room Checks and Search | Should Have | FR-CLS-05 | Nusratilloh |
| US-CLS-05 | Search and Filter Classrooms | 10 Room Checks and Search | Should Have | FR-CLS-09 | Nusratilloh |
| US-CLS-06 | Import the Class Schedule | 11 Class Schedules | Must Have | FR-CLS-06 | Nusratilloh |
| US-CLS-07 | Add, Edit or Cancel a Schedule Entry | 11 Class Schedules | Must Have | FR-CLS-07 | Nusratilloh |
| US-CLS-08 | View a Room's Timetable | 11 Class Schedules | Must Have | FR-CLS-08 | Nusratilloh |
| US-ISS-01 | Record an Issue | 12 Reporting Issues | Must Have | FR-ISS-01, FR-ISS-02, FR-ISS-03 | Nusratilloh |
| US-ISS-02 | List and Filter Issues | 12 Reporting Issues | Must Have | FR-ISS-04 | Nusratilloh |
| US-ISS-03 | Change an Issue's Status | 13 Handling Issues | Must Have | FR-ISS-05 | Nusratilloh |
| US-ISS-04 | Add Comments and Progress Notes | 13 Handling Issues | Should Have | FR-ISS-06 | Nusratilloh |
| US-ISS-05 | Resolve an Issue | 13 Handling Issues | Must Have | FR-ISS-07, FR-ISS-09 | Nusratilloh |
| US-ISS-06 | Mark Duplicates and Flag Repeat Problems | 13 Handling Issues | Must Have | FR-ISS-08 | Nusratilloh |
| US-ISS-07 | View Issue History | 13 Handling Issues | Must Have | FR-ISS-10 | Nusratilloh |
| US-ORD-01 | Flag Low-Stock Items for Ordering | 14 Order Management | Must Have | FR-ORD-01, FR-AST-14 | Tom |
| US-ORD-02 | Track Orders and Their Status | 14 Order Management | Must Have | FR-ORD-02, FR-ORD-05 | Tom |
| US-ORD-03 | Receive an Order | 14 Order Management | Must Have | FR-ORD-03, FR-AST-13 | Tom |
| US-ORD-04 | Search and Filter Orders | 14 Order Management | Must Have | FR-ORD-04 | Tom |
| US-RPT-01 | Create a Report | 15 Report Management | Must Have | FR-RPT-01, FR-RPT-09 | Tom |
| US-RPT-02 | Group Reports by Project | 15 Report Management | Should Have | FR-RPT-02 | Tom |
| US-RPT-03 | Notify Reviewers of a Submitted Report | 15 Report Management | Must Have | FR-RPT-03 | Tom |
| US-RPT-04 | Change a Report's Status | 15 Report Management | Must Have | FR-RPT-04 | Tom |
| US-RPT-05 | Create a Report from a Daily Template | 15 Report Management | Should Have | FR-RPT-05 | Tom |
| US-RPT-06 | Search and Filter Reports | 15 Report Management | Must Have | FR-RPT-08 | Tom |
| US-RPT-07 | Receive the Monthly Summary | 15 Report Management | Should Have | FR-RPT-07 | Tom |
| US-RPT-08 | View Audit History | 16 Audit | Must Have | FR-RPT-06, FR-RPT-08 | Tom |

**Total:** 58 stories (AST 11, USR 6, PRJ 7, NTF 7, CLS 8, ISS 7, ORD 4, RPT 8).

## 4. User Stories

### Epic 1: Inventory Records

#### US-AST-01: Register an Item

**Story ID:** US-AST-01  
**Title:** Register an Item  
**Epic:** Inventory Records  
**User Role:** Student Assistant  
**User Story:** As a Student Assistant, I want to register a new item with its asset tag and details, so that the IT department knows what equipment it owns and where it is.  
**Priority:** Must Have  
**Related Requirement:** FR-AST-01, FR-AST-02, BR-01, NFR-AST-03  
**Preconditions:** The SA is logged in. The item's category and location exist.  
**Acceptance Criteria:**
- The SA can enter asset tag, serial number, model, manufacturer, category, location, status, purchase date, warranty end date and notes.
- A new item is saved with status Available.
- The system prevents duplicate asset tag values.
- An asset tag used by a Retired item is also rejected (asset tags are never reused).
- A missing required field shows a clear inline error next to that field and nothing is saved.

**Dependencies:** US-USR-01  
**Notes:** Use case: UC-AST-01. Classes: `Item`, `Category`, `Location`, `ItemStatus`.

#### US-AST-02: Edit Item Details

**Story ID:** US-AST-02  
**Title:** Edit Item Details  
**Epic:** Inventory Records  
**User Role:** Student Assistant  
**User Story:** As a Student Assistant, I want to edit an item's details, so that the inventory stays accurate when an item moves or a record was entered incorrectly.  
**Priority:** Must Have  
**Related Requirement:** FR-AST-03, BR-01, BR-07  
**Preconditions:** The SA is logged in. The item exists and is not Retired.  
**Acceptance Criteria:**
- The SA can change permitted fields and save them.
- Changing the asset tag to one that already exists is rejected.
- A Retired item is read-only and cannot be edited.
- The change records the user, timestamp, and old and new values (BR-03).

**Dependencies:** US-AST-01  
**Notes:** Use case: UC-AST-01. Classes: `Item`. Status changes happen through lending, return, incident and retire stories, not this edit.

#### US-AST-03: Search and Filter Inventory

**Story ID:** US-AST-03  
**Title:** Search and Filter Inventory  
**Epic:** Inventory Records  
**User Role:** Student Assistant, Admin  
**User Story:** As a Student Assistant, I want to search and filter items by asset tag, serial number, model, category, location and status, so that I can find a specific item or see what is available quickly.  
**Priority:** Must Have  
**Related Requirement:** FR-AST-04, NFR-AST-01  
**Preconditions:** The user is logged in.  
**Acceptance Criteria:**
- The user can search by asset tag, serial number and model.
- The user can filter by category, location and status, and combine filters.
- Only items matching all entered values are listed.
- The system displays a suitable message when no results are found.
- Results return within 2 seconds for up to 5,000 items.

**Dependencies:** US-AST-01  
**Notes:** Use case: UC-AST-02. Classes: `Item`.

### Epic 2: Consumable Stock

#### US-AST-04: Track Consumable Stock

**Story ID:** US-AST-04  
**Title:** Track Consumable Stock  
**Epic:** Consumable Stock  
**User Role:** Student Assistant  
**User Story:** As a Student Assistant, I want to record supplies going in and out by quantity, so that I always know how many cables, adapters and toner we have.  
**Priority:** Must Have  
**Related Requirement:** FR-AST-05, BR-11  
**Preconditions:** The SA is logged in. The consumable exists.  
**Acceptance Criteria:**
- The SA can record a stock-in, which increases the quantity on hand.
- The SA can record a stock-out (issue), which decreases the quantity on hand.
- Each stock-in and stock-out is recorded with the quantity, the SA who did it, the recipient for a stock-out, and the time.
- A stock-out larger than the quantity on hand is rejected and the quantity is unchanged (quantity cannot go below zero).
- Consumables cannot be lent out and are not returned.

**Dependencies:** US-USR-01  
**Notes:** Use case: UC-AST-05. Classes: `Consumable`, `StockTransaction`. Low-stock flagging and automatic quantity update on order arrival are covered by US-ORD-01 and US-ORD-03.

### Epic 3: Lending

#### US-AST-05: Lend Out an Item

**Story ID:** US-AST-05  
**Title:** Lend Out an Item  
**Epic:** Lending  
**User Role:** Student Assistant  
**User Story:** As a Student Assistant, I want to lend out an item and record who has it and when it is due, so that every lent item can be tracked and returned on time.  
**Priority:** Must Have  
**Related Requirement:** FR-AST-06, BR-07, BR-08, BR-09  
**Preconditions:** The SA is logged in. The item exists.  
**Acceptance Criteria:**
- The SA can record borrower name, school ID, email, borrower type, checkout date, due date and condition out (Good / Fair / Poor + notes).
- Only an item with status Available can be lent out; otherwise the system shows the item's current status and stops.
- The default due date is 7 days for students and 30 days for faculty/staff; a date beyond the maximum loan length is rejected.
- A borrower with an overdue item, or a student who already holds 2 items, is blocked.
- After confirmation, the loan is created, the item status becomes On Loan, and the loan records the SA who processed it.

**Dependencies:** US-AST-01, US-USR-01  
**Notes:** Use case: UC-AST-03 (full specification in SP2 Section 10). Classes: `Loan`, `Borrower`, `Item`. Borrowers do not log in (A-02).

#### US-AST-06: Record an Item Return

**Story ID:** US-AST-06  
**Title:** Record an Item Return  
**Epic:** Lending  
**User Role:** Student Assistant  
**User Story:** As a Student Assistant, I want to record when a lent item comes back and its condition, so that the loan is closed and the item's status is correct.  
**Priority:** Must Have  
**Related Requirement:** FR-AST-07, BR-10  
**Preconditions:** The SA is logged in. The item has an open loan.  
**Acceptance Criteria:**
- The SA can record the return date, condition in, notes, and the SA who received it.
- A return in good condition closes the loan and sets the item to Available.
- A return in damaged condition closes the loan and sets the item to Damaged, not Available.
- An item with no open loan cannot be returned and the system shows a clear message.
- The loan record is kept after the return (records are never deleted).

**Dependencies:** US-AST-05  
**Notes:** Use case: UC-AST-03. Classes: `Loan`, `Item`.

#### US-AST-07: Extend a Loan

**Story ID:** US-AST-07  
**Title:** Extend a Loan  
**Epic:** Lending  
**User Role:** Student Assistant  
**User Story:** As a Student Assistant, I want to extend a loan's due date once, so that a borrower who still needs an item can keep it without a new checkout.  
**Priority:** Should Have  
**Related Requirement:** FR-AST-12, BR-08  
**Preconditions:** The SA is logged in. The loan is open and has not been extended before.  
**Acceptance Criteria:**
- The SA can extend an open loan's due date by up to 7 days.
- A loan can be extended only once; a second extension is rejected.
- The new due date and the SA who extended it are recorded.

**Dependencies:** US-AST-05  
**Notes:** Use case: UC-AST-03. Classes: `Loan`.

#### US-AST-08: View Overdue Loans

**Story ID:** US-AST-08  
**Title:** View Overdue Loans  
**Epic:** Lending  
**User Role:** Admin, Student Assistant  
**User Story:** As an Admin, I want to see all overdue loans, so that I can follow up on late items.  
**Priority:** Must Have  
**Related Requirement:** FR-AST-08  
**Preconditions:** The user is logged in.  
**Acceptance Criteria:**
- The list shows every loan whose due date has passed and that is not returned.
- Each row shows the borrower, contact, item, due date and days overdue.
- A loan due today is not listed.
- A returned loan is never listed.

**Dependencies:** US-AST-05, US-AST-06  
**Notes:** Use case: UC-AST-04. Classes: `Loan`, `Borrower`.

#### US-AST-09: View Loan History

**Story ID:** US-AST-09  
**Title:** View Loan History  
**Epic:** Lending  
**User Role:** Admin, Student Assistant  
**User Story:** As an Admin, I want to see the loan history of an item and of a borrower, so that I can check who had an item and how a borrower has used the lending service.  
**Priority:** Should Have  
**Related Requirement:** FR-AST-09, NFR-AST-04  
**Preconditions:** The user is logged in.  
**Acceptance Criteria:**
- The user can view all past and current loans for one item.
- The user can view all past and current loans for one borrower.
- Each entry shows checkout date, due date, return date, condition out and condition in.
- Loans of Retired items remain visible in the history.

**Dependencies:** US-AST-05, US-AST-06  
**Notes:** Use case: UC-AST-03. Classes: `Loan`, `Item`, `Borrower`.

### Epic 4: Item Lifecycle

#### US-AST-10: Report an Item Lost or Damaged

**Story ID:** US-AST-10  
**Title:** Report an Item Lost or Damaged  
**Epic:** Item Lifecycle  
**User Role:** Student Assistant  
**User Story:** As a Student Assistant, I want to report an item as Lost or Damaged with a description, so that nobody lends it out and IT knows it needs attention.  
**Priority:** Must Have  
**Related Requirement:** FR-AST-10, BR-07  
**Preconditions:** The SA is logged in. The item exists and is not Retired.  
**Acceptance Criteria:**
- The SA can report an item as Lost or Damaged with a description and date.
- An empty description shows an inline error and nothing is saved.
- After saving, the item status becomes Lost or Damaged and an incident record is created.
- A Lost or Damaged item cannot be lent out.
- The report records the SA who filed it and when.

**Dependencies:** US-AST-01  
**Notes:** Use case: UC-AST-06. Classes: `ItemIncident`, `Item`.

#### US-AST-11: Retire an Item

**Story ID:** US-AST-11  
**Title:** Retire an Item  
**Epic:** Item Lifecycle  
**User Role:** Admin  
**User Story:** As an Admin, I want to retire an item with a reason and date, so that obsolete equipment leaves active inventory but its history is kept.  
**Priority:** Must Have  
**Related Requirement:** FR-AST-11, BR-02, BR-05, BR-07, BR-18  
**Preconditions:** The Admin is logged in. The item exists.  
**Acceptance Criteria:**
- The Admin can retire an item with a reason and date.
- The item status becomes Retired; the item is read-only and cannot be lent.
- The item and its history are kept, not deleted.
- A retired item is removed from its classroom and ignored in room status calculation.
- The Retire option is not available to an SA.

**Dependencies:** US-USR-06  
**Notes:** Use case: UC-AST-01. Classes: `Item`, `ItemIncident`.

### Epic 5: Authentication

#### US-USR-01: Log In and Log Out

**Story ID:** US-USR-01  
**Title:** Log In and Log Out  
**Epic:** Authentication  
**User Role:** Admin, Student Assistant  
**User Story:** As a Student Assistant, I want to log in with my school email and password and log out when I am done, so that only I can act under my account.  
**Priority:** Must Have  
**Related Requirement:** FR-USR-01, FR-USR-02, FR-USR-07, BR-04, NFR-USR-01, NFR-USR-03  
**Preconditions:** The user has an active account.  
**Acceptance Criteria:**
- An active user with a correct school email and password is logged in.
- A wrong password or unknown email shows the same error message, which does not reveal whether the email exists.
- After 5 consecutive failed attempts, the account is locked for 15 minutes.
- A deactivated or locked account cannot log in.
- A logged-in user can log out and returns to the login page.

**Dependencies:** US-USR-04  
**Notes:** Use case: UC-USR-01. Classes: `User`, `Role`. Passwords are stored only as salted hashes (NFR-USR-01).

#### US-USR-02: Change My Own Password

**Story ID:** US-USR-02  
**Title:** Change My Own Password  
**Epic:** Authentication  
**User Role:** Admin, Student Assistant  
**User Story:** As a Student Assistant, I want to change my own password, so that I can keep my account secure.  
**Priority:** Should Have  
**Related Requirement:** FR-USR-08, BR-06  
**Preconditions:** The user is logged in.  
**Acceptance Criteria:**
- The logged-in user can change their own password.
- A new password shorter than 10 characters, or without both letters and digits, is rejected with the password rule shown.
- After the change, the new password is required at the next login.

**Dependencies:** US-USR-01  
**Notes:** Use case: UC-USR-03. Classes: `User`.

#### US-USR-03: Reset a User's Password

**Story ID:** US-USR-03  
**Title:** Reset a User's Password  
**Epic:** Authentication  
**User Role:** Admin  
**User Story:** As an Admin, I want to reset a user's password to a temporary one, so that a user who forgot their password can get back into the system.  
**Priority:** Should Have  
**Related Requirement:** FR-USR-09, BR-05, BR-06  
**Preconditions:** The Admin is logged in. The target account exists.  
**Acceptance Criteria:**
- The Admin can set a temporary password for a user.
- At the next login, the user must change the temporary password before continuing.
- An SA cannot reset another user's password.

**Dependencies:** US-USR-01, US-USR-02  
**Notes:** Use case: UC-USR-03. Classes: `User`.

### Epic 6: Account Administration

#### US-USR-04: Create a User Account

**Story ID:** US-USR-04  
**Title:** Create a User Account  
**Epic:** Account Administration  
**User Role:** Admin  
**User Story:** As an Admin, I want to create accounts for new staff, so that each person has their own login.  
**Priority:** Must Have  
**Related Requirement:** FR-USR-03, BR-04, BR-05  
**Preconditions:** The Admin is logged in.  
**Acceptance Criteria:**
- The Admin can enter full name, school email, school ID, role and an optional access end date; the account is saved as active.
- A school email or school ID that already has an account is rejected (one account per person; shared accounts are not allowed).
- An SA cannot create accounts.

**Dependencies:** None (the first Admin account is created in advance, FR-USR-05).  
**Notes:** Use case: UC-USR-02. Classes: `User`, `Role`.

#### US-USR-05: Change a User's Role or Status

**Story ID:** US-USR-05  
**Title:** Change a User's Role or Status  
**Epic:** Account Administration  
**User Role:** Admin  
**User Story:** As an Admin, I want to change a user's role and deactivate or reactivate their account, so that people who leave lose access while their past actions stay on record.  
**Priority:** Must Have  
**Related Requirement:** FR-USR-04, BR-02, BR-04, BR-05, BR-06  
**Preconditions:** The Admin is logged in. The target account exists.  
**Acceptance Criteria:**
- The Admin can change a user's role between Admin and Student Assistant.
- A deactivated account cannot log in; a reactivated account can log in again.
- Deactivating or demoting the last active Admin is blocked (at least one active Admin must always exist).
- Accounts are never deleted; records created by a deactivated user still show their name.
- An SA cannot change roles or account status.

**Dependencies:** US-USR-04  
**Notes:** Use case: UC-USR-02. Classes: `User`, `Role`. Policy: an SA's account is deactivated within 1 business day of leaving the job (BR-06).

#### US-USR-06: Restrict Actions by Role

**Story ID:** US-USR-06  
**Title:** Restrict Actions by Role  
**Epic:** Account Administration  
**User Role:** Admin  
**User Story:** As an Admin, I want Admin-only actions blocked for Student Assistants, so that only the Admin can manage accounts, retire items and perform other Admin-only work.  
**Priority:** Must Have  
**Related Requirement:** FR-USR-05, BR-04, BR-05  
**Preconditions:** The Admin and Student Assistant roles exist (created in advance).  
**Acceptance Criteria:**
- An SA does not see Admin-only actions (create accounts, assign roles, deactivate accounts, retire items, and the Admin-only actions on other pages, e.g. assigning, rejecting and closing issues).
- An SA who tries to open an Admin-only function by any route receives an access-denied message and nothing changes.
- An Admin can perform every SA action plus the Admin-only actions.
- Only a logged-in user can add or change records.

**Dependencies:** US-USR-01  
**Notes:** Use case: UC-USR-01. Classes: `User`, `Role`.

### Epic 7: Project and Task Management

#### US-PRJ-01: Create a Project

**Story ID:** US-PRJ-01  
**Title:** Create a Project  
**Epic:** Project and Task Management  
**User Role:** Admin or Student Assistant  
**User Story:** As an Admin or Student Assistant, I want to create a project with basic details, so that the team can organize related work.  
**Priority:** Must Have  
**Related Requirement:** FR-PRJ-01, NFR-PRJ-02  
**Preconditions:** The user is logged in.  
**Acceptance Criteria:**
- The user can enter a project name, description, start date, optional due date and status.
- The system assigns the project a unique project ID.
- The project can be found and updated using its project ID.
- Missing or invalid required values are reported and nothing is saved.

**Dependencies:** US-USR-01  
**Notes:** Use case: UC-PRJ-02. Classes: `Project`. Project status values are not defined in SP2 (Confirm).

#### US-PRJ-02: Create a Project from a Template

**Story ID:** US-PRJ-02  
**Title:** Create a Project from a Template  
**Epic:** Project and Task Management  
**User Role:** Admin or Student Assistant  
**User Story:** As an Admin or Student Assistant, I want to maintain project templates and start a project from one, so that recurring work is quicker to set up.  
**Priority:** Must Have  
**Related Requirement:** FR-PRJ-02, BR-13  
**Preconditions:** The user is logged in. A template exists when creating a project from it.  
**Acceptance Criteria:**
- The user can create and edit a project template containing reusable task definitions.
- The user can select a template and enter the new project's details.
- The system creates a new project and new task records from the template's task definitions.
- Later edits to the created project or its tasks do not change the template.
- A confirmation message is displayed, or the reason the project could not be created.

**Dependencies:** US-PRJ-01  
**Notes:** Use case: UC-PRJ-01. Classes: `ProjectTemplate`, `TemplateTask`, `Project`, `Task`. Whether templates include default assignees, priorities or relative due dates is marked Confirm in SP2.

#### US-PRJ-03: Create a Task

**Story ID:** US-PRJ-03  
**Title:** Create a Task  
**Epic:** Project and Task Management  
**User Role:** Admin or Student Assistant  
**User Story:** As an Admin or Student Assistant, I want to create a standalone task or a task linked to a project, so that work can be tracked in the right context.  
**Priority:** Must Have  
**Related Requirement:** FR-PRJ-03, BR-14  
**Preconditions:** The user is logged in. If linking to a project, the project exists.  
**Acceptance Criteria:**
- The user can enter a task title, description, status and optional due date.
- The user can save the task without a project or linked to one existing project.
- A standalone task can be linked to a project later.
- Invalid required values or project links are reported and nothing is saved.

**Dependencies:** US-PRJ-01 when linking to a project.  
**Notes:** Use case: UC-PRJ-02. Classes: `Task`, `Project`. Task statuses follow BR-15.

#### US-PRJ-04: Assign or Reassign a Task

**Story ID:** US-PRJ-04  
**Title:** Assign or Reassign a Task  
**Epic:** Project and Task Management  
**User Role:** Admin or Student Assistant  
**User Story:** As an Admin or Student Assistant, I want to assign or reassign a task to one or more staff members, so that everyone can see who is responsible for the work.  
**Priority:** Must Have  
**Related Requirement:** FR-PRJ-04, BR-14  
**Preconditions:** The user is logged in. The task and the selected staff accounts exist.  
**Acceptance Criteria:**
- The user can assign a task to one or more Admins or SAs.
- The task shows its current assignee(s) after saving.
- When reassigned, the task keeps its status, and the previous and new assignments appear in its assignment history.
- The new assignee(s) receive a notification (US-NTF-01).

**Dependencies:** US-PRJ-03  
**Notes:** Use case: UC-PRJ-02. Classes: `Task`, `TaskAssignment`. Multiple assignees are a draft assumption marked Confirm in FR-PRJ-04.

#### US-PRJ-05: Update Task Progress

**Story ID:** US-PRJ-05  
**Title:** Update Task Progress  
**Epic:** Project and Task Management  
**User Role:** Admin or Student Assistant  
**User Story:** As an Admin or Student Assistant, I want to update a task's status and see project progress, so that the team can track work toward completion.  
**Priority:** Must Have  
**Related Requirement:** FR-PRJ-05, BR-15  
**Preconditions:** The user is logged in. The task exists.  
**Acceptance Criteria:**
- The user can set a task's status to To Do, In Progress or Complete.
- The task shows its saved status.
- For a task linked to a project, the project view shows the updated progress.
- A project is shown as complete only when all its tasks are Complete.
- The status change is recorded in the audit history with old and new values.

**Dependencies:** US-PRJ-03  
**Notes:** Use case: UC-PRJ-03. Classes: `Task`, `Project`. Status values are draft values marked Confirm in FR-PRJ-05.

#### US-PRJ-06: Search and Filter Work

**Story ID:** US-PRJ-06  
**Title:** Search and Filter Work  
**Epic:** Project and Task Management  
**User Role:** Admin or Student Assistant  
**User Story:** As an Admin or Student Assistant, I want to search projects and tasks by text and filter them by status, assignee and due date, so that I can find the work I need.  
**Priority:** Should Have  
**Related Requirement:** FR-PRJ-06, NFR-PRJ-03  
**Preconditions:** The user is logged in.  
**Acceptance Criteria:**
- The user can search projects and tasks by text.
- The user can filter by status, assignee and due date, and combine filters.
- Results match the entered text and all selected filters.
- The system displays a suitable message when no results are found.

**Dependencies:** US-PRJ-01, US-PRJ-03  
**Notes:** Use case: UC-PRJ-02. Classes: `Project`, `Task`. Required filters are marked Confirm in SP2.

#### US-PRJ-07: Hand Off an Unfinished Task

**Story ID:** US-PRJ-07  
**Title:** Hand Off an Unfinished Task  
**Epic:** Project and Task Management  
**User Role:** Admin or Student Assistant  
**User Story:** As an Admin or Student Assistant taking over work, I want an unfinished task handed off to me with its status and history, so that I can continue it without losing context.  
**Priority:** Must Have  
**Related Requirement:** FR-PRJ-07, BR-14  
**Preconditions:** The user is logged in. An unfinished task exists. The receiving account exists.  
**Acceptance Criteria:**
- The user can hand off an unfinished task to an Admin or SA taking over the work.
- The task's status is unchanged by the handoff.
- The assignment history keeps the previous and new assignees.
- The task shows its current assignee(s) after the handoff.

**Dependencies:** US-PRJ-04  
**Notes:** Use case: UC-PRJ-02. Classes: `Task`, `TaskAssignment`.

### Epic 8: Staff Notifications

#### US-NTF-01: Notify Staff About New Work and Issues

**Story ID:** US-NTF-01  
**Title:** Notify Staff About New Work and Issues  
**Epic:** Staff Notifications  
**User Role:** Admin or Student Assistant  
**User Story:** As an Admin or Student Assistant, I want a notification when a task is newly assigned or an issue is reported, so that I can respond to work that needs attention.  
**Priority:** Must Have  
**Related Requirement:** FR-NTF-01, BR-16, NFR-NTF-01  
**Preconditions:** The task assignment or issue report is saved successfully.  
**Acceptance Criteria:**
- A new task assignment creates a notification linked to that assignment.
- A newly reported issue creates a notification linked to that issue.
- Each notification has one recipient and one triggering event.
- Each notification creation is recorded with a timestamp and its triggering event.
- A failed notification does not undo the saved task assignment or issue report.

**Dependencies:** US-PRJ-04, US-ISS-01  
**Notes:** Use case: UC-NTF-01. Classes: `Notification`, `NotificationService` (Observer pattern per the proposal).

#### US-NTF-02: Route Notifications to the Right Recipients

**Story ID:** US-NTF-02  
**Title:** Route Notifications to the Right Recipients  
**Epic:** Staff Notifications  
**User Role:** Admin or Student Assistant  
**User Story:** As an Admin or Student Assistant, I want each notification to show who it is for, what event caused it and what work item it concerns, so that I know why I received it.  
**Priority:** Must Have  
**Related Requirement:** FR-NTF-02, BR-16  
**Preconditions:** A notification event occurs.  
**Acceptance Criteria:**
- Each notification is routed to its applicable recipient(s).
- Each notification shows the recipient, event type and related project, task or issue.
- Task assignment notifications go to the new assignee(s).
- Issue notifications are not sent to a fixed role until the routing rule is confirmed.

**Dependencies:** US-NTF-01  
**Notes:** Use case: UC-NTF-01. Classes: `Notification`, `NotificationService`. Issue routing is marked Confirm in FR-NTF-02.

#### US-NTF-03: Receive a Shift Summary

**Story ID:** US-NTF-03  
**Title:** Receive a Shift Summary  
**Epic:** Staff Notifications  
**User Role:** Admin or Student Assistant on the current shift  
**User Story:** As a Student Assistant starting a shift, I want a notification listing the work scheduled for my shift, so that I can plan what I need to finish.  
**Priority:** Must Have  
**Related Requirement:** FR-NTF-03, BR-16  
**Preconditions:** The current shift roster lists the staff member.  
**Acceptance Criteria:**
- When a shift begins, each staff member on that shift's roster receives a notification.
- The notification lists the work scheduled for that shift.
- Staff not on the current shift roster do not receive that shift's summary.
- The notification shows its creation time and shift.

**Dependencies:** US-PRJ-04  
**Notes:** Use case: UC-NTF-01. Classes: `Notification`, `NotificationService`. Supported shifts, roster source, send time and handling of overdue/unassigned work are marked Confirm in FR-NTF-03.

#### US-NTF-04: View My Notifications

**Story ID:** US-NTF-04  
**Title:** View My Notifications  
**Epic:** Staff Notifications  
**User Role:** Admin or Student Assistant  
**User Story:** As an Admin or Student Assistant, I want to view my notifications with their read state and related work item, so that I can review the updates I received.  
**Priority:** Must Have  
**Related Requirement:** FR-NTF-04, FR-NTF-08  
**Preconditions:** The user is logged in.  
**Acceptance Criteria:**
- The user sees an in-app list of notifications addressed to them.
- Each notification is marked read or unread.
- Each notification shows its creation time and related work item when one exists.
- Notifications for other recipients are not shown.
- Each notification has a unique notification ID and is found by that ID.

**Dependencies:** US-NTF-01  
**Notes:** Use case: UC-NTF-02. Classes: `Notification`.

#### US-NTF-05: Mark a Notification Read or Unread

**Story ID:** US-NTF-05  
**Title:** Mark a Notification Read or Unread  
**Epic:** Staff Notifications  
**User Role:** Admin or Student Assistant  
**User Story:** As an Admin or Student Assistant, I want to mark my notifications read or unread, so that I can keep track of what I have reviewed.  
**Priority:** Should Have  
**Related Requirement:** FR-NTF-05, FR-NTF-08, NFR-NTF-01  
**Preconditions:** The user is logged in. The notification is addressed to the user.  
**Acceptance Criteria:**
- The user can mark a notification read and mark it unread.
- The displayed read state matches the saved state.
- The update is applied by notification ID and changes only that notification.
- A user cannot change another recipient's notification.
- Each read-state change is recorded with the user and timestamp.

**Dependencies:** US-NTF-04  
**Notes:** Use case: UC-NTF-02. Classes: `Notification`. Delete, mark-all-read and open-linked-item are marked Confirm in FR-NTF-05 and are not assumed.

#### US-NTF-06: Notify Project Members

**Story ID:** US-NTF-06  
**Title:** Notify Project Members  
**Epic:** Staff Notifications  
**User Role:** Admin or Student Assistant who is a project member  
**User Story:** As a project member, I want to be notified when my project is created, updated or someone is added to it, so that I stay informed about changes to my project.  
**Priority:** Must Have  
**Related Requirement:** FR-NTF-06, BR-16  
**Preconditions:** The project event is saved. Project membership is known.  
**Acceptance Criteria:**
- Creating a project, updating a project, or adding a user to it creates notifications for the project's members.
- Each notification identifies the project and the event.
- Only members of that project receive these notifications.

**Dependencies:** US-PRJ-01  
**Notes:** Use case: UC-NTF-01. Classes: `Notification`, `NotificationService`, `Project`.

#### US-NTF-07: Receive Email Copies of Notifications

**Story ID:** US-NTF-07  
**Title:** Receive Email Copies of Notifications  
**Epic:** Staff Notifications  
**User Role:** Admin or Student Assistant  
**User Story:** As an Admin or Student Assistant, I want notifications sent to my registered email as well as shown in the app, so that I see important updates outside the system.  
**Priority:** Must Have  
**Related Requirement:** FR-NTF-07, BR-16  
**Preconditions:** A notification is created. The recipient has a registered email address.  
**Acceptance Criteria:**
- The system sends the notification to the recipient's registered email address.
- The in-app notification is always kept.
- The notification records whether the email was delivered.
- An email failure does not remove the in-app notification.

**Dependencies:** US-NTF-01  
**Notes:** Use case: UC-NTF-01. Classes: `NotificationService`. **Conflict:** SP2 Section 13 lists email delivery as out of scope.

### Epic 9: Classroom Setup

#### US-CLS-01: Manage Classrooms

**Story ID:** US-CLS-01  
**Title:** Manage Classrooms  
**Epic:** Classroom Setup  
**User Role:** Admin  
**User Story:** As an Admin, I want to add, edit and deactivate classrooms, so that the room list always matches the rooms we support.  
**Priority:** Must Have  
**Related Requirement:** FR-CLS-01, BR-02, BR-18  
**Preconditions:** The Admin is logged in. The building and room exist as a Location.  
**Acceptance Criteria:**
- The Admin can add and edit a classroom linked to a Location, with capacity and room type.
- A Location that already has a classroom cannot get a second one.
- A classroom with installed equipment or future classes cannot be deactivated, and the system says why.
- A deactivated classroom is hidden from active lists but kept; there is no delete.

**Dependencies:** Location records (AST page).  
**Notes:** Use case: UC-CLS-01. Classes: `Classroom`, `Location`.

#### US-CLS-02: Move or Remove Installed Equipment

**Story ID:** US-CLS-02  
**Title:** Move or Remove Installed Equipment  
**Epic:** Classroom Setup  
**User Role:** Student Assistant  
**User Story:** As a Student Assistant, I want to move a PC or monitor to another classroom or remove it, so that the system shows where every machine really is.  
**Priority:** Should Have  
**Related Requirement:** FR-CLS-02, BR-18  
**Preconditions:** The SA is logged in. The item is installed in a classroom.  
**Acceptance Criteria:**
- The SA can move an installed item to another active classroom; it then appears only in the new classroom.
- The SA can remove an installed item; it is no longer listed in any classroom.
- Moving or removing an item does not change its inventory status (A-06).
- Each move or removal is recorded in the audit log with the user and time.

**Dependencies:** US-CLS-01  
**Notes:** Use case: UC-CLS-02. Classes: `RoomEquipment`, `Item`.

#### US-CLS-03: Set Equipment Condition

**Story ID:** US-CLS-03  
**Title:** Set Equipment Condition  
**Epic:** Classroom Setup  
**User Role:** Student Assistant, Admin  
**User Story:** As a Student Assistant, I want to set the condition of a PC or monitor with a reason, so that everyone can see which equipment works and why it changed.  
**Priority:** Must Have  
**Related Requirement:** FR-CLS-03, FR-CLS-04, BR-03, NFR-CLS-01  
**Preconditions:** The user is logged in. The equipment is installed in a classroom.  
**Acceptance Criteria:**
- The condition list is Working, Faulty, Under Repair, Out of Service, Missing (A-07), the same for PCs and monitors.
- A reason is required; without it the change is not saved and a message asks for the reason.
- The audit log records the old value, new value, reason, user and time.
- The classroom status is recalculated after the change.
- The SA can change a condition in no more than 3 clicks from the classroom page.

**Dependencies:** US-CLS-01  
**Notes:** Use case: UC-CLS-02. Classes: `RoomEquipment`, `Classroom`, `EquipmentCondition`, `RoomStatus`. FR-CLS-03 wording says "monitor ... using the same list" and SP2 Section 12 names it "Set PC status", so this story covers both.

### Epic 10: Room Checks and Search

#### US-CLS-04: See Rooms Overdue for a Check

**Story ID:** US-CLS-04  
**Title:** See Rooms Overdue for a Check  
**Epic:** Room Checks and Search  
**User Role:** Admin  
**User Story:** As an Admin, I want to see each classroom's last-checked date with overdue rooms flagged, so that no room goes too long without a check.  
**Priority:** Should Have  
**Related Requirement:** FR-CLS-05, BR-20  
**Preconditions:** Classrooms exist.  
**Acceptance Criteria:**
- The classroom list shows a last-checked date for every classroom.
- A classroom not checked within 7 days is flagged.
- A classroom checked within the last 7 days is not flagged.
- When an SA records a room check, the last-checked date updates and the flag is cleared.

**Dependencies:** US-CLS-01  
**Notes:** Use case: UC-CLS-03. Classes: `Classroom`, `RoomCheck`.

#### US-CLS-05: Search and Filter Classrooms

**Story ID:** US-CLS-05  
**Title:** Search and Filter Classrooms  
**Epic:** Room Checks and Search  
**User Role:** Student Assistant, Admin  
**User Story:** As a Student Assistant, I want to search and filter classrooms, so that I can quickly find a free, working room when someone needs one.  
**Priority:** Should Have  
**Related Requirement:** FR-CLS-09  
**Preconditions:** The user is logged in.  
**Acceptance Criteria:**
- The user can filter by building, type, capacity, status and free time slot, and combine filters.
- A classroom with a class in the selected time slot is not shown as free.
- Deactivated classrooms are not shown.
- The system displays a suitable message when no results are found.

**Dependencies:** US-CLS-01, US-CLS-06 or US-CLS-07  
**Notes:** Use case: UC-CLS-05. Classes: `Classroom`, `ScheduleEntry`.

### Epic 11: Class Schedules

#### US-CLS-06: Import the Class Schedule

**Story ID:** US-CLS-06  
**Title:** Import the Class Schedule  
**Epic:** Class Schedules  
**User Role:** Admin  
**User Story:** As an Admin, I want to import class schedule entries from a CSV file, so that I do not have to enter every class by hand.  
**Priority:** Must Have  
**Related Requirement:** FR-CLS-06, BR-19  
**Preconditions:** The Admin is logged in. The classrooms in the file exist.  
**Acceptance Criteria:**
- Valid rows are saved as schedule entries and the number accepted is shown.
- Invalid rows (e.g. unknown room) are rejected and listed with the reason; valid rows are still saved.
- A row that overlaps an active entry in the same room, same day and same term dates is rejected.
- Imported entries appear in the room timetable.

**Dependencies:** US-CLS-01  
**Notes:** Use case: UC-CLS-04. Classes: `ScheduleImport`, `ScheduleEntry`. The CSV comes from the registrar export (A-09).

#### US-CLS-07: Add, Edit or Cancel a Schedule Entry

**Story ID:** US-CLS-07  
**Title:** Add, Edit or Cancel a Schedule Entry  
**Epic:** Class Schedules  
**User Role:** Admin  
**User Story:** As an Admin, I want to add, edit and cancel schedule entries manually, so that I can fix mistakes and handle changes not in the CSV.  
**Priority:** Must Have  
**Related Requirement:** FR-CLS-07, BR-19  
**Preconditions:** The Admin is logged in. The classroom exists and is active.  
**Acceptance Criteria:**
- The Admin can add or edit an entry with course, instructor, room, day, time and term.
- An entry that overlaps another active entry in the same room on the same day within the same term dates is blocked and the conflict is shown.
- A cancelled entry is kept for history and no longer shown in timetables.
- Every add, edit and cancel is recorded in the audit log.

**Dependencies:** US-CLS-01  
**Notes:** Use case: UC-CLS-04. Classes: `ScheduleEntry`.

#### US-CLS-08: View a Room's Timetable

**Story ID:** US-CLS-08  
**Title:** View a Room's Timetable  
**Epic:** Class Schedules  
**User Role:** Student Assistant, Admin  
**User Story:** As a Student Assistant, I want to see a classroom's timetable by day or week, so that I know when I can work in the room without interrupting a class.  
**Priority:** Must Have  
**Related Requirement:** FR-CLS-08, BR-19  
**Preconditions:** The user is logged in. The classroom exists.  
**Acceptance Criteria:**
- The user can switch between day view and week view.
- Classes are listed in time order with course, instructor and time.
- Cancelled entries are not shown.
- The system displays a suitable message when a day has no classes.

**Dependencies:** US-CLS-06 or US-CLS-07  
**Notes:** Use case: UC-CLS-05. Classes: `ScheduleEntry`, `Classroom`.

### Epic 12: Reporting Issues

#### US-ISS-01: Record an Issue

**Story ID:** US-ISS-01  
**Title:** Record an Issue  
**Epic:** Reporting Issues  
**User Role:** Student Assistant  
**User Story:** As a Student Assistant, I want to record an issue for a classroom, and for a specific PC or monitor when known, so that a reported problem is not lost.  
**Priority:** Must Have  
**Related Requirement:** FR-ISS-01, FR-ISS-02, FR-ISS-03, BR-01, BR-21, BR-22, NFR-ISS-03  
**Preconditions:** The SA is logged in. The classroom exists and is active.  
**Acceptance Criteria:**
- The SA can enter classroom, optional PC or monitor, category, severity, description, reporter name, reporter type and contact.
- Category is one of Hardware, Software, Network, Room/Facility, Other; severity is one of Low, Medium, High, Critical.
- Only items installed in the selected classroom can be chosen.
- An issue missing classroom, category, severity, description or reporter name is rejected, and the message names the missing field next to it.
- The saved issue gets a unique ID, the logged-in user and the timestamp, and starts as Open.

**Dependencies:** US-CLS-01  
**Notes:** Use case: UC-ISS-01. Classes: `Issue`, `IssueCategory`, `Severity`, `IssueStatus`. UC-ISS-01 says equipment or room status is updated "if applicable"; the exact rule is not defined in the merged SP2 (Confirm).

#### US-ISS-02: List and Filter Issues

**Story ID:** US-ISS-02  
**Title:** List and Filter Issues  
**Epic:** Reporting Issues  
**User Role:** Student Assistant, Admin  
**User Story:** As a Student Assistant, I want to filter the issue list, so that I can see only the problems that matter right now, such as everything open in one lab.  
**Priority:** Must Have  
**Related Requirement:** FR-ISS-04, BR-22, NFR-ISS-02  
**Preconditions:** The user is logged in.  
**Acceptance Criteria:**
- The user can filter by status, classroom, item, category, severity and date, and combine filters.
- Each row shows the issue ID, classroom, item, severity, status and date.
- Issues past their target resolution time (Critical 1 day, High 3 days, Medium 7 days, Low 14 days) are shown as overdue.
- The system displays a suitable message when no results are found.
- The list loads within 2 seconds for up to 5,000 issues.

**Dependencies:** US-ISS-01  
**Notes:** Use case: UC-ISS-02. Classes: `Issue`.

### Epic 13: Handling Issues

#### US-ISS-03: Change an Issue's Status

**Story ID:** US-ISS-03  
**Title:** Change an Issue's Status  
**Epic:** Handling Issues  
**User Role:** Student Assistant, Admin  
**User Story:** As a Student Assistant, I want to move an issue through its statuses, so that everyone can see where the work stands.  
**Priority:** Must Have  
**Related Requirement:** FR-ISS-05, BR-23, A-12  
**Preconditions:** The user is logged in. The issue exists.  
**Acceptance Criteria:**
- Allowed transitions are: Open → Assigned → In Progress → Resolved → Closed; Open or Assigned → Rejected or Duplicate; Resolved → In Progress (reopen).
- Any other transition is blocked (e.g. Open → Closed).
- Closed, Rejected and Duplicate are final; no further changes are allowed.
- Only the Admin can assign, reject and close issues; an SA who tries receives an error message.
- Each status change is saved in the issue history with the user and time.

**Dependencies:** US-ISS-01  
**Notes:** Use case: UC-ISS-03, UC-ISS-04. Classes: `Issue`, `IssueUpdate`, `IssueStatus`.

#### US-ISS-04: Add Comments and Progress Notes

**Story ID:** US-ISS-04  
**Title:** Add Comments and Progress Notes  
**Epic:** Handling Issues  
**User Role:** Student Assistant, Admin  
**User Story:** As a Student Assistant, I want to add comments and progress notes to an issue, so that the next person knows what was already tried.  
**Priority:** Should Have  
**Related Requirement:** FR-ISS-06, BR-02  
**Preconditions:** The user is logged in. The issue exists.  
**Acceptance Criteria:**
- The user can add a comment or progress note to an issue.
- Each comment shows who wrote it and when.
- An empty comment cannot be posted.
- Comments cannot be deleted.

**Dependencies:** US-ISS-01  
**Notes:** Use case: UC-ISS-03. Classes: `IssueUpdate`.

#### US-ISS-05: Resolve an Issue

**Story ID:** US-ISS-05  
**Title:** Resolve an Issue  
**Epic:** Handling Issues  
**User Role:** Student Assistant, Admin  
**User Story:** As a Student Assistant, I want to resolve an issue with notes on what I did and have the equipment status updated, so that the fix is recorded and I do not update the equipment separately.  
**Priority:** Must Have  
**Related Requirement:** FR-ISS-07, FR-ISS-09, BR-23, NFR-ISS-05  
**Preconditions:** The user is logged in. The issue is In Progress.  
**Acceptance Criteria:**
- Resolving without resolution notes is rejected.
- With notes, the issue becomes Resolved and the user and time are saved.
- The item is set to the status chosen at resolution (default Working), only if no other unresolved issue references it.
- The issue change and the item status change are saved together or not at all.

**Dependencies:** US-ISS-03, US-CLS-03  
**Notes:** Use case: UC-ISS-03. Classes: `Issue`, `RoomEquipment`.

#### US-ISS-06: Mark Duplicates and Flag Repeat Problems

**Story ID:** US-ISS-06  
**Title:** Mark Duplicates and Flag Repeat Problems  
**Epic:** Handling Issues  
**User Role:** Student Assistant, Admin  
**User Story:** As a Student Assistant, I want to mark an issue as a duplicate of an earlier one and be warned when the same problem keeps happening, so that we do not fix the same thing twice and repeat problems get attention.  
**Priority:** Must Have  
**Related Requirement:** FR-ISS-08, BR-23  
**Preconditions:** The user is logged in. The issue is Open or Assigned. The original issue exists.  
**Acceptance Criteria:**
- Marking an issue Duplicate requires selecting an existing original issue.
- The duplicate is linked to the original.
- A Duplicate issue is final.
- When one issue happens more than the threshold (3) times, the system flags it and sends a notification.

**Dependencies:** US-ISS-01, US-ISS-03, US-NTF-01  
**Notes:** Use case: UC-ISS-04. Classes: `Issue`. Recipient of the repeat-problem notification is not defined in SP2 (Confirm).

#### US-ISS-07: View Issue History

**Story ID:** US-ISS-07  
**Title:** View Issue History  
**Epic:** Handling Issues  
**User Role:** Admin  
**User Story:** As an Admin, I want to see every status change and comment on an issue, so that I know exactly what happened and who did it.  
**Priority:** Must Have  
**Related Requirement:** FR-ISS-10, BR-02, NFR-ISS-04  
**Preconditions:** The issue exists.  
**Acceptance Criteria:**
- Every status change and comment is kept in the issue history with the user and time.
- The history is shown in time order on the issue.
- Issues and their history are never deleted and are kept at least 3 years.

**Dependencies:** US-ISS-03, US-ISS-04  
**Notes:** Use case: UC-ISS-03. Classes: `IssueUpdate`.

### Epic 14: Order Management

#### US-ORD-01: Flag Low-Stock Items for Ordering

**Story ID:** US-ORD-01  
**Title:** Flag Low-Stock Items for Ordering  
**Epic:** Order Management  
**User Role:** Student Assistant  
**User Story:** As a Student Assistant, I want the system to flag items that are almost out of stock, so that I do not have to check stock levels manually.  
**Priority:** Must Have  
**Related Requirement:** FR-ORD-01, FR-AST-14, BR-12, BR-16  
**Preconditions:** The item has a low-stock threshold.  
**Acceptance Criteria:**
- When an item's quantity falls below its threshold, the system flags the item.
- The flagged item is automatically added to an order (SP2 Section 6.4 note).
- An item cannot have more than one open order at the same time.
- A notification is created on the Notifications page.

**Dependencies:** US-AST-04, US-NTF-01  
**Notes:** Use case: UC-ORD-03. Classes: `StockMonitor`, `Consumable`, `OrderService`. The SP2 note says Gmail; SP2 Section 13 lists email as out of scope.

#### US-ORD-02: Track Orders and Their Status

**Story ID:** US-ORD-02  
**Title:** Track Orders and Their Status  
**Epic:** Order Management  
**User Role:** Student Assistant  
**User Story:** As a Student Assistant, I want to see every order and its status in one place, so that I can keep track of what has been requested and what has arrived.  
**Priority:** Must Have  
**Related Requirement:** FR-ORD-02, FR-ORD-05, BR-01, BR-02, BR-12  
**Preconditions:** The SA is logged in.  
**Acceptance Criteria:**
- The SA can create an order; it is saved as Requested with a unique order ID.
- The SA can move an order through its statuses: Requested, Ordered, Partially Arrived, Arrived, Cancelled.
- The order table shows each order's ID, item, quantity and current status, including all statuses.
- Orders are never deleted.
- Each status change is recorded in the audit log with the user and time.

**Dependencies:** US-USR-01  
**Notes:** Use case: UC-ORD-01. Classes: `Order`, `OrderStatus`, `OrderService`.

#### US-ORD-03: Receive an Order

**Story ID:** US-ORD-03  
**Title:** Receive an Order  
**Epic:** Order Management  
**User Role:** Student Assistant  
**User Story:** As a Student Assistant, I want the inventory quantity updated automatically when an order arrives, so that I do not have to update it by hand.  
**Priority:** Must Have  
**Related Requirement:** FR-ORD-03, FR-AST-13, BR-03  
**Preconditions:** The order exists and has not arrived yet.  
**Acceptance Criteria:**
- When an order's status changes to Arrived, the received quantity is added to the inventory.
- The updated quantity is shown on the inventory page right after the change.
- The automatic quantity change is recorded in the audit log with the order ID.

**Dependencies:** US-ORD-02, US-AST-04  
**Notes:** Use case: UC-ORD-02. Classes: `Order`, `OrderService`, `Consumable`, `StockTransaction`.

#### US-ORD-04: Search and Filter Orders

**Story ID:** US-ORD-04  
**Title:** Search and Filter Orders  
**Epic:** Order Management  
**User Role:** Student Assistant  
**User Story:** As a Student Assistant, I want to search and filter orders, so that I can find a specific order quickly.  
**Priority:** Must Have  
**Related Requirement:** FR-ORD-04  
**Preconditions:** The SA is logged in.  
**Acceptance Criteria:**
- The SA can search orders by order ID or item.
- The SA can filter orders by status.
- The system displays a suitable message when no results are found.

**Dependencies:** US-ORD-02  
**Notes:** Use case: UC-ORD-01. Classes: `Order`.

### Epic 15: Report Management

#### US-RPT-01: Create a Report

**Story ID:** US-RPT-01  
**Title:** Create a Report  
**Epic:** Report Management  
**User Role:** Student Assistant  
**User Story:** As a Student Assistant, I want to create a new report, so that the team can see what happened and stay informed.  
**Priority:** Must Have  
**Related Requirement:** FR-RPT-01, FR-RPT-09  
**Preconditions:** The SA is logged in.  
**Acceptance Criteria:**
- The SA can create a new report.
- All mandatory fields are required before submitting.
- The report is saved with status Submitted and a unique report ID.
- A confirmation message is displayed.

**Dependencies:** US-USR-01  
**Notes:** Use case: UC-RPT-01. Classes: `Report`, `DailyReport`, `ReportService`.

#### US-RPT-02: Group Reports by Project

**Story ID:** US-RPT-02  
**Title:** Group Reports by Project  
**Epic:** Report Management  
**User Role:** Admin  
**User Story:** As an Admin, I want reports grouped by project, so that I can review all reports for one project together.  
**Priority:** Should Have  
**Related Requirement:** FR-RPT-02  
**Preconditions:** The Admin is logged in.  
**Acceptance Criteria:**
- A report can be linked to a project.
- The Admin can view reports grouped by project.
- Selecting a project shows all reports linked to it.
- Reports not linked to a project are shown in a separate group.

**Dependencies:** US-RPT-01, US-PRJ-01  
**Notes:** Use case: UC-RPT-01. Classes: `Report`, `Project`, `ReportService`.

#### US-RPT-03: Notify Reviewers of a Submitted Report

**Story ID:** US-RPT-03  
**Title:** Notify Reviewers of a Submitted Report  
**Epic:** Report Management  
**User Role:** Admin  
**User Story:** As an Admin assigned to review reports, I want to be notified when a report is submitted, so that I can review it promptly.  
**Priority:** Must Have  
**Related Requirement:** FR-RPT-03  
**Preconditions:** A report has assigned reviewers.  
**Acceptance Criteria:**
- When a report is submitted, each assigned reviewer receives a notification.
- The notification includes the report ID.
- The notification appears on the Notifications page.

**Dependencies:** US-RPT-01, US-NTF-01  
**Notes:** Use case: UC-RPT-01. Classes: `ReportService`, `NotificationService`.

#### US-RPT-04: Change a Report's Status

**Story ID:** US-RPT-04  
**Title:** Change a Report's Status  
**Epic:** Report Management  
**User Role:** Admin  
**User Story:** As an Admin, I want to change a report's status, so that the author and team know the outcome of the review.  
**Priority:** Must Have  
**Related Requirement:** FR-RPT-04, BR-03  
**Preconditions:** The Admin is logged in. The report exists.  
**Acceptance Criteria:**
- A report's status is one of Submitted, Reviewed, Rejected, Passed.
- The Admin can change a report's status.
- The new status is saved and shown on the report.
- The status change is recorded in the audit log with the user and time.
- A confirmation message is displayed.

**Dependencies:** US-RPT-01  
**Notes:** Use case: UC-RPT-01 (Admin reviews). Classes: `Report`, `ReportStatus`.

#### US-RPT-05: Create a Report from a Daily Template

**Story ID:** US-RPT-05  
**Title:** Create a Report from a Daily Template  
**Epic:** Report Management  
**User Role:** Student Assistant  
**User Story:** As a Student Assistant on the morning shift, I want to start the morning report from a template, so that I complete the daily checklist quickly and consistently.  
**Priority:** Should Have  
**Related Requirement:** FR-RPT-05  
**Preconditions:** The user is logged in. A daily report template exists.  
**Acceptance Criteria:**
- The system provides daily report templates, such as the morning report.
- The user can create a report from a template with the template's checklist pre-filled.
- The report created from the template is saved like any other report.

**Dependencies:** US-RPT-01  
**Notes:** Use case: UC-RPT-01. Classes: `ReportTemplate`, `DailyReport`.

#### US-RPT-06: Search and Filter Reports

**Story ID:** US-RPT-06  
**Title:** Search and Filter Reports  
**Epic:** Report Management  
**User Role:** Admin, Student Assistant  
**User Story:** As an Admin, I want to search and filter reports, so that I can find a specific report later.  
**Priority:** Must Have  
**Related Requirement:** FR-RPT-08, FR-RPT-09  
**Preconditions:** The user is logged in.  
**Acceptance Criteria:**
- The user can search reports by report ID or keyword.
- The user can filter reports by status, project and date.
- The system displays a suitable message when no results are found.

**Dependencies:** US-RPT-01  
**Notes:** Use case: UC-RPT-01. Classes: `ReportService`.

#### US-RPT-07: Receive the Monthly Summary

**Story ID:** US-RPT-07  
**Title:** Receive the Monthly Summary  
**Epic:** Report Management  
**User Role:** Admin  
**User Story:** As an Admin, I want the system to send a monthly summary automatically, so that I can review the month's reports and orders without compiling them myself.  
**Priority:** Should Have  
**Related Requirement:** FR-RPT-07, BR-17  
**Preconditions:** Reports or orders exist for the month.  
**Acceptance Criteria:**
- The system generates a summary of the month's reports and orders automatically.
- The summary is sent only at the end of each month.

**Dependencies:** US-RPT-01, US-ORD-02  
**Notes:** Use case: UC-RPT-02. Classes: `MonthlySummaryReport`, `ReportService`.

### Epic 16: Audit

#### US-RPT-08: View Audit History

**Story ID:** US-RPT-08  
**Title:** View Audit History  
**Epic:** Audit  
**User Role:** Admin, Student Assistant  
**User Story:** As an Admin, I want to view and search the audit history of all tracked activities, so that I can trace any change back to who made it and when.  
**Priority:** Must Have  
**Related Requirement:** FR-RPT-06, FR-RPT-08, FR-RPT-09, FR-USR-06, BR-02, BR-03  
**Preconditions:** The user is logged in.  
**Acceptance Criteria:**
- The audit history includes all tracked activities, including tasks, orders, reports and their progress.
- Each audit record has a unique ID and shows the user, action, record, old and new values, and timestamp.
- Automatic changes also show the triggering event (e.g. the issue ID).
- The user can search and filter audit records.
- Audit records cannot be edited or deleted and are kept permanently.

**Dependencies:** US-USR-01  
**Notes:** Use case: UC-RPT-03. Classes: `AuditRecord`, `AuditLog`. Audit storage is shared by all pages (A-13).

---

## 5. Story Refinement Check

Each story was checked against Guidance Section 10: it names the user role and benefit, covers one main goal, has measurable acceptance criteria using SP2 values, lists dependencies, has a priority, and links to its SP2 requirement and use case. Effort estimates are added by the team during sprint planning.

## 6. INVEST Checklist

✓ = met · ~ = met with a noted dependency

| Story | I | N | V | E | S | T | Note |
|---|---|---|---|---|---|---|---|
| US-AST-01 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | |
| US-AST-02 | ~ | ✓ | ✓ | ✓ | ✓ | ✓ | Needs an existing item |
| US-AST-03 | ~ | ✓ | ✓ | ✓ | ✓ | ✓ | Needs item data |
| US-AST-04 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | |
| US-AST-05 | ~ | ✓ | ✓ | ✓ | ~ | ✓ | Largest AST story; can split checkout and eligibility checks |
| US-AST-06 | ~ | ✓ | ✓ | ✓ | ✓ | ✓ | Needs US-AST-05 |
| US-AST-07 | ~ | ✓ | ✓ | ✓ | ✓ | ✓ | Needs US-AST-05 |
| US-AST-08 | ~ | ✓ | ✓ | ✓ | ✓ | ✓ | Needs loan data |
| US-AST-09 | ~ | ✓ | ✓ | ✓ | ✓ | ✓ | Needs loan data |
| US-AST-10 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | |
| US-AST-11 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | |
| US-USR-01 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | |
| US-USR-02 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | |
| US-USR-03 | ~ | ✓ | ✓ | ✓ | ✓ | ✓ | Needs US-USR-02 for forced change |
| US-USR-04 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | |
| US-USR-05 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | |
| US-USR-06 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | |
| US-PRJ-01 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | |
| US-PRJ-02 | ~ | ✓ | ✓ | ✓ | ✓ | ✓ | Needs US-PRJ-01 |
| US-PRJ-03 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | |
| US-PRJ-04 | ~ | ✓ | ✓ | ✓ | ✓ | ✓ | Needs US-PRJ-03 |
| US-PRJ-05 | ~ | ✓ | ✓ | ✓ | ✓ | ✓ | Needs US-PRJ-03 |
| US-PRJ-06 | ~ | ✓ | ✓ | ✓ | ✓ | ✓ | Needs project/task data |
| US-PRJ-07 | ~ | ✓ | ✓ | ✓ | ✓ | ✓ | Needs US-PRJ-04 |
| US-NTF-01 | ~ | ✓ | ✓ | ✓ | ✓ | ✓ | Needs task and issue events |
| US-NTF-02 | ~ | ✓ | ✓ | ✓ | ✓ | ✓ | Issue routing to confirm |
| US-NTF-03 | ~ | ✓ | ✓ | ~ | ✓ | ✓ | Shift details to confirm |
| US-NTF-04 | ~ | ✓ | ✓ | ✓ | ✓ | ✓ | Needs notifications |
| US-NTF-05 | ~ | ✓ | ✓ | ✓ | ✓ | ✓ | Needs US-NTF-04 |
| US-NTF-06 | ~ | ✓ | ✓ | ✓ | ✓ | ✓ | Needs project events |
| US-NTF-07 | ~ | ✓ | ✓ | ~ | ✓ | ✓ | Email scope conflict to resolve |
| US-CLS-01 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | |
| US-CLS-02 | ~ | ✓ | ✓ | ✓ | ✓ | ✓ | Needs US-CLS-01 |
| US-CLS-03 | ~ | ✓ | ✓ | ✓ | ✓ | ✓ | Needs installed equipment |
| US-CLS-04 | ~ | ✓ | ✓ | ✓ | ✓ | ✓ | Needs room check records |
| US-CLS-05 | ~ | ✓ | ✓ | ✓ | ✓ | ✓ | Needs schedule data |
| US-CLS-06 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | |
| US-CLS-07 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | |
| US-CLS-08 | ~ | ✓ | ✓ | ✓ | ✓ | ✓ | Needs schedule data |
| US-ISS-01 | ✓ | ✓ | ✓ | ✓ | ~ | ✓ | Larger story (form + validation + ID) |
| US-ISS-02 | ~ | ✓ | ✓ | ✓ | ✓ | ✓ | Needs issue data |
| US-ISS-03 | ~ | ✓ | ✓ | ✓ | ✓ | ✓ | Needs US-ISS-01 |
| US-ISS-04 | ~ | ✓ | ✓ | ✓ | ✓ | ✓ | Needs US-ISS-01 |
| US-ISS-05 | ~ | ✓ | ✓ | ✓ | ✓ | ✓ | Needs US-ISS-03, US-CLS-03 |
| US-ISS-06 | ~ | ✓ | ✓ | ✓ | ✓ | ✓ | Needs US-NTF-01 |
| US-ISS-07 | ~ | ✓ | ✓ | ✓ | ✓ | ✓ | Needs issue updates |
| US-ORD-01 | ~ | ✓ | ✓ | ✓ | ✓ | ✓ | Needs US-AST-04, US-NTF-01 |
| US-ORD-02 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | |
| US-ORD-03 | ~ | ✓ | ✓ | ✓ | ✓ | ✓ | Needs US-ORD-02 |
| US-ORD-04 | ~ | ✓ | ✓ | ✓ | ✓ | ✓ | Needs order data |
| US-RPT-01 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | |
| US-RPT-02 | ~ | ✓ | ✓ | ✓ | ✓ | ✓ | Needs US-PRJ-01 |
| US-RPT-03 | ~ | ✓ | ✓ | ✓ | ✓ | ✓ | Needs US-NTF-01 |
| US-RPT-04 | ~ | ✓ | ✓ | ✓ | ✓ | ✓ | Needs US-RPT-01 |
| US-RPT-05 | ~ | ✓ | ✓ | ✓ | ✓ | ✓ | Needs US-RPT-01 |
| US-RPT-06 | ~ | ✓ | ✓ | ✓ | ✓ | ✓ | Needs report data |
| US-RPT-07 | ~ | ✓ | ✓ | ✓ | ✓ | ✓ | Needs report and order data |
| US-RPT-08 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | |

## 7. Definition of Done

A user story is complete when:

- The required functionality has been implemented.
- The code follows the project's object-oriented design (NFR-RPT-04, NFR-CLS-03).
- Input validation has been added: invalid input shows a clear inline error message and nothing is saved (NFR-AST-03, NFR-ISS-03, NFR-RPT-03).
- Every acceptance criterion has been tested, including a failing case for each business rule in the story.
- Every create, update and status change records the logged-in user and timestamp in the audit log (FR-USR-06, BR-03).
- Records are never hard-deleted (BR-02, NFR-AST-04, NFR-ISS-04) and data remains available after the program is closed (NFR-RPT-02).
- An SA cannot reach Admin-only features by any route (FR-USR-05).
- Pages work on current Chrome, Edge, Firefox and Safari at widths ≥ 768 px (NFR-AST-05, NFR-CLS-02).
- Related classes and UML diagrams are updated if necessary.
- The feature does not introduce known errors.
- The project team and supervisor accept the result.

