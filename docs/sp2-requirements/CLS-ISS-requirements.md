# SP2 – Requirements: Classrooms & Schedules (CLS), Issue Logs (ISS)

**Owner:** _<your name>_ · **Issue:** #_<issue number>_ · **Milestone:** SP2 – Requirements Collection

Written to fit the existing AST/USR requirements: same roles (Admin, Student Assistant), same `Item`, `Location`, `User` and `AuditLogEntry` classes, same priority letters and ID style.

---

## 1. Stakeholders & Actors

| Code | Stakeholder | Role in these pages |
|---|---|---|
| ITS | IT Supervisor | Admin user. Manages classrooms, imports schedules, assigns and closes issues |
| SA | Student Assistant | Daily user. Installs equipment, updates PC/monitor status, records room checks, records and resolves issues |
| FAC | Instructor / faculty | Teaches in classrooms. Needs working rooms and PCs. Not a system user |
| REP | Reporter (instructor, student, staff) | Notices a problem and tells IT. Not a system user; SA records the issue for them |
| TEAM | Project team | Builds and tests the system |
| INS | Course instructor | Reviews requirements |

**Actors:** IT Supervisor (Admin), Student Assistant. Admin can do everything an SA can.

## 2. Gathering Questions

### Classrooms & Schedules

**Rooms and equipment**
1. Which buildings and rooms are covered (lecture rooms, computer labs, both)?
2. What equipment does each room have (student PCs, teaching PC, monitors, projector)? Which of these do we track?
3. Are classroom PCs and monitors the same assets as in the AST inventory (same asset tag)?
4. Can a PC or monitor move between rooms? Who records the move?
5. Can a room have different capacity or layout (rows, seat numbers)? Do we track the seat position of each PC?
6. Can a room be closed temporarily (renovation, maintenance)? Who decides?

**Status**
7. What statuses can a PC or monitor have (working, faulty, under repair, out of service, missing)?
8. Is the room status entered by hand or calculated from its equipment? What makes a room "usable"?
9. Who may change a status? Is a reason required?
10. How long must status history be kept?

**Room checks**
11. How often is each room checked? Who checks it?
12. What is checked (power on, display, keyboard/mouse, network, log-in, projector)?
13. What happens when a check finds a problem: a status change, an issue, or both?
14. Should the system warn when a room is overdue for a check?

**Schedule**
15. Where does class schedule data come from (registrar export, spreadsheet, manual)? In what file format?
16. What fields does a schedule entry need (course code, title, instructor, room, day, start/end time, term dates)?
17. Do classes repeat weekly? Are one-off or cancelled classes needed?
18. How should the schedule be used (timetable per room, find a free room, warn when a class is in a broken room)?
19. If the schedule is imported again, should it replace old entries or update them?
20. Who is allowed to see the schedule: only staff, or also students and faculty?

### Issue Logs

**Reporting**
21. Who reports issues today and how (walk-in, email, phone, paper note)?
22. Do reporters need an account, or does an SA record the issue for them?
23. What information does an issue need (classroom, equipment, category, severity, description, reporter, date)?
24. Which categories exist (hardware, software, network, room/facility, other)?
25. How is severity decided and what does each level mean?
26. Can one issue cover several items, or is it one issue per item?

**Handling**
27. What issue statuses exist?
28. Who resolves issues? Who assigns them? Who may close or reject them?
29. What must be recorded on resolution (what was done, who, when)?
30. Is there a target time to fix an issue for each severity?
31. Can a resolved issue be reopened? For how long?
32. Can an issue be deleted, or only closed or rejected?

**Duplicates and effects**
33. How should duplicate reports be handled (warn, merge, link)?
34. Should a new issue automatically change the status of the related PC or monitor?
35. Should it change the status of the classroom? What if the problem is with the room and not an item (no power, projector)?
36. When an issue is resolved, should the item return to Working automatically? What if another issue is still open on it?
37. Who needs to be notified of new or resolved issues? (Notifications belong to the NTF page.)
38. Where should issue changes appear in the audit log?

## 3. Assumptions (confirm with IT Supervisor)

**Classrooms & Schedules**
- A-CLS-01: A classroom is a `Location` (building + room) from the AST page, extended with capacity, type and check information.
- A-CLS-02: Classroom PCs and monitors are `Item` records (category Desktop or Monitor) with asset tags. Installing an item in a classroom does not change its `ItemStatus`.
- A-CLS-03: Equipment condition is a separate status: **Working, Faulty, Under Repair, Out of Service, Missing**.
- A-CLS-04: Each computer lab is checked at least once every 7 days by an SA.
- A-CLS-05: The schedule comes from a registrar CSV export, imported by the Admin. Manual entries are also allowed.
- A-CLS-06: The schedule is used for timetables, finding free rooms and warnings. It does not book rooms.
- A-CLS-07: Only logged-in SA and Admin users view the data this semester.

**Issue Logs**
- A-ISS-01: Reporters do not log in (same idea as A-01 for borrowers). They tell IT in person, by email or by phone and an SA records the issue.
- A-ISS-02: Categories: Hardware, Software, Network, Room/Facility, Other. Severity: Low, Medium, High, Critical.
- A-ISS-03: Statuses: Open, Assigned, In Progress, Resolved, Closed, Duplicate, Rejected.
- A-ISS-04: SAs and the Admin resolve issues; only the Admin assigns, rejects and closes.
- A-ISS-05: Audit log storage is shared with the Reports & Audit page (RPT). Notifications are handled by NTF.

---

## 4. Functional Requirements

Priority: **M** = Must Have · **S** = Should Have · **C** = Could Have · **W** = Will Not Have (this semester)

### Classrooms & Schedules

| ID | Requirement | Priority |
|---|---|---|
| FR-CLS-01 | The system shall let the Admin add, edit and deactivate classrooms, each linked to a Location, with capacity and room type. | M |
| FR-CLS-03 | The system shall let an SA move installed equipment to another classroom or remove it. | S |
| FR-CLS-05 | The system shall let an SA or Admin set a monitor's condition status using the same list. | M |
| FR-CLS-06 | The system shall require a reason for every condition change and record the user and timestamp in the audit log. | M |
| FR-CLS-09 | The system shall show each classroom's last-checked date and flag classrooms not checked within 7 days. | S |
| FR-CLS-10 | The system shall let the Admin import class schedule entries from a CSV file. | M |
| FR-CLS-12 | The system shall let the Admin add, edit and cancel schedule entries manually. | M |
| FR-CLS-14 | The system shall show a classroom's timetable by day or week. | M |
| FR-CLS-15 | The system shall let users search and filter classrooms by building, type, capacity, status and free time slot. | S |
| FR-CLS-19 | Self-service timetable view for students and faculty. | S |

### Issue Logs

| ID | Requirement | Priority |
|---|---|---|
| FR-ISS-01 | The system shall let an SA record an issue for a classroom, optionally for one installed PC or monitor, with category, severity, description and reporter name, type and contact. | M |
| FR-ISS-02 | The system shall reject an issue missing classroom, category, severity, description or reporter name, naming the missing field. | M |
| FR-ISS-03 | The system shall assign each issue a unique ID and store the logged-in user and timestamp. | M |
| FR-ISS-04 | The system shall list issues with filters by status, classroom, item, category, severity and date. | M |
| FR-ISS-05 | The system shall let the Admin assign an issue to an SA or Admin. | M |
| FR-ISS-06 | The system shall let an SA or Admin change an issue's status following the allowed transitions (BR-ISS-04). | M |
| FR-ISS-07 | The system shall let users add comments and progress notes to an issue. | S |
| FR-ISS-08 | The system shall require resolution notes to resolve an issue. | M |
| FR-ISS-09 | The system shall let an SA or Admin reopen a Resolved issue within 7 days. | S |
| FR-ISS-10 | The system shall list open issues for the same item, or same classroom and category, before a new issue is saved. | S |
| FR-ISS-11 | The system shall let an SA or Admin mark an issue as Duplicate and link it to the original. | S |
| FR-ISS-12 | The system shall set the related item to Faulty when a Hardware issue is recorded for it, unless it is already Faulty, Under Repair or Out of Service. | M |
| FR-ISS-13 | The system shall set the item to Under Repair when its issue moves to In Progress. | S |
| FR-ISS-14 | The system shall set the item to the status chosen at resolution (default Working), only if no other unresolved issue references the item. | M |
| FR-ISS-15 | The system shall set the classroom to "Closed for Maintenance" when a Critical issue with no item is recorded, and clear it when that issue is resolved and no other Critical room-level issue is open. | S |
| FR-ISS-16 | The system shall keep a history of every status change and comment on an issue with user and time. | M |
| FR-ISS-17 | The system shall close a Resolved issue automatically after 7 days without reopening. | C |
| FR-ISS-18 | The system shall highlight issues past their target resolution time. | C |
| FR-ISS-19 | The system shall show issue counts by status, severity and classroom. | C |
| FR-ISS-20 | The system shall export the filtered issue list to CSV. | C |
| FR-ISS-21 | Photo attachments on issues. | W |
| FR-ISS-22 | Self-service report form for students and faculty. | W |
| FR-ISS-23 | Email/SMS notifications (handled by NTF). | W |

## 5. Non-Functional Requirements

| ID | Category | Requirement | Priority |
|---|---|---|---|
| NFR-CLS-01 | Usability | An SA can change an equipment status in no more than 3 clicks from the classroom page. | S |
| NFR-CLS-02 | Performance | Timetable and classroom search return within 2 seconds for up to 100 classrooms and 5,000 schedule entries. | S |
| NFR-CLS-03 | Usability | Invalid input (time range, duplicate seat label, bad CSV row) shows a clear inline error message. | M |
| NFR-CLS-04 | Reliability | Classrooms, schedule entries and status history are never hard-deleted; history is kept at least 3 years. | M |
| NFR-CLS-05 | Performance | A 500-row schedule import finishes within 10 seconds. | C |
| NFR-CLS-06 | Compatibility | Pages work on current Chrome, Edge, Firefox, Safari at widths ≥ 768 px. | S |
| NFR-CLS-07 | Maintainability | UI, business logic and storage are separate layers; object data is encapsulated. | S |
| NFR-ISS-01 | Usability | An SA can record an issue in under 1 minute with no more than 6 required fields. | S |
| NFR-ISS-02 | Performance | The issue list loads within 2 seconds for up to 5,000 issues. | S |
| NFR-ISS-03 | Usability | Required fields show clear inline error messages. | M |
| NFR-ISS-04 | Reliability | Issues and their history are never hard-deleted; kept at least 3 years. | M |
| NFR-ISS-05 | Integrity | An issue change and the resulting equipment status change are saved together or not at all. | M |
| NFR-ISS-06 | Security | Only logged-in SA and Admin users can record or change issues; every change is attributed to a user. | M |
| NFR-ISS-07 | Compatibility | Pages work on current Chrome, Edge, Firefox, Safari at widths ≥ 768 px. | S |

## 6. Business Rules

| ID | Rule |
|---|---|
| BR-CLS-01 | A classroom is one Location (building + room); each Location has at most one classroom record. |
| BR-CLS-02 | Only items in the Desktop or Monitor category can be installed in a classroom. |
| BR-CLS-03 | An item is installed in at most one classroom at a time. Retired or Lost items cannot be installed, and an installed item cannot be lent out. |
| BR-CLS-04 | Equipment condition is one of: Working, Faulty, Under Repair, Out of Service, Missing. It is separate from `ItemStatus`. |
| BR-CLS-05 | Every condition change records user, timestamp, old value, new value and reason. |
| BR-CLS-06 | Classroom status is **Available** if every installed PC is Working, **Limited** if at least one but not all are Working, **Unusable** if no PC is Working or the classroom has no PC. |
| BR-CLS-07 | The Admin can mark a classroom "Closed for Maintenance"; this overrides the derived status. |
| BR-CLS-08 | Classrooms are deactivated, never deleted. A classroom with installed equipment or future classes cannot be deactivated. |
| BR-CLS-09 | Two active schedule entries cannot overlap in the same room on the same day within the same term dates. |
| BR-CLS-10 | A cancelled schedule entry is kept for history and excluded from timetables. |
| BR-CLS-11 | Each computer lab must be checked at least once every 7 days. |
| BR-CLS-12 | When an item is retired (BR-AST-08) it is removed from its classroom and ignored in status calculation. |
| BR-ISS-01 | Every issue refers to one classroom. The item is optional and, if given, must be installed in that classroom. |
| BR-ISS-02 | Only a logged-in SA or Admin records issues; the reporter's name and type are always stored. |
| BR-ISS-03 | Severity is Low, Medium, High or Critical. Critical means scheduled classes cannot be held in the room. |
| BR-ISS-04 | Allowed transitions: Open → Assigned → In Progress → Resolved → Closed; Open or Assigned → Rejected or Duplicate; Resolved → In Progress (reopen). Closed, Rejected and Duplicate are final. |
| BR-ISS-05 | An issue cannot be Resolved without resolution notes. |
| BR-ISS-06 | Only the Admin assigns, rejects and closes issues. An SA or Admin can progress and resolve them. |
| BR-ISS-07 | A Duplicate issue must link to an existing original issue. |
| BR-ISS-08 | A Resolved issue becomes Closed after 7 days without reopening. A reopened issue keeps its ID and history. |
| BR-ISS-09 | Issues are never deleted. |
| BR-ISS-10 | Only a Hardware issue with an item changes equipment status. The classroom status is never set directly except by BR-ISS-12. |
| BR-ISS-11 | An item returns to Working only if no other unresolved issue references it. |
| BR-ISS-12 | A Critical issue with no item sets the classroom to "Closed for Maintenance" until it is resolved and no other Critical room-level issue is open. |
| BR-ISS-13 | Target resolution time: Critical 1 day, High 3 days, Medium 7 days, Low 14 days. |
| BR-ISS-14 | Every automatic equipment or classroom status change is written to the audit log with the issue ID. |

---

## 7. Main Use Cases

| ID | Use Case | Primary Actor | Result |
|---|---|---|---|
| UC-CLS-01 | Manage Classroom | Admin | Classroom created, updated or deactivated |
| UC-CLS-02 | Install / Move Equipment | SA | PC or monitor installed in, moved between, or removed from a classroom |
| UC-CLS-03 | Update Equipment Status | SA / Admin | Condition changed, reason and user logged, room status recalculated |
| UC-CLS-04 | Record Room Check | SA | Check results saved; last-checked date updated |
| UC-CLS-05 | Import Class Schedule | Admin | Valid rows saved; rejected rows listed |
| UC-CLS-06 | Manage Schedule Entry | Admin | Entry added, edited or cancelled |
| UC-CLS-07 | View Room Timetable | SA / Admin | Day or week schedule of a classroom shown |
| UC-CLS-08 | Search Classrooms | SA / Admin | Matching classrooms and status listed |
| UC-CLS-09 | View Classroom Dashboard | Admin / SA | Counts by status and warnings shown |
| UC-CLS-10 | Export Classroom Report | Admin / SA | CSV file downloaded |
| UC-ISS-01 | Report Issue | SA | Issue saved as Open; equipment/room status updated if applicable |
| UC-ISS-02 | View / Filter Issues | SA / Admin | Matching issues listed |
| UC-ISS-03 | Assign Issue | Admin | Issue Assigned to a user |
| UC-ISS-04 | Update Issue Status | SA / Admin | Status and note saved in issue history |
| UC-ISS-05 | Resolve Issue | SA / Admin | Issue Resolved; equipment status set |
| UC-ISS-06 | Reopen Issue | SA / Admin | Resolved issue returns to In Progress |
| UC-ISS-07 | Mark Duplicate | SA / Admin | Issue linked to original and set to Duplicate |
| UC-ISS-08 | Comment on Issue | SA / Admin | Comment added to issue history |
| UC-ISS-09 | Reject / Close Issue | Admin | Issue Rejected or Closed |
| UC-ISS-10 | View Issue Summary | Admin | Counts and overdue issues shown or exported |

## 8. Use-Case Specifications

### UC-CLS-03 – Update Equipment Status

| Field | Description |
|---|---|
| **Primary actor** | Student Assistant (Admin can also do it) |
| **Stakeholders** | IT Supervisor (needs accurate room status), Instructor (needs usable PCs) |
| **Preconditions** | User is logged in. The classroom exists and the item is installed in it. |
| **Trigger** | An SA finds or is told that a PC or monitor is not working, or has been fixed. |
| **Postconditions** | Item condition is updated; audit log entry saved with old status, new status, reason, user and time; classroom status recalculated. |

**Main flow**
1. SA opens a classroom page.
2. System lists installed PCs and monitors with their current condition.
3. SA selects an item.
4. SA chooses a new condition status.
5. System asks for a reason.
6. SA enters the reason and confirms.
7. System validates the status and reason.
8. System saves the new condition and writes an audit log entry.
9. System recalculates the classroom status (BR-CLS-06).
10. System shows a confirmation and the new classroom status.

**Alternate flows**
- 4a. Chosen status equals the current one → system shows "No change" and returns to step 3.
- 9a. Classroom becomes Unusable and has upcoming classes → system shows a schedule warning (FR-CLS-16).

**Exception flows**
- 6a. Reason is empty → system asks for it again.
- 8a. Save fails → no change is made and the SA is asked to retry.
- 8b. Item was changed by someone else meanwhile → system shows the new status and asks the SA to confirm again.
- Any step: SA cancels → nothing is saved.

**Related:** FR-CLS-04, FR-CLS-05, FR-CLS-06, FR-CLS-07, FR-CLS-16, BR-CLS-04–06, FR-USR-06

### UC-ISS-01 – Report Issue

| Field | Description |
|---|---|
| **Primary actor** | Student Assistant |
| **Stakeholders** | Reporter (wants the problem fixed), IT Supervisor (tracks problems), Instructor (needs a usable room) |
| **Preconditions** | SA is logged in. The classroom exists and is active. |
| **Trigger** | A reporter tells IT about a problem in a classroom (in person, email or phone). |
| **Postconditions** | Issue saved with status Open, unique ID, user and timestamp; equipment/classroom status updated where rules apply; action in the audit log. |

**Main flow**
1. SA opens *Report Issue*.
2. SA selects the building and classroom.
3. SA optionally selects an installed PC or monitor.
4. SA selects the category and severity.
5. SA enters the description.
6. SA enters the reporter's name, type and contact.
7. System checks for open issues on the same item (or same classroom and category) and finds none.
8. SA submits.
9. System validates the required fields.
10. System creates the issue with a unique ID, status Open, the SA and the timestamp.
11. If the category is Hardware and an item was selected, system sets the item to Faulty (unless already Faulty, Under Repair or Out of Service) and logs the change with the issue ID.
12. If severity is Critical and no item was selected, system sets the classroom to Closed for Maintenance (BR-ISS-12).
13. System recalculates the classroom status and shows a confirmation with the issue ID.

**Alternate flows**
- 3a. Reporter does not know the item → issue is saved for the classroom only; no equipment status changes.
- 7a. Matching open issues exist → system lists them. SA either adds a comment to an existing issue (flow ends) or continues with a new issue (go to step 8).
- 11a. Category is not Hardware → no equipment status change (BR-ISS-10).

**Exception flows**
- 9a. A required field is missing → system highlights it and returns to the form.
- 11b. Equipment update fails → the whole submission is rolled back and the SA is asked to retry (NFR-ISS-05).
- Any step: SA cancels → nothing is saved.

**Related:** FR-ISS-01, FR-ISS-02, FR-ISS-03, FR-ISS-10, FR-ISS-12, FR-ISS-15, BR-ISS-01–03, BR-ISS-10–12, FR-USR-06

---

## 9. Acceptance Criteria

**FR-CLS-04 – Set PC status**
- Given a logged-in SA and a PC installed in a classroom, when the SA picks a new status and gives a reason, then the PC shows the new status and an audit log entry stores old status, new status, reason, user and time.
- Given no reason is entered, when the SA confirms, then the change is rejected with "Reason is required".
- Given the last Working PC in a room is set to Faulty, when the change is saved, then the classroom status becomes Unusable.

**FR-CLS-10 / FR-CLS-11 – Import schedule**
- Given a valid CSV, when the Admin imports it, then every row becomes a schedule entry and the system shows the accepted count.
- Given a row with an unknown room or an end time before the start time, when the file is imported, then that row is rejected and listed with a reason, and the valid rows are still saved.
- Given an imported entry for room 201, when a user opens room 201's timetable, then the entry appears at the right day and time.

**FR-CLS-14 – Room timetable**
- Given a classroom with entries on Monday, when a user selects that room and Monday, then the entries are shown in time order.
- Given a cancelled entry, when the timetable is shown, then the entry is not displayed.
- Given a room with no classes, when the timetable is shown, then "No classes scheduled" appears.

**FR-ISS-01 / FR-ISS-02 / FR-ISS-03 – Record an issue**
- Given a logged-in SA, when all required fields are filled and the form is submitted, then an issue is saved with a unique ID, status Open, the SA's user ID and a timestamp.
- Given the description is empty, when the SA submits, then the issue is not saved and the message names the description field.
- Given an issue is saved, when the issue list is opened, then the issue appears with its classroom, item, severity and status.

**FR-ISS-12 / FR-ISS-14 – Equipment status follows issues**
- Given a Working PC, when a Hardware issue is recorded for it, then the PC becomes Faulty and an audit entry references the issue ID.
- Given a PC already Under Repair, when a Hardware issue is recorded, then its status does not change.
- Given an issue is resolved and no other unresolved issue references the PC, when the SA chooses the default, then the PC becomes Working.
- Given a second unresolved issue exists for the same PC, when the first is resolved, then the PC's status is not changed.
- Given a Software issue is recorded for a PC, then the PC's status does not change.

**FR-ISS-08 – Resolution notes**
- Given an issue In Progress, when the SA resolves it without notes, then the system rejects it with "Resolution notes are required".
- Given notes are entered, when the SA resolves it, then the status is Resolved with the resolver and time stored.

---

## 10. Proposed Classes

Reused from AST/USR (not redefined): `User`, `Role`, `Item` (category Desktop/Monitor), `Location`, `AuditLogEntry`.

| Class | Attributes |
|---|---|
| **Classroom** | classroomId, location: Location, capacity, roomType (LECTURE/COMPUTER_LAB), isActive, closedForMaintenance: boolean, closedReason, lastCheckedAt |
| **RoomEquipment** | roomEquipmentId, classroom: Classroom, item: Item, seatLabel, condition: EquipmentCondition, installedAt, removedAt, updatedBy: User, updatedAt |
| **RoomCheck** | checkId, classroom: Classroom, checkedBy: User, checkedAt, notes |
| **RoomCheckResult** | resultId, roomCheck: RoomCheck, roomEquipment: RoomEquipment, observedCondition: EquipmentCondition, comment |
| **ScheduleEntry** | entryId, classroom: Classroom, courseCode, courseTitle, instructorName, dayOfWeek, startTime, endTime, termStart, termEnd, status (ACTIVE/CANCELLED), source (IMPORT/MANUAL), scheduleImport: ScheduleImport, createdBy: User, createdAt |
| **ScheduleImport** | importId, fileName, importedBy: User, importedAt, rowsAccepted, rowsRejected |
| **Issue** | issueId, classroom: Classroom, roomEquipment: RoomEquipment (optional), category: IssueCategory, severity: Severity, description, status: IssueStatus, reporterName, reporterType (STUDENT/FACULTY/STAFF), reporterContact, createdBy: User, createdAt, assignedTo: User, targetDate, resolutionNotes, resolvedBy: User, resolvedAt, duplicateOf: Issue |
| **IssueUpdate** | updateId, issue: Issue, user: User, timestamp, oldStatus, newStatus, comment |

**Enums:** `EquipmentCondition` = WORKING, FAULTY, UNDER_REPAIR, OUT_OF_SERVICE, MISSING · `RoomStatus` (derived) = AVAILABLE, LIMITED, UNUSABLE, CLOSED · `IssueCategory` = HARDWARE, SOFTWARE, NETWORK, ROOM_FACILITY, OTHER · `Severity` = LOW, MEDIUM, HIGH, CRITICAL · `IssueStatus` = OPEN, ASSIGNED, IN_PROGRESS, RESOLVED, CLOSED, DUPLICATE, REJECTED

**Relationships:** Location 1–0..1 Classroom · Classroom 1–* RoomEquipment · Item 1–* RoomEquipment (history of installs; at most one active) · Classroom 1–* ScheduleEntry · ScheduleImport 1–* ScheduleEntry · Classroom 1–* RoomCheck · RoomCheck 1–* RoomCheckResult · Classroom 1–* Issue · RoomEquipment 0..1–* Issue · Issue 1–* IssueUpdate · Issue *–0..1 Issue (duplicateOf) · User 1–* Issue, IssueUpdate, RoomCheck · AuditLogEntry records every change (shared with RPT).

Diagram: [`cls-iss-classes.puml`](cls-iss-classes.puml) → `cls-iss-classes.png`.

---

## 11. Traceability Matrix

| Requirement | Stakeholder | Use Case | Class | Test Case |
|---|---|---|---|---|
| FR-CLS-01 | ITS | UC-CLS-01 | Classroom, Location | TC-CLS-01 |
| FR-CLS-02 | SA, ITS | UC-CLS-02 | RoomEquipment, Item | TC-CLS-02 |
| FR-CLS-03 | SA | UC-CLS-02 | RoomEquipment | TC-CLS-03 |
| FR-CLS-04 | SA, FAC | UC-CLS-03 | RoomEquipment | TC-CLS-04 |
| FR-CLS-05 | SA, FAC | UC-CLS-03 | RoomEquipment | TC-CLS-05 |
| FR-CLS-06 | ITS, INS | UC-CLS-03 | RoomEquipment, AuditLogEntry | TC-CLS-06 |
| FR-CLS-07 | ITS, FAC | UC-CLS-03, UC-CLS-09 | Classroom | TC-CLS-07 |
| FR-CLS-08 | SA | UC-CLS-04 | RoomCheck, RoomCheckResult | TC-CLS-08 |
| FR-CLS-09 | ITS | UC-CLS-04, UC-CLS-09 | Classroom, RoomCheck | TC-CLS-09 |
| FR-CLS-10 | ITS | UC-CLS-05 | ScheduleImport, ScheduleEntry | TC-CLS-10 |
| FR-CLS-11 | ITS | UC-CLS-05 | ScheduleImport | TC-CLS-11 |
| FR-CLS-12 | ITS | UC-CLS-06 | ScheduleEntry | TC-CLS-12 |
| FR-CLS-13 | ITS | UC-CLS-06 | ScheduleEntry | TC-CLS-13 |
| FR-CLS-14 | SA, ITS, FAC | UC-CLS-07 | ScheduleEntry, Classroom | TC-CLS-14 |
| FR-CLS-15 | SA, ITS | UC-CLS-08 | Classroom, ScheduleEntry | TC-CLS-15 |
| FR-CLS-16 | ITS, FAC | UC-CLS-03, UC-CLS-09 | Classroom, ScheduleEntry | TC-CLS-16 |
| FR-CLS-17 | ITS | UC-CLS-09 | Classroom, RoomEquipment | TC-CLS-17 |
| FR-CLS-18 | ITS | UC-CLS-10 | Classroom, ScheduleEntry | TC-CLS-18 |
| FR-ISS-01 | SA, REP | UC-ISS-01 | Issue | TC-ISS-01 |
| FR-ISS-02 | SA | UC-ISS-01 | Issue | TC-ISS-02 |
| FR-ISS-03 | ITS, INS | UC-ISS-01 | Issue, AuditLogEntry | TC-ISS-03 |
| FR-ISS-04 | SA, ITS | UC-ISS-02 | Issue | TC-ISS-04 |
| FR-ISS-05 | ITS | UC-ISS-03 | Issue, User | TC-ISS-05 |
| FR-ISS-06 | SA, ITS | UC-ISS-04 | Issue, IssueUpdate | TC-ISS-06 |
| FR-ISS-07 | SA, ITS | UC-ISS-08 | IssueUpdate | TC-ISS-07 |
| FR-ISS-08 | SA, ITS | UC-ISS-05 | Issue | TC-ISS-08 |
| FR-ISS-09 | SA, REP | UC-ISS-06 | Issue, IssueUpdate | TC-ISS-09 |
| FR-ISS-10 | SA | UC-ISS-01 | Issue | TC-ISS-10 |
| FR-ISS-11 | SA, ITS | UC-ISS-07 | Issue | TC-ISS-11 |
| FR-ISS-12 | SA, FAC | UC-ISS-01 | Issue, RoomEquipment | TC-ISS-12 |
| FR-ISS-13 | SA | UC-ISS-04 | Issue, RoomEquipment | TC-ISS-13 |
| FR-ISS-14 | SA, ITS | UC-ISS-05 | Issue, RoomEquipment | TC-ISS-14 |
| FR-ISS-15 | ITS, FAC | UC-ISS-01, UC-ISS-05 | Issue, Classroom | TC-ISS-15 |
| FR-ISS-16 | ITS, INS | UC-ISS-04, UC-ISS-08 | IssueUpdate | TC-ISS-16 |
| FR-ISS-17 | ITS | UC-ISS-09 | Issue | TC-ISS-17 |
| FR-ISS-18 | ITS | UC-ISS-10 | Issue | TC-ISS-18 |
| FR-ISS-19 | ITS | UC-ISS-10 | Issue | TC-ISS-19 |
| FR-ISS-20 | ITS | UC-ISS-10 | Issue | TC-ISS-20 |
| NFR-CLS-01 | SA | UC-CLS-03 | UI | TC-CLS-N01 |
| NFR-CLS-02 | SA, ITS | UC-CLS-07, UC-CLS-08 | ScheduleEntry, Classroom | TC-CLS-N02 |
| NFR-CLS-03 | SA, ITS | UC-CLS-02, 05, 06 | ScheduleImport | TC-CLS-N03 |
| NFR-CLS-04 | ITS, INS | UC-CLS-01, 03, 06 | Classroom, ScheduleEntry | TC-CLS-N04 |
| NFR-CLS-05 | ITS | UC-CLS-05 | ScheduleImport | TC-CLS-N05 |
| NFR-CLS-06 | SA | all CLS UCs | — | TC-CLS-N06 |
| NFR-CLS-07 | TEAM, INS | all CLS UCs | — | TC-CLS-N07 (design review) |
| NFR-ISS-01 | SA | UC-ISS-01 | Issue | TC-ISS-N01 |
| NFR-ISS-02 | SA, ITS | UC-ISS-02 | Issue | TC-ISS-N02 |
| NFR-ISS-03 | SA | UC-ISS-01, UC-ISS-05 | Issue | TC-ISS-N03 |
| NFR-ISS-04 | ITS, INS | UC-ISS-04, UC-ISS-09 | Issue, IssueUpdate | TC-ISS-N04 |
| NFR-ISS-05 | ITS, TEAM | UC-ISS-01, UC-ISS-05 | Issue, RoomEquipment | TC-ISS-N05 |
| NFR-ISS-06 | ITS | all ISS UCs | User, AuditLogEntry | TC-ISS-N06 |
| NFR-ISS-07 | SA | all ISS UCs | — | TC-ISS-N07 |
| BR-CLS-01 | ITS | UC-CLS-01 | Classroom | TC-CLS-01 |
| BR-CLS-02 | ITS | UC-CLS-02 | RoomEquipment, Item | TC-CLS-02 |
| BR-CLS-03 | ITS | UC-CLS-02 | RoomEquipment, Item | TC-CLS-B03 |
| BR-CLS-04 | ITS | UC-CLS-03 | RoomEquipment | TC-CLS-04 |
| BR-CLS-05 | ITS, INS | UC-CLS-03 | AuditLogEntry | TC-CLS-06 |
| BR-CLS-06 | ITS, FAC | UC-CLS-03, UC-CLS-09 | Classroom | TC-CLS-07 |
| BR-CLS-07 | ITS | UC-CLS-01 | Classroom | TC-CLS-07 |
| BR-CLS-08 | ITS | UC-CLS-01 | Classroom | TC-CLS-B08 |
| BR-CLS-09 | ITS | UC-CLS-06 | ScheduleEntry | TC-CLS-13 |
| BR-CLS-10 | ITS | UC-CLS-06, UC-CLS-07 | ScheduleEntry | TC-CLS-14 |
| BR-CLS-11 | ITS | UC-CLS-04 | Classroom, RoomCheck | TC-CLS-09 |
| BR-CLS-12 | ITS | UC-CLS-02 | RoomEquipment | TC-CLS-B12 |
| BR-ISS-01 | ITS | UC-ISS-01 | Issue | TC-ISS-01 |
| BR-ISS-02 | ITS | UC-ISS-01 | Issue | TC-ISS-02 |
| BR-ISS-03 | ITS, FAC | UC-ISS-01 | Issue | TC-ISS-B03 |
| BR-ISS-04 | ITS | UC-ISS-04 | Issue | TC-ISS-06 |
| BR-ISS-05 | ITS | UC-ISS-05 | Issue | TC-ISS-08 |
| BR-ISS-06 | ITS | UC-ISS-03, 05, 09 | Issue | TC-ISS-B06 |
| BR-ISS-07 | ITS | UC-ISS-07 | Issue | TC-ISS-11 |
| BR-ISS-08 | ITS | UC-ISS-06, UC-ISS-09 | Issue | TC-ISS-09, TC-ISS-17 |
| BR-ISS-09 | ITS, INS | UC-ISS-09 | Issue | TC-ISS-N04 |
| BR-ISS-10 | ITS | UC-ISS-01 | Issue, RoomEquipment | TC-ISS-12 |
| BR-ISS-11 | ITS | UC-ISS-05 | Issue, RoomEquipment | TC-ISS-14 |
| BR-ISS-12 | ITS, FAC | UC-ISS-01, UC-ISS-05 | Issue, Classroom | TC-ISS-15 |
| BR-ISS-13 | ITS | UC-ISS-10 | Issue | TC-ISS-18 |
| BR-ISS-14 | ITS, INS | UC-ISS-01, UC-ISS-05 | AuditLogEntry | TC-ISS-16 |

---

## 12. Validation Checklist

| Criterion | How it was applied | Result / changes |
|---|---|---|
| **Correct** | Each requirement maps to a gathering question and a stakeholder need; terms match the AST/USR page (Admin, SA, Item, Location). | Assumptions A-CLS-01–07 and A-ISS-01–05 to be confirmed by the IT Supervisor. |
| **Complete** | Every starter question is answered; every use case has at least one FR; every FR has a use case, class and test case. | Added FR-CLS-16 (warn on scheduled class in broken room) and FR-ISS-15 (room-level Critical issue) after the starter question on classroom status. |
| **Clear** | One "shall" statement per requirement; vague words replaced by numbers (2 s, 7 days, 3 clicks, 1 minute). | Status values, transitions and severities are listed in BR-CLS-04, BR-ISS-03, BR-ISS-04. |
| **Consistent** | Checked CLS against ISS and against AST/USR. | Condition values are the same in CLS and ISS; BR-ISS-10–14 match FR-ISS-12–15; classroom equipment uses `Item` and does not change `ItemStatus`; audit logging follows FR-USR-06. |
| **Testable** | Every requirement has a test case ID; Must-Haves have Given/When/Then criteria in section 9. | All rows in section 11 have a TC. |
| **Feasible** | Scope fits one semester and the team's stack. | Self-service views, live registrar integration, booking, photos and notifications set to Will Not Have. |
| **In scope** | Kept to CLS and ISS pages. | Item registration and lending stay in AST; accounts in USR; audit log viewing in RPT; notifications in NTF. |

## 13. Diagrams

- Class diagram: [`cls-iss-classes.puml`](cls-iss-classes.puml) → `cls-iss-classes.png`

## 14. Decisions to Record

See `docs/design-decisions.md`: DD-CLS-01 (equipment condition separate from `ItemStatus`), DD-CLS-02 (derived classroom status), DD-ISS-01 (issues update equipment status automatically), DD-ISS-02 (reporters do not log in).
