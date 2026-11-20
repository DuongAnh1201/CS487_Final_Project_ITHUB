// Accounts (US-USR-02–05), read-only audit (US-RPT-07/08), and My account.
import { api, badge, fmtDate, fmtDateTime, html, initials, isAdmin, raw, roleLabel, startPage, toast } from "../app.js";
import { actions, attr, forms, fragment, input, personName, quickSearch, read, rows, select, values } from "./page-forms.js";

const user = await startPage();
const root = document.getElementById("page-content");
const state = { users: [], directory: [], selected: null, offset: 0, limit: 100, auditFilters: {}, records: [] };
const roles = values(["STUDENT_ASSISTANT", "ADMIN"]);
const name = (id) => personName([...state.users, ...state.directory], id);

function shell() {
  root.innerHTML = html`<section class="card"><div class="card-h"><div><div class="muted">Administration &amp; account</div><h1>${isAdmin(user) ? "Users & accounts" : "My account & audit log"}</h1></div>${isAdmin(user) ? raw(html`<button class="btn btn-brand" data-admin-only data-action="new-user">Create account</button>`) : ""}</div></section>
  ${isAdmin(user) ? raw(html`<div class="split" data-admin-only><section class="card grow"><form data-form="users-search" class="fields">${input("Name, email or school ID", "q", "", "search")}${select("Role", "role", roles, null, "All roles")}${select("Status", "status", values(["ACTIVE", "INACTIVE"]), null, "All statuses")}<button class="btn" type="submit">Search users</button></form><div class="table-scroll"><table><thead><tr><th>Name</th><th>School ID</th><th>Role</th><th>Access ends</th><th>Last login</th><th>Status</th><th></th></tr></thead><tbody id="users"></tbody></table></div></section><section id="user-editor" class="card side" hidden></section></div>`) : ""}
  <section class="card" id="audit"><div class="card-h"><div><h2 class="card-t">Audit log</h2><p class="muted">Read-only history of every change.</p></div>${badge("Read only")}</div><form data-form="audit-search" class="fields">${select("Person", "user_id", state.directory.map((person) => ({ value: person.id, text: person.full_name })), null, "Any person (includes system)")}${input("Record type", "entity_type")}${input("Record ID", "entity_id")}${input("Action", "action")}${input("From", "date_from", "", "date")}${input("To", "date_to", "", "date")}${select("Rows per page", "limit", [25, 100, 500].map((n) => ({ value: n, text: String(n) })), 100, null)}<button class="btn" type="submit">Search audit</button></form><div class="table-scroll"><table><thead><tr><th>When</th><th>Who</th><th>Action</th><th>Record</th><th>Old value</th><th>New value</th></tr></thead><tbody id="audit-rows"></tbody></table></div><div class="card-h"><span id="audit-page" class="muted"></span><div class="actions"><button class="btn" data-action="previous" data-managed-disabled>Previous</button><button class="btn" data-action="next" data-managed-disabled>Next</button></div></div><div id="audit-detail" class="pad" hidden></div></section>
  <section class="card" id="my-account"><div class="card-h"><h2 class="card-t">My account</h2><button class="btn" data-logout>Log out</button></div><div class="pad stack"><div class="spread"><span class="av">${initials(user.full_name)}</span><strong>${user.full_name}</strong>${badge(user.status)}</div><dl class="profile"><div><dt>Name</dt><dd>${user.full_name}</dd></div><div><dt>Email</dt><dd>${user.email}</dd></div><div><dt>School ID</dt><dd>${user.school_id}</dd></div><div><dt>Role</dt><dd>${roleLabel(user.role)}</dd></div><div><dt>Access ends</dt><dd>${fmtDate(user.access_end_date)}</dd></div><div><dt>Last login</dt><dd>${fmtDateTime(user.last_login_at)}</dd></div></dl><form data-form="password" class="stack"><h3>Change password</h3>${input("Current password", "current_password", "", "password", true)}${input("New password", "new_password", "", "password", true)}<button class="btn" type="submit">Change password</button></form></div></section>`;
  // startPage wires static data-logout before this dynamic section exists.
  root.querySelector("[data-logout]").addEventListener("click", async () => { const { logout } = await import("../app.js"); await logout(); });
  root.querySelector('[name="current_password"]').autocomplete = "current-password";
  root.querySelector('[name="new_password"]').autocomplete = "new-password";
  if (isAdmin(user)) quickSearch(root.querySelector('[data-form="users-search"]'));
}
async function loadUsers(query = {}) {
  const { q, ...filters } = query;
  state.users = await api.get("/users", filters);
  const needle = (q ?? "").toLocaleLowerCase();
  const visible = state.users.filter((person) => `${person.full_name} ${person.email} ${person.school_id}`.toLocaleLowerCase().includes(needle));
  document.getElementById("users").innerHTML = visible.length ? visible.map((person) => html`<tr><td><strong>${person.full_name}</strong><div class="muted">${person.email}</div></td><td>${person.school_id}</td><td>${roleLabel(person.role)}</td><td>${fmtDate(person.access_end_date)}</td><td>${fmtDateTime(person.last_login_at)}</td><td>${badge(person.status)}</td><td><button class="btn" data-action="edit-user" data-id="${person.id}">Edit</button></td></tr>`).join("") : html`<tr><td colspan="7" class="empty">No users match your filters.</td></tr>`;
}
function userEditor(person = null) {
  state.selected = person;
  const element = document.getElementById("user-editor");
  element.hidden = false;
  element.innerHTML = html`<div class="card-h"><h2 class="card-t">${person ? `Edit · ${person.full_name}` : "Create account"}</h2><button class="btn" data-action="close-user">Cancel</button></div><div class="pad stack"><form data-form="user" data-id="${person?.id ?? ""}" class="stack">${person ? raw(html`${select("Role", "role", roles, person.role, null)}${select("Status", "status", values(["ACTIVE", "INACTIVE"]), person.status, null)}<p class="muted">At least one active Admin must remain. Accounts are never deleted.</p>`) : raw(html`${input("Full name", "full_name", "", "text", true)}${input("School email", "email", "", "email", true)}${input("School ID", "school_id", "", "text", true)}${select("Role", "role", roles, "STUDENT_ASSISTANT", null)}${input("Access end date", "access_end_date", "", "date")}${input("Temporary password", "temporary_password", "", "password", true)}`)}<button class="btn btn-brand" type="submit">${person ? "Save account" : "Create account"}</button></form>${person ? raw(html`<form data-form="reset-password" class="stack"><h3>Reset password</h3><p class="muted">Sets a temporary password and ends all sessions for this user.</p>${input("Temporary password", "temporary_password", "", "password", true)}<button class="btn" type="submit">Reset password</button></form>`) : ""}</div>`;
  element.querySelector('[name="temporary_password"]')?.setAttribute("autocomplete", "new-password");
  element.scrollIntoView({ behavior: "smooth", block: "start" });
}
async function loadAudit() {
  state.records = await api.get("/audit", { ...state.auditFilters, limit: state.limit, offset: state.offset });
  document.getElementById("audit-rows").innerHTML = state.records.length ? state.records.map((record) => html`<tr><td><a href="#audit-detail" data-action="audit-detail" data-id="${record.id}">${fmtDateTime(record.timestamp)}</a></td><td>${name(record.actor_id)}</td><td>${record.action}</td><td>${record.entity_type} · ${record.entity_id}</td><td><pre class="audit-value">${JSON.stringify(record.old_value, null, 2) ?? "—"}</pre></td><td><pre class="audit-value">${JSON.stringify(record.new_value, null, 2) ?? "—"}</pre></td></tr>`).join("") : html`<tr><td colspan="6" class="empty">No audit entries match your filters.</td></tr>`;
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
    document.getElementById("user-editor").hidden = true;
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
  "close-user": () => { document.getElementById("user-editor").hidden = true; },
  previous: () => auditPage(Math.max(0, state.offset - state.limit)),
  next: () => auditPage(state.offset + state.limit),
  "audit-detail": async (button) => {
    const record = await api.get(`/audit/${button.dataset.id}`); const detail = document.getElementById("audit-detail");
    detail.innerHTML = html`<h3>Audit entry #${record.id}</h3><p>${record.entity_type} · ${record.entity_id} · ${record.action} · ${record.status}</p><pre class="report-content">${JSON.stringify(record, null, 2)}</pre>`;
    detail.hidden = false; detail.scrollIntoView({ behavior: "smooth" });
  },
});
try {
  state.directory = await api.get("/users/directory"); shell();
  const query = new URLSearchParams(location.search); const form = root.querySelector('[data-form="audit-search"]');
  for (const field of ["entity_type", "entity_id", "action", "user_id"]) if (query.has(field)) { form.elements[field].value = query.get(field); state.auditFilters[field] = query.get(field); }
  await Promise.all([loadAudit(), ...(isAdmin(user) ? [loadUsers()] : [])]);
} catch (error) { toast(error.message, "bad"); root.insertAdjacentHTML("beforeend", html`<p class="empty" role="alert">${error.message} <a href="admin.html">Reload account</a></p>`); }
