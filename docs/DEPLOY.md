# Deploying IT-Hub: Render + Supabase

One Render web service runs the FastAPI backend, which also serves the frontend at `/app`.
The database is a Supabase PostgreSQL project. Docker is not needed.

```
Browser ──► Render web service (uvicorn, src/backend) ──► Supabase PostgreSQL (session pooler)
             ├─ /app/...  static frontend (src/frontend)
             └─ /auth, /ast, /orders, ...  JSON API
```

## 1. Supabase

1. Create a project at supabase.com. Pick a region close to the Render region and save the **database
   password**: it goes into the connection string.
2. **Turn off the Data API**: Project Settings → Data API → disable. The app talks to Postgres directly and
   never uses Supabase's REST API, and turning it off means the public "anon" key cannot reach the tables.
   The first migration also enables row-level security on every table, so they stay closed even if the
   Data API is turned back on.
3. Copy the connection string: **Connect** → **Session pooler** (port 5432). Do not use "Direct connection":
   it is IPv6-only and Render cannot reach it. The string looks like
   `postgresql://postgres.<project-ref>:<db-password>@aws-0-<region>.pooler.supabase.com:5432/postgres`.
   Paste it as is: the app switches it to the `psycopg` driver itself. The transaction pooler (port 6543)
   also works.

There is nothing to create by hand: on its first start the app runs the Alembic migrations, which build
every table and enum type, then seeds the first Admin and the default report templates.

Free-tier notes: a project with no activity for about a week is paused; restore it from the dashboard.
Back up before demos you care about (Database → Backups, or `pg_dump`).

## 2. Render

Either create the service from the Blueprint (`render.yaml` at the repo root: New → Blueprint), or by hand:

| Setting | Value |
|---|---|
| Type | Web Service, runtime Python |
| Branch | `main` (after Tom promotes `dev`), or `dev` for a preview |
| Build command | `pip install -r src/backend/requirements.txt` |
| Start command | `cd src/backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Health check path | `/health` |

Environment variables (Render dashboard → Environment; never commit them):

| Variable | Required | Value |
|---|---|---|
| `PYTHON_VERSION` | yes | `3.13.7` |
| `ITHUB_DATABASE_URL` | yes | the Supabase session-pooler string from step 1 |
| `ITHUB_SECRET_KEY` | yes | a long random string (the Blueprint generates one) |
| `ITHUB_ADMIN_PASSWORD` | yes | the first Admin's temporary password; changed at first login |
| `ITHUB_APP_BASE_URL` | yes | `https://<service>.onrender.com/app` (links in emails) |
| `ITHUB_RESEND_API_KEY`, `ITHUB_EMAIL_FROM` | for email | see `src/backend/README.md` → Enabling email |
| `ITHUB_RESEND_WEBHOOK_SECRET` | for delivery status | Resend webhook URL: `https://<service>.onrender.com/webhooks/resend` |
| `ITHUB_GOOGLE_CLIENT_IDS` | for Google sign-in | also add the Render URL as an authorised JavaScript origin in Google Cloud |

Then open `https://<service>.onrender.com/` and sign in as `admin@sfbu.edu`.

The free plan sleeps after 15 idle minutes; the first request afterwards takes about a minute.

## 3. Schema changes later

Every model change ships with an Alembic migration (`src/backend/README.md` → Database and migrations).
On the next deploy the app applies it at startup, so there is nothing to run by hand and no data is lost.
