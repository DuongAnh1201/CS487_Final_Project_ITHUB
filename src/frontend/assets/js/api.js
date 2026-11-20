// IT-Hub API client: one place that talks to the backend (see docs/api/README.md).

// Served by the backend at /app → same origin. Opened from another server → the local backend.
// Override with window.ITHUB_API_BASE before this module loads.
const API_BASE = window.ITHUB_API_BASE
  ?? (location.pathname.startsWith("/app/") ? "" : "http://127.0.0.1:8000");

const TOKEN_KEY = "ithub.token";
const USER_KEY = "ithub.user";

/** An API error with the server's message and, for malformed input, one message per field. */
export class ApiError extends Error {
  constructor(status, detail) {
    const fields = {};
    let message;
    if (Array.isArray(detail)) {
      // FastAPI validation list: {loc: ["body", "quantity"], msg}
      for (const item of detail) {
        const field = item.loc?.slice(1).join(".") || "form";
        fields[field] = item.msg;
      }
      message = Object.values(fields)[0] ?? "Please check the form.";
    } else {
      message = detail || `Request failed (${status}).`;
    }
    super(message);
    this.status = status;
    this.fields = fields;
  }
}

/** Sends JSON requests with the bearer token and turns errors into ApiError. */
export class ApiClient {
  constructor(baseUrl = API_BASE, storage = sessionStorage) {
    this.baseUrl = baseUrl;
    this.storage = storage;
  }

  get token() { return this.storage.getItem(TOKEN_KEY); }

  get user() {
    const raw = this.storage.getItem(USER_KEY);
    return raw ? JSON.parse(raw) : null;
  }

  /** Remember the session returned by /auth/login or /auth/google. */
  saveSession({ access_token, user }) {
    this.storage.setItem(TOKEN_KEY, access_token);
    this.saveUser(user);
  }

  saveUser(user) { this.storage.setItem(USER_KEY, JSON.stringify(user)); }

  clearSession() {
    this.storage.removeItem(TOKEN_KEY);
    this.storage.removeItem(USER_KEY);
  }

  /**
   * Call the API. `query` values that are empty are left out.
   * With `redirect` (default) a 401 sends the user to the login page and a
   * "Password change required." 403 to the change-password view.
   */
  async request(method, path, { body, query, redirect = true } = {}) {
    const url = new URL(this.baseUrl + path, location.href);
    for (const [key, value] of Object.entries(query ?? {})) {
      if (value !== undefined && value !== null && value !== "") url.searchParams.set(key, value);
    }
    const headers = { Accept: "application/json" };
    if (body !== undefined) headers["Content-Type"] = "application/json";
    if (this.token) headers.Authorization = `Bearer ${this.token}`;

    let response;
    try {
      response = await fetch(url, { method, headers, body: body === undefined ? undefined : JSON.stringify(body) });
    } catch {
      throw new ApiError(0, "Cannot reach the IT-Hub server. Check that the backend is running.");
    }
    const data = response.status === 204 ? null : await response.json().catch(() => null);
    if (response.ok) return data;

    const error = new ApiError(response.status, data?.detail);
    if (redirect && response.status === 401) {
      this.clearSession();
      const expired = error.message.startsWith("Session expired") ? "?expired=1" : "";
      location.href = `login.html${expired}`;
    } else if (redirect && response.status === 403 && error.message === "Password change required.") {
      location.href = "login.html?change=1";
    }
    throw error;
  }

  get(path, query, options) { return this.request("GET", path, { ...options, query }); }
  post(path, body = {}, options) { return this.request("POST", path, { ...options, body }); }
  put(path, body = {}, options) { return this.request("PUT", path, { ...options, body }); }
  patch(path, body = {}, options) { return this.request("PATCH", path, { ...options, body }); }
}

export const api = new ApiClient();
