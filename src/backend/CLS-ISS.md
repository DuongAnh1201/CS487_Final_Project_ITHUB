# CLS and ISS backend

The routers expose JSON REST endpoints under `/classrooms`, `/classroom-equipment`, `/schedule`, and `/issues`. Interactive API contracts are available through the application's `/docs` endpoint. No records are hard deleted.

## Workflows

- `POST /classrooms`, `PATCH /classrooms/{id}`, and `POST /classrooms/{id}/deactivate` provide Admin classroom management (FR-CLS-01, BR-18, US-CLS-01).
- `POST /classrooms/{id}/equipment` installs eligible Desktop/Monitor items. Equipment `condition`, `move`, and `remove` actions require the last returned `version` (FR-CLS-02–04, US-CLS-02/03).
- `POST /classrooms/{id}/checks` takes one result for every installed item, including its version. Checks record history and refresh the overdue flag (BR-20, US-CLS-04).
- `GET /classrooms` combines building, room type, minimum capacity, derived status and a dated free slot (`slot_date`, `start_time`, `end_time`) using AND filters (FR-CLS-09, US-CLS-05).
- `POST /schedule/imports` accepts JSON containing `file_name` and CSV `content`. It stores good rows and reports row numbers/reasons for rejected rows, including conflicts with earlier accepted rows (FR-CLS-06, US-CLS-06). The expected header is `course_code,course_title,instructor,building,room,day,start_time,end_time,term_start,term_end`.
- `/schedule/entries` supports create, full edit (`PUT /{id}`), and cancellation (`POST /{id}/cancel`). `/classrooms/{id}/timetable?day=YYYY-MM-DD&view=day|week` returns ordered meetings and explicit empty-day messages (BR-19, US-CLS-07/08).
- `/issues` supports creation, SQL-filtered lists (maximum 50 rows/page), detail, possible-duplicate lookup, status transitions, resolution, duplicate linking, comments, and chronological history (FR-ISS-01–10, US-ISS-01–07).

All issue mutation requests include the current `version`. `/issues/{id}/status` accepts `status`, optional `note`, `assignee_id`, `original_id`, and `new_condition`; specialized resolve and duplicate endpoints use the same state machine. Role checks also live inside managers. Status changes cannot bypass required resolution/rejection notes or duplicate validation.

Desktop condition determines Available/Limited/Unusable; monitors do not affect status. Admin closures and unresolved Critical room issues independently keep a room Closed. Resolving an automatic closure retains the Admin override (DD-CLS-02). Hardware effects follow the same AST item across retained installation records, and another unresolved issue prevents restoring its condition (DD-ISS-01, FR-ISS-09).

## AST integration pending #55

`cls.integrations.AssetGateway` is the temporary boundary requested by #56. It returns `AssetItem(id, category, status)` and `AssetLocation(id, building, room)` from `find_item`, `find_location`, and `find_location_by_room`. Lookups must raise the shared `NotFoundError` when an ID is absent; room lookup returns `None` when unmatched. Bind an adapter around #55's `AssetManager` through the `get_asset_gateway` dependency (or `app.state.asset_gateway`). Until configured, AST-dependent operations return an explicit conflict rather than creating duplicate inventory/location storage. No AST tables are defined here; external IDs are validated through this boundary.

AST lending must call `ClassroomManager.is_item_installed(item_id)` and retirement must call `remove_retired_item(item_id, actor)` inside its own transaction (DD-CLS-01, BR-18). CLS never changes `ItemStatus`.

## Transactions and events

Managers flush through repositories; `get_db` commits once on success and rolls back on error. Every mutation includes its audit record in that transaction. Automatic changes include the triggering issue ID and reason in the audit JSON. No core, shared or NTF files are changed.

After saving the issue/effects/audit, `IssueManager` publishes `ISSUE_REPORTED`; canonical duplicate report four flags the original and publishes `REPEAT_PROBLEM` once. The shared EventPublisher isolates Observer failures with savepoints. Notification delivery is not allowed to undo the issue change.

Run the full suite from `src/backend` using `.venv/bin/pytest`. Coverage includes the 49 transition pairs, permissions, stale edits and repository optimistic locking, history immutability, duplicate chains and thresholds, moves, partial CSV imports, schedule boundaries, checks, search, automatic closures, shared notifications and audit-failure rollback.
