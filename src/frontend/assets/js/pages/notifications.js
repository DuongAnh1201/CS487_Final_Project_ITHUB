// NTF: own notifications, real shift roster and Admin email delivery controls (#78/#83).
import { api, badge, fmtDateTime, html, isAdmin, label, raw, startPage, toast, timeAgo } from "../app.js";
import { $, action, bindForm, detail, field, payload, select, setQuery, table, today } from "./forms.js";

const user = await startPage();
let people = [];
let request = 0;
const person = (id) => people.find((p) => p.id === id)?.full_name ?? `User #${id}`;
function recordLink(n) {
  const page = { Order: "orders.html", Report: "reports.html", Issue: "issues.html", Project: "projects.html", Task: "projects.html", Item: "inventory.html", Asset: "inventory.html", Classroom: "classrooms.html" }[n.related_type];
  if (!page || !n.related_id) return null;
  return `${page}?${n.related_type === "Task" ? "task" : "id"}=${n.related_id}`;
}
function eventIcon(n) {
  const group = n.related_type;
  const colour = {Report:["#E7E0F5","#4A3577"],Issue:["#FCDDC7","#7A3D12"],Order:["#DDF2E6","#1F5A3B"]}[group] || ["#D6E6F7","#1C4E7A"];
  const path = group === "Order" ? raw(html`<path d="M21 8l-9-5-9 5 9 5 9-5z"></path><path d="M3 8v8l9 5 9-5V8"></path>`) : group === "Report" ? raw(html`<path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"></path><path d="M14 3v6h6"></path>`) : raw(html`<path d="M9 11l3 3 8-8"></path><path d="M20 12v7a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h9"></path>`);
  return raw(html`<span class="tile" style="width:34px;height:34px;background:${colour[0]};color:${colour[1]}"><svg aria-hidden="true" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">${path}</svg></span>`);
}
async function updateBell() {
  const unread = await api.get("/notifications", { unread_only: true });
  const bell = document.querySelector('header a.ib[href="notifications.html"]');
  bell.setAttribute("aria-label", `Notifications, ${unread.length} unread`);
  bell.querySelector("span").textContent = String(unread.length);
  bell.querySelector("span").hidden = unread.length === 0;
  $("#mark-all").disabled = unread.length === 0;
}
async function loadNotifications() {
  const ticket = ++request;
  try {
    const rows = await api.get("/notifications", { unread_only: $("#unread-only").checked });
    if (ticket !== request) return;
    const q = $("#header-search").value.trim().toLowerCase();
    const visible = rows.filter((n) => `${n.message} ${label(n.event_type)}`.toLowerCase().includes(q));
    $("#notification-count").textContent = visible.length;
    $("#notification-list").innerHTML = visible.length ? html`${raw(visible.map((n) => html`<div class="nrow" id="notification-${n.id}"><a href="notifications.html?id=${n.id}" data-detail="${n.id}" aria-label="Notification details">${eventIcon(n)}</a><div style="flex:1;min-width:0"><a href="${recordLink(n) || `notifications.html?id=${n.id}`}" ${raw(!recordLink(n) ? html`data-detail="${n.id}"` : html``)} style="color:inherit"><strong>${label(n.event_type)}</strong> · ${n.message}</a><div class="muted" style="font-size:12px;margin-top:2px" title="${fmtDateTime(n.created_at)}">${timeAgo(n.created_at)} · Email ${label(n.email_status)}</div></div><div style="display:flex;align-items:center;gap:8px">${raw(!n.is_read ? html`<span style="width:9px;height:9px;border-radius:50%;background:#1F6B7A;margin-top:6px" aria-label="Unread"></span>` : html``)}<button class="btn" style="min-height:28px;padding:0 8px;font-size:12px" data-read="${n.id}" data-next="${!n.is_read}">${n.is_read ? "Mark unread" : "Mark read"}</button></div></div>`).join(""))}` : html`<p class="empty">${$("#unread-only").checked ? "No unread notifications match." : "No notifications match."}</p>`;
    await updateBell();
  } catch (error) { $("#notification-list").innerHTML = html`<p class="empty">${error.message}</p>`; toast(error.message, "bad"); }
}
async function openNotification(id) {
  try {
    const n = await api.get(`/notifications/${id}`);
    $("#notification-detail").innerHTML = html`${detail(label(n.event_type), [["Message", n.message], ["Created", fmtDateTime(n.created_at)], ["Read", n.is_read ? "Yes" : "No"], ["Read at", fmtDateTime(n.read_at)], ["Email", badge(n.email_status)], ["Email attempts", n.email_attempts]])}<div class="fields">${raw(recordLink(n) ? html`<a class="btn" href="${recordLink(n)}">Open related ${label(n.related_type)}</a>` : html``)}<button class="btn" id="close-notification">Close detail</button></div>`;
    $("#notification-detail").hidden = false;
    setQuery({ id });
    $("#close-notification").onclick = () => { $("#notification-detail").hidden = true; setQuery({}); };
  } catch (error) { toast(error.message, "bad"); }
}
let shiftLoading = null;
async function shiftForm() {
  if (!$("#shift-summary").hidden && $("#send-summary")) return;
  if (!shiftLoading) shiftLoading = buildShiftForm().finally(() => { shiftLoading = null; });
  return shiftLoading;
}
async function buildShiftForm() {
  try {
    people = await api.get("/users/directory");
    $("#shift-summary").innerHTML = html`<div class="card-h"><h2 class="card-t">Shift summary</h2></div><form id="send-summary" class="fields" style="gap:12px"><div style="display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px">${select("Shift", "shift", [["MORNING", "Morning"], ["AFTERNOON", "Afternoon"], ["EVENING", "Evening"]])}${field("Date", "shift_date", "date", today(), true)}</div><div><span class="lbl">People on shift</span><div style="display:flex;gap:6px;flex-wrap:wrap" id="recipient-chips"></div><details id="recipient-picker" style="margin-top:6px"><summary class="btn" style="min-height:28px;padding:0 10px;font-size:12px">+ Add / change people</summary><div style="padding-top:8px">${select("Select people on shift", "user_ids", people.map((p) => [p.id, `${p.full_name} · ${label(p.role)}`]), [user.id], true, true)}</div></details></div><p class="muted" style="margin:0;font-size:12px">Each person gets a summary of their open tasks.</p><button class="btn btn-brand" type="submit">Send summary</button></form>`;
    const picker = $("#send-summary [name=user_ids]");
    const chips = () => {
      $("#recipient-chips").innerHTML = html`${raw([...picker.selectedOptions].map((option) => html`<span class="b b-neutral" style="padding:4px 10px">${person(Number(option.value))}<button type="button" data-remove-recipient="${option.value}" aria-label="Remove ${person(Number(option.value))}" style="border:0;background:transparent;color:inherit;cursor:pointer">×</button></span>`).join(""))}`;
    };
    picker.onchange = chips;
    picker.oninvalid = () => { $("#recipient-picker").open = true; };
    $("#recipient-chips").onclick = (event) => { const button = event.target.closest("[data-remove-recipient]"); if (!button) return; [...picker.options].find((option) => option.value === button.dataset.removeRecipient).selected = false; if (!picker.selectedOptions.length) $("#recipient-picker").open = true; chips(); };
    chips();
    $("#shift-summary").hidden = false;
    bindForm($("#send-summary"), async (data) => {
      await api.post("/notifications/shift-summary", data);
      toast("Shift summaries sent.");
      $("#shift-summary").hidden = true;
      await loadNotifications();
    });
  } catch (error) { toast(error.message, "bad"); }
}
async function loadEmail() {
  if (!isAdmin(user)) return;
  try {
    const [config, rows] = await Promise.all([api.get("/notifications/email/config"), api.get("/notifications/email/deliveries", payload($("#delivery-filters")))]);
    $("#email-config").innerHTML = html`${detail("Configuration", [["Sending", config.enabled ? "Enabled" : "Log only (no email sent)"], ["Provider", config.provider], ["From", config.from_address || "—"], ["Delivery webhooks", config.webhook_enabled ? "Enabled" : "Not configured"]])}`;
    $("#email-deliveries").innerHTML = html`${table(["Notification", "Recipient", "Event", "Created", "Sent", "Email", "Attempts", "Last error", "Action"], rows.map((d) => html`<tr><td>#${d.id}</td><td>${person(d.recipient_id)}</td><td>${label(d.event_type)}</td><td>${fmtDateTime(d.created_at)}</td><td>${fmtDateTime(d.sent_at)}</td><td>${badge(d.email_status)}</td><td>${d.attempts}</td><td style="white-space:normal;max-width:260px">${d.error || "—"}</td><td>${raw(["FAILED", "BOUNCED"].includes(d.email_status) && d.attempts < 3 ? html`<button class="btn" data-retry="${d.id}">Retry email</button>` : html``)}</td></tr>`), "No email deliveries match these filters.")}`;
  } catch (error) { $("#email-deliveries").innerHTML = html`<p class="empty">${error.message}</p>`; toast(error.message, "bad"); }
}
$("#unread-only").onchange = loadNotifications;
$("#refresh-notifications").onclick = loadNotifications;
$("#open-summary").onclick = (event) => action(event.currentTarget, async () => { await shiftForm(); $("#shift-summary").scrollIntoView({behavior:"smooth",block:"nearest"}); });
$("#header-search").addEventListener("input", loadNotifications);
$("#mark-all").onclick = (event) => action(event.currentTarget, async () => {
  const unread = await api.get("/notifications", { unread_only: true });
  // Sequential writes avoid competing SQLite transactions; already-saved read states survive a later failure.
  try { for (const n of unread) await api.patch(`/notifications/${n.id}`, { read: true }); toast("All notifications marked read."); }
  finally { await loadNotifications(); }
});
$("#notification-list").onclick = (event) => {
  const toggle = event.target.closest("[data-read]");
  if (toggle) action(toggle, async () => {
    await api.patch(`/notifications/${toggle.dataset.read}`, { read: toggle.dataset.next === "true" });
    await loadNotifications();
    if (new URLSearchParams(location.search).get("id") === toggle.dataset.read) await openNotification(Number(toggle.dataset.read));
  });
  const link = event.target.closest("[data-detail]");
  if (link) { event.preventDefault(); openNotification(Number(link.dataset.detail)); }
};
try { people = await api.get("/users/directory"); } catch (error) { toast(error.message, "bad"); }
if (isAdmin(user)) {
  $("#email-panel").hidden = false;
  $("#delivery-recipient").innerHTML = html`<option value="">Anyone</option>${raw(people.map((p) => html`<option value="${p.id}">${p.full_name}</option>`).join(""))}`;
  $("#refresh-email").onclick = loadEmail;
  $("#delivery-filters").onsubmit = (event) => { event.preventDefault(); loadEmail(); };
  bindForm($("#email-test"), async (data) => {
    const result = await api.post("/notifications/email/test", data);
    $("#email-test-result").textContent = `Test: ${label(result.status)}${result.message_id ? ` · ${result.message_id}` : ""}`;
    toast(`Test email: ${label(result.status)}.`, ["FAILED", "BOUNCED"].includes(result.status) ? "bad" : "good");
    await loadEmail();
  });
  $("#email-deliveries").onclick = (event) => {
    const button = event.target.closest("[data-retry]");
    if (button) action(button, async () => { const result = await api.post(`/notifications/${button.dataset.retry}/email/retry`); toast(`Email: ${label(result.email_status)}.`); await loadEmail(); });
  };
  await loadEmail();
}
await loadNotifications();
await shiftForm();
const id = new URLSearchParams(location.search).get("id");
if (id) await openNotification(Number(id));
