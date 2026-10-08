# Design Decisions

## DD-CLS-01 – Classroom equipment condition is separate from `ItemStatus`
- **Context:** Classroom PCs and monitors are `Item` records (AST). `ItemStatus` (Available, On Loan, Damaged, Lost, Retired) describes lending, not whether a classroom PC works.
- **Options:** (a) reuse `ItemStatus`; (b) add a separate `EquipmentCondition` on a `RoomEquipment` link.
- **Decision:** (b). Condition values: Working, Faulty, Under Repair, Out of Service, Missing. Installed items cannot be lent.
- **Consequences:** No change to AST statuses. Retiring an item removes it from its classroom.
- **Requirements:** FR-CLS-02, FR-CLS-04, BR-CLS-03, BR-CLS-04, BR-CLS-12

## DD-CLS-02 – Classroom status is derived, with an Admin override
- **Context:** Entering room status by hand would drift from equipment status.
- **Decision:** Status is calculated: Available (all PCs Working), Limited (some), Unusable (none). The Admin can set "Closed for Maintenance", which overrides it.
- **Consequences:** One source of truth (equipment). Schedule warnings use the derived status.
- **Requirements:** FR-CLS-07, FR-CLS-16, BR-CLS-06, BR-CLS-07

## DD-ISS-01 – Issues update equipment status automatically
- **Context:** Starter question: should a new issue change the status of the item or classroom?
- **Options:** (a) manual updates only; (b) automatic update with rules.
- **Decision:** (b). A Hardware issue on an item sets it to Faulty; In Progress sets Under Repair; resolution sets the chosen status (default Working) only if no other unresolved issue references the item. A Critical issue with no item sets the classroom to Closed for Maintenance. Classroom status is otherwise derived, never set by an issue directly. Every automatic change is audit-logged with the issue ID, in one transaction (NFR-ISS-05).
- **Consequences:** Less double entry; ISS depends on CLS classes.
- **Requirements:** FR-ISS-12–15, BR-ISS-10–12, BR-ISS-14, NFR-ISS-05

## DD-ISS-02 – Reporters do not log in
- **Context:** Only two roles exist (Admin, Student Assistant); borrowers already do not log in (A-01).
- **Decision:** Instructors, students and staff report problems to IT, and an SA records the issue with the reporter's name, type and contact. A self-service report form is Will Not Have this semester.
- **Consequences:** Simpler access control; SA does the data entry.
- **Requirements:** FR-ISS-01, FR-ISS-22 (W), BR-ISS-02
