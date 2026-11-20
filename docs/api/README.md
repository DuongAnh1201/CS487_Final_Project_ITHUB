# IT Inventory Tracker: API guide for the frontend

A JSON REST API (FastAPI). Everything below is also available interactively: start the backend and open
**`/docs`** (Swagger UI) or **`/redoc`**. The OpenAPI file is `/openapi.json`.

> **Status of this guide.** It covers every page: USR (auth, users, Google sign-in), AST, CLS, ISS, PRJ, NTF, ORD and
> RPT. The `/docs` page is always the source of truth for what is running.

## 1. Run it, open the docs, export the spec

```bash
cd src/backend
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
# optional: put settings in src/backend/.env (see "Settings" below)
.venv/bin/uvicorn app.main:app --reload   # http://127.0.0.1:8000
```

- Interactive docs: <http://127.0.0.1:8000/docs>. Click **Authorize**, paste the `access_token` from a login.
- Export the spec while the server runs: `curl http://127.0.0.1:8000/openapi.json -o openapi.json`
- Or export it without starting the server:
  `.venv/bin/python -c "import json; from app.main import create_app; print(json.dumps(create_app().openapi(), indent=2))" > openapi.json`
  (generate a TypeScript client from it with any OpenAPI generator, for example `openapi-typescript`).
- Tests: `.venv/bin/pytest`.

The first start creates the database and one Admin (`ITHUB_ADMIN_EMAIL`, default `admin@sfbu.edu`) with a
temporary password that must be changed at first login. There is no default password: if
`ITHUB_ADMIN_PASSWORD` is unset, a random one is generated and logged once at WARNING (`Initial admin password: ...`),
so copy it from the first start-up log; if it is set, that value is used.

### Settings (environment variables, all prefixed `ITHUB_`)

| Variable | Default | Meaning |
|---|---|---|
| `ITHUB_CORS_ORIGINS` | `http://localhost:5173` | Browser origins allowed to call the API. Comma-separated or a JSON list. Set it to your frontend's URL(s) in every environment. |
| `ITHUB_DATABASE_URL` | `sqlite:///./ithub.db` | Database. |
| `ITHUB_SECRET_KEY` | placeholder | Must be a long random string in production. |
| `ITHUB_SESSION_TIMEOUT_MINUTES` | `30` | Idle timeout. |

CORS allows all methods and headers from the listed origins, and does not use cookies (the API uses a bearer token).

## 2. Authentication

1. `POST /auth/login` with `{"email": "...", "password": "..."}`.
2. The response is:

   ```json
   {
     "access_token": "kQ3...",
     "token_type": "bearer",
     "must_change_password": false,
     "user": {"id": 2, "full_name": "Sam Assistant", "email": "sa@sfbu.edu", "school_id": "SA-001",
              "role": "STUDENT_ASSISTANT", "status": "ACTIVE", "must_change_password": false,
              "access_end_date": null, "last_login_at": "2026-01-05T09:00:00", "created_at": "2026-01-04T10:00:00"}
   }
   ```

3. Send the token on **every** other request: `Authorization: Bearer <access_token>`.
4. Keep the token in memory (or `sessionStorage`). There are no cookies.

```js
const res = await fetch(`${API}/orders`, { headers: { Authorization: `Bearer ${token}` } });
if (res.status === 401) { /* go to the login screen */ }
```

Rules the UI should know:

| Rule | Behaviour |
|---|---|
| **Idle timeout** | A session ends after **30 minutes without any request**. Each request resets the timer. After that the API answers `401` with `"Session expired. Please log in again."`. |
| **Lockout** | After **5 wrong passwords in a row** the account is locked for **15 minutes**: `401` `"Account locked. Try again in 15 minutes."`. |
| **Generic login error** | An unknown email, a wrong password and a deactivated account all return `401` `"Invalid email or password."`. |
| **Temporary password** | Accounts created by an Admin, and accounts after an Admin reset, have `must_change_password: true`. Until the user calls `POST /auth/change-password`, every other route answers `403` `"Password change required."`. Only `/auth/me`, `/auth/logout` and `/auth/change-password` work. Show a "choose a new password" screen right after login. |
| **Password rule** | At least 10 characters, with letters and digits: `422` `"Password must be at least 10 characters and include letters and digits."`. |
| **Log out** | `POST /auth/logout` ends the session. Then drop the token. |

Accounts are created by an Admin only (`POST /users`); there is no self-registration.

**Google sign-in:** `POST /auth/google` with `{"id_token": "<Google ID token>"}` returns the same response
as `/auth/login`. `GET /auth/config` returns `{"google_enabled": bool, "google_client_id": string|null}`: show the
"Sign in with Google" button only when `google_enabled` is true, and initialise Google Identity Services with
`google_client_id`. Only existing accounts can sign in this way. Until it is configured, `/auth/google` answers `503`
`"Google sign-in is not configured."`. Setup steps for whoever configures it are in the backend `README.md`.

## 3. Roles

There are two roles: `ADMIN` (IT supervisor) and `STUDENT_ASSISTANT`. An Admin can do everything an SA can.

| Action | Student Assistant | Admin |
|---|---|---|
| Log in/out, change own password | yes | yes |
| Orders (create, place, receive, cancel, search) | yes | yes |
| Reports, templates, review, monthly summary | yes | yes |
| Notifications (own), shift summary | yes | yes |
| View the audit log | yes | yes |
| Create accounts, change role/status, reset passwords, list users | **no (`403`)** | yes |
| Retire equipment, create asset categories (AST) | **no (`403`)** | yes |
| Create/edit/deactivate classrooms, set a closure, import or edit the schedule (CLS) | **no (`403`)** | yes |
| Assign, reject or close an issue (ISS) | **no (`403`)** | yes |

A report can only be **reviewed by a user who was assigned as a reviewer** on it (any role), not by every Admin.
Hide Admin-only screens for SAs, but do not rely on that: the API enforces it and answers `403` `"Access denied."`.

## 4. Errors

Business-rule errors always look like this, with one of these status codes:

```json
{ "detail": "An account with this email or school ID already exists." }
```

| Status | Meaning |
|---|---|
| `401` | Not logged in, session expired, or bad credentials. Send the user to the login screen. |
| `403` | Role not allowed, or a temporary password must be changed first. |
| `404` | The record, or a record it refers to (for example an unknown `item_id`), does not exist. |
| `409` | Conflicts with existing data or the record's current state (duplicate email, second open order for an item, report already submitted, ...). |
| `422` | The input breaks a rule. **Two shapes:** a business rule gives `{"detail": "<message>"}`; a malformed body or query (missing field, wrong type, number out of range) gives FastAPI's validation list `{"detail": [{"loc": ["body", "quantity"], "msg": "...", "type": "..."}]}`. Handle both: show `detail` when it is a string, otherwise map each `loc` to a field. |
| `503` | A feature is not configured (Google sign-in). |

Messages are written for end users and can be shown as they are. Unknown routes give `404 {"detail": "Not Found"}` and a
wrong method gives `405`.

## 5. Conventions

- **JSON** in and out. Dates are `YYYY-MM-DD`; timestamps are ISO 8601 in **UTC without a zone suffix** (`2026-01-05T09:00:00`).
- **Enums** are upper-case strings (`STUDENT_ASSISTANT`, `PARTIALLY_ARRIVED`). Unknown values give `422`.
- **IDs** are integers, unique per kind (order 7, report 7 and user 7 are different records).
- **Nothing is deleted.** There are no `DELETE` routes: accounts are deactivated, orders cancelled, audit records are permanent.
- **Filters** are query parameters and are combined with AND. List routes return an array; an empty array means "no results".
- **Request bodies** have an example in `/docs` (Schemas section or the route's *Request body*).

## 6. Endpoints

All routes need the bearer token except `GET /health`, `POST /auth/login`, `POST /auth/google` and
`GET /auth/config`. "Any" means Admin or Student Assistant.

### Auth and users (USR)

| Route | Who | Purpose |
|---|---|---|
| `POST /auth/login` | public | Log in with school email and password. |
| `POST /auth/google` | public | Sign in with a Google ID token `{id_token}`; existing accounts only. `503` until configured. |
| `GET /auth/config` | public | `{google_enabled, google_client_id}` for the login screen. |
| `POST /auth/logout` | any | End the session. |
| `GET /auth/me` | any | The logged-in user. |
| `POST /auth/change-password` | any | `{current_password, new_password}`. Clears `must_change_password`. |
| `POST /users` | Admin | Create an account: `{full_name, email, school_id, role, access_end_date?, temporary_password}`. |
| `GET /users?role=&status=` | Admin | List users. |
| `GET /users/directory?q=` | any | Active staff as `[{id, full_name, role}]`, sorted by name; `q` matches part of a name. Use it for member, assignee, reviewer and recipient pickers (both roles). |
| `GET /users/{id}` | Admin | One user. |
| `PATCH /users/{id}` | Admin | Change `role` and/or `status` (`ACTIVE`/`INACTIVE`). The last active Admin cannot be demoted or deactivated (`409 "At least one active Admin is required."`). |
| `POST /users/{id}/reset-password` | Admin | Set a temporary password; the user must change it at next login and is logged out everywhere. |

An account past its `access_end_date` is deactivated automatically at its next login attempt.

### Notifications (NTF)

| Route | Purpose |
|---|---|
| `GET /notifications?unread_only=` | My notifications, newest first. Each has `id`, `event_type`, `message`, `related_type` + `related_id` (what it is about, for example `Order` 7), `created_at`, `is_read`, `read_at`, `email_status`, `email_attempts`. |
| `GET /notifications/{id}` | One of mine (someone else's gives `404`). |
| `PATCH /notifications/{id}` | `{"read": true|false}`. |
| `POST /notifications/shift-summary` | `{shift: MORNING|AFTERNOON|EVENING, shift_date, user_ids: [...]}`: sends each rostered user a summary of their open tasks. |

`event_type` values: `TASK_ASSIGNED`, `ISSUE_REPORTED`, `REPEAT_PROBLEM`, `PROJECT_CREATED`, `PROJECT_UPDATED`,
`PROJECT_MEMBER_ADDED`, `ORDER_ARRIVED`, `LOW_STOCK`, `REPORT_SUBMITTED`, `REPORT_REVIEWED`, `MONTHLY_SUMMARY`,
`SHIFT_SUMMARY`, `GENERAL`. Use `related_type`/`related_id` to link to the item. Poll `GET /notifications?unread_only=true`
for a badge count (there is no push channel). You are never notified about your own actions.

Email copy (Resend): `email_status` is one of `PENDING`, `SENT`, `DELIVERED`, `BOUNCED`, `COMPLAINED`, `FAILED`,
`SKIPPED` (no email provider configured). Admin and retry routes:

| Route | Who | Purpose |
|---|---|---|
| `GET /notifications/email/config` | Admin | `{enabled, provider: "resend"\|"log", from_address, webhook_enabled}`. Never the API key. |
| `POST /notifications/email/test` | Admin | `{to?}` (default: me) sends a test email, returns `{status, message_id}`. `503 "Email sending is not configured."` when off; `502` when the provider rejects it. |
| `GET /notifications/email/deliveries?status=&recipient_id=&date_from=&date_to=` | Admin | Delivery log: `id, recipient_id, event_type, email_status, attempts, error, sent_at, created_at`. |
| `POST /notifications/{id}/email/retry` | owner or Admin | Re-send a `FAILED`/`BOUNCED` email. `409` for other statuses or after 3 attempts; `404` for someone else's. |
| `POST /webhooks/resend` | public (signed) | Called by Resend, not by the frontend: Svix signature headers, `401` if invalid or older than 5 minutes, `503` without `ITHUB_RESEND_WEBHOOK_SECRET`. Sets `DELIVERED`/`BOUNCED`/`COMPLAINED`. |

### Orders (ORD)

| Route | Purpose |
|---|---|
| `POST /orders` | `{item_id, quantity, vendor?}`. `item_id` is a consumable's id. One **open** order per item (`409 "This item already has an open order."`). |
| `GET /orders?q=&status=&item_id=&date_from=&date_to=` | Search by order id or item name; filter by status, item and request date. |
| `GET /orders/summary` | `{total, by_status}`. |
| `GET /orders/{id}` | One order. |
| `POST /orders/{id}/place` | `REQUESTED` → `ORDERED`. |
| `POST /orders/{id}/receive` | `{quantity}`: the received amount is added to stock automatically, exactly once. Partial deliveries are allowed. |
| `POST /orders/{id}/cancel` | Only from `REQUESTED` or `ORDERED`. The order stays in the list. |

Order states: `REQUESTED` → `ORDERED` → `PARTIALLY_ARRIVED` → `ARRIVED`, or `CANCELLED` (from `REQUESTED`/`ORDERED`).
`ARRIVED` and `CANCELLED` are final. Orders are also created **automatically** (`requested_by: null`) when a consumable's
stock falls below its reorder threshold. Every order has `quantity_ordered`, `quantity_received` and `remaining_quantity`.

### Reports (RPT)

| Route | Purpose |
|---|---|
| `GET /report-templates` · `POST` · `GET/PUT /report-templates/{id}` | Daily-report checklists. A "Morning checklist" template exists from the start. |
| `POST /reports` | New **draft**: `{title?, description?, template_id?, shift?, project_id?, task_id?}`. With a template the checklist is pre-filled (title optional); without one a `title` is required. |
| `GET /reports?q=&status=&project_id=&author_id=&date_from=&date_to=&report_type=` | Search by id or keyword; filter. |
| `GET /reports/by-project` | Groups `[{project_id, reports}]`; reports without a project are the last group (`project_id: null`). |
| `GET /reports/{id}` | One report, including `content` (the rendered text), `checklist_answers`, `reviewer_ids`. |
| `PATCH /reports/{id}` | Edit title, description or links (only while `DRAFT` or `REVIEWED`). |
| `PUT /reports/{id}/answers` | `{answers: {"<checklist item>": "<answer>"}}`. |
| `POST /reports/{id}/submit` | `{reviewer_ids: [...]}` (at least one the first time). Notifies the reviewers. |
| `POST /reports/{id}/review` | `{status: REVIEWED|REJECTED|PASSED, comment}`. A comment is required for `REVIEWED` and `REJECTED`. Only an assigned reviewer; notifies the author. |
| `GET /reports/{id}/history` | Every status change: old/new status, who, when, comment. |
| `POST /reports/monthly-summary` | `{month, year}`: only on or after the last day of that month, once per month. Reviewers are the active Admins. |

Report states: `DRAFT` → (submit) `SUBMITTED` → (review) `PASSED` | `REJECTED` | `REVIEWED`. `PASSED` and `REJECTED` are final;
a `REVIEWED` report can be edited and submitted again. `report_type` is `DAILY` or `MONTHLY_SUMMARY`.

### Audit log (RPT)

| Route | Purpose |
|---|---|
| `GET /audit?user_id=&entity_type=&entity_id=&action=&date_from=&date_to=&limit=&offset=` | Newest first. `limit` 1-500 (default 100), `offset` for paging. |
| `GET /audit/{id}` | One record: `id`, `timestamp`, `actor_id` (null = system), `action`, `entity_type`, `entity_id`, `old_value`, `new_value`, `status`. |

Read-only: audit records can never be changed or deleted. Examples: `entity_type=Order`, `action=RECEIVE`.

### Projects and tasks (PRJ)

Any logged-in user can use these routes (same access for Admin and SA).

| Route | Purpose |
|---|---|
| `GET /templates` · `POST /templates` · `GET/PUT /templates/{id}` | Project templates: `{name, description, tasks: [{title, description?, relative_due_days?, default_priority?}]}`, at least one task. |
| `POST /projects` | `{name, description?, start_date, due_date?, status?, member_ids?}`. The creator is a member automatically. |
| `POST /projects/from-template` | `{template_id, name, description?, start_date, due_date?, status?, member_ids?}`: creates the project and its tasks in one step; a task's `due_date` is `start_date + relative_due_days`. The copies are independent of the template. |
| `GET /projects?q=&status=&assignee_id=&due_before=&due_after=` | Search and filter. Every project has `total_tasks`, `completed_tasks`, `progress` (percent). |
| `GET /projects/{id}` | The project with its tasks. |
| `PATCH /projects/{id}` | Edit; `status: COMPLETED` is allowed only when every task is `COMPLETE` (`422`); a completed project goes back to `ACTIVE` if a task is reopened or added. |
| `GET /projects/{id}/members` · `POST /projects/{id}/members` | Member ids; add `{user_id}` (members are notified). |
| `POST /tasks` | `{title, description?, status?, priority?, due_date?, project_id?, assignee_ids?}`. Without `project_id` it is a standalone task. |
| `GET /tasks?q=&status=&assignee_id=&project_id=&due_before=&due_after=` | Search and filter. |
| `GET /tasks/{id}` · `PATCH /tasks/{id}` | One task; edit it, or link a standalone task to a project once with `project_id`. |
| `PUT /tasks/{id}/status` | `{status: TODO|IN_PROGRESS|COMPLETE}`. |
| `PUT /tasks/{id}/assignees` | `{user_ids: [...]}` (at least one): the full set of assignees. Newly added users are notified. |
| `POST /tasks/{id}/handoff` | `{to_user_id}`: hand an unfinished task to someone else; status unchanged. |
| `GET /tasks/{id}/assignments` | Assignment history, oldest first (`active` is false once ended). |

Task statuses: `TODO`, `IN_PROGRESS`, `COMPLETE`; priorities `LOW`, `MEDIUM`, `HIGH`; project statuses `PLANNED`, `ACTIVE`,
`ON_HOLD`, `COMPLETED`.

### Assets and lending (AST), under `/ast`

Dates are `YYYY-MM-DD`. Equipment and consumables share one id space: the same `item_id` is used by lending, classrooms,
orders and stock routes. Borrower types: `STUDENT`, `FACULTY`, `STAFF`. Item conditions: `Good`, `Fair`, `Poor`, `Damaged`.
Item statuses: `Available`, `On Loan`, `Lost`, `Damaged`, `Retired` (a retired item is read-only and its asset tag is never reused).

| Route | Who | Purpose |
|---|---|---|
| `GET /ast/categories` · `POST /ast/categories` | any · Admin | Category lookup; `{name, is_consumable}`. |
| `GET /ast/locations` · `POST /ast/locations` | any | Locations: `{building, room, description?}`. |
| `POST /ast/items` | any | Register equipment (starts `Available`): `{asset_tag, serial_number, model, manufacturer, category_id, location_id, purchase_date?, warranty_end_date?, notes?}`. The asset tag must be unique, retired items included. |
| `GET /ast/items?asset_tag=&serial_number=&model=&category_id=&location_id=&status=` | any | Search; filters combine with AND. |
| `GET /ast/items/{id}` · `PATCH /ast/items/{id}` | any | One item; edit descriptive fields (not `status`). |
| `POST /ast/items/{id}/incidents` | any | Report `Lost` or `Damaged`: `{type, description, date?}`. |
| `POST /ast/items/{id}/retire` | Admin | `{reason, date?}`; also removes it from its classroom. |
| `GET /ast/consumables` · `POST /ast/consumables` | any | Supplies; create with `{name, category_id, location_id, reorder_threshold, unit}` (stock starts at 0). |
| `GET /ast/consumables/{id}` · `.../transactions` | any | Quantity (`quantity_on_hand`, `reorder_threshold`) and movement history. |
| `POST /ast/consumables/{id}/stock-in` · `.../stock-out` | any | `{quantity, note?}`; stock-out also needs `issued_to` and cannot exceed what is on hand. When stock falls below the threshold an order is created automatically and Admins are notified (see Orders). |
| `GET /ast/borrowers` · `POST /ast/borrowers` | any | Borrower lookup; `{school_id, full_name, email, type, department?}`. |
| `POST /ast/loans` | any | Lend: `{item_id, borrower_id, condition_out, checkout_date?, due_date?, notes?}`. Students: at most 2 items, 7 days; faculty/staff: 30 days. |
| `GET /ast/loans?item_id=&borrower_id=` | any | Loan history. |
| `POST /ast/items/{id}/return` | any | `{condition_in, return_date?, notes?}`. |
| `POST /ast/loans/{id}/extend` | any | `{due_date}`; once per loan, at most 7 days. |
| `GET /ast/overdue` | any | Overdue loans with borrower contact and days overdue. |

### Classrooms and schedules (CLS)

Edits to installed equipment and rooms use **optimistic locking**: send back the `version` you last read. A stale
`version` returns `409`; reload and retry. Room status (`AVAILABLE`, `LIMITED`, `UNUSABLE`, `CLOSED`) is derived from
the installed desktops and any closure or unresolved critical issue. Room types: `LECTURE`, `COMPUTER_LAB`.

| Route | Who | Purpose |
|---|---|---|
| `POST /classrooms` · `PATCH /classrooms/{id}` | Admin | `{location_id, capacity, room_type}`; edit `{capacity, room_type}`. |
| `GET /classrooms` | any | Search by building, room type, minimum capacity, status and a free slot (`slot_date`, `start_time`, `end_time`). |
| `GET /classrooms/{id}` · `GET /classrooms/{id}/equipment` | any | The room with its derived status; current installations. |
| `POST /classrooms/{id}/deactivate` · `POST /classrooms/{id}/closure` | Admin | Deactivate an unused room; `{closed, reason?}` maintenance override. |
| `POST /classrooms/{id}/equipment` | any | Install a Desktop or Monitor: `{item_id, seat_label?}`. |
| `POST /classroom-equipment/{id}/condition` | any | `{condition, reason, version}`: `WORKING`, `FAULTY`, `UNDER_REPAIR`, `OUT_OF_SERVICE`, `MISSING`. |
| `POST /classroom-equipment/{id}/move` · `.../remove` | any | `{to_classroom_id, version}`; `{version}`. History is kept. |
| `POST /classrooms/{id}/checks` | any | Record every installed item's observed condition: `{notes?, results: [{room_equipment_id, observed_condition, comment?, version}]}`. |
| `POST /schedule/imports` · `GET /schedule/imports/{id}` | Admin · any | Registrar CSV as JSON `{file_name, content}`: good rows are stored, rejected rows come back with row number and reason. |
| `POST /schedule/entries` · `PUT /schedule/entries/{id}` · `POST /schedule/entries/{id}/cancel` | Admin | Meetings: `{classroom_id, course_code, course_title, instructor_name, day_of_week, start_time, end_time, term_start, term_end}`; cancelling keeps the record. |
| `GET /classrooms/{id}/timetable?day=YYYY-MM-DD&view=day|week` | any | Ordered meetings. |

### Issues (ISS)

Every change sends the issue's current `version` (`409` when stale). Statuses: `OPEN`, `ASSIGNED`, `IN_PROGRESS`,
`RESOLVED`, `CLOSED`, `DUPLICATE`, `REJECTED`. `GET /issues/{id}` lists the transitions allowed for the current user, so
the UI can offer only valid buttons; the target statuses `ASSIGNED`, `REJECTED` and `CLOSED` are Admin-only (`403 "Not allowed for your role."`).
Severities: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`; categories: `HARDWARE`, `SOFTWARE`, `NETWORK`, `ROOM_FACILITY`, `OTHER`.

| Route | Purpose |
|---|---|
| `POST /issues` | `{classroom_id, room_equipment_id?, category, severity, description, reporter_name, reporter_type, reporter_contact?}`. Automatic effects: a hardware issue on a working item marks it `FAULTY`; a critical issue without an item closes the room. Admins are notified (`ISSUE_REPORTED`). |
| `GET /issues` | Filter and page (50 rows). |
| `GET /issues/possible-duplicates` | Existing reports that look like the one being entered, to show before saving. |
| `GET /issues/{id}` · `GET /issues/{id}/history` | Detail with legal transitions; chronological timeline. |
| `POST /issues/{id}/status` | `{status, version, note?, assignee_id?, original_id?, new_condition?}`. |
| `POST /issues/{id}/resolve` | `{notes, new_condition?, version}`. |
| `POST /issues/{id}/duplicate` | `{original_id, version}`; a fourth report of the same problem flags it as a repeat problem (Admins notified: `REPEAT_PROBLEM`). |
| `POST /issues/{id}/comments` | `{text, version}`. |

### Health

`GET /health` returns `{"status": "ok"}` without login. Use it for uptime checks.

## 7. Typical frontend flows

- **Start-up:** `GET /health` → show login. After login store the token; if `must_change_password` go to the change-password screen first.
- **Every screen:** call the API with the bearer token; on `401` return to login; on `403` show "not allowed".
- **Order arrives:** `GET /orders?status=ORDERED` → `POST /orders/{id}/receive` with the quantity → the response has the new status;
  refresh the inventory page to show the higher stock; a notification goes to the requester.
- **Daily report:** `GET /report-templates` → `POST /reports {template_id, shift}` → `PUT /reports/{id}/answers` → `POST /reports/{id}/submit {reviewer_ids}`.
- **Reviewer inbox:** `GET /notifications?unread_only=true`, filter `event_type == "REPORT_SUBMITTED"`, open `related_id`, then `POST /reports/{id}/review`.
