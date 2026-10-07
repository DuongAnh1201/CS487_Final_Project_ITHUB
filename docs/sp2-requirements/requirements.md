# SP2 Requirements: Projects & Tasks and Notifications

**Project:** IT Inventory Tracker  
**Course:** CS487 – Object-Oriented Design and Analysis  
**Scope owner:** Requirements / Documentation  
**Status:** Draft for team validation  
**Prepared:** October 6, 2026

## 1. Purpose and scope

This document specifies the proposed requirements for Projects & Tasks (`PRJ`) and Notifications (`NTF`) in the IT Inventory Tracker. The proposal says IT staff use the system to create and assign project work, launch recurring work from reusable project templates, receive notifications about scheduled work, and be notified of new tasks and issues.

These requirements are a requirements elicitation baseline, not a claim that unresolved policy choices have already been approved. Items marked **Confirm** need an answer from the team or instructor before they are treated as final. Draft status values and recipient rules below are explicit recommendations to make the requirements reviewable and testable.

**In scope:** project and task records, templates, assignments, task progress, shift-based scheduled-work notifications, task/issue event notifications, and in-app notification read state.

**Out of scope per proposal:** barcode/RFID hardware, automatic device discovery, vendor-portal integration, and a mobile application. This section does not define requirements for the rest of inventory management.

## 2. Stakeholders and actors

| Stakeholder / actor | Interest in these pages |
|---|---|
| IT staff (supervisors and student assistants) | Create and follow projects/tasks; receive relevant notifications. The proposal gives all users the same access. |
| IT project/task creator or assigner | Set up project work, choose a template, assign staff, and update progress. The proposal does not define a separate permission role. |
| Assigned staff member | See assigned work, update task progress, and read notifications. |
| IT department / project team | Have recurring work started consistently and know who was notified about work. |
| Course team / instructor | Validate requirements, scope, priorities, and the decisions marked Confirm. |

## 3. Requirement conventions

- **Must** means needed for the proposal's stated core behavior or the minimum useful PRJ/NTF pages.
- **Should** means useful but can be deferred if the team narrows SP2 scope.
- Every requirement uses a stable ID. Tests in the traceability table are proposed test case IDs, not evidence that implementation already exists.
- All users are IT staff and have equal access unless the team revises the proposal. Do not infer supervisor-only permissions.

## 4. Functional requirements

### Projects & Tasks (`PRJ`)

| ID | Priority | Requirement |
|---|---|---|
| PRJ-FR-01 | Must | The system shall assign each project a unique project_id and use it to retrieve and update the project. An authenticated IT staff user shall be able to create a project with a name, description, start date, optional due date, and status. |
| PRJ-FR-02 | Must | The system shall allow an IT staff user to create and maintain a project template containing reusable task definitions, and to create a project from a selected template. Creating from a template shall create a new project and new task records based on the template. **Confirm:** whether template metadata includes default assignees, priorities, or relative due dates. |
| PRJ-FR-03 | Must | The system shall allow an IT staff user to create a task either as a standalone task or linked to a project. A standalone task may be linked to a project later. Each task shall have a title, description, status, and optional due date. |
| PRJ-FR-04 | Must | The system shall allow an IT staff user to assign or reassign a task to one or more IT staff users and show its current assignee(s). **Draft assumption—Confirm:** the proposal says tasks are assigned to team members but does not specify whether multiple assignees are permitted. |
| PRJ-FR-05 | Must | The system shall allow an IT staff user to update a task's status and shall show task progress within the project. **Draft values—Confirm:** To Do, In Progress, and Complete. Define project completion as all project tasks Complete, unless the team chooses a different rule. |
| PRJ-FR-06 | Should | The system shall allow an IT staff user to find projects and tasks by text and filter them by status, assignee, and due date. **Confirm:** required filters and whether reports/search share this behavior. |
| PRJ-FR-07 | Should | The system shall allow an IT staff user to mark a project complete and reopen it when work resumes. **Confirm:** whether project status is derived from task statuses or set independently. |
| PRJ-FR-08 | Must | The system shall allow an IT staff user to hand off an unfinished task to the staff member taking over the work. The task shall keep its current status and retain its assignment history. |

### Notifications (`NTF`)

| ID | Priority | Requirement |
|---|---|---|
| NTF-FR-01 | Must | When a task is newly assigned or an issue is reported, the system shall create a notification associated with that event. This supports the proposal's Observer-pattern examples of notifying users about new tasks and issues. |
| NTF-FR-02 | Must | The system shall route each notification to the applicable recipient(s) and display the recipient, event type, and related project/task/issue. **Draft routing—Confirm:** task assignment goes to the new assignee(s); issue notification goes to the issue reporter and/or designated IT staff group. Do not send to a fixed role until the team defines one. |
| NTF-FR-03 | Must | The system shall generate a scheduled-work notification for staff assigned to a shift when that shift begins, listing their work scheduled for that shift. **Confirm:** supported shifts, shift roster source, exact send time, and treatment of overdue/unassigned work. The proposal's morning classroom-check is an example, not a finalized schedule rule. |
| NTF-FR-04 | Must | The system shall provide an in-app list of a user's notifications and indicate which notifications are read and unread. A notification shall identify its creation time and related work item when one exists. |
| NTF-FR-05 | Should | The system shall allow a user to mark a notification read and unread. **Confirm:** whether users may delete notifications, mark all read, or open the linked work item directly. |
| NTF-FR-06 | Should | The system shall retain notifications for a team-approved retention period and support viewing retained notification history. **Blocked decision—Confirm:** retention period and whether expiry/deletion is automatic. No duration is assumed here. |
| NTF-FR-07 | Must | When a project is created, updated, or a user is added to it, the system shall notify the project’s members. Only members of that project shall receive these notifications. |
| NTF-FR-08 | Must | The system shall send each notification to the recipient’s registered email address as well as show it in the app. It shall record whether the email was delivered; email failure shall not remove the in-app notification. |
| NTF-FR-09 | Must | The system shall give each notification a unique notification_id and use it to find and update that notification. |

## 5. Non-functional requirements

| ID | Priority | Requirement |
|---|---|---|
| PRJ-NFR-01 | Must | Every create, edit, assignment, reassignment, and status change to a project, task, or template shall be attributable to the authenticated user and recorded in the audit history with when, what, and old/new values where applicable. The proposal requires a complete audit history and describes these AuditLog fields. |
| NTF-NFR-01 | Must | Every notification creation and user read-state change shall be attributable to a user or system event and have a recorded timestamp in the audit history. The notification record shall identify its recipient and triggering event so the notification can be traced. **Confirm:** whether read-state changes are included in the project's global audit history. |
| PRJ-NFR-02 | Must | Only authenticated IT department staff shall use PRJ and NTF functions. All staff shall have the same access under the proposal's single-user-kind model. |
| PRJ-NFR-03 | Should | Project and task records shall be searchable/filterable as specified in PRJ-FR-06, and notification history shall be retrievable as specified in NTF-FR-06. **Confirm:** expected data volume and response-time targets before adding a performance threshold. |

## 6. Business rules

| ID | Rule | Status / source |
|---|---|---|
| BR-01 | A project template is a reusable set of task definitions. Instantiating it creates a distinct project and task records; subsequent edits to the project do not silently edit the template. | Derived from proposal's reusable list of tasks; team should confirm copy behavior. |
| BR-02 | A task may be standalone or linked to one project. A standalone task may be linked to a project later. | Added from team feedback. |
| BR-03 | A task is assigned to at least one IT staff member before it is considered assigned. Multiple assignees are permitted in this draft. | Assumption; confirm cardinality. |
| BR-04 | Draft task statuses are To Do, In Progress, and Complete. | Proposed values; confirm names and transitions. |
| BR-05 | A project is complete only when all of its tasks are Complete. | Proposed rule; confirm whether a project can be manually completed or reopened. |
| BR-06 | Every notification must have one recipient and one triggering event; a single event may create notifications for multiple recipients. | Draft rule needed for traceability; confirm issue recipient routing. |
| BR-07 | Shift notifications are generated from the current shift roster and work scheduled for that shift. | Shift roster and send timing remain open. |
| BR-08 | Changes to projects, tasks, templates, notification creation, and notification read state are audit events. | Derived from proposal's complete audit-history objective; confirm read-state auditing. |
| BR-09 | All authenticated IT staff can use these pages with the same access. | Explicit in proposal. |
| BR-10 | An unfinished task may be reassigned to the staff member taking over; its status and assignment history are preserved. | Added from team feedback. |
| BR-11 | Project-activity notifications go only to members of the affected project. | Added from team feedback. |
| BR-12 | Each notification has a unique ID. Email delivery is in addition to the in-app notification. | Added from team feedback. |

## 7. Main use cases

| Use case | Primary actor | Result |
|---|---|---|
| PRJ-UC-01 Create Project from Template | IT staff member | A new project and independent tasks are created from a reusable template and appear in project work. |
| PRJ-UC-02 Create or Update Project Task | IT staff member | A task is added or edited and associated with its project. |
| PRJ-UC-03 Assign or Reassign Task | IT staff member | The selected IT staff member(s) are recorded as assignee(s); the relevant assignee notification is created. |
| PRJ-UC-04 Update Task Progress | IT staff member | Task status and project progress reflect the update; completion behavior follows the approved rule. |
| NTF-UC-01 Notify Staff of New Work or Issue | System (triggered by task/issue event) | A notification is created for each approved recipient and is available in that user's notification list. |
| NTF-UC-02 Send Shift Work Summary | System (scheduled trigger) | Staff on the active shift receive a summary of work scheduled for that shift. |
| NTF-UC-03 Review and Mark Notification | IT staff member | The user views the notification and updates its read state. |

## 8. Full use-case specification: Create Project from Template

| Field | Specification |
|---|---|
| Use case ID / name | PRJ-UC-01 — Create Project from Template |
| Primary actor | IT staff member |
| Goal | Start a project using reusable task definitions without re-entering each task. |
| Preconditions | The actor is authenticated. At least one usable project template exists. |
| Trigger | The actor chooses **Create project from template**. |
| Main success flow | 1. System presents available templates. 2. Actor selects a template. 3. System displays the template's task definitions. 4. Actor enters project details (name, description, start date, optional due date) and reviews the tasks. 5. Actor confirms creation. 6. System creates a new project and new task records based on the template. 7. System records the creation in the audit history and displays the new project. |
| Alternate flow A — edit task list before creation | At step 4, actor removes or adjusts copied tasks if the team approves template customization. System validates and continues at step 5. **Confirm whether permitted.** |
| Alternate flow B — no templates available | At step 1, system explains that no template is available and offers the actor the normal create-project flow if supported. No project is created from a template. |
| Alternate flow C — invalid details | At step 5, system identifies missing or invalid fields and keeps the entered values for correction. No project or task records are created until validation passes. |
| Alternate flow D — creation fails | If persistence fails at step 6, system reports the failure and does not leave a partial project without its copied tasks. |
| Postconditions on success | A project exists with task records based on the template; the template remains reusable and unchanged; an audit event identifies the actor and time. |
| Postconditions on failure | No partial project/task set is left behind. |
| Business rules | BR-01; BR-08; BR-09. |
| Related requirements | PRJ-FR-01, PRJ-FR-02, PRJ-NFR-01, PRJ-NFR-02. |
| Open decisions | Required fields; whether copied tasks are editable before/after creation; whether assignees and relative due dates copy from templates; duplicate project naming rules. |

## 9. Acceptance criteria for Must requirements

### PRJ-FR-02 — Create a project from a template

- **Given** an authenticated IT staff member and a template with three task definitions, **when** the user creates a project from that template and confirms valid project details, **then** the system creates one new project with three new tasks containing the template task definitions.
- **Then** editing a copied task does not change the source template or a project previously created from that template.
- **Then** the audit history records the actor and creation time for the new project and tasks.
- **Given** required project details are invalid, **when** the user confirms, **then** the system identifies the invalid fields and creates no project or task records.

### NTF-FR-01 — Create event notifications

- **Given** an authenticated user assigns a task to another staff member, **when** the assignment is saved, **then** the system creates a notification linked to that task and assignment event for the approved recipient(s).
- **Given** an issue is reported, **when** the issue is saved, **then** the system creates a notification linked to that issue for the approved recipient(s).
- **Then** each notification is distinguishable as read or unread and records its creation time.
- **Then** if saving the triggering task/issue event fails, the system does not leave an unlinked notification for an event that was never committed.

**Acceptance criteria dependency:** NTF-FR-01 can be fully tested after NTF-FR-02 recipient rules are approved. Recipient examples above expose the decision rather than presuming it is settled.

## 10. Proposed classes and attributes

Attributes are initial domain-model suggestions; types, IDs, and additional classes should be aligned with the team's class diagram and database design.

| Class | Proposed attributes | Responsibility / relationship |
|---|---|---|
| Project | project_id, name, description, start_date, due_date, status, created_by, created_at, template_id (optional) | Groups tasks; optionally records its originating template. |
| Task | task_id, project_id, title, description, status, due_date, created_by, created_at, updated_at | Unit of work belonging to one project. |
| ProjectTemplate | template_id, name, description, task_definitions, created_by, created_at, updated_at | Reusable project/task definition. `task_definitions` may become a separate `TemplateTask` class. |
| TemplateTask (optional) | template_task_id, template_id, title, description, relative_due_days, default_priority | Represents one reusable task; include relative due dates/priority only if approved. |
| User | user_id, name, login | Existing proposal class; each is IT department staff. |
| TaskAssignment (recommended if multiple assignees) | task_id, user_id, assigned_by, assigned_at, active | Models the many-to-many task/user association and assignment history. If one assignee only, an assignee field on Task may suffice. |
| Notification | notification_id, recipient_id, event_type, message, created_at, read_at, related_type, related_id | In-app event record; `read_at` null indicates unread. |
| NotificationService | — | Creates and routes notifications from task/issue events and shift schedules; candidate Observer subscriber. |
| AuditLog | audit_id, actor_id, entity_type, entity_id, action, timestamp, old_value, new_value | Records who changed what and when, per proposal. |

**Proposed relationships:** Project 1 — 0..* Task; ProjectTemplate 1 — 1..* TemplateTask (or embedded task definitions); Task 0..* — 0..* User through TaskAssignment (pending assignee decision); User 1 — 0..* Notification; each Notification references one event and optionally one related entity; AuditLog references an actor and changed entity.

## 11. Traceability matrix

| Requirement | Stakeholder | Use case | Proposed class(es) | Proposed test case |
|---|---|---|---|---|
| PRJ-FR-01 | IT staff | PRJ-UC-01 | Project, User | PRJ-TC-01 Create project with valid fields; reject invalid required fields. |
| PRJ-FR-02 | IT staff; project team | PRJ-UC-01 | ProjectTemplate, TemplateTask, Project, Task | PRJ-TC-02 Instantiate template; verify copied tasks and source-template independence. |
| PRJ-FR-03 | IT staff | PRJ-UC-02 | Project, Task | PRJ-TC-03 Add/edit task and verify project association. |
| PRJ-FR-04 | IT staff; assigned staff | PRJ-UC-03 | Task, User, TaskAssignment, Notification | PRJ-TC-04 Assign/reassign user(s); verify current assignee list and event notification. |
| PRJ-FR-05 | IT staff; project team | PRJ-UC-04 | Task, Project | PRJ-TC-05 Change task status; verify task and project progress rule. |
| PRJ-FR-06 | IT staff | PRJ-UC-02 | Project, Task | PRJ-TC-06 Search/filter known records by approved criteria. |
| PRJ-FR-07 | IT staff; project team | PRJ-UC-04 | Project, Task | PRJ-TC-07 Complete/reopen project according to approved rule. |
| PRJ-NFR-01 | IT department; auditor | PRJ-UC-01–04 | AuditLog, User, Project, Task, ProjectTemplate | PRJ-TC-08 Verify actor/time/action/old-new values for create, edit, assignment, and status changes. |
| PRJ-NFR-02 | IT department | All PRJ / NTF use cases | User, authentication service | PRJ-TC-09 Verify unauthenticated access is blocked and authenticated staff share the same authorization. |
| PRJ-NFR-03 | IT staff | PRJ-UC-02; NTF-UC-03 | Project, Task, Notification | PRJ-TC-10 Verify approved project/task filters and retained notification retrieval. |
| NTF-FR-01 | IT staff; project team | NTF-UC-01 | Notification, NotificationService, Task, Issue | NTF-TC-01 Trigger task assignment and issue report; verify linked notification exists. |
| NTF-FR-02 | IT staff; notification recipients | NTF-UC-01, NTF-UC-02 | Notification, User, NotificationService | NTF-TC-02 Verify only approved recipients receive each event type. |
| NTF-FR-03 | Staff working a shift | NTF-UC-02 | Notification, NotificationService, User, Task, ClassSchedule (if used) | NTF-TC-03 At configured shift start, verify roster recipients and scheduled task summary. |
| NTF-FR-04 | IT staff | NTF-UC-03 | Notification, User | NTF-TC-04 Verify list, unread/read indicators, timestamp, and related work link. |
| NTF-FR-05 | IT staff | NTF-UC-03 | Notification, AuditLog | NTF-TC-05 Mark notification read/unread; verify state and audit event. |
| NTF-FR-06 | IT staff; IT department | NTF-UC-03 | Notification | NTF-TC-06 Verify notification remains available through approved retention period and expires per policy. |
| NTF-NFR-01 | IT department; auditor | NTF-UC-01–03 | Notification, NotificationService, AuditLog, User | NTF-TC-07 Verify recipient, triggering event, creation time, and read-state actor/time are traceable. |

## 12. Validation checklist

| Check | Result | Evidence / follow-up |
|---|---|---|
| Correct | Pass with review needed | Statements follow the proposal: projects/tasks, templates, staff assignment, scheduled-work notifications, task/issue events, audit history, and authenticated staff. Team should validate draft policy choices. |
| Complete | Partial, suitable draft | Covers required assignment deliverables. Team answers are still needed for fields, status values, assignee count, recipient routing, shift policy, and retention. |
| Clear | Pass | Requirements use one principal behavior per statement, modal verbs, IDs, and explicit confirmation notes. |
| Consistent | Pass with open choices | Equal staff access is applied throughout. Proposed completion, recipient, shift, and retention rules are flagged for confirmation. |
| Testable | Pass after confirmation | Each requirement has an observable result and a proposed test ID. Ambiguous policy values are explicitly called out. |
| Feasible | Pass | Proposed behavior fits the stated Python/SQLite prototype and avoids external hardware/vendor/mobile scope. |
| In scope | Pass | Limited to PRJ and NTF plus their audit/authentication dependencies; excluded proposal integrations remain excluded. |

## 13. Decisions to confirm with the team

1. Which project/task fields are mandatory? Can tasks/projects omit due dates?
2. What are the final project and task statuses, and can completed work be reopened?
3. Can one task have multiple assignees? Who may assign/reassign, if all users have equal access?
4. Does a project complete automatically when all tasks are complete, or can it be set manually?
5. Which values belong in a project template, and are task copies editable?
6. Which shifts exist, where is the roster stored, and when is each shift notification sent?
7. Which task/issue events notify which recipients? Should the actor be notified about their own action?
8. What should shift summaries contain, including overdue or unassigned work?
9. Can users mark all as read, delete notifications, or follow a notification to the work item?
10. How long are notifications retained, and are read-state changes part of the global audit history?

## 14. Sources

- *Project Proposal: IT Inventory Tracker*, provided project proposal (especially objectives, proposed features, class list, scope, and expected outcome).
- SP2 Requirements / Documentation assignment and starter questions supplied with this task.
