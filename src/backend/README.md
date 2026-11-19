# IT Inventory Tracker: backend

FastAPI + SQLAlchemy (SQLite). Run from this folder:

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env        # then edit
.venv/bin/uvicorn app.main:app --reload
.venv/bin/pytest            # tests
```

The first start creates the tables and one Admin from the `ITHUB_ADMIN_*` settings. The Admin's password is
temporary and must be changed at first login (`POST /auth/change-password`).
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
