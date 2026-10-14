# IT Inventory Tracker — Projects, Tasks, and Notifications User Stories

**Author:** Luke Gregory Pamaos  
**Source:** SP2 Requirements Collection, Sections 5–6 and 9; Project Proposal  
**Scope:** Projects & Tasks (PRJ) and Notifications (NTF)

## Epics

- **Project and task management:** create projects and templates, manage tasks and assignments, track progress, find work, and hand off unfinished tasks.
- **Staff notifications:** notify staff about work and issues, provide shift summaries, and let users review and manage their notifications.

## Project and Task Management

### US-PRJ-01: Create a Project

**Story ID:** US-PRJ-01  
**Title:** Create a Project  
**Epic:** Project and task management  
**User Role:** Admin or Student Assistant  
**User Story:** As an Admin or Student Assistant, I want to create a project with a unique ID and basic details so that the team can organize related work.  
**Priority:** Must Have  
**Related Requirement:** FR-PRJ-01  
**Preconditions:** The user is authenticated.  
**Acceptance Criteria:**
- The user can enter a project name, description, start date, optional due date, and status.
- The system assigns the project a unique project ID.
- The saved project can be found and updated using its project ID.
- The system confirms successful creation and reports validation errors for missing or invalid required values.
**Dependencies:** None.  
**Notes:** Project status values are not defined in SP2 and need team confirmation.

### US-PRJ-02: Manage a Project Template and Create a Project from It

**Story ID:** US-PRJ-02  
**Title:** Create a Project from a Template  
**Epic:** Project and task management  
**User Role:** Admin or Student Assistant  
**User Story:** As an Admin or Student Assistant, I want to maintain reusable task definitions and start a project from a template so that recurring work is quicker to set up.  
**Priority:** Must Have  
**Related Requirement:** FR-PRJ-02  
**Preconditions:** The user is authenticated; a template exists to create a project from.  
**Acceptance Criteria:**
- The user can create and edit a project template containing reusable task definitions.
- The user can select a template and provide the new project’s required details.
- The system creates a new project and new task records from the template’s definitions.
- Editing a task in the created project does not change the template or another project created from it.
- The system confirms successful creation or explains why it could not be completed.
**Dependencies:** US-PRJ-01.  
**Notes:** Whether template metadata includes default assignees, priorities, or relative due dates is marked for confirmation in SP2.

### US-PRJ-03: Create a Standalone or Project Task

**Story ID:** US-PRJ-03  
**Title:** Create a Task  
**Epic:** Project and task management  
**User Role:** Admin or Student Assistant  
**User Story:** As an Admin or Student Assistant, I want to create a standalone task or a task linked to a project so that work can be tracked in the right context.  
**Priority:** Must Have  
**Related Requirement:** FR-PRJ-03  
**Preconditions:** The user is authenticated; if linking a task to a project, that project exists.  
**Acceptance Criteria:**
- The user can enter a task title, description, status, and optional due date.
- The user can save the task without a project or link it to one existing project.
- The user can link a standalone task to a project later.
- The system confirms a successful save and identifies invalid required values or project links.
**Dependencies:** US-PRJ-01 when linking to a project.  
**Notes:** Task status values follow BR-15: To Do, In Progress, and Complete.

### US-PRJ-04: Assign or Reassign a Task

**Story ID:** US-PRJ-04  
**Title:** Assign a Task  
**Epic:** Project and task management  
**User Role:** Admin or Student Assistant  
**User Story:** As an Admin or Student Assistant, I want to assign or reassign a task to one or more staff members so that everyone can see who is responsible for the work.  
**Priority:** Must Have  
**Related Requirement:** FR-PRJ-04  
**Preconditions:** The user is authenticated; the task and selected staff accounts exist.  
**Acceptance Criteria:**
- The user can assign a task to one or more Admins or Student Assistants.
- The task displays its current assignee or assignees after saving.
- When reassigned, the task retains its current status and its previous and new assignments are available in its assignment history.
- The system confirms a successful assignment or explains why it could not be completed.
**Dependencies:** US-PRJ-03.  
**Notes:** Multiple assignees are allowed by the SP2 draft requirement and BR-14.

### US-PRJ-05: Update Task Status and View Project Progress

**Story ID:** US-PRJ-05  
**Title:** Update Task Progress  
**Epic:** Project and task management  
**User Role:** Admin or Student Assistant  
**User Story:** As an Admin or Student Assistant, I want to update a task’s status and see project progress so that the team can track work toward completion.  
**Priority:** Must Have  
**Related Requirement:** FR-PRJ-05  
**Preconditions:** The user is authenticated; the task exists.  
**Acceptance Criteria:**
- The user can set a task status to To Do, In Progress, or Complete.
- The task displays its saved status.
- For a task linked to a project, the project view reflects task progress after the update.
- A project is shown as complete only when all its tasks are Complete.
- The system confirms a successful update and reports invalid status values.
**Dependencies:** US-PRJ-03; project progress depends on project tasks.  
**Notes:** Status names and project completion rule follow BR-15; SP2 labels these as draft values to confirm.

### US-PRJ-06: Find Projects and Tasks

**Story ID:** US-PRJ-06  
**Title:** Search and Filter Work  
**Epic:** Project and task management  
**User Role:** Admin or Student Assistant  
**User Story:** As an Admin or Student Assistant, I want to search projects and tasks by text and filter them by status, assignee, and due date so that I can find the work I need to review.  
**Priority:** Should Have  
**Related Requirement:** FR-PRJ-06  
**Preconditions:** The user is authenticated; projects or tasks exist.  
**Acceptance Criteria:**
- The user can search projects and tasks using text.
- The user can filter results by status, assignee, and due date.
- Results match the entered text and selected filters.
- The system shows a clear empty state when no records match.
**Dependencies:** US-PRJ-01 and US-PRJ-03.  
**Notes:** SP2 marks the required filter behavior for confirmation.

### US-PRJ-07: Hand Off an Unfinished Task

**Story ID:** US-PRJ-07  
**Title:** Hand Off an Unfinished Task  
**Epic:** Project and task management  
**User Role:** Admin or Student Assistant  
**User Story:** As an Admin or Student Assistant taking over work, I want an unfinished task reassigned to me while keeping its status and history so that I can continue it without losing context.  
**Priority:** Must Have  
**Related Requirement:** FR-PRJ-07  
**Preconditions:** The user is authenticated; an unfinished task exists; the receiving Admin or Student Assistant account exists.  
**Acceptance Criteria:**
- The user can hand off an unfinished task to an Admin or Student Assistant.
- The task’s status is unchanged by the handoff.
- The task’s assignment history retains the prior and new assignee information.
- The task displays the current assignee or assignees after the handoff.
**Dependencies:** US-PRJ-04.  
**Notes:** The task’s assignment history is part of the handoff record.

## Staff Notifications

### US-NTF-01: Receive Notifications for New Assignments and Reported Issues

**Story ID:** US-NTF-01  
**Title:** Notify Staff About New Work and Issues  
**Epic:** Staff notifications  
**User Role:** Admin or Student Assistant receiving a notification  
**User Story:** As an Admin or Student Assistant, I want a notification when a task is newly assigned or an issue is reported so that I can respond to work that needs attention.  
**Priority:** Must Have  
**Related Requirement:** FR-NTF-01  
**Preconditions:** The triggering task assignment or issue report is successfully recorded.  
**Acceptance Criteria:**
- A successful new task assignment creates a notification associated with that assignment event.
- A successfully reported issue creates a notification associated with that issue event.
- Each created notification has one recipient and one triggering event.
- A failed notification creation does not undo the successfully saved task assignment or issue report.
**Dependencies:** US-PRJ-04 for task assignment; issue reporting is handled by the ISS page.  
**Notes:** Recipient routing is specified in FR-NTF-02; SP2 does not settle who receives issue notifications.

### US-NTF-02: Route Notifications to the Right Recipients

**Story ID:** US-NTF-02  
**Title:** Route Notifications  
**Epic:** Staff notifications  
**User Role:** Admin or Student Assistant receiving a notification  
**User Story:** As an Admin or Student Assistant, I want each notification to show its recipient, event type, and related work item so that I can tell why I received it and what it concerns.  
**Priority:** Must Have  
**Related Requirement:** FR-NTF-02  
**Preconditions:** A notification event occurs and its applicable recipient or recipients are defined.  
**Acceptance Criteria:**
- Each notification is routed to its applicable recipient or recipients.
- Each notification identifies its recipient and event type.
- When a related project, task, or issue exists, the notification identifies that work item.
- Task assignment notifications go to the new assignee or assignees.
- The system does not send an issue notification to a fixed role or group until that routing rule is confirmed.
**Dependencies:** US-NTF-01.  
**Notes:** Issue recipient policy is marked for confirmation in SP2. Each individual notification has one recipient, per BR-16.

### US-NTF-03: Receive a Shift Work Summary

**Story ID:** US-NTF-03  
**Title:** Receive a Shift Summary  
**Epic:** Staff notifications  
**User Role:** Admin or Student Assistant assigned to the active shift  
**User Story:** As a staff member starting a shift, I want a notification listing the work scheduled for my shift so that I can plan the work I need to complete.  
**Priority:** Must Have  
**Related Requirement:** FR-NTF-03  
**Preconditions:** The current shift roster identifies the staff member; shift work is available.  
**Acceptance Criteria:**
- When a shift begins, the system generates a notification for each staff member assigned to that shift.
- The notification lists work scheduled for that shift.
- Staff who are not on the current shift roster do not receive that shift’s summary.
- The notification identifies its creation time and applicable shift.
**Dependencies:** Shift roster and work schedule data are available.  
**Notes:** Supported shifts, roster source, exact send time, and handling of overdue or unassigned work need confirmation. The proposal gives the morning classroom-check as an example.

### US-NTF-04: View Notifications

**Story ID:** US-NTF-04  
**Title:** View My Notifications  
**Epic:** Staff notifications  
**User Role:** Admin or Student Assistant  
**User Story:** As an Admin or Student Assistant, I want to view my notifications with their read state and related work item so that I can review updates I have received.  
**Priority:** Must Have  
**Related Requirement:** FR-NTF-04  
**Preconditions:** The user is authenticated.  
**Acceptance Criteria:**
- The user can view a list containing notifications addressed to them.
- Each notification is visibly marked read or unread.
- Each notification shows its creation time.
- When a related work item exists, the notification identifies it.
- Notifications belonging only to other recipients are not shown in the user’s list.
**Dependencies:** US-NTF-01 or another notification-generating event.  
**Notes:** In-app notifications are in scope per the proposal.

### US-NTF-05: Change Notification Read State

**Story ID:** US-NTF-05  
**Title:** Mark a Notification Read or Unread  
**Epic:** Staff notifications  
**User Role:** Admin or Student Assistant  
**User Story:** As an Admin or Student Assistant, I want to mark my notification read or unread so that I can keep track of updates I have reviewed.  
**Priority:** Should Have  
**Related Requirement:** FR-NTF-05  
**Preconditions:** The user is authenticated; the notification is addressed to that user.  
**Acceptance Criteria:**
- The user can mark their notification read.
- The user can mark their notification unread.
- The displayed read state changes to match the saved state.
- The user cannot change the read state of another recipient’s notification.
**Dependencies:** US-NTF-04.  
**Notes:** Delete, mark-all-read, and direct-open behavior are left for confirmation in SP2 and are not assumed here.

### US-NTF-06: Notify Project Members About Project Changes

**Story ID:** US-NTF-06  
**Title:** Notify Project Members  
**Epic:** Staff notifications  
**User Role:** Admin or Student Assistant who belongs to a project  
**User Story:** As a project member, I want to be notified when a project is created, updated, or a user is added to it so that I can stay informed about changes to my project.  
**Priority:** Must Have  
**Related Requirement:** FR-NTF-06  
**Preconditions:** The project event is successfully saved; project membership is known.  
**Acceptance Criteria:**
- Creating a project, updating a project, or adding a user to a project generates notifications for the project’s members.
- Each notification identifies the project event and project.
- Only members of that project receive its project notifications.
- Each notification has one recipient and one triggering event.
**Dependencies:** US-PRJ-01 for project creation; project updates and membership are recorded in project management.  
**Notes:** Project notification recipients follow FR-NTF-06 and BR-16.

### US-NTF-07: Receive Notifications by Email and In App

**Story ID:** US-NTF-07  
**Title:** Receive Email Copies of Notifications  
**Epic:** Staff notifications  
**User Role:** Admin or Student Assistant  
**User Story:** As an Admin or Student Assistant, I want notifications sent to my registered email as well as shown in the app so that I can see important updates outside the system.  
**Priority:** Must Have  
**Related Requirement:** FR-NTF-07  
**Preconditions:** A notification is created; the recipient has a registered email address.  
**Acceptance Criteria:**
- The system keeps the in-app notification when attempting email delivery.
- The system attempts to send the notification to the recipient’s registered email address.
- The notification records whether email delivery succeeded or failed.
- Email delivery failure does not remove the in-app notification.
**Dependencies:** US-NTF-01 and a registered recipient email address.  
**Notes:** SP2 FR-NTF-07 requires email, but Section 13 lists email delivery as out of scope and A-13 says in-app notifications are handled by NTF. This conflict must be resolved by the team before implementation. The proposal’s Observer pattern is a design note, not part of the user story.

### US-NTF-08: Find and Update a Notification by Its Unique ID

**Story ID:** US-NTF-08  
**Title:** Identify a Notification Uniquely  
**Epic:** Staff notifications  
**User Role:** Admin or Student Assistant  
**User Story:** As an Admin or Student Assistant, I want each of my notifications to be uniquely identifiable so that the correct notification is displayed and its read state can be updated.  
**Priority:** Must Have  
**Related Requirement:** FR-NTF-08  
**Preconditions:** A notification has been created for the user.  
**Acceptance Criteria:**
- Each notification has a unique notification ID.
- The system can find and update the notification using that ID.
- Updating one notification does not change another notification.
- Each notification remains associated with its recipient and triggering event.
**Dependencies:** US-NTF-01.  
**Notes:** The unique ID and notification event association are verification details, not separate user goals.

## Refinement and INVEST Check

- Each story has one main user goal, a named beneficiary, and a link to its SP2 requirement.
- Acceptance criteria describe observable results, including key routing, status, history, and failure behavior.
- Must Have and Should Have requirements are each represented once; the nine NTF acceptance checks are contained within the eight NTF stories rather than split into extra stories.
- Dependencies identify related work without preventing stories from being estimated separately where practical.
- Open decisions from SP2 are called out in Notes instead of being silently treated as finalized policy.
- The stories are implementation-neutral. The proposal’s classes, operations, and Observer pattern are referenced only as notes where useful.

## Definition of Done

For each story, completion should be reviewed against the course Definition of Done: functionality implemented, input validation added, acceptance criteria tested, related object-oriented design and UML updated when needed, no known errors introduced, and acceptance by the project team and supervisor.
