// Shared page start-up and render helpers. Every signed-in page calls startPage() first.
import { api, ApiError } from "./api.js";

export { api, ApiError };

const UNREAD_POLL_MS = 60_000;

// ---- start-up -----------------------------------------------------------------------------------

/**
 * Guard a signed-in page and fill the shared header. Resolves to the current user.
 * - No token → login page; temporary password → change-password view.
 * - Elements marked [data-admin-only] (and the "Admin" nav link) are hidden for Student Assistants.
 */
export async function startPage() {
  if (!api.token) {
    location.href = "login.html";
    return new Promise(() => {});  // stop the page while the browser navigates
  }
  const user = await api.get("/auth/me");
  api.saveUser(user);
  if (user.must_change_password) {
    location.href = "login.html?change=1";
    return new Promise(() => {});
  }
  document.body.classList.toggle("is-admin", isAdmin(user));
  if (!isAdmin(user)) {
    document.querySelectorAll("[data-admin-only]").forEach((el) => { el.hidden = true; });
    document.querySelectorAll('nav a[href="admin.html"]').forEach((a) => {
      if (a.textContent.trim() === "Admin") a.hidden = true;
    });
  }
  fillHeader(user);
  pollUnread();
  return user;
}

export function isAdmin(user = api.user) { return user?.role === "ADMIN"; }

/** Log out on the server, forget the token and go to the login page. */
export async function logout() {
  try { await api.post("/auth/logout", {}, { redirect: false }); } catch { /* already gone */ }
  api.clearSession();
  location.href = "login.html";
}

function fillHeader(user) {
  const account = document.querySelector('header a[aria-label="My account"]');
  if (account) {
    account.textContent = initials(user.full_name);
    account.title = `${user.full_name} · ${roleLabel(user.role)}`;
  }
  document.querySelectorAll("[data-user-name]").forEach((el) => { el.textContent = user.full_name; });
  document.querySelectorAll("[data-user-first-name]").forEach((el) => { el.textContent = user.full_name.split(" ")[0]; });
  document.querySelectorAll("[data-user-role]").forEach((el) => { el.textContent = roleLabel(user.role); });
  document.querySelectorAll("[data-logout]").forEach((el) => el.addEventListener("click", (event) => {
    event.preventDefault();
    logout();
  }));
}

async function pollUnread() {
  const bell = document.querySelector('header a.ib[href="notifications.html"]');
  if (!bell) return;
  const update = async () => {
    try {
      const unread = await api.get("/notifications", { unread_only: true });
      const count = bell.querySelector("span");
      if (count) {
        count.textContent = unread.length > 99 ? "99+" : String(unread.length);
        count.hidden = unread.length === 0;
      }
      bell.setAttribute("aria-label", `Notifications, ${unread.length} unread`);
    } catch { /* the next poll retries */ }
  };
  await update();
  setInterval(update, UNREAD_POLL_MS);
}

// ---- formatting ---------------------------------------------------------------------------------

const ESCAPES = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };

/** Escape text for HTML. */
export function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, (ch) => ESCAPES[ch]);
}

/** Tagged template that escapes every interpolated value; nest html`` or raw() results to keep them as HTML. */
export function html(strings, ...values) {
  return strings.reduce((out, part, i) => out + part + (i < values.length ? toHtml(values[i]) : ""), "");
}

class RawHtml { constructor(text) { this.text = text; } toString() { return this.text; } }

/** Mark trusted HTML (built with html``) so html`` does not escape it. */
export function raw(text) { return new RawHtml(text); }

function toHtml(value) {
  if (value instanceof RawHtml) return value.text;
  if (Array.isArray(value)) return value.map(toHtml).join("");
  return esc(value);
}

// The server sends UTC timestamps without a zone suffix.
function parseUtc(value) { return new Date(/[zZ]|[+-]\d\d:\d\d$/.test(value) ? value : `${value}Z`); }

/** "Nov 19, 2026" for a YYYY-MM-DD date or a timestamp. */
export function fmtDate(value) {
  if (!value) return "—";
  const date = value.length === 10 ? new Date(`${value}T00:00:00`) : parseUtc(value);
  return date.toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" });
}

/** Local date and time for a UTC timestamp. */
export function fmtDateTime(value) {
  if (!value) return "—";
  return parseUtc(value).toLocaleString(undefined, { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" });
}

/** "12 min ago", "3 h ago", "2 d ago". */
export function timeAgo(value) {
  if (!value) return "";
  const minutes = Math.round((Date.now() - parseUtc(value).getTime()) / 60_000);
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes} min ago`;
  if (minutes < 60 * 24) return `${Math.round(minutes / 60)} h ago`;
  return `${Math.round(minutes / 1440)} d ago`;
}

export function initials(name = "") {
  return name.split(/\s+/).filter(Boolean).slice(0, 2).map((w) => w[0].toUpperCase()).join("") || "?";
}

export function roleLabel(role) { return role === "ADMIN" ? "Admin" : "Student Assistant"; }

/** "PARTIALLY_ARRIVED" → "Partially arrived". */
export function label(value) {
  if (!value) return "";
  const text = String(value).replace(/_/g, " ").toLowerCase();
  return text.charAt(0).toUpperCase() + text.slice(1);
}

// One colour family per status across the app (see the frontend README palette).
const BADGE_KIND = {
  good: ["AVAILABLE", "ACTIVE", "WORKING", "ARRIVED", "PASSED", "RESOLVED", "COMPLETE", "COMPLETED", "RETURNED", "SENT", "DELIVERED", "GOOD", "LOW"],
  info: ["IN_PROGRESS", "ORDERED", "SUBMITTED", "ASSIGNED", "ON_LOAN", "OPEN_LOAN", "PLANNED", "PENDING", "UNDER_REPAIR"],
  warn: ["LIMITED", "PARTIALLY_ARRIVED", "REVIEWED", "OPEN", "FAULTY", "ON_HOLD", "FAIR", "MEDIUM", "HIGH", "REQUESTED"],
  bad: ["UNUSABLE", "REJECTED", "LOST", "DAMAGED", "MISSING", "OUT_OF_SERVICE", "CRITICAL", "FAILED", "BOUNCED", "POOR", "OVERDUE"],
  final: ["CLOSED", "CANCELLED", "RETIRED", "DUPLICATE", "INACTIVE"],
};
const KIND_OF = Object.fromEntries(Object.entries(BADGE_KIND).flatMap(([kind, list]) => list.map((s) => [s, kind])));

/** A status badge using the page's .b / .b-* classes. Pass `kind` to override the colour. */
export function badge(status, kind) {
  const key = String(status ?? "").toUpperCase().replace(/ /g, "_");
  return raw(html`<span class="b b-${kind ?? KIND_OF[key] ?? "neutral"}">${label(status)}</span>`);
}

// ---- forms and feedback -------------------------------------------------------------------------

/** Form fields as an object; empty strings become null and number inputs become numbers. */
export function formData(form) {
  const data = {};
  for (const el of form.elements) {
    if (!el.name || el.disabled) continue;
    if (el.type === "checkbox") data[el.name] = el.checked;
    else if (el.type === "number") data[el.name] = el.value === "" ? null : Number(el.value);
    else if (el.multiple) data[el.name] = [...el.selectedOptions].map((o) => o.value);
    else data[el.name] = el.value.trim() === "" ? null : el.value.trim();
  }
  return data;
}

/** Show an ApiError on a form: field messages next to [name] inputs, the rest as a toast. */
export function showFormError(form, error) {
  form.querySelectorAll(".field-error").forEach((el) => el.remove());
  let shown = false;
  for (const [field, message] of Object.entries(error.fields ?? {})) {
    const input = form.querySelector(`[name="${CSS.escape(field)}"]`);
    if (!input) continue;
    input.insertAdjacentHTML("afterend", html`<p class="field-error" role="alert">${message}</p>`);
    shown = true;
  }
  if (!shown) toast(error.message, "bad");
}

/** A short message in the corner. kind: good | bad | info. */
export function toast(message, kind = "good") {
  let box = document.getElementById("toasts");
  if (!box) {
    box = document.createElement("div");
    box.id = "toasts";
    box.setAttribute("aria-live", "polite");
    document.body.append(box);
  }
  const item = document.createElement("div");
  item.className = `toast toast-${kind}`;
  item.textContent = message;
  box.append(item);
  setTimeout(() => item.remove(), kind === "bad" ? 7000 : 4000);
}

/** Run an async action from a button: disable it meanwhile and toast any error. */
export async function withBusy(button, action) {
  button.disabled = true;
  try { return await action(); } catch (error) {
    if (error instanceof ApiError) toast(error.message, "bad"); else throw error;
  } finally { button.disabled = false; }
}

/** Replace a container's content, or show an empty-state line. */
export function renderList(container, items, renderItem, emptyText = "Nothing here yet.") {
  container.innerHTML = items.length
    ? items.map(renderItem).join("")
    : html`<p class="empty">${emptyText}</p>`;
}

// Styles for the helpers above (each mockup page carries its own <style>; these are additions).
document.head.insertAdjacentHTML("beforeend", `<style>
#toasts{position:fixed;right:20px;bottom:20px;display:flex;flex-direction:column;gap:8px;z-index:1000;max-width:380px}
.toast{padding:12px 16px;border-radius:8px;font:500 14px 'Inter',system-ui,sans-serif;box-shadow:0 6px 20px rgba(0,0,0,.12)}
.toast-good{background:#DDF2E6;color:#1F5A3B}.toast-bad{background:#FBDDE0;color:#8A1C2B}.toast-info{background:#DCEBF9;color:#1C4E7A}
.field-error{margin:6px 0 0;font-size:12px;color:#8A1C2B}
.empty{margin:0;padding:16px;color:#5A6472;font-size:13px}
[hidden]{display:none!important}
</style>`);
