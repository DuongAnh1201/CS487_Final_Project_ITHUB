# Design decisions — SP2 PRJ / NTF

**Status:** Proposed decisions for team review; not approved until the team confirms them.  
**Date:** October 6, 2026

| ID | Decision | Rationale | Status |
|---|---|---|---|
| DD-PRJ-01 | Creating a project from a template copies task definitions into independent task records and preserves the source template. | Supports repeated work without later project edits changing the reusable template. | Proposed; confirm copy/edit behavior. |
| DD-PRJ-02 | Model task assignees through a `TaskAssignment` association so the design can represent multiple staff members and assignment history. | Proposal says tasks are assigned to team members but does not define cardinality; association avoids locking the class model to one assignee. | Proposed; confirm one vs. many. |
| DD-PRJ-03 | Use draft task statuses To Do, In Progress, Complete, and define project completion as all tasks Complete. | Gives tests and progress display a concrete baseline. | Proposed; confirm statuses and completion rule. |
| DD-NTF-01 | Represent each in-app notification as a record with one recipient, event reference, creation timestamp, and read timestamp. | Supports unread state, event traceability, and audit requirements. | Proposed; confirm deletion and retention. |
| DD-NTF-02 | Use an Observer-style notification service for task assignment and issue events, consistent with the proposal's pattern candidates. | Connects domain events to notifications without making task/issue classes render notifications. | Proposed for design; confirm recipient policy. |
| DD-NTF-03 | Generate a shift summary from a configured shift roster and the work scheduled for that shift. | Matches the proposal's example of notifying morning shift about classroom checks and to-do work. | Proposed; shift roster, timing, and content need definition. |

## Open decisions

- Required Project and Task fields and optional due dates.
- Project and Task status values, allowed transitions, and reopen behavior.
- Assignee cardinality and reassignment policy.
- Template fields, whether copied tasks are editable, and relative due-date rules.
- Notification event/recipient matrix, including issue recipients and whether actors receive notifications.
- Supported shifts, roster source, send time, overdue/unassigned task handling, and empty-shift behavior.
- Notification actions, retention period, expiry behavior, and whether read-state changes enter the global audit log.
