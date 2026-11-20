# IT-Hub: frontend design (static HTML)

Every IT-Hub screen as plain HTML, CSS and JavaScript modules. There is no build step: the backend serves this folder.

## Run it

```bash
cd src/backend
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --reload
```

Open <http://127.0.0.1:8000/>, which redirects to `/app/login.html`. The pages and the API share one origin, so no CORS
setup is needed. On the first start the backend creates the Admin `admin@sfbu.edu` and logs a temporary password once
(or uses `ITHUB_ADMIN_PASSWORD`). The data lives in SQLite, in `src/backend/ithub.db`.

To serve the pages from another server instead (for example `npx serve -l 5173 src/frontend`), keep the backend on port
8000: the client then calls `http://127.0.0.1:8000`, which `ITHUB_CORS_ORIGINS` already allows for port 5173.

## Pages

| File | Screen |
|---|---|
| `index.html` | Home / dashboard |
| `login.html` | Sign-in, forced password change, session expired |
| `inventory.html` | Equipment, consumables, lending |
| `classrooms.html` | Rooms, seat map (click a seat), timetable, schedule import |
| `issues.html` | Issue list, detail, timeline, report form |
| `projects.html` | Projects, task board, templates |
| `orders.html` | Order summary, list, detail, receive |
| `reports.html` | Daily reports, reviews, history |
| `admin.html` | Users, audit log, my account |
| `notifications.html` | Notifications, shift summary, status badges, messages, empty state |

## Notes

- The pages show the **Admin** view. In the Student Assistant view, Admin-only buttons are hidden.
- **Styles:** each page carries its styles in its own `<style>` block in `<head>`. The shared classes are `.card`, `.btn`, `.btn-brand`, `.b-*` (status badges), `.input` and `.nav`.
- **Palette:** brand sage `#BFE3D0` / `#173F2D`, charcoal text `#2B2F36`, teal links `#1F6B7A`, SFBU gold `#8A6A2F`, cream background `#F7F5F2`.
- **Status colours:** good `#DDF2E6`, warning `#FCEBCF`, bad `#FBDDE0`, in progress `#DCEBF9`, neutral `#EEF0F3`, final/archived `#E7E0F5`.
- **Font:** Inter, loaded from Google Fonts, so you need an internet connection for it. Without one, the pages fall back to the system font.
- **Data:** wired pages load real API records. Unwired mockups retain sample data until their page-wiring tasks land.
- **Wiring to the backend:** see `docs/api/README.md` and the live `/docs` page.

## How a page is wired

| File | Role |
|---|---|
| `assets/js/api.js` | `api.get/post/put/patch(path, ...)`: sends the bearer token, raises `ApiError` (`.message`, `.status`, `.fields`). A `401` goes to the login page; "Password change required." goes to the change-password view. |
| `assets/js/app.js` | `startPage()` guards the page, fills the header (initials, unread badge) and hides `[data-admin-only]` for Student Assistants. It also has helpers: `html`/`raw` (escaping templates), `badge(status)`, `fmtDate`, `fmtDateTime`, `timeAgo`, `label`, `formData`, `showFormError`, `toast`, `withBusy`, `renderList`. |
| `assets/css/app.css` | Shared additions: `[hidden]`, toasts, field errors, empty states. Every page links it after its own `<style>`. |
| `assets/js/pages/<page>.js` | One module per page, loaded with `<script type="module" src="assets/js/pages/<page>.js">`. |

Conventions:

1. Start every signed-in page with `const user = await startPage();`.
2. Keep the mockup markup and classes. Add `id` or `data-*` hooks, then replace the sample rows with rendered data.
3. Build markup with `` html`...` `` only, so every value is escaped. Never put server text into `innerHTML` without it.
4. Mark Admin-only controls with `data-admin-only`. The server enforces roles anyway.
5. Show server messages as they are: `toast(error.message, "bad")`, or `showFormError(form, error)` for forms.
6. Open a record from another page with `?id=<id>` (for example `issues.html?id=5`).

`login.html` and `index.html` are the reference pages.

## Inventory, Orders and Notifications (#81)

These pages follow the shared start-up and error-handling pattern. Each loads its
own module in `assets/js/pages/`; `forms.js` supplies escaped form/table helpers.
No new build step or runtime package is needed. All people selectors use
`GET /users/directory` for both roles.

- Inventory has equipment search and details, registration/editing, incidents and
  Admin retirement; stock and movement history with automatic-order links; borrower,
  checkout/return/extension, history and overdue views; category/location creation.
- Orders has live summary counts, text/status/date filters, manual creation,
  placement, partial/full receipt and cancellation. Automatic orders show **System**.
- Notifications has unread/all views, read/unread and mark-all controls, related-record
  links, and directory-selected shift summaries. Admins also see email configuration,
  a test-send control, filtered delivery history and failed/bounced-email retry.
  Server messages (including unconfigured email) are shown unchanged.

Deep links: `inventory.html?id=<item>`, `?consumable=<item>`, `?loan=<loan>`, or
`?tab=equipment|consumables|loans|overdue|borrowers|lookups`; `orders.html?id=<order>`;
`notifications.html?id=<notification>`. The mockup side panels contain live forms
or selected-record details; secondary operation forms open on demand.

Checks:

```bash
node --test src/frontend/tests/forms.test.mjs
node --check src/frontend/assets/js/pages/forms.js
node --check src/frontend/assets/js/pages/inventory.js
node --check src/frontend/assets/js/pages/orders.js
node --check src/frontend/assets/js/pages/notifications.js
cd src/backend && .venv/bin/pytest -q
```

Browser review should cover Admin and SA sessions: create lookup/equipment/borrower,
edit, lend/extend/return, incidents/retire, consumable movements and auto orders;
manual orders, duplicate rejection, partial/full receipts and cancellation; notification
read state and shift roster selection; email configuration/test/error/retry; deep links,
empty/filter states, and narrow screens. Use a disposable database for write scenarios.
Real outbound email requires a configured provider; UI retry can also be verified
against a simulated failed delivery without sending external email.

The layout was checked side by side against Tom's mockups at commit `597d2f5`: original column widths, stacked cards, horizontal tabs, compact filter rows and sidebar structure are preserved. Sample-only errors and records are replaced by real conditional states.
