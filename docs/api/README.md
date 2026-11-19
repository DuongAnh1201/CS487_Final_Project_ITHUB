# IT Inventory Tracker: API guide for the frontend

A JSON REST API (FastAPI). Everything below is also available interactively: start the backend and open
**`/docs`** (Swagger UI) or **`/redoc`**. The OpenAPI file is `/openapi.json`.

> **Status of this guide.** It covers the pages merged when it was written: USR (auth and users), NTF, ORD and RPT.
> Sections marked *pending* describe pull requests that are open but not merged yet; Assets (AST), Classrooms (CLS)
> and Issues (ISS) are added when they merge. The `/docs` page is always the source of truth for what is running.

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

The first start creates the database and one Admin (`ITHUB_ADMIN_EMAIL`, default `admin@sfbu.edu`) with the
temporary password `ITHUB_ADMIN_PASSWORD`, which must be changed at first login.

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

*Pending (#63), Google sign-in:* `POST /auth/google` with `{"id_token": "<Google ID token>"}` returns the same response
as `/auth/login`. `GET /auth/config` returns `{"google_enabled": bool, "google_client_id": string|null}`: show the
"Sign in with Google" button only when `google_enabled` is true, and initialise Google Identity Services with
`google_client_id`. Only existing accounts can sign in this way. Until it is configured, `/auth/google` answers `503`
`"Google sign-in is not configured."`.

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

All routes need the bearer token except `GET /health`, `POST /auth/login` (and `/auth/google`, `/auth/config` when
Google sign-in merges). "Any" means Admin or Student Assistant.

### Auth and users (USR)

| Route | Who | Purpose |
|---|---|---|
| `POST /auth/login` | public | Log in with school email and password. |
| `POST /auth/logout` | any | End the session. |
| `GET /auth/me` | any | The logged-in user. |
| `POST /auth/change-password` | any | `{current_password, new_password}`. Clears `must_change_password`. |
| `POST /users` | Admin | Create an account: `{full_name, email, school_id, role, access_end_date?, temporary_password}`. |
| `GET /users?role=&status=` | Admin | List users. |
| `GET /users/{id}` | Admin | One user. |
| `PATCH /users/{id}` | Admin | Change `role` and/or `status` (`ACTIVE`/`INACTIVE`). The last active Admin cannot be demoted or deactivated (`409 "At least one active Admin is required."`). |
| `POST /users/{id}/reset-password` | Admin | Set a temporary password; the user must change it at next login and is logged out everywhere. |

An account past its `access_end_date` is deactivated automatically at its next login attempt.

### Notifications (NTF)

| Route | Purpose |
|---|---|
| `GET /notifications?unread_only=` | My notifications, newest first. Each has `id`, `event_type`, `message`, `related_type` + `related_id` (what it is about, for example `Order` 7), `created_at`, `is_read`, `read_at`, `email_status`. |
| `GET /notifications/{id}` | One of mine (someone else's gives `404`). |
| `PATCH /notifications/{id}` | `{"read": true|false}`. |
| `POST /notifications/shift-summary` | `{shift: MORNING|AFTERNOON|EVENING, shift_date, user_ids: [...]}`: sends each rostered user a summary of their open tasks. |

`event_type` values: `TASK_ASSIGNED`, `ISSUE_REPORTED`, `REPEAT_PROBLEM`, `PROJECT_CREATED`, `PROJECT_UPDATED`,
`PROJECT_MEMBER_ADDED`, `ORDER_ARRIVED`, `LOW_STOCK`, `REPORT_SUBMITTED`, `REPORT_REVIEWED`, `MONTHLY_SUMMARY`,
`SHIFT_SUMMARY`, `GENERAL`. Use `related_type`/`related_id` to link to the item. Poll `GET /notifications?unread_only=true`
for a badge count (there is no push channel). You are never notified about your own actions.

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

### Projects and tasks (PRJ), *pending (#61)*

`/templates` (project templates), `/projects` (create, search, update, complete/reopen, members, `POST /projects/from-template`)
and `/tasks` (create, search, status, `PUT /tasks/{id}/assignees`, `POST /tasks/{id}/handoff`, assignment history).
Task statuses: `TODO`, `IN_PROGRESS`, `COMPLETE`. A project can be completed only when all its tasks are complete.

### Assets, Classrooms, Issues (AST, CLS, ISS), *pending*

Added when these pages merge.

### Health

`GET /health` returns `{"status": "ok"}` without login. Use it for uptime checks.

## 7. Typical frontend flows

- **Start-up:** `GET /health` → show login. After login store the token; if `must_change_password` go to the change-password screen first.
- **Every screen:** call the API with the bearer token; on `401` return to login; on `403` show "not allowed".
- **Order arrives:** `GET /orders?status=ORDERED` → `POST /orders/{id}/receive` with the quantity → the response has the new status;
  refresh the inventory page to show the higher stock; a notification goes to the requester.
- **Daily report:** `GET /report-templates` → `POST /reports {template_id, shift}` → `PUT /reports/{id}/answers` → `POST /reports/{id}/submit {reviewer_ids}`.
- **Reviewer inbox:** `GET /notifications?unread_only=true`, filter `event_type == "REPORT_SUBMITTED"`, open `related_id`, then `POST /reports/{id}/review`.
