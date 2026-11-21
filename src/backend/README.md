# IT Inventory Tracker: backend

FastAPI + SQLAlchemy: SQLite locally, PostgreSQL (Supabase) in production. Run from this folder:

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env        # then edit
.venv/bin/uvicorn app.main:app --reload
.venv/bin/pytest            # tests
```

The first start creates the tables and one Admin from the `ITHUB_ADMIN_*` settings. There is **no default
password**: if `ITHUB_ADMIN_PASSWORD` is unset, a random temporary password is generated and logged once at
WARNING level (`Initial admin password: ...`), so copy it from the first start-up log. If you set
`ITHUB_ADMIN_PASSWORD` it is used instead. Either way the password is temporary and must be changed at the
first password login (`POST /auth/change-password`). An Admin who only signs in with Google never uses it,
so keep it secret or reset it later (`POST /users/{id}/reset-password`).

### Database and migrations

- **Local / tests (SQLite):** tables are built straight from the models at startup. After a model change,
  delete the local `ithub.db` and restart.
- **Production (PostgreSQL / Supabase):** the app runs the Alembic migrations in `migrations/` at startup
  (`alembic upgrade head`; safe on every restart). Set `ITHUB_DATABASE_URL` to the Supabase connection string;
  setup steps are in [`docs/DEPLOY.md`](../../docs/DEPLOY.md).
- **Changing a model** therefore also needs a migration, or `tests/test_database.py` fails:
  ```bash
  ITHUB_DATABASE_URL=postgresql://... .venv/bin/alembic revision --autogenerate -m "add x to y"
  ```
  Review the generated file in `migrations/versions/`. A migration that adds a table must also call
  `ENABLE ROW LEVEL SECURITY` on it (see `lock_down_data_api` in the first migration).
- **Run the whole suite on PostgreSQL** (wipes that database's `public` schema before every test):
  ```bash
  docker run -d --rm --name ithub-pg -e POSTGRES_PASSWORD=pg -p 54329:5432 postgres:17-alpine
  ITHUB_TEST_DATABASE_URL=postgresql://postgres:pg@127.0.0.1:54329/postgres .venv/bin/pytest
  ```

## Enabling Google sign-in

Google sign-in is built in but **disabled** until it is configured, in one of two ways. Until then
`POST /auth/google` returns `503 "Google sign-in is not configured."` and `GET /auth/config` returns
`"google_enabled": false`.

- **Firebase Authentication (used for the MVP):** set the `ITHUB_FIREBASE_*` settings below.
- **Google Identity Services directly:** set `ITHUB_GOOGLE_CLIENT_IDS` (further down).

If both are set, Firebase is used. The sign-in rules at the end of this section apply to both.

### Through Firebase Authentication

The free Spark plan is enough; Blaze is not needed.

1. In the [Firebase console](https://console.firebase.google.com/) create a project (or add Firebase to the
   Google Cloud project you have).
2. **Build > Authentication > Get started > Sign-in method > Google > Enable**, pick a support email, save.
3. **Authentication > Settings > Authorized domains**: add the deployed host, e.g. `ithub.onrender.com`.
   `localhost` is there already; use `http://localhost:8000/` (not `127.0.0.1`) locally, or add `127.0.0.1`.
4. **Project settings > General > Your apps > Web (`</>`)**: register the app (no Firebase Hosting) and copy
   these values from `firebaseConfig`. They are public by design (the login page needs them); the authorized
   domains protect the project. Analytics is not used.

   ```bash
   ITHUB_FIREBASE_PROJECT_ID=it-hub-a7cf9                          # projectId
   ITHUB_FIREBASE_API_KEY=AIza...                                  # apiKey
   ITHUB_FIREBASE_AUTH_DOMAIN=it-hub-a7cf9.firebaseapp.com         # authDomain (optional, this is the default)
   ITHUB_FIREBASE_APP_ID=1:295459341438:web:...                    # appId (optional)
   ITHUB_GOOGLE_HOSTED_DOMAIN=sfbu.edu                             # optional: only @sfbu.edu emails
   ```

5. Check it: `GET /auth/config` returns `"google_provider": "firebase"` and the `firebase` settings, and the
   login page shows **Sign in with Google**.

How it works: the login page loads the Firebase JS SDK from Google's CDN, opens the Google popup
(`signInWithPopup`), sends Firebase's ID token to `POST /auth/google`, and signs out of Firebase again
(IT-Hub keeps its own session). The backend (`FirebaseIdTokenVerifier`) checks the token's signature,
expiry, audience and issuer for this project, and accepts only the Google provider. It links the user by
the Google account id, so accounts linked earlier through Google Identity Services keep matching. Firebase
tokens have no `hd` claim, so `ITHUB_GOOGLE_HOSTED_DOMAIN` is checked against the verified email's domain.

### Through Google Identity Services

1. Open the [Google Cloud console](https://console.cloud.google.com/), create or pick a project, and go to
   **APIs & Services > OAuth consent screen**. Choose **Internal** if the school uses Google Workspace
   (only school accounts can sign in), otherwise **External**.
2. Go to **APIs & Services > Credentials > Create credentials > OAuth client ID** and choose
   **Application type: Web application**.
3. Under **Authorized JavaScript origins** add every origin the frontend is served from, for example
   `http://localhost:5173` for development and the production URL. No redirect URI is needed for the
   ID-token flow.
4. Copy the **Client ID** (it ends in `.apps.googleusercontent.com`). There is no client secret to store.
5. Set the environment variables (in `.env` or the process environment) and restart the backend:

   ```bash
   ITHUB_GOOGLE_CLIENT_IDS=1234567890-abc.apps.googleusercontent.com   # comma-separated for several
   ITHUB_GOOGLE_HOSTED_DOMAIN=sfbu.edu                                  # optional: only this Workspace domain
   ```

6. Check it: `GET /auth/config` now returns `"google_provider": "google"` and the client ID.

How the frontend uses it: load Google Identity Services ("Sign in with Google") with the client ID from
`GET /auth/config`, take the ID token it returns, and send `POST /auth/google` with `{"id_token": "..."}`.
The response is the same as `POST /auth/login` (`access_token`, `user`), and the token is used as a Bearer token.

### Sign-in rules (both ways)

- Only **existing** accounts can sign in. Accounts are still created by an Admin; Google never creates one.
  The Google email must match the account's email.
- Unknown, deactivated, ended-access, unverified or wrong-domain accounts get `401 "Invalid email or password."`.
  A locked account gets the lock message.
- The first Google sign-in stores the Google account id (`sub`) on the user; later sign-ins must match it.
- Google sessions have the same 30-minute idle expiry. They are not forced through the temporary-password
  change (no password is used); password login keeps working and still forces it.

## Enabling email (Resend)

Notification emails are built in but **disabled** until `ITHUB_RESEND_API_KEY` and `ITHUB_EMAIL_FROM` are both set.
Until then each notification is saved with `email_status` `SKIPPED` (the message is only logged) and
`POST /notifications/email/test` returns `503 "Email sending is not configured."`.

1. Create a [Resend](https://resend.com) account, add and verify your sending domain, and create an API key.
2. Set the variables (in `.env` or the process environment) and restart the backend:

   ```bash
   ITHUB_RESEND_API_KEY=re_xxxxxxxxxxxx
   ITHUB_EMAIL_FROM="IT Inventory Tracker <noreply@yourdomain.edu>"   # must use the verified domain
   ITHUB_EMAIL_REPLY_TO=it-help@yourdomain.edu                         # optional
   ITHUB_APP_BASE_URL=https://tracker.yourdomain.edu                   # frontend origin for email links
   ```

3. As an Admin, check `GET /notifications/email/config`, then send yourself `POST /notifications/email/test`.
4. Optional delivery tracking: in Resend add a webhook to `https://<backend>/webhooks/resend` for
   `email.delivered`, `email.bounced`, `email.complained` and `email.delivery_delayed`, then set
   `ITHUB_RESEND_WEBHOOK_SECRET` to its signing secret (`whsec_...`). Without it the webhook route answers `503`.

The API key is never logged or returned. Sending is synchronous (10-second timeout); a provider error marks the
email `FAILED` and keeps the in-app notification. A `FAILED` or `BOUNCED` email can be retried up to 3 attempts in
total. Notification columns changed (email message id, sent time, attempts): delete the local `ithub.db` once.
