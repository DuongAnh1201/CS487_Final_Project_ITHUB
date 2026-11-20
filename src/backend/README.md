# IT Inventory Tracker: backend

FastAPI + SQLAlchemy (SQLite). Run from this folder:

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
There are no migrations yet: after a model change, delete the local `ithub.db` and restart.

## Enabling Google sign-in

Google sign-in is built in but **disabled** until you set `ITHUB_GOOGLE_CLIENT_IDS`. Until then
`POST /auth/google` returns `503 "Google sign-in is not configured."` and `GET /auth/config` returns
`{"google_enabled": false, "google_client_id": null}`.

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

6. Check it: `GET /auth/config` now returns `"google_enabled": true` and the client ID.

How the frontend uses it: load Google Identity Services ("Sign in with Google") with the client ID from
`GET /auth/config`, take the ID token it returns, and send `POST /auth/google` with `{"id_token": "..."}`.
The response is the same as `POST /auth/login` (`access_token`, `user`), and the token is used as a Bearer token.

Rules:

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
