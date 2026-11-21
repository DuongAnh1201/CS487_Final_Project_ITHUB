// Accounts (US-USR-02–05), read-only audit (US-RPT-07/08), and My account.
import { api, badge, fmtDate, fmtDateTime, html, initials, isAdmin, label, raw, roleLabel, startPage, toast } from "../app.js";
import { changeRows, fieldPairs, summary } from "./audit-format.js";
import { actions, compactFilters, pageIcon, plusIcon, attr, forms, fragment, input, personName, quickSearch, read, rows, select, values } from "./page-forms.js";

const user = await startPage();
const root = document.getElementById("page-content");
root.inert = true;
root.setAttribute("aria-busy", "true");
const state = { users: [], directory: [], selected: null, offset: 0, limit: 100, auditFilters: {}, records: [] };
const roles = values(["STUDENT_ASSISTANT", "ADMIN"]);
const name = (id) => personName([...state.users, ...state.directory], id);
const AUDIT_CELL_FIELDS = 3;
// Up to three "Field: value" lines per cell; the full text is in the tooltip and the entry detail.
const auditValue = (value) => {
  const pairs = fieldPairs(value);
  if (!pairs.length) return raw(html`<span class="muted">—</span>`);
  const shown = pairs.slice(0, AUDIT_CELL_FIELDS).map(([key, text]) => key === "Value" ? html`<div class="audit-value">${text}</div>` : html`<div class="audit-value"><span class="muted">${key}:</span> ${text}</div>`).join("");
  const more = pairs.length > AUDIT_CELL_FIELDS ? html`<div class="muted audit-more">+${pairs.length - AUDIT_CELL_FIELDS} more</div>` : "";
  return raw(html`<div title="${summary(value)}">${raw(shown)}${raw(more)}</div>`);
};

function shell() {
  root.innerHTML = html`<section class="card"><div class="page-heading">${pageIcon("admin")}<div class="heading-copy"><div class="eyebrow muted">${isAdmin(user) ? "Admin" : "Account"}</div><h1>${isAdmin(user) ? "Users & accounts" : "My account & audit log"}</h1></div>${isAdmin(user) ? raw(html`<button class="btn btn-brand" data-admin-only data-action="new-user">${plusIcon()} Create account</button>`) : ""}</div></section>
  ${isAdmin(user) ? raw(html`<div class="admin-workspace" data-admin-only><section class="card"><form data-form="users-search" class="filter-bar">${input("Name, email or school ID", "q", "", "search")}${select("Role", "role", roles, null, "All roles")}${select("Status", "status", values(["ACTIVE", "INACTIVE"]), null, "All statuses")}<button class="btn" type="submit">Search</button></form><div class="table-scroll"><table><thead><tr><th>Name</th><th>School ID</th><th>Role</th><th>Access ends</th><th>Last login</th><th>Status</th><th></th></tr></thead><tbody id="users"></tbody></table></div></section><section id="user-editor" class="card"></section></div>`) : ""}
  <section class="card" id="audit"><div class="card-h"><div><h2 class="card-t"><span class="tile audit-tile">◷</span>Audit log</h2><p class="section-caption">Read-only history of every change.</p></div>${badge("Read only")}</div><form data-form="audit-search" class="filter-bar audit-filters">${select("Person", "user_id", state.directory.map((person) => ({ value: person.id, text: person.full_name })), null, "Any person (includes system)")}${input("Record type", "entity_type")}${input("Record ID", "entity_id")}${input("Action", "action")}${input("From", "date_from", "", "date")}${input("To", "date_to", "", "date")}${select("Rows per page", "limit", [25, 100, 500].map((n) => ({ value: n, text: String(n) })), 100, null)}<button class="btn" type="submit">Search</button></form><div class="table-scroll"><table><thead><tr><th>When</th><th>Who</th><th>Action</th><th>Record</th><th>Old value</th><th>New value</th></tr></thead><tbody id="audit-rows"></tbody></table></div><div class="audit-footer"><span id="audit-page" class="muted"></span><div class="actions"><button class="btn btn-small" data-action="previous" data-managed-disabled>Previous</button><button class="btn btn-small" data-action="next" data-managed-disabled>Next</button></div></div><div id="audit-detail" class="pad" hidden></div></section>
  <section class="card account-card" id="my-account"><div class="card-h"><h2 class="card-t">My account</h2><button class="btn" data-logout>Log out</button></div><div class="account-profile"><span class="account-avatar">${initials(user.full_name)}</span><dl class="profile"><div><dt>Name</dt><dd>${user.full_name}</dd></div><div><dt>Email</dt><dd>${user.email}</dd></div><div><dt>School ID</dt><dd>${user.school_id}</dd></div><div><dt>Role</dt><dd>${roleLabel(user.role)}</dd></div><div><dt>Last login</dt><dd>${fmtDateTime(user.last_login_at)}</dd></div><div><dt>Access ends</dt><dd>${fmtDate(user.access_end_date)}</dd></div></dl></div><details class="account-password"><summary class="btn">Change password</summary><form data-form="password" class="stack">${input("Current password", "current_password", "", "password", true)}${input("New password", "new_password", "", "password", true)}<button class="btn" type="submit">Change password</button></form></details></section>`;
  root.querySelector("[data-logout]").addEventListener("click", async () => { const { logout } = await import("../app.js"); await logout(); });
  root.querySelector('[name="current_password"]').autocomplete = "current-password";
  root.querySelector('[name="new_password"]').autocomplete = "new-password";
  compactFilters(root);
  if (isAdmin(user)) { clearUserEditor(); quickSearch(root.querySelector('[data-form="users-search"]')); }
}

async function loadUsers(query = {}) {
  const { q, ...filters } = query;
  state.users = await api.get("/users", filters);
  const needle = (q ?? "").toLocaleLowerCase();
  const visible = state.users.filter((person) => `${person.full_name} ${person.email} ${person.school_id}`.toLocaleLowerCase().includes(needle));
  document.getElementById("users").innerHTML = visible.length ? visible.map((person) => html`<tr data-user-id="${person.id}" class="${state.selected?.id === person.id ? "selected-row" : ""}"><td title="${person.full_name}"><strong>${person.full_name}</strong><div class="muted" title="${person.email}">${person.email}</div></td><td title="${person.school_id}">${person.school_id}</td><td>${badge(roleLabel(person.role), person.role === "ADMIN" ? "final" : "info")}</td><td>${fmtDate(person.access_end_date)}</td><td>${fmtDateTime(person.last_login_at)}</td><td>${badge(person.status)}</td><td><button class="btn" data-action="edit-user" data-id="${person.id}">Edit</button></td></tr>`).join("") : html`<tr><td colspan="7" class="empty">No users match your filters.</td></tr>`;
}
function userEditor(person = null, focus = true) {
  state.selected = person;
  const element = document.getElementById("user-editor");
  element.innerHTML = html`<div class="card-h"><h2 class="card-t">${person ? `Edit · ${person.full_name}` : "Create account"}</h2><div class="actions">${person ? badge(roleLabel(person.role), person.role === "ADMIN" ? "final" : "info") : ""}<button class="btn btn-small" data-action="close-user">Cancel</button></div></div><div class="pad stack"><form data-form="user" data-id="${person?.id ?? ""}" class="stack">${person ? raw(html`${select("Role", "role", roles, person.role, null)}<div class="account-state">${select("Account status", "status", values(["ACTIVE", "INACTIVE"]), person.status, null)}${badge(person.status)}</div><p class="section-caption">At least one active Admin is required. Accounts are never deleted.</p>`) : raw(html`${input("Full name", "full_name", "", "text", true)}<div class="form-row">${input("School email", "email", "", "email", true)}${input("School ID", "school_id", "", "text", true)}</div><div class="form-row">${select("Role", "role", roles, "STUDENT_ASSISTANT", null)}${input("Access end date", "access_end_date", "", "date")}</div>${input("Temporary password", "temporary_password", "", "password", true)}`)}<div class="actions"><button class="btn btn-brand" type="submit">${person ? "Save account" : "Create account"}</button>${person ? raw(html`<button class="btn" type="button" data-action="toggle-reset">Reset password</button><button class="btn danger-link" type="button" data-action="toggle-user">${person.status === "ACTIVE" ? "Deactivate" : "Activate"}</button>`) : ""}</div></form>${person ? raw(html`<p class="section-caption">Reset sets a temporary password and logs the user out everywhere.</p><form data-form="reset-password" class="stack" hidden>${input("Temporary password", "temporary_password", "", "password", true)}<button class="btn" type="submit">Set temporary password</button></form>`) : ""}</div>`;
  element.querySelector('[name="temporary_password"]')?.setAttribute("autocomplete", "new-password");
  root.querySelectorAll("#users [data-user-id]").forEach((row) => row.classList.toggle("selected-row", Number(row.dataset.userId) === person?.id));
  if (focus && matchMedia("(max-width: 950px)").matches) element.scrollIntoView({ behavior: "smooth", block: "start" });
}

function clearUserEditor() {
  state.selected = null;
  document.getElementById("user-editor").innerHTML = html`<div class="card-h"><h2 class="card-t">Manage account</h2></div><p class="empty">Select an account to edit, or create a new one.</p>`;
  root.querySelectorAll("#users .selected-row").forEach((row) => row.classList.remove("selected-row"));
}

async function loadAudit() {
  state.records = await api.get("/audit", { ...state.auditFilters, limit: state.limit, offset: state.offset });
  document.getElementById("audit-rows").innerHTML = state.records.length ? state.records.map((record) => html`<tr><td><a href="#audit-detail" data-action="audit-detail" data-id="${record.id}">${fmtDateTime(record.timestamp)}</a></td><td>${name(record.actor_id)}</td><td>${label(record.action)}</td><td>${record.entity_type} · ${record.entity_id}</td><td>${auditValue(record.old_value)}</td><td>${auditValue(record.new_value)}</td></tr>`).join("") : html`<tr><td colspan="6" class="empty">No audit entries match your filters.</td></tr>`;
  document.getElementById("audit-page").textContent = state.records.length ? `Entries ${state.offset + 1}–${state.offset + state.records.length}` : "No entries on this page";
  root.querySelector('[data-action="previous"]').disabled = state.offset === 0;
  root.querySelector('[data-action="next"]').disabled = state.records.length < state.limit;
}
async function auditPage(offset) {
  const previousOffset = state.offset;
  try { state.offset = offset; await loadAudit(); }
  catch (error) { state.offset = previousOffset; throw error; }
  finally {
    root.querySelector('[data-action="previous"]').disabled = state.offset === 0;
    root.querySelector('[data-action="next"]').disabled = state.records.length < state.limit;
  }
}
forms(root, {
  "users-search": (form) => loadUsers(read(form)),
  user: async (form) => {
    const data = read(form);
    if (form.dataset.id) await api.patch(`/users/${form.dataset.id}`, data); else await api.post("/users", data);
    clearUserEditor();
    await loadUsers(); toast("Account saved.");
    // Refresh one's own role/status immediately; startPage applies the current server guard.
    if (Number(form.dataset.id) === user.id) location.reload();
  },
  "reset-password": async (form) => { await api.post(`/users/${state.selected.id}/reset-password`, read(form)); form.reset(); toast("Temporary password set. The user must change it at sign-in."); if (state.selected.id === user.id) location.href = "login.html"; },
  "audit-search": async (form) => { const { limit, ...query } = read(form); state.auditFilters = query; state.limit = Number(limit); state.offset = 0; await loadAudit(); },
  password: async (form) => { const result = await api.post("/auth/change-password", read(form)); form.reset(); toast(result.message); },
});
actions(root, {
  "new-user": () => userEditor(), "edit-user": async (button) => userEditor(await api.get(`/users/${button.dataset.id}`)),
  "close-user": () => clearUserEditor(),
  "toggle-reset": () => { const form = root.querySelector('[data-form="reset-password"]'); form.hidden = !form.hidden; if (!form.hidden) form.querySelector("input").focus(); },
  "toggle-user": async () => {
    const person = await api.patch(`/users/${state.selected.id}`, { status: state.selected.status === "ACTIVE" ? "INACTIVE" : "ACTIVE" });
    await loadUsers(); userEditor(person, false); toast("Account saved."); if (person.id === user.id) location.reload();
  },
  previous: () => auditPage(Math.max(0, state.offset - state.limit)),
  next: () => auditPage(state.offset + state.limit),
  "audit-detail": async (button) => {
    const record = await api.get(`/audit/${button.dataset.id}`); const detail = document.getElementById("audit-detail");
    const changes = changeRows(record.old_value, record.new_value);
    detail.innerHTML = html`<h3>Audit entry #${record.id}</h3><dl class="profile audit-meta"><div><dt>When</dt><dd>${fmtDateTime(record.timestamp)}</dd></div><div><dt>Who</dt><dd>${name(record.actor_id)}</dd></div><div><dt>Action</dt><dd>${label(record.action)}</dd></div><div><dt>Record</dt><dd>${record.entity_type} · ${record.entity_id}</dd></div><div><dt>Result</dt><dd>${badge(record.status)}</dd></div></dl>${raw(changes.length ? html`<div class="table-scroll"><table class="audit-changes"><thead><tr><th>Field</th><th>Before</th><th>After</th></tr></thead><tbody>${raw(changes.map((row) => html`<tr class="${row.changed ? "changed" : ""}"><td>${row.field}</td><td>${row.before}</td><td>${row.after}</td></tr>`).join(""))}</tbody></table></div>` : html`<p class="empty">No field values were recorded for this entry.</p>`)}`;
    detail.hidden = false; detail.scrollIntoView({ behavior: "smooth" });
  },
});
try {
  state.directory = await api.get("/users/directory"); shell();
  const query = new URLSearchParams(location.search); const form = root.querySelector('[data-form="audit-search"]');
  for (const field of ["entity_type", "entity_id", "action", "user_id"]) if (query.has(field)) { form.elements[field].value = query.get(field); state.auditFilters[field] = query.get(field); }
  await Promise.all([loadAudit(), ...(isAdmin(user) ? [loadUsers()] : [])]);
  if (isAdmin(user) && state.users.length) userEditor(state.users[0], false);
} catch (error) { toast(error.message, "bad"); root.insertAdjacentHTML("beforeend", html`<p class="empty" role="alert">${error.message} <a href="admin.html">Reload account</a></p>`); }
finally { root.inert = false; root.removeAttribute("aria-busy"); }
