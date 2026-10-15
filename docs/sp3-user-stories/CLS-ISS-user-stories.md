# SP3 User Stories: Classrooms & Schedules, Issue Logs

**Owner:** @nusratillokh-dev
**Issue:** #16 (part of #13)
**Milestone:** SP3 User Stories
**Source:** `docs/sp2-requirements/CLS-ISS-requirements.md`

These stories cover only my own pages from SP2: Classrooms & Schedules (CLS) and Issue Logs (ISS). I wrote one story for every Must and Should requirement, which gives 20 stories. Could Have and Will Not Have items (FR-ISS-19, FR-ISS-20, FR-ISS-21) are left out on purpose.

## Who uses these pages

**Admin (IT Supervisor).** Manages classrooms, imports schedules, assigns, rejects and closes issues. The Admin can also do everything a Student Assistant can.

**Student Assistant (SA).** The person in the rooms every day. Updates equipment status, records room checks, logs issues for people and fixes them.

**Faculty and students.** They don't log in to manage anything. They just want working rooms and to see when a room is free.

## Quick reference

Equipment condition: Working, Faulty, Under Repair, Out of Service, Missing

Issue severity: Low, Medium, High, Critical (Critical means classes can't be held in that room)

Target fix time: Critical 1 day, High 3 days, Medium 7 days, Low 14 days

Issue status flow:

```
Open → Assigned → In Progress → Resolved → Closed
Open or Assigned → Rejected or Duplicate
Resolved → In Progress   (reopen)
Closed, Rejected and Duplicate are final
```

## Epics

| Epic | What it covers | Stories |
|---|---|---|
| E1 Classroom Setup | Adding rooms and keeping track of what's installed in them | US-CLS-01, 02, 03, 04 |
| E2 Room Checks & Search | Knowing which rooms were checked and finding the right room | US-CLS-05, 09 |
| E3 Class Schedules | Getting the timetable into the system and viewing it | US-CLS-06, 07, 08, 10 |
| E4 Reporting Issues | Logging a problem quickly and correctly | US-ISS-01, 02, 03, 04 |
| E5 Handling Issues | Moving an issue from open to fixed and keeping a record | US-ISS-05 to US-ISS-10 |

# Epic 1: Classroom Setup

## US-CLS-01: Manage classrooms

**Epic:** E1 Classroom Setup
**User Role:** Admin
**User Story:** As the Admin, I want to add, edit and deactivate classrooms so that the room list always matches the real buildings we support.
**Priority:** Must
**Related Requirement:** FR-CLS-01, BR-CLS-01, BR-CLS-08
**Preconditions:** Admin is logged in. The building and room already exist as a Location on the AST page.

**Acceptance Criteria:**
1. Given I'm the Admin, when I add a classroom with a Location, capacity and room type (Lecture or Computer Lab), then it shows up in the classroom list.
2. Given a Location already has a classroom, when I try to add a second one for it, then the system blocks it and tells me the room already exists.
3. Given a classroom with no equipment and no future classes, when I deactivate it, then it disappears from active lists but is still kept in the system.
4. Given a classroom that still has equipment or future classes, when I try to deactivate it, then the system refuses and tells me why.
5. There is no delete button. Classrooms can only be deactivated.
6. Every add, edit and deactivate is written to the audit log with my name and the time.

**Dependencies:** Location records from the AST page. Audit log from the RPT page.
**Notes:** Classes: Classroom, Location, AuditLogEntry. Operations: Classroom.create(), update(), deactivate().

## US-CLS-02: Move or remove installed equipment

**Epic:** E1 Classroom Setup
**User Role:** Student Assistant
**User Story:** As an SA, I want to move a PC or monitor to another classroom or take it out so that the system shows where every machine really is.
**Priority:** Should
**Related Requirement:** FR-CLS-03, BR-CLS-12
**Preconditions:** SA is logged in. The item is currently installed in a classroom.

**Acceptance Criteria:**
1. Given a PC installed in room 201, when I move it to room 305, then it shows in room 305 and no longer in room 201.
2. Given an installed monitor, when I remove it, then it is no longer listed in any classroom and the remove date is saved.
3. An item can only be installed in one classroom at a time.
4. Moving or removing an item does not change its inventory status on the AST page.
5. The old room's install record is kept as history, not erased.
6. Each move or removal is written to the audit log with user and time.

**Dependencies:** US-CLS-01. Item records from AST.
**Notes:** Classes: RoomEquipment, Item. A move closes the old RoomEquipment record and opens a new one.

## US-CLS-03: Set a monitor's condition

**Epic:** E1 Classroom Setup
**User Role:** Student Assistant, Admin
**User Story:** As an SA, I want to set a monitor's condition so that everyone can see which monitors work and which don't.
**Priority:** Must
**Related Requirement:** FR-CLS-05
**Preconditions:** User is logged in. The monitor is installed in a classroom.

**Acceptance Criteria:**
1. The condition list is Working, Faulty, Under Repair, Out of Service, Missing. It's the same list used for PCs.
2. Given a Working monitor, when I set it to Faulty and give a reason, then the monitor shows Faulty right away.
3. Given I pick the same condition it already has, then the system says "No change" and saves nothing.
4. I can change the condition in 3 clicks or less from the classroom page.
5. After the change, the classroom status is recalculated.

**Dependencies:** US-CLS-02, US-CLS-04
**Notes:** Classes: RoomEquipment, Classroom. Enum: EquipmentCondition. Operation: RoomEquipment.setCondition().

## US-CLS-04: Reason and record for every condition change

**Epic:** E1 Classroom Setup
**User Role:** Admin
**User Story:** As the Admin, I want every condition change to have a reason and a record of who did it so that I can trace what happened to any machine.
**Priority:** Must
**Related Requirement:** FR-CLS-06, BR-CLS-05
**Preconditions:** A user is changing the condition of a PC or monitor.

**Acceptance Criteria:**
1. Given I leave the reason empty, when I confirm, then the change is not saved and I see "Reason is required".
2. Given I enter a reason, when the change is saved, then the audit log stores the old value, new value, reason, user and time.
3. The audit entry can be found on the RPT audit page.
4. If the save fails, nothing is changed and I'm asked to try again.

**Dependencies:** US-CLS-03. Audit log from RPT.
**Notes:** Classes: RoomEquipment, AuditLogEntry.

# Epic 2: Room Checks & Search

## US-CLS-05: See which rooms are overdue for a check

**Epic:** E2 Room Checks & Search
**User Role:** Admin
**User Story:** As the Admin, I want to see each classroom's last checked date and have overdue rooms flagged so that no lab goes too long without someone looking at it.
**Priority:** Should
**Related Requirement:** FR-CLS-09, BR-CLS-11
**Preconditions:** Classrooms exist. SAs record room checks.

**Acceptance Criteria:**
1. The classroom list shows a "Last checked" date for every room.
2. Given a lab was last checked 8 days ago, then it is flagged as overdue.
3. Given a lab was checked 3 days ago, then it is not flagged.
4. Given a room has never been checked, then it shows "Never checked" and is flagged.
5. When an SA records a new check, the date updates and the flag goes away.

**Dependencies:** US-CLS-01. Room check recording.
**Notes:** Classes: Classroom (lastCheckedAt), RoomCheck. The 7 day limit comes from BR-CLS-11.

## US-CLS-09: Search and filter classrooms

**Epic:** E2 Room Checks & Search
**User Role:** Student Assistant, Admin
**User Story:** As an SA, I want to search and filter classrooms so that I can quickly find a free room that works when someone needs one.
**Priority:** Should
**Related Requirement:** FR-CLS-15
**Preconditions:** User is logged in. Classrooms and schedules exist.

**Acceptance Criteria:**
1. I can filter by building, room type, minimum capacity, status and a free time slot.
2. Filters can be combined. For example: Computer Lab, at least 30 seats, free Tuesday 2 to 4 pm.
3. Results show each room's name, capacity and current status.
4. A room with a class in the chosen time slot does not appear as free.
5. If nothing matches, I see "No classrooms match your filters".
6. Deactivated rooms are not shown.

**Dependencies:** US-CLS-01, US-CLS-06, US-CLS-07
**Notes:** Classes: Classroom, ScheduleEntry. Operation: ClassroomService.search(filters).

# Epic 3: Class Schedules

## US-CLS-06: Import the schedule from a CSV

**Epic:** E3 Class Schedules
**User Role:** Admin
**User Story:** As the Admin, I want to import the class schedule from the registrar's CSV so that I don't have to type in every class by hand.
**Priority:** Must
**Related Requirement:** FR-CLS-10, BR-CLS-09
**Preconditions:** Admin is logged in. Classrooms in the file already exist.

**Acceptance Criteria:**
1. Given a valid CSV, when I import it, then every row becomes a schedule entry and I see how many were accepted.
2. Given a row with an unknown room or an end time before the start time, then that row is rejected and listed with the reason, and the good rows are still saved.
3. Given a row that overlaps another class in the same room, same day and same term, then that row is rejected.
4. Each import keeps the file name, who imported it, when, and the accepted and rejected counts.
5. Imported entries show up in the room timetable at the right day and time.

**Dependencies:** US-CLS-01
**Notes:** Classes: ScheduleImport, ScheduleEntry (source = IMPORT).

## US-CLS-07: Add, edit or cancel a class by hand

**Epic:** E3 Class Schedules
**User Role:** Admin
**User Story:** As the Admin, I want to add, edit and cancel schedule entries myself so that I can fix mistakes and handle changes the CSV didn't include.
**Priority:** Must
**Related Requirement:** FR-CLS-12, BR-CLS-09, BR-CLS-10
**Preconditions:** Admin is logged in. The classroom exists and is active.

**Acceptance Criteria:**
1. I can add an entry with course code, title, instructor, room, day, start and end time, and term dates.
2. If the new or edited entry overlaps another active class in that room, the system blocks it and shows the conflicting class.
3. When I cancel an entry, it stays in the system for history but no longer shows on the timetable.
4. An end time before the start time is rejected.
5. Every add, edit and cancel is written to the audit log.

**Dependencies:** US-CLS-01, US-CLS-08
**Notes:** Classes: ScheduleEntry (source = MANUAL, status ACTIVE or CANCELLED).

## US-CLS-08: View a room's timetable

**Epic:** E3 Class Schedules
**User Role:** Student Assistant, Admin
**User Story:** As an SA, I want to see a classroom's timetable by day or by week so that I know when I can get in to fix or check things without interrupting a class.
**Priority:** Must
**Related Requirement:** FR-CLS-14
**Preconditions:** User is logged in. The classroom exists.

**Acceptance Criteria:**
1. I can switch between a day view and a week view.
2. Given a room with classes on Monday, when I open Monday, then the classes are listed in time order.
3. Cancelled classes are not shown.
4. Given a room with no classes that day, then I see "No classes scheduled".
5. Each class shows the course code, title, instructor and time.

**Dependencies:** US-CLS-06 or US-CLS-07
**Notes:** Classes: ScheduleEntry, Classroom.

## US-CLS-10: Self service timetable for students and faculty

**Epic:** E3 Class Schedules
**User Role:** Student, Faculty
**User Story:** As an instructor, I want to look up a room's timetable myself so that I don't have to email IT just to ask if a room is free.
**Priority:** Should
**Related Requirement:** FR-CLS-19
**Preconditions:** Schedule entries exist.

**Acceptance Criteria:**
1. Students and faculty can open a room's timetable in a view only page.
2. They can see the day and week view, the same as US-CLS-08.
3. They cannot add, edit or cancel anything.
4. They don't see equipment details, issue details or who made changes.
5. Cancelled classes are hidden.

**Dependencies:** US-CLS-08
**Notes:** SP2 assumption A-CLS-07 says only SA and Admin view data this semester, so this needs a quick check with the IT Supervisor before we build it. Reuses the timetable view with a read only role.

# Epic 4: Reporting Issues

## US-ISS-01: Record an issue

**Epic:** E4 Reporting Issues
**User Role:** Student Assistant
**User Story:** As an SA, I want to record an issue for a classroom, and for a specific PC or monitor if I know it, so that the problem someone told me about doesn't get lost.
**Priority:** Must
**Related Requirement:** FR-ISS-01, BR-ISS-01, BR-ISS-02, BR-ISS-03
**Preconditions:** SA is logged in. The classroom exists and is active.

**Acceptance Criteria:**
1. The form has: classroom, optional PC or monitor, category, severity, description, reporter name, reporter type (student, faculty, staff) and contact.
2. Category is one of Hardware, Software, Network, Room/Facility, Other.
3. Severity is one of Low, Medium, High, Critical.
4. Only items installed in the chosen classroom appear in the item list.
5. Given a Hardware issue on a Working PC, when I submit, then the PC becomes Faulty and the audit log mentions the issue ID.
6. Given a Software issue, the PC's condition does not change.
7. Given a Critical issue with no item picked, the classroom is marked Closed for Maintenance.
8. The target fix date is set from severity: Critical 1 day, High 3 days, Medium 7 days, Low 14 days.
9. I can finish the form in under 1 minute.
10. If any part of the save fails, nothing is saved at all.

**Dependencies:** US-CLS-01, US-CLS-02
**Notes:** Classes: Issue, RoomEquipment, Classroom. Operation: IssueService.create().

## US-ISS-02: Clear errors for missing fields

**Epic:** E4 Reporting Issues
**User Role:** Student Assistant
**User Story:** As an SA, I want the form to tell me exactly what I missed so that I can fix it fast and not save a half empty issue.
**Priority:** Must
**Related Requirement:** FR-ISS-02, NFR-ISS-03
**Preconditions:** SA is filling in the issue form.

**Acceptance Criteria:**
1. Classroom, category, severity, description and reporter name are required.
2. Given the description is empty, when I submit, then the issue is not saved and the message names the description field.
3. The error shows next to the field, not just at the top of the page.
4. Whatever I already typed stays in the form.
5. Contact and item are optional and never block saving.

**Dependencies:** US-ISS-01
**Notes:** Validation lives in the Issue class or service, not only in the page.

## US-ISS-03: Unique ID and who logged it

**Epic:** E4 Reporting Issues
**User Role:** Admin
**User Story:** As the Admin, I want every issue to get its own ID and record who logged it and when so that we can talk about an issue clearly and know where it came from.
**Priority:** Must
**Related Requirement:** FR-ISS-03
**Preconditions:** An issue is being saved.

**Acceptance Criteria:**
1. Each saved issue gets a unique ID that is never reused.
2. The logged in user and the exact time are saved automatically. Nobody types them in.
3. A new issue always starts as Open.
4. The confirmation message shows the new issue ID.

**Dependencies:** US-ISS-01. User accounts from USR.
**Notes:** Classes: Issue (issueId, createdBy, createdAt).

## US-ISS-04: List and filter issues

**Epic:** E4 Reporting Issues
**User Role:** Student Assistant, Admin
**User Story:** As an SA, I want to filter the issue list so that I can see just the problems that matter to me right now, like everything open in one lab.
**Priority:** Must
**Related Requirement:** FR-ISS-04, NFR-ISS-02
**Preconditions:** User is logged in.

**Acceptance Criteria:**
1. I can filter by status, classroom, item, category, severity and date range.
2. Filters can be used together.
3. Each row shows the issue ID, classroom, item, severity, status and date.
4. If nothing matches, I see "No issues found".
5. The list loads in 2 seconds or less with up to 5,000 issues.
6. Issues past their target date are easy to spot.

**Dependencies:** US-ISS-01
**Notes:** Classes: Issue. Operation: IssueService.search(filters).

# Epic 5: Handling Issues

## US-ISS-05: Change an issue's status

**Epic:** E5 Handling Issues
**User Role:** Student Assistant, Admin
**User Story:** As an SA, I want to move an issue through its statuses so that everyone can see where the work stands.
**Priority:** Must
**Related Requirement:** FR-ISS-06, BR-ISS-04
**Preconditions:** User is logged in. The issue exists.

**Acceptance Criteria:**
1. Allowed moves are only: Open → Assigned → In Progress → Resolved → Closed.
2. Open or Assigned can also go to Rejected or Duplicate.
3. Resolved can go back to In Progress (reopen).
4. Closed, Rejected and Duplicate are final. No further changes are allowed.
5. Only the Admin can assign, reject or close. An SA who tries gets a "Not allowed" message.
6. Given an issue is Open, when someone tries to jump straight to Closed, then the system blocks it.
7. The status menu only offers the moves that are allowed from the current status.

**Dependencies:** US-ISS-01, US-ISS-10
**Notes:** Classes: Issue, IssueUpdate. Enum: IssueStatus. Operation: Issue.changeStatus().

## US-ISS-06: Add comments and progress notes

**Epic:** E5 Handling Issues
**User Role:** Student Assistant, Admin
**User Story:** As an SA, I want to add notes to an issue so that the next person knows what I already tried.
**Priority:** Should
**Related Requirement:** FR-ISS-07
**Preconditions:** User is logged in. The issue exists.

**Acceptance Criteria:**
1. I can add a comment to any issue that isn't in a final status.
2. Each comment shows who wrote it and when.
3. Comments show newest first.
4. An empty comment can't be posted.
5. Comments can't be deleted.

**Dependencies:** US-ISS-01
**Notes:** Classes: IssueUpdate (comment).

## US-ISS-07: Resolution notes are required

**Epic:** E5 Handling Issues
**User Role:** Student Assistant, Admin
**User Story:** As an SA, I want the system to ask what I did to fix an issue so that if it happens again we know what worked.
**Priority:** Must
**Related Requirement:** FR-ISS-08, BR-ISS-05
**Preconditions:** The issue is In Progress.

**Acceptance Criteria:**
1. Given no notes, when I try to resolve, then it's rejected with "Resolution notes are required".
2. Given notes are entered, when I resolve, then the status becomes Resolved and my name and the time are saved.
3. The notes appear on the issue page.

**Dependencies:** US-ISS-05
**Notes:** Classes: Issue (resolutionNotes, resolvedBy, resolvedAt).

## US-ISS-08: Mark duplicates and flag repeat problems

**Epic:** E5 Handling Issues
**User Role:** Student Assistant, Admin
**User Story:** As an SA, I want to mark an issue as a duplicate of an older one so that we don't fix the same thing twice, and I want the system to warn us when the same problem keeps coming back.
**Priority:** Must
**Related Requirement:** FR-ISS-11, BR-ISS-07
**Preconditions:** Both the new issue and the original exist. The new issue is Open or Assigned.

**Acceptance Criteria:**
1. When I mark an issue as Duplicate, I have to pick the original issue. I can't leave it blank.
2. The duplicate links to the original and the original lists all its duplicates.
3. When I start a new issue, the system shows open issues for the same item, or the same room and category, so I can spot a duplicate before saving.
4. When the same problem is reported more than 3 times, the original is flagged as a repeat problem.
5. When that flag is set, a notification is sent to the Admin.
6. Once marked Duplicate, the issue is final.

**Dependencies:** US-ISS-01, US-ISS-05. Notifications from NTF.
**Notes:** Classes: Issue (duplicateOf). The threshold of 3 comes from FR-ISS-11. Sending is handled by the NTF page.

## US-ISS-09: Equipment goes back to Working only when it's safe

**Epic:** E5 Handling Issues
**User Role:** Student Assistant, Admin
**User Story:** As an SA, I want the PC or monitor to go back to the right status when I resolve an issue so that I don't have to update it separately, but not if something else is still wrong with it.
**Priority:** Must
**Related Requirement:** FR-ISS-14, BR-ISS-14, NFR-ISS-05
**Preconditions:** An issue linked to an item is being resolved.

**Acceptance Criteria:**
1. When I resolve, I pick the item's new status. The default is Working.
2. Given no other unresolved issue is on that item, then the item gets the status I picked.
3. Given another unresolved issue is still on that item, then the item's status does not change.
4. The automatic change is written to the audit log with the issue ID.
5. The issue update and the item update save together, or neither saves.
6. The classroom status is recalculated after the change.

**Dependencies:** US-ISS-07, US-CLS-03
**Notes:** Classes: Issue, RoomEquipment, AuditLogEntry.

## US-ISS-10: Full history on every issue

**Epic:** E5 Handling Issues
**User Role:** Admin
**User Story:** As the Admin, I want to see every status change and comment on an issue so that I know exactly what happened and who did it.
**Priority:** Must
**Related Requirement:** FR-ISS-16, BR-ISS-09, NFR-ISS-04
**Preconditions:** The issue exists.

**Acceptance Criteria:**
1. Every status change saves the old status, new status, user and time.
2. Every comment is saved in the same history.
3. The history is shown in order on the issue page.
4. Issues and their history are never deleted and are kept at least 3 years.
5. No one, including the Admin, can edit past history entries.

**Dependencies:** US-ISS-05, US-ISS-06
**Notes:** Classes: IssueUpdate.

# Refinement and Quality Checks

## How I refined the stories

I went through each story and asked:

1. Does it talk about what the user needs, not how we code it? Class names only appear in Notes.
2. Is it small enough to finish in one sprint? I split "manage schedule" into import, manual edit and timetable view for this reason.
3. Can every acceptance criterion be tested with a clear pass or fail? I replaced words like "fast" with numbers (2 seconds, 1 minute, 3 clicks, 7 days).
4. Are status transitions and severity rules spelled out? They are in US-ISS-01, US-ISS-05 and US-ISS-07.
5. Does it match the SP2 requirements and not the other members' pages?

## Definition of Done

A story is done when:

1. All its acceptance criteria pass when tested.
2. Required fields show a clear error message next to the field.
3. Every change that should be logged shows up in the audit log with user and time.
4. Nothing that should be kept (classrooms, issues, history) can be deleted.
5. The page works on Chrome, Edge, Firefox and Safari at 768 px wide and up.
6. The code has been reviewed by one other team member.

## INVEST Check

I = Independent, N = Negotiable, V = Valuable, E = Estimable, S = Small, T = Testable

| Story | Requirement | Priority | I | N | V | E | S | T |
|---|---|---|---|---|---|---|---|---|
| US-CLS-01 | FR-CLS-01 | Must | Yes | Yes | Yes | Yes | Yes | Yes |
| US-CLS-02 | FR-CLS-03 | Should | Partly, needs CLS-01 | Yes | Yes | Yes | Yes | Yes |
| US-CLS-03 | FR-CLS-05 | Must | Yes | Yes | Yes | Yes | Yes | Yes |
| US-CLS-04 | FR-CLS-06 | Must | Yes | Yes | Yes | Yes | Yes | Yes |
| US-CLS-05 | FR-CLS-09 | Should | Yes | Yes | Yes | Yes | Yes | Yes |
| US-CLS-06 | FR-CLS-10 | Must | Yes | Yes | Yes | Yes | Yes | Yes |
| US-CLS-07 | FR-CLS-12 | Must | Yes | Yes | Yes | Yes | Yes | Yes |
| US-CLS-08 | FR-CLS-14 | Must | Yes | Yes | Yes | Yes | Yes | Yes |
| US-CLS-09 | FR-CLS-15 | Should | Partly, needs schedule data | Yes | Yes | Yes | Yes | Yes |
| US-CLS-10 | FR-CLS-19 | Should | Partly, reuses CLS-08 | Yes | Yes | Yes | Yes | Yes |
| US-ISS-01 | FR-ISS-01 | Must | Yes | Yes | Yes | Yes | Medium | Yes |
| US-ISS-02 | FR-ISS-02 | Must | Yes | Yes | Yes | Yes | Yes | Yes |
| US-ISS-03 | FR-ISS-03 | Must | Yes | Yes | Yes | Yes | Yes | Yes |
| US-ISS-04 | FR-ISS-04 | Must | Yes | Yes | Yes | Yes | Yes | Yes |
| US-ISS-05 | FR-ISS-06 | Must | Yes | Yes | Yes | Yes | Yes | Yes |
| US-ISS-06 | FR-ISS-07 | Should | Yes | Yes | Yes | Yes | Yes | Yes |
| US-ISS-07 | FR-ISS-08 | Must | Yes | Yes | Yes | Yes | Yes | Yes |
| US-ISS-08 | FR-ISS-11 | Must | Partly, needs NTF | Yes | Yes | Yes | Medium | Yes |
| US-ISS-09 | FR-ISS-14 | Must | Partly, needs CLS-03 | Yes | Yes | Yes | Yes | Yes |
| US-ISS-10 | FR-ISS-16 | Must | Yes | Yes | Yes | Yes | Yes | Yes |

**Open questions for the IT Supervisor**

1. US-CLS-10: are students and faculty allowed to view timetables this semester, or should we push it to later?
2. US-ISS-08: should the repeat problem flag trigger at more than 3 reports, or at exactly 3?
