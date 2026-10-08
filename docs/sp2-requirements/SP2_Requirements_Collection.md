# SP2 – Requirements Collection: IT Inventory Tracker

**Course:** CS487 – Object-Oriented Design and Analysis  
**Milestone:** SP2 – Requirements Collection  
**Team:** Duong Anh Nguyen (Tom), Zafar Azatov, Luke Gregory Pamaos, Nusratilloh Soliev

## Table of Contents
1. [Project Title](#1-project-title)
2. [Stakeholder Summary](#2-stakeholder-summary)
3. [Requirement-Gathering Methods](#3-requirement-gathering-methods)
4. [Requirement-Gathering Questions](#4-requirement-gathering-questions)
5. [Assumptions and Conventions](#5-assumptions-and-conventions)
6. [Functional Requirements](#6-functional-requirements)
7. [Non-Functional Requirements](#7-non-functional-requirements)
8. [Business Rules](#8-business-rules)
9. [Main Use Cases](#9-main-use-cases)
10. [Use-Case Specification](#10-use-case-specification)
11. [Proposed Object-Oriented Classes](#11-proposed-object-oriented-classes)
12. [Acceptance Criteria](#12-acceptance-criteria)
13. [Out-of-Scope Requirements](#13-out-of-scope-requirements)
14. [Validation](#14-validation)

---

## 1. Project Title

IT Inventory Tracker

| Pages | ID prefix | Owner |
|---|---|---|
| Assets & Lending | AST | Zafar Azatov |
| Login & Users | USR | Zafar Azatov |
| Projects & Tasks | PRJ | Luke Gregory Pamaos |
| Notifications | NTF | Luke Gregory Pamaos |
| Classrooms & Schedules | CLS | Nusratilloh Soliev |
| Issue Logs | ISS | Nusratilloh Soliev |
| Orders | ORD | Duong Anh Nguyen (Tom) |
| Reports & Audit | RPT | Duong Anh Nguyen (Tom) |

## 2. Stakeholder Summary

| Code | Stakeholder | Role | Pages |
|---|---|---|---|
| ITS | IT Supervisor (Admin) | System user with full access. Manages user accounts, classrooms, class schedules, and lending policy; retires items; assigns and closes issues; approves orders; reviews reports, audits, and monthly summaries; sets up projects and assigns tasks. | All |
| SA | Student Assistant | Daily system user. Registers, lends, and returns items; issues supplies; installs classroom equipment and records room checks; records and resolves issues; creates daily reports; tracks and receives orders; works on assigned tasks and reads notifications. | All |

**Actors:** IT Supervisor (Admin), Student Assistant. Admin can do everything an SA can.

## 3. Requirement-Gathering Methods

- **Document review:** examine existing forms, tickets, and documents used for reports and orders.
- **Questionnaires:** collect common needs for a tracking system from IT department staff.
- **Use-case discussions:** describe typical interactions between users and the system.

## 4. Requirement-Gathering Questions

Questions asked of the IT Supervisor and Student Assistants for each page.

### 4.1 Assets & Lending (AST) — Zafar Azatov

| ID | Topic | Question |
|---|---|---|
| Q-AST-01 | Item records | What details are recorded for each item? |
| Q-AST-02 |  | Which item types do we track? |
| Q-AST-03 |  | How are locations described (building and room, closet, rack, desk)? |
| Q-AST-04 |  | Is there existing data (Excel/CSV) to import? |
| Q-AST-05 | Consumables | Are consumables (cables, toner, adapters) tracked by quantity? |
| Q-AST-06 | Lending | How are items lent out today? |
| Q-AST-07 |  | What is recorded at checkout and return? |
| Q-AST-08 | Lost, damaged, retired | What is the process for a lost or damaged item, and who approves it? |
| Q-AST-09 |  | Who can retire an item, and what happens to it and its history? |

### 4.2 Login & Users (USR) — Zafar Azatov

| ID | Topic | Question |
|---|---|---|
| Q-USR-01 | Accounts | What information does a user account need (name, school email, school ID, role)? |
| Q-USR-02 |  | Who creates accounts? Can users self-register? |
| Q-USR-03 |  | What roles exist and what can each do? |
| Q-USR-04 |  | What happens to SA accounts when they graduate or leave the job? |
| Q-USR-05 | Login | How do users log in: username + password, school email, school ID, SSO? |
| Q-USR-06 |  | What are the password rules (length, complexity, expiry)? |
| Q-USR-07 |  | Should accounts lock after failed attempts? How many, and for how long? |
| Q-USR-08 |  | How are forgotten passwords handled? |
| Q-USR-09 |  | Should sessions time out after inactivity? How long? |
| Q-USR-10 | Accountability | Must every change be tied to the logged-in user? Is shared login ever allowed? |

### 4.3 Projects & Tasks (PRJ) — Luke Gregory Pamaos

| ID | Topic | Question |
|---|---|---|
| Q-PRJ-01 | Fields | Which project/task fields are mandatory? Can tasks/projects omit due dates? |
| Q-PRJ-02 | Status | What are the final project and task statuses, and can completed work be reopened? |
| Q-PRJ-03 | Assignment | Can one task have multiple assignees? Who may assign/reassign, if the Admin and SAs have equal access? |
| Q-PRJ-04 | Templates | Which values belong in a project template, and are task copies editable? |

### 4.4 Notifications (NTF) — Luke Gregory Pamaos

| ID | Topic | Question |
|---|---|---|
| Q-NTF-01 | Shifts | Which shifts exist, where is the roster stored, and when is each shift notification sent? |
| Q-NTF-02 |  | What should shift summaries contain, including overdue or unassigned work? |
| Q-NTF-03 | Recipients | Which task/issue events notify which recipients? Should the actor be notified about their own action? |
| Q-NTF-04 | Read state | Can users mark all as read, delete notifications, or follow a notification to the work item? |
| Q-NTF-05 | Retention | How long are notifications retained, and are read-state changes part of the global audit history? |

### 4.5 Classrooms & Schedules (CLS) — Nusratilloh Soliev

| ID | Topic | Question |
|---|---|---|
| Q-CLS-01 | Rooms and equipment | Which rooms are covered (lecture rooms, computer labs)? |
| Q-CLS-02 |  | Which room equipment do we track (student PCs, teaching PC, monitors, projector)? |
| Q-CLS-03 | Status | What statuses can a PC or monitor have? |
| Q-CLS-04 | Room checks | How often is each room checked, by whom, and should overdue checks be flagged? |
| Q-CLS-05 |  | What does a check cover (power, display, peripherals, network, login, projector)? |
| Q-CLS-06 | Schedule | Where does schedule data come from, and in what format? |
| Q-CLS-07 |  | What fields does a schedule entry need, do classes repeat weekly, and how is the schedule used (room timetable, free-room search, broken-room warning)? |
| Q-CLS-08 |  | Does re-importing the schedule replace or update existing entries? |

### 4.6 Issue Logs (ISS) — Nusratilloh Soliev

| ID | Topic | Question |
|---|---|---|
| Q-ISS-01 | Reporting | Who reports issues today, and how (walk-in, email, phone, paper note)? |
| Q-ISS-02 |  | Do reporters need an account, or does an SA record the issue for them? |
| Q-ISS-03 |  | What information does an issue need (classroom, equipment, category, severity, description, reporter, date)? |
| Q-ISS-04 |  | Which categories exist (hardware, software, network, room/facility, other)? |
| Q-ISS-05 |  | How is severity decided, and what does each level mean? |
| Q-ISS-06 |  | Can one issue cover several items, or is it one issue per item? |
| Q-ISS-07 | Handling | What issue statuses exist? |
| Q-ISS-08 |  | Who assigns, resolves, closes, or rejects issues? |
| Q-ISS-09 |  | What must be recorded on resolution (what was done, who, when)? |
| Q-ISS-10 |  | Is there a target time to fix an issue for each severity? |
| Q-ISS-11 |  | Can a resolved issue be reopened? For how long? |
| Q-ISS-12 |  | Can an issue be deleted, or only closed or rejected? |
| Q-ISS-13 | Duplicates and effects | How should duplicate reports be handled (warn, merge, link)? |
| Q-ISS-14 |  | Should a new issue automatically change the status of the related PC or monitor? |
| Q-ISS-15 |  | Should it change the classroom status? What if the problem is with the room, not an item (no power, projector)? |
| Q-ISS-16 |  | When an issue is resolved, should the item return to Working automatically, even if another issue is still open on it? |
| Q-ISS-17 |  | Who needs to be notified of new or resolved issues? |
| Q-ISS-18 |  | Where should issue changes appear in the audit log? |

### 4.7 Orders (ORD) — Duong Anh Nguyen (Tom)

| ID | Topic | Question |
|---|---|---|
| Q-ORD-01 | Status | What statuses can an order have? |
| Q-ORD-02 | Arrival | When an order arrives, what is the next step? |
| Q-ORD-03 | Flagging | When should an order be flagged? What event triggers an automatic order? |

### 4.8 Reports & Audit (RPT) — Duong Anh Nguyen (Tom)

| ID | Topic | Question |
|---|---|---|
| Q-RPT-01 | Status | What statuses can a report have? |
| Q-RPT-02 | Content | What components does a report contain, and which reports are required? |
| Q-RPT-03 |  | Why do we need each report? |
| Q-RPT-04 | Format | What format should reports use? Should they be editable after submission? |
| Q-RPT-05 | Workflow | What is the next step after a report is received? |

## 5. Assumptions and Conventions

To be confirmed with the IT Supervisor.

**Users and access**
- A-01: Two roles exist this semester: **Admin** (IT Supervisor) and **Student Assistant**. The Admin can do everything an SA can. On the PRJ and NTF pages, both have the same access.
- A-02: Only logged-in Admins and SAs use the system. Borrowers and issue reporters do not log in; they contact IT in person, by email, or by phone, and an SA records the loan or issue for them.
- A-03: Login uses school email + password (SSO can be done using Google Firebase).

**Assets and lending**
- A-04: Default loan length is 7 days for students, 30 days for faculty/staff.

**Classrooms and schedules**
- A-05: A classroom is a `Location` (building + room) from the AST page, extended with capacity, type, and check information.
- A-06: Classroom PCs and monitors are `Item` records (category Desktop or Monitor) with asset tags. Installing an item in a classroom does not change its `ItemStatus`.
- A-07: Equipment condition is a separate status: **Working, Faulty, Under Repair, Out of Service, Missing**.
- A-08: Each computer lab is checked at least once every 7 days by an SA.
- A-09: The schedule comes from a registrar CSV export imported by the Admin; manual entries are also allowed. It is used for timetables, finding free rooms, and warnings. It does not book rooms.

**Issues**
- A-10: Issue categories: Hardware, Software, Network, Room/Facility, Other. Severity: Low, Medium, High, Critical.
- A-11: Issue statuses: Open, Assigned, In Progress, Resolved, Closed, Duplicate, Rejected.
- A-12: SAs and the Admin resolve issues; only the Admin assigns, rejects, and closes them.

**Shared services**
- A-13: Audit log storage is shared by all pages and viewed on the Reports & Audit page (RPT). Notifications are handled by the Notifications page (NTF).

**Conventions**
- Items marked **Confirm** need an answer from the team or instructor before they are treated as final.

## 6. Functional Requirements

Priority: **Must Have** · **Should Have**

### 6.1 Assets & Lending (AST), Login & Users (USR) — Zafar Azatov

#### Assets & Lending

| ID | Requirement | Priority |
|---|---|---|
| FR-AST-01 | The system shall let an SA register an item with asset tag, serial number, model, manufacturer, category, location, status, purchase date, warranty end date, and notes. | Must Have |
| FR-AST-02 | The system shall reject an item whose asset tag already exists. | Must Have |
| FR-AST-03 | The system shall let an SA edit an item's details. | Must Have |
| FR-AST-04 | The system shall let users search and filter items by asset tag, serial number, model, category, location, and status. | Must Have |
| FR-AST-05 | The system shall track consumables by quantity, recording each stock-in and stock-out. | Must Have |
| FR-AST-06 | The system shall let an SA lend out an item, recording borrower name, school ID, email, borrower type, checkout date, due date, condition out, and the SA who processed it. | Must Have |
| FR-AST-07 | The system shall let an SA record a return, capturing return date, condition in, notes, and the SA who received it. | Must Have |
| FR-AST-08 | The system shall list all overdue loans (due date passed, not returned). | Must Have |
| FR-AST-09 | The system shall show loan history per item and per borrower. | Should Have |
| FR-AST-10 | The system shall let an SA report an item as Lost or Damaged with a description and date. | Must Have |
| FR-AST-11 | The system shall let the Admin retire an item with a reason and date. | Must Have |
| FR-AST-12 | The system shall let an SA extend a loan's due date once, within the maximum loan length. | Should Have |
| FR-AST-13 | The system should automatically update the quantity when an order is set to received. | Must Have |
| FR-AST-14 | The system should automatically flag and send a notification when the quantity of an item is under the threshold. | Must Have |

#### Login & Users

| ID | Requirement | Priority |
|---|---|---|
| FR-USR-01 | The system shall authenticate users with school email and password. | Must Have |
| FR-USR-02 | The system shall let a logged-in user log out. | Must Have |
| FR-USR-03 | The system shall let the Admin create user accounts with full name, school email, school ID, role, and optional access end date. | Must Have |
| FR-USR-04 | The system shall let the Admin change a user's role and deactivate or reactivate an account. | Must Have |
| FR-USR-05 | The system shall restrict actions by role (Admin, Student Assistant) (This is created in advance). | Must Have |
| FR-USR-06 | The system shall record the logged-in user and timestamp on every create, update, and status change. | Must Have |
| FR-USR-07 | The system shall lock an account for 15 minutes after 5 consecutive failed login attempts. | Should Have |
| FR-USR-08 | The system shall let a user change their own password. | Should Have |
| FR-USR-09 | The system shall let the Admin reset a user's password to a temporary one that must be changed at next login. | Should Have |

### 6.2 Projects & Tasks (PRJ), Notifications (NTF) — Luke Gregory Pamaos

#### Projects & Tasks (`PRJ`)

| ID | Requirement | Priority |
|---|---|---|
| FR-PRJ-01 | The system shall assign each project a unique project_id and use it to retrieve and update the project. An authenticated Admin or SA shall be able to create a project with a name, description, start date, optional due date, and status. | Must Have |
| FR-PRJ-02 | The system shall allow an Admin or SA to create and maintain a project template containing reusable task definitions, and to create a project from a selected template. Creating from a template shall create a new project and new task records based on the template. **Confirm:** whether template metadata includes default assignees, priorities, or relative due dates. | Must Have |
| FR-PRJ-03 | The system shall allow an Admin or SA to create a task either as a standalone task or linked to a project. A standalone task may be linked to a project later. Each task shall have a title, description, status, and optional due date. | Must Have |
| FR-PRJ-04 | The system shall allow an Admin or SA to assign or reassign a task to one or more Admins or SAs and show its current assignee(s). **Draft assumption—Confirm:** the proposal says tasks are assigned to team members but does not specify whether multiple assignees are permitted. | Must Have |
| FR-PRJ-05 | The system shall allow an Admin or SA to update a task's status and shall show task progress within the project. **Draft values—Confirm:** To Do, In Progress, and Complete. Define project completion as all project tasks Complete, unless the team chooses a different rule. | Must Have |
| FR-PRJ-06 | The system shall allow an Admin or SA to find projects and tasks by text and filter them by status, assignee, and due date. **Confirm:** required filters and whether reports/search share this behavior. | Should Have |
| FR-PRJ-07 | The system shall allow an Admin or SA to hand off an unfinished task to the Admin or SA taking over the work. The task shall keep its current status and retain its assignment history. | Must Have |

#### Notifications (`NTF`)

| ID | Requirement | Priority |
|---|---|---|
| FR-NTF-01 | When a task is newly assigned or an issue is reported, the system shall create a notification associated with that event. This supports the proposal's Observer-pattern examples of notifying users about new tasks and issues. | Must Have |
| FR-NTF-02 | The system shall route each notification to the applicable recipient(s) and display the recipient, event type, and related project/task/issue. **Draft routing—Confirm:** task assignment goes to the new assignee(s); issue notification goes to the issue reporter and/or designated Admin/SA group. Do not send to a fixed role until the team defines one. | Must Have |
| FR-NTF-03 | The system shall generate a scheduled-work notification for staff assigned to a shift when that shift begins, listing their work scheduled for that shift. **Confirm:** supported shifts, shift roster source, exact send time, and treatment of overdue/unassigned work. The proposal's morning classroom-check is an example, not a finalized schedule rule. | Must Have |
| FR-NTF-04 | The system shall provide an in-app list of a user's notifications and indicate which notifications are read and unread. A notification shall identify its creation time and related work item when one exists. | Must Have |
| FR-NTF-05 | The system shall allow a user to mark a notification read and unread. **Confirm:** whether users may delete notifications, mark all read, or open the linked work item directly. | Should Have |
| FR-NTF-06 | When a project is created, updated, or a user is added to it, the system shall notify the project’s members. Only members of that project shall receive these notifications. | Must Have |
| FR-NTF-07 | The system shall send each notification to the recipient’s registered email address as well as show it in the app. It shall record whether the email was delivered; email failure shall not remove the in-app notification. | Must Have |
| FR-NTF-08 | The system shall give each notification a unique notification_id and use it to find and update that notification. | Must Have |

### 6.3 Classrooms & Schedules (CLS), Issue Logs (ISS) — Nusratilloh Soliev

#### Classrooms & Schedules

| ID | Requirement | Priority |
|---|---|---|
| FR-CLS-01 | The system shall let the Admin add, edit and deactivate classrooms, each linked to a Location, with capacity and room type. | Must Have |
| FR-CLS-02 | The system shall let an SA move installed equipment to another classroom or remove it. | Should Have |
| FR-CLS-03 | The system shall let an SA or Admin set a monitor's condition status using the same list. | Must Have |
| FR-CLS-04 | The system shall require a reason for every condition change and record the user and timestamp in the audit log. | Must Have |
| FR-CLS-05 | The system shall show each classroom's last-checked date and flag classrooms not checked within 7 days. | Should Have |
| FR-CLS-06 | The system shall let the Admin import class schedule entries from a CSV file. | Must Have |
| FR-CLS-07 | The system shall let the Admin add, edit and cancel schedule entries manually. | Must Have |
| FR-CLS-08 | The system shall show a classroom's timetable by day or week. | Must Have |
| FR-CLS-09 | The system shall let users search and filter classrooms by building, type, capacity, status and free time slot. | Should Have |

#### Issue Logs

| ID | Requirement | Priority |
|---|---|---|
| FR-ISS-01 | The system shall let an SA record an issue for a classroom, optionally for one installed PC or monitor, with category, severity, description and reporter name, type and contact. | Must Have |
| FR-ISS-02 | The system shall reject an issue missing classroom, category, severity, description or reporter name, naming the missing field. | Must Have |
| FR-ISS-03 | The system shall assign each issue a unique ID and store the logged-in user and timestamp. | Must Have |
| FR-ISS-04 | The system shall list issues with filters by status, classroom, item, category, severity and date. | Must Have |
| FR-ISS-05 | The system shall let an SA or Admin change an issue's status following the allowed transitions (BR-23). | Must Have |
| FR-ISS-06 | The system shall let users add comments and progress notes to an issue. | Should Have |
| FR-ISS-07 | The system shall require resolution notes to resolve an issue. | Must Have |
| FR-ISS-08 | The system shall let an SA or Admin mark an issue as Duplicate and link it to the original and auto flag and send a notification when one issue happens more than the threshold (3). | Must Have |
| FR-ISS-09 | The system shall set the item to the status chosen at resolution (default Working), only if no other unresolved issue references the item. | Must Have |
| FR-ISS-10 | The system shall keep a history of every status change and comment on an issue with user and time. | Must Have |

### 6.4 Orders (ORD), Reports & Audit (RPT) — Duong Anh Nguyen (Tom)

#### Reports & Audit

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

#### Orders

| ID | Requirement | Priority |
|---|---|---|
| FR-ORD-01 | The system shall link orders to the inventory and automatically flag items that are almost out of stock. | Must Have |
| FR-ORD-02 | The system shall track every order and its status. | Must Have |
| FR-ORD-03 | When an order's status changes to Arrived, the system shall automatically add the received quantity to the inventory. | Must Have |
| FR-ORD-04 | The system shall allow users to search and filter orders. | Must Have |
| FR-ORD-05 | The system shall assign a unique ID to every order. | Must Have |

> **Note:** "Almost out of stock" means the quantity of an item is less than a threshold. The item is then automatically added to an order, and a notification is sent through Gmail and on the Notifications page.

## 7. Non-Functional Requirements

### 7.1 Assets & Lending (AST), Login & Users (USR) — Zafar Azatov

| ID | Category | Requirement | Priority |
|---|---|---|---|
| NFR-AST-01 | Performance | Inventory search returns results within 2 seconds for up to 5,000 items. | Should Have |
| NFR-AST-02 | Usability | An SA can complete a checkout in under 1 minute and no more than 3 screens. | Should Have |
| NFR-AST-03 | Usability | Required fields show clear inline error messages on invalid input. | Must Have |
| NFR-AST-04 | Reliability | Item and loan records are never hard-deleted; history is kept at least 3 years. | Must Have |
| NFR-AST-05 | Compatibility | Pages work on current Chrome, Edge, Firefox, Safari at widths ≥ 768 px. | Should Have |
| NFR-USR-01 | Security | Passwords are stored only as salted hashes (bcrypt or Argon2). | Must Have |
| NFR-USR-02 | Security | Sessions expire after 30 minutes of inactivity. | Should Have |
| NFR-USR-03 | Security | Login errors do not reveal whether the email exists. | Should Have |
| NFR-USR-04 | Performance | Login completes within 2 seconds under normal load. | Should Have |

### 7.2 Projects & Tasks (PRJ), Notifications (NTF) — Luke Gregory Pamaos

| ID | Requirement | Priority |
|---|---|---|
| NFR-PRJ-01 | Every create, edit, assignment, reassignment, and status change to a project, task, or template shall be attributable to the authenticated user and recorded in the audit history with when, what, and old/new values where applicable. The proposal requires a complete audit history and describes these AuditLog fields. | Must Have |
| NFR-NTF-01 | Every notification creation and user read-state change shall be attributable to a user or system event and have a recorded timestamp in the audit history. The notification record shall identify its recipient and triggering event so the notification can be traced. **Confirm:** whether read-state changes are included in the project's global audit history. | Must Have |
| NFR-PRJ-02 | Only an authenticated Admin or SA shall use PRJ and NTF functions. Both shall have the same access on these pages. | Must Have |
| NFR-PRJ-03 | Project and task records shall be searchable/filterable as specified in FR-PRJ-06. **Confirm:** expected data volume and response-time targets before adding a performance threshold. | Should Have |

### 7.3 Classrooms & Schedules (CLS), Issue Logs (ISS) — Nusratilloh Soliev

| ID | Category | Requirement | Priority |
|---|---|---|---|
| NFR-CLS-01 | Usability | An SA can change an equipment status in no more than 3 clicks from the classroom page. | Should Have |
| NFR-CLS-02 | Compatibility | Pages work on current Chrome, Edge, Firefox, Safari at widths ≥ 768 px. | Should Have |
| NFR-CLS-03 | Maintainability | UI, business logic and storage are separate layers; object data is encapsulated. | Should Have |
| NFR-ISS-01 | Usability | An SA can record an issue in under 1 minute with no more than 6 required fields. | Should Have |
| NFR-ISS-02 | Performance | The issue list loads within 2 seconds for up to 5,000 issues. | Should Have |
| NFR-ISS-03 | Usability | Required fields show clear inline error messages. | Must Have |
| NFR-ISS-04 | Reliability | Issues and their history are never hard-deleted; kept at least 3 years. | Must Have |
| NFR-ISS-05 | Integrity | An issue change and the resulting equipment status change are saved together or not at all. | Must Have |

### 7.4 Orders (ORD), Reports & Audit (RPT) — Duong Anh Nguyen (Tom)

These apply to both pages.

| ID | Requirement | Priority |
|---|---|---|
| NFR-RPT-01 | The system shall be easy to use and understand. | Must Have |
| NFR-RPT-02 | The system shall store all data within its own database, and the data shall remain available after the program is closed. | Must Have |
| NFR-RPT-03 | The system shall display a clear error message for invalid input. | Must Have |
| NFR-RPT-04 | The design shall follow object-oriented principles. | Must Have |

## 8. Business Rules

| ID | Area | Business rule |
|---|---|---|
| BR-01 | Records | Every record (item, loan, user, project, task, notification, classroom, issue, order, report, audit record) has a unique ID and is found and updated by that ID. Asset tags are unique and never reused. |
| BR-02 |  | Records are never deleted: items are retired, accounts and classrooms are deactivated, schedule entries are cancelled, issues are closed, and audit records are kept permanently. |
| BR-03 |  | Every change records the user, timestamp, old and new values, and reason where required, and is written to the audit log. Automatic changes also record the triggering event (e.g. the issue ID). |
| BR-04 | Access | Only a logged-in Admin or SA can add or change records. Each person has one account; shared accounts are not allowed. Deactivated or locked accounts cannot log in. |
| BR-05 |  | Only the Admin creates accounts, assigns roles, deactivates accounts, and retires items. At least one active Admin account must always exist. |
| BR-06 |  | Passwords are at least 10 characters and contain letters and digits. An SA's account is deactivated within 1 business day of leaving the job. |
| BR-07 | Lending | Only items with status **Available** can be lent out. Retired items are read-only and cannot be lent. |
| BR-08 |  | Default loan length: 7 days (students), 30 days (faculty/staff). Max one extension of 7 days. |
| BR-09 |  | A student borrower may hold at most 2 items at a time. A borrower with an overdue item cannot borrow until it is returned. |
| BR-10 |  | An item returned in damaged condition is set to **Damaged**, not Available. |
| BR-11 | Stock and orders | Consumables are issued, not lent, and are not returned. Consumable quantity cannot go below zero. |
| BR-12 |  | An item cannot have more than one open order at the same time. |
| BR-13 | Projects | A project template is a reusable set of task definitions. Creating a project from it copies the tasks; later edits to the project do not change the template. |
| BR-14 |  | A task may be standalone or linked to one project, is assigned to one or more Admins or SAs, and keeps its status and assignment history when reassigned. |
| BR-15 |  | Task statuses are To Do, In Progress, and Complete. A project is complete only when all of its tasks are Complete. |
| BR-16 | Notifications | Every notification has one recipient and one triggering event. Project notifications go only to project members; shift notifications are generated from the current shift roster. Email delivery is in addition to the in-app notification. |
| BR-17 |  | The monthly summary is sent only at the end of each month. |
| BR-18 | Classrooms | A classroom is one Location (building + room). A classroom with installed equipment or future classes cannot be deactivated. A retired item is removed from its classroom and ignored in status calculation. |
| BR-19 |  | Two active schedule entries cannot overlap in the same room on the same day within the same term dates. Cancelled entries are kept for history and excluded from timetables. |
| BR-20 |  | Each computer lab must be checked at least once every 7 days. |
| BR-21 | Issues | Every issue refers to one classroom and, optionally, one item installed in that classroom. The reporter's name and type are always stored. |
| BR-22 |  | Severity is Low, Medium, High, or Critical (Critical means scheduled classes cannot be held in the room). Target resolution time: Critical 1 day, High 3 days, Medium 7 days, Low 14 days. |
| BR-23 |  | Allowed transitions: Open → Assigned → In Progress → Resolved → Closed; Open or Assigned → Rejected or Duplicate; Resolved → In Progress (reopen). Closed, Rejected, and Duplicate are final. An issue cannot be Resolved without resolution notes, and a Duplicate must link to an existing original issue. |

## 9. Main Use Cases

| ID | Use case | Primary actor | Result |
|---|---|---|---|
| UC-AST-01 | Manage Item (register, update, retire) | SA (Admin retires) | Item saved with status Available, updated, or retired as read-only |
| UC-AST-02 | Search Inventory | Admin / SA | Matching items listed |
| UC-AST-03 | Lend Out and Return Item | SA | Loan opened with item On Loan, or closed with item Available or Damaged |
| UC-AST-04 | View Overdue Loans | Admin / SA | Overdue loans listed |
| UC-AST-05 | Manage Consumable Stock (issue, restock, track quantity) | SA | Stock quantity updated |
| UC-AST-06 | Report Lost or Damaged Item | SA | Item status Lost or Damaged with an incident record |
| UC-USR-01 | Log In / Log Out | Admin / SA | Authenticated session started or ended |
| UC-USR-02 | Manage User Account (create, deactivate) | Admin | Account created, or deactivated so it cannot log in |
| UC-USR-03 | Manage Password (change own, reset) | Admin / SA | Password updated, or temporary password set by the Admin |
| UC-PRJ-01 | Create Project from Template | Admin / SA | A new project and independent tasks are created from a reusable template |
| UC-PRJ-02 | Manage Task (create, update, assign, reassign) | Admin / SA | Task added or edited, assignees recorded, and assignees notified |
| UC-PRJ-03 | Update Task Progress | Admin / SA | Task status and project progress reflect the update |
| UC-NTF-01 | Send Notification (new work or issue, shift summary) | System | Notifications created for each recipient; staff on the active shift receive their work summary |
| UC-NTF-02 | Review and Mark Notification | Admin / SA | The user views a notification and updates its read state |
| UC-CLS-01 | Manage Classroom | Admin | Classroom created, updated, or deactivated |
| UC-CLS-02 | Manage Classroom Equipment (install, move, update status) | Admin / SA | Equipment placed or its condition changed; reason and user logged; room status recalculated |
| UC-CLS-03 | Record Room Check | SA | Check results saved; last-checked date updated |
| UC-CLS-04 | Manage Class Schedule (import, add, edit, cancel) | Admin | Schedule entries saved; rejected import rows listed |
| UC-CLS-05 | View Classrooms (search, timetable, dashboard, export) | Admin / SA | Matching classrooms, timetables, status counts, or CSV file shown |
| UC-ISS-01 | Report Issue | SA | Issue saved as Open; equipment or room status updated if applicable |
| UC-ISS-02 | View Issues (filter, summary) | Admin / SA | Matching issues, counts, and overdue issues shown |
| UC-ISS-03 | Handle Issue (assign, update, comment, resolve, reopen) | Admin / SA (Admin assigns) | Status, notes, and comments saved in issue history; equipment status set on resolution |
| UC-ISS-04 | Close Issue (mark duplicate, reject, close) | Admin / SA (Admin rejects and closes) | Issue linked as Duplicate, Rejected, or Closed |
| UC-ORD-01 | Manage Order (create, update status) | SA | Order recorded as Requested and moved through its statuses |
| UC-ORD-02 | Receive Order | SA | Order marked Arrived and the inventory quantity increases |
| UC-ORD-03 | Flag Low Stock | System | Items almost out of stock are flagged for ordering |
| UC-RPT-01 | Manage Report (create, review) | Admin / SA (Admin reviews) | Report saved, optionally from a daily template, and set to Reviewed, Rejected, or Passed |
| UC-RPT-02 | Send Monthly Summary | System | A summary of reports and orders is sent at month end |
| UC-RPT-03 | View Audit History | Admin / SA | Audit records matching the search or filter are displayed |

## 10. Use-Case Specification

### UC-AST-03 – Lend Out Item

| Field | Description |
|---|---|
| **Primary actor** | Student Assistant |
| **Stakeholders** | IT Supervisor (tracks equipment) |
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
- 7a. SA changes the due date → system accepts it only within the maximum loan length (BR-08).

**Exception flows**
- 2a. Asset tag not found → system shows "Item not found"; SA re-enters or cancels.
- 6a. Borrower has an overdue item → system blocks the loan and lists the overdue item (BR-09).
- 6b. Student already holds 2 items → system blocks the loan (BR-09).
- 9a. Save fails → no loan is created and the item stays Available.

**Related:** FR-AST-06, FR-AST-08, BR-07–BR-09, FR-USR-06

## 11. Proposed Object-Oriented Classes

| Page | Class | Main responsibilities |
|---|---|---|
| Shared | User | Store a staff member's account (name, school email, role, status); verify login, lock after failed attempts, and force a password change when required |
|  | Role (enum) | Admin, Student Assistant |
|  | Location | Describe a building, room, or storage area where items and classrooms are |
|  | AuditRecord | Store one change: user, action, entity, old and new values, timestamp, and status |
|  | AuditLog | Add and search audit records; never delete them |
| AST | Item | Store an asset's tag, serial number, model, category, location, and status; change status when lent, returned, reported, or retired |
|  | ItemStatus (enum) | Available, On Loan, Damaged, Lost, Retired |
|  | Category | Group items by type (e.g. Desktop, Monitor, Supply) and mark whether the type is consumable |
|  | Consumable | Track the quantity on hand of a supply and flag it when it falls below its reorder threshold |
|  | StockTransaction | Record each stock-in or stock-out of a consumable, with who did it and who received it |
|  | Borrower | Store a borrower's school ID, name, contact, and type, and check whether they may borrow |
|  | Loan | Record a checkout and return: item, borrower, dates, condition out and in, and staff involved; detect overdue loans |
|  | ItemIncident | Record a lost, damaged, or retired event for an item with its description and reporter |
| PRJ | Project | Group related tasks, track project status and dates, and record its originating template |
|  | Task | Represent one unit of work with a status and due date, standalone or linked to a project |
|  | ProjectTemplate | Hold a reusable set of task definitions and create new projects from it |
|  | TemplateTask | Represent one reusable task definition inside a template |
|  | TaskAssignment | Link a task to its assignees and keep the assignment history |
| NTF | Notification | Store one in-app message for one recipient, linked to its triggering event, with read or unread state |
|  | NotificationService | Create and route notifications from task, issue, project, and shift events; send email copies (Observer subscriber) |
| CLS | Classroom | Represent a room with its capacity, type, and active state; derive its status from its equipment; track the last check date |
|  | RoomEquipment | Link an installed PC or monitor to a classroom and track its condition |
|  | EquipmentCondition (enum) | Working, Faulty, Under Repair, Out of Service, Missing |
|  | RoomStatus (enum) | Available, Limited, Unusable, Closed (derived) |
|  | RoomCheck | Record a room check by an SA with its results for each piece of equipment |
|  | ScheduleEntry | Store one class meeting (course, instructor, room, day, time, term) and prevent overlaps |
|  | ScheduleImport | Import schedule entries from a CSV file and report accepted and rejected rows |
| ISS | Issue | Record a reported problem for a classroom or item; enforce allowed status transitions; update equipment status |
|  | IssueCategory (enum) | Hardware, Software, Network, Room/Facility, Other |
|  | Severity (enum) | Low, Medium, High, Critical |
|  | IssueStatus (enum) | Open, Assigned, In Progress, Resolved, Closed, Duplicate, Rejected |
|  | IssueUpdate | Record each status change or comment on an issue with the user and time |
| ORD | Order | Store item, quantity ordered and received, vendor, requester, dates, and status |
|  | OrderStatus (enum) | Requested, Ordered, Partially Arrived, Arrived, Cancelled |
|  | OrderService | Create orders, update status, receive orders, and prevent duplicate open orders |
|  | StockMonitor | Watch inventory quantities and flag items that fall below their threshold |
| RPT | Report (abstract) | Common report data: ID, title, author, project, status, created date |
|  | DailyReport | A report filled in by a student assistant, such as the morning report |
|  | MonthlySummaryReport | A report generated by the system at month end from reports and orders |
|  | ReportTemplate | A reusable checklist used to create daily reports |
|  | ReportStatus (enum) | Submitted, Reviewed, Rejected, Passed |
|  | ReportService | Create, group, review, and search reports; send the monthly summary |

## 12. Acceptance Criteria

| Requirement | Acceptance criterion |
|---|---|
| FR-AST-02 | Unique asset tag |
| FR-AST-06 | Lend out item |
| FR-AST-07 | Return item |
| FR-USR-01 | Log in |
| FR-USR-06 | Changes tied to user |
| FR-PRJ-02 | Create a project from a template |
| FR-NTF-01 | Create event notifications |
| FR-CLS-03 | Set PC status |
| FR-CLS-06 | Import schedule |
| FR-CLS-08 | Room timetable |
| FR-ISS-01 / FR-ISS-02 / FR-ISS-03 | Record an issue |
| FR-ISS-07 | Resolution notes |
| FR-ISS-09 | Equipment status follows issues |
| FR-ORD-01 | Flag low stock |
| FR-ORD-03 | Receive an order |
| FR-RPT-04 | Change a report's status |
| FR-RPT-06 | Keep audit records |
| FR-RPT-07 | Send the monthly summary |

## 13. Out-of-Scope Requirements

The following are excluded from this semester's version of the system:

- Single sign-on with the school identity provider
- Item reservations in advance
- Photo attachments on items or issues
- Barcode or RFID hardware and scanning
- Automatic network discovery of devices
- Vendor portal integration, or placing orders directly with vendors (the system only flags and tracks orders)
- Online payment, vendor invoicing, and budget or accounting management
- Email or SMS delivery of notifications and summaries (delivered inside the system only)
- Editing or deleting audit records
- Mobile application

## 14. Validation

| Criterion | How it was applied | Result |
|---|---|---|
| **Correct** | Each requirement maps to a gathering question (section 4) and a need of the IT Supervisor or Student Assistants. Terms are shared across pages (Admin, SA, `Item`, `Location`, `User`). | Assumptions in section 5 to be confirmed by the IT Supervisor; draft PRJ/NTF policy choices are marked **Confirm**. |
| **Complete** | Every use case has at least one FR; every FR has a use case and a class. | Added loan extension (FR-AST-12), a schedule warning for broken rooms, and a room-level Critical issue rule after review. Still open: required fields, status values, assignee count, notification recipients, and shift policy. |
| **Clear** | One "shall" statement per requirement; vague words replaced by numbers (2 s, 7 days, 3 clicks, 1 minute). | Measurable limits in NFR-AST-01/02 and NFR-USR-04; status values and transitions in A-07, A-11, BR-22, and BR-23. |
| **Consistent** | FRs checked against BRs and across pages. | Lockout values match in FR-USR-07 and UC-USR-01; loan lengths match in BR-08 and UC-AST-03; condition values match in CLS and ISS; classroom equipment uses `Item` without changing `ItemStatus`; audit logging follows FR-USR-06 on every page. |
| **Testable** | Key Must-Have requirements have named acceptance criteria. | See section 12. |
| **Feasible** | Scope fits one semester and the Python/SQLite stack. | Excluded features are listed in section 13. |
| **In scope** | Each page keeps to its own responsibilities. | Item registration and lending in AST; accounts in USR; project work in PRJ; notifications in NTF; classrooms in CLS; issues in ISS; orders in ORD; audit log viewing in RPT. |