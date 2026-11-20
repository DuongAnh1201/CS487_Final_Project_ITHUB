// Issues: filtered list with paging, report form with possible duplicates, detail with allowed transitions.
import {
  ApiError, api, badge, fmtDateTime, formData, html, label, raw, renderList, showFormError, startPage, timeAgo, toast,
  withBusy,
} from "../app.js";
import { itemLabel, loadItems, loadUsers, roomName, submitterOf, userName, wireDialog } from "../lookups.js";

const $ = (id) => document.getElementById(id);
const PATH = ["OPEN", "ASSIGNED", "IN_PROGRESS", "RESOLVED", "CLOSED"];
const CONDITIONS = ["WORKING", "FAULTY", "UNDER_REPAIR", "OUT_OF_SERVICE", "MISSING"];
const TICK = raw(html`<svg aria-hidden="true" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round"><path d="M5 12l5 5 9-10"></path></svg>`);
// Button text for each target status; the server decides which of them are offered (allowed_next_statuses).
const ACTION = {
  ASSIGNED: ["Assign", "assign"], IN_PROGRESS: ["Start work", "direct"], RESOLVED: ["Resolve", "resolve"],
  CLOSED: ["Close", "note"], REJECTED: ["Reject", "note-required"], DUPLICATE: ["Mark as duplicate", "duplicate"], OPEN: ["Reopen", "note"],
};

const user = await startPage();
const issueId = Number(new URLSearchParams(location.search).get("id")) || null;
const state = {
  rooms: new Map(), users: new Map(), items: new Map(), equipment: new Map(), page: 1, issue: null,
  newCondition: "WORKING", pending: null, original: null,
};

document.querySelectorAll("dialog").forEach(wireDialog);

/** Run a write; a 409 on a versioned action shows the "Reload?" banner. */
function act(button, action) {
  return withBusy(button, async () => {
    try { return await action(); } catch (error) {
      if (error instanceof ApiError && error.status === 409) {
        $("conflict").hidden = false;
        toast(error.message, "bad");
        return undefined;
      }
      throw error;
    }
  });
}

const issueRoom = (issue) => { const room = state.rooms.get(issue.classroom_id); return room ? roomName(room) : `Room #${issue.classroom_id}`; };
const issueItem = (issue) => issue.room_equipment_id === null ? "Whole room"
  : state.equipment.get(issue.room_equipment_id) ?? `Item #${issue.room_equipment_id}`;
const issueNumber = (id, list) => list.find((i) => i.id === id)?.issue_id ?? `#${id}`;

/** Remember "seat · asset tag" labels of a room's installed equipment. */
async function learnEquipment(classroomId) {
  const rows = await api.get(`/classrooms/${classroomId}/equipment`).catch(() => []);
  for (const e of rows) state.equipment.set(e.id, `${e.seat_label ? `${e.seat_label} · ` : ""}${itemLabel(state.items, e.item_id)}`);
  return rows;
}

// ---- list ---------------------------------------------------------------------------------------

function listQuery() {
  const data = formData($("filters"));
  const query = { page: state.page, page_size: 50 };
  for (const key of ["status", "severity", "category", "classroom_id", "date_from", "date_to"]) if (data[key]) query[key] = data[key];
  return { query, assignee: data.assignee };
}

async function loadList() {
  const { query, assignee } = listQuery();
  const body = $("issue-rows");
  let page;
  try { page = await api.get("/issues", query); } catch (error) {
    body.innerHTML = html`<tr><td colspan="9" class="empty">${error.message}</td></tr>`;
    return;
  }
  await Promise.all([...new Set(page.items.map((i) => i.classroom_id))].map(learnEquipment));
  const items = page.items.filter((i) => !assignee || (assignee === "me" ? i.assigned_to === user.id : i.assigned_to === null));
  renderList(body, items, (i) => html`<tr${i.id === issueId ? raw(' style="background:#F2F7F4"') : ""}><td><a href="issues.html?id=${i.id}" style="font-weight:700">${i.issue_id}</a></td><td style="max-width:280px;overflow:hidden;text-overflow:ellipsis" title="${i.description}">${i.description}${i.is_repeat_problem ? raw(html` <span class="b b-warn" style="margin-left:4px">Repeat problem</span>`) : ""}</td><td>${issueRoom(i)}</td><td class="${i.room_equipment_id === null ? "muted" : ""}">${issueItem(i)}</td><td>${label(i.category)}</td><td>${badge(i.severity)}</td><td>${badge(i.status)}${i.is_overdue ? raw(html` <span class="b b-bad">Overdue</span>`) : ""}</td><td>${timeAgo(i.created_at)}</td><td class="${i.assigned_to === null ? "muted" : ""}">${i.assigned_to === null ? "Unassigned" : userName(state.users, i.assigned_to)}</td></tr>`,
  page.message ?? "No issues match these filters.");
  if (!items.length) body.innerHTML = html`<tr><td colspan="9" class="empty">${page.message ?? "No issues match these filters."}</td></tr>`;
  const pages = Math.max(1, Math.ceil(page.total / page.page_size));
  $("page-info").textContent = `Page ${page.page} of ${pages} · ${page.total} issue${page.total === 1 ? "" : "s"} · ${page.page_size} rows per page`;
  $("prev").disabled = page.page <= 1;
  $("next").disabled = page.page >= pages;
}

$("filters").addEventListener("change", () => { state.page = 1; loadList(); });
$("prev").addEventListener("click", () => { state.page -= 1; loadList(); });
$("next").addEventListener("click", () => { state.page += 1; loadList(); });

// ---- detail -------------------------------------------------------------------------------------

async function loadDetail() {
  $("conflict").hidden = true;
  const [issue, history] = await Promise.all([api.get(`/issues/${issueId}`), api.get(`/issues/${issueId}/history`)]);
  state.issue = issue;
  await learnEquipment(issue.classroom_id);
  renderDetail(issue);
  renderTimeline(history);
}

function renderDetail(issue) {
  $("detail").hidden = false;
  document.title = `IT-Hub · ${issue.issue_id}`;
  $("d-title").textContent = `${issue.issue_id} · ${label(issue.category)}`;
  $("d-repeat").hidden = !issue.is_repeat_problem;
  $("d-overdue").hidden = !issue.is_overdue;
  const reporter = `${issue.reporter_name} (${label(issue.reporter_type)})${issue.reporter_contact ? ` · ${issue.reporter_contact}` : ""}`;
  const room = state.rooms.get(issue.classroom_id);
  $("d-sub").innerHTML = html`${room ? raw(html`<a href="classrooms.html?id=${room.id}">${roomName(room)}</a>`) : issueRoom(issue)} · ${issueItem(issue)} · ${label(issue.severity)} · reported by ${reporter} · ${issue.assigned_to === null ? "unassigned" : `assigned to ${userName(state.users, issue.assigned_to)}`} · target ${issue.target_date}`;
  $("d-desc").textContent = issue.description;
  $("d-resolution").hidden = !issue.resolution_notes;
  $("d-resolution").textContent = issue.resolution_notes ? `Resolution: ${issue.resolution_notes}` : "";

  const at = PATH.indexOf(issue.status);
  const steps = PATH.map((s, i) => html`<div class="step ${at < 0 || i > at ? "next" : i < at ? "done" : "cur"}" role="listitem" ${i === at ? raw('aria-current="step"') : ""}>${i < at ? TICK : ""}${label(s)}</div>`);
  if (at < 0) steps.push(html`<div class="step cur" role="listitem" aria-current="step">${label(issue.status)}${issue.duplicate_of_id ? ` of #${issue.duplicate_of_id}` : ""}</div>`);
  $("d-path").innerHTML = steps.join("");

  const actions = issue.allowed_next_statuses.filter((s) => ACTION[s]);
  $("d-actions").innerHTML = actions.length ? actions.map((s) => html`<button class="btn ${s === "RESOLVED" ? "btn-brand" : ""}" data-status="${s}" ${s === "REJECTED" ? raw('style="color:#8A1C2B"') : ""}>${ACTION[s][0]}</button>`).join("")
    : html`<span class="muted" style="font-size:13px">No further status changes for you.</span>`;
  $("d-actions").querySelectorAll("[data-status]").forEach((b) => b.addEventListener("click", () => startAction(b.dataset.status, b)));
  $("form-resolve").hidden = true;
}

function renderTimeline(recorded) {
  // The server records changes after the report; show the report itself as the first entry.
  const issue = state.issue;
  const history = recorded.some((u) => !u.old_status && u.new_status) ? recorded
    : [{ user_id: issue.created_by, timestamp: issue.created_at, old_status: null, new_status: "OPEN", comment: "" }, ...recorded];
  const dot = (bg, fg, inner) => html`<span style="width:28px;height:28px;border-radius:50%;background:${bg};color:${fg};display:grid;place-items:center;font-size:11px;font-weight:700">${inner}</span>`;
  const rows = [...history].reverse().map((u, i, all) => {
    const who = userName(state.users, u.user_id);
    const changed = u.new_status && u.new_status !== u.old_status;
    const line = !u.old_status && u.new_status ? raw(html`Reported by <strong>${who}</strong> · status ${badge(u.new_status)}`)
      : changed ? raw(html`Status ${badge(u.old_status)} → ${badge(u.new_status)} by <strong>${who}</strong>`)
        : raw(html`<strong>${who}</strong> commented`);
    const note = u.comment ? raw(html`<div style="margin-top:6px;padding:10px 12px;background:#F7F9FB;border:1px solid #EDF0F4;border-radius:8px;white-space:pre-wrap">${u.comment}</div>`) : "";
    const icon = changed || (!u.old_status && u.new_status) ? dot("#DCEBF9", "#1C4E7A", "→") : dot("#FBD9C4", "#6B3418", who.split(/\s+/).map((w) => w[0]).slice(0, 2).join(""));
    return html`<div style="display:flex;gap:12px;padding-bottom:14px"><div style="display:flex;flex-direction:column;align-items:center">${raw(icon)}${i < all.length - 1 ? raw('<span style="flex:1;width:2px;background:#DCE1E8;margin-top:4px"></span>') : ""}</div><div style="flex:1;min-width:0"><div>${line}</div>${note}<div class="muted" style="font-size:12px;margin-top:4px">${fmtDateTime(u.timestamp)}</div></div></div>`;
  });
  renderList($("timeline"), rows, (row) => row, "No activity yet.");
}

$("btn-reload").addEventListener("click", () => loadDetail());

function startAction(status, button) {
  const kind = ACTION[status][1];
  state.pending = status;
  if (kind === "direct") {
    act(button, async () => {
      await api.post(`/issues/${issueId}/status`, { status, version: state.issue.version });
      toast("Status updated.");
      await loadDetail();
    });
  } else if (kind === "resolve") {
    openResolve();
  } else if (kind === "duplicate") {
    openDuplicate();
  } else {
    $("status-title").textContent = ACTION[status][0];
    $("assignee-field").hidden = kind !== "assign";
    $("sn-label").textContent = kind === "note-required" ? "Reason (required)" : "Note (optional)";
    if (kind === "assign") {
      const people = [...state.users.values()].filter((u) => !u.status || u.status === "ACTIVE");
      $("sa").innerHTML = people.map((u) => html`<option value="${u.id}" ${u.id === state.issue.assigned_to ? raw("selected") : ""}>${u.full_name} · ${label(u.role)}</option>`).join("");
    }
    $("sn").value = "";
    $("dlg-status").showModal();
  }
}

$("form-status").addEventListener("submit", (event) => {
  event.preventDefault();
  const data = formData(event.target);
  const body = { status: state.pending, version: state.issue.version, note: data.note ?? "" };
  if (state.pending === "ASSIGNED") body.assignee_id = Number(data.assignee_id);
  act(submitterOf(event), async () => {
    await api.post(`/issues/${issueId}/status`, body);
    $("dlg-status").close();
    toast("Status updated.");
    await loadDetail();
  }).catch((error) => showFormError(event.target, error));
});

function openResolve() {
  const form = $("form-resolve");
  form.hidden = false;
  form.reset();
  $("cond-field").hidden = state.issue.room_equipment_id === null;
  $("cond-label").textContent = `New condition for ${issueItem(state.issue)}`;
  state.newCondition = "WORKING";
  paintConditions();
  form.scrollIntoView({ block: "nearest" });
}

function paintConditions() {
  $("cond-seg").innerHTML = CONDITIONS.map((c) => html`<button type="button" class="${c === state.newCondition ? "on" : ""}" aria-pressed="${c === state.newCondition}" data-condition="${c}">${label(c)}</button>`).join("");
  $("cond-seg").querySelectorAll("button").forEach((b) => b.addEventListener("click", () => { state.newCondition = b.dataset.condition; paintConditions(); }));
}

$("cancel-resolve").addEventListener("click", () => { $("form-resolve").hidden = true; });
$("form-resolve").addEventListener("submit", (event) => {
  event.preventDefault();
  act(submitterOf(event), async () => {
    await api.post(`/issues/${issueId}/resolve`, { notes: $("rn").value.trim(), new_condition: state.newCondition, version: state.issue.version });
    toast("Issue resolved.");
    await loadDetail();
  }).catch((error) => showFormError(event.target, error));
});

async function openDuplicate() {
  const issue = state.issue;
  const page = await api.get("/issues", { classroom_id: issue.classroom_id, page_size: 50 });
  const candidates = page.items.filter((i) => i.id !== issue.id && !i.duplicate_of_id);
  $("do").innerHTML = candidates.length
    ? candidates.map((i) => html`<option value="${i.id}">${i.issue_id} · ${i.description.slice(0, 50)} · ${label(i.status)}</option>`).join("")
    : html`<option value="">No other issues in this room</option>`;
  $("dlg-duplicate").showModal();
}

$("form-duplicate").addEventListener("submit", (event) => {
  event.preventDefault();
  act(submitterOf(event), async () => {
    await api.post(`/issues/${issueId}/duplicate`, { original_id: Number($("do").value), version: state.issue.version });
    $("dlg-duplicate").close();
    toast("Marked as a duplicate.");
    await loadDetail();
  }).catch((error) => showFormError(event.target, error));
});

$("form-comment").addEventListener("submit", (event) => {
  event.preventDefault();
  act(submitterOf(event), async () => {
    await api.post(`/issues/${issueId}/comments`, { text: formData(event.target).text ?? "", version: state.issue.version });
    event.target.reset();
    toast("Comment added.");
    await loadDetail();
  }).catch((error) => showFormError(event.target, error));
});

// ---- report form --------------------------------------------------------------------------------

async function loadReportEquipment() {
  const classroomId = $("rc").value;
  const rows = classroomId ? await learnEquipment(classroomId) : [];
  $("ri").innerHTML = html`<option value="">Whole room</option>${rows.map((e) => raw(html`<option value="${e.id}">${state.equipment.get(e.id)}</option>`))}`;
  await checkDuplicates();
}

async function checkDuplicates() {
  const box = $("dups");
  const classroomId = $("rc").value;
  state.original = null;
  if (!classroomId) { box.hidden = true; return; }
  const found = await api.get("/issues/possible-duplicates", {
    classroom_id: classroomId, category: $("rk").value, room_equipment_id: $("ri").value,
  }).catch(() => []);
  box.hidden = !found.length;
  box.innerHTML = html`<strong style="font-size:13px;color:#7A4A00">Possible duplicates</strong>${found.map((i) => raw(html`<div style="display:flex;justify-content:space-between;gap:8px;align-items:center;font-size:13px"><span><a href="issues.html?id=${i.id}">${i.issue_id}</a> ${i.description.slice(0, 60)} · ${label(i.status)}</span><button class="btn" type="button" data-original="${i.id}" data-number="${i.issue_id}" style="min-height:30px;padding:0 10px">Attach</button></div>`))}<span id="attached" class="muted" style="font-size:12px" hidden></span>`;
  box.querySelectorAll("[data-original]").forEach((b) => b.addEventListener("click", () => {
    const on = state.original !== Number(b.dataset.original);
    state.original = on ? Number(b.dataset.original) : null;
    box.querySelectorAll("[data-original]").forEach((x) => { x.textContent = x === b && on ? "Attached" : "Attach"; });
    $("attached").hidden = !on;
    $("attached").textContent = on ? `This report will be saved and linked as a duplicate of ${b.dataset.number}.` : "";
  }));
}

["rc", "ri", "rk"].forEach((id) => $(id).addEventListener("change", () => (id === "rc" ? loadReportEquipment() : checkDuplicates())));

$("form-report").addEventListener("submit", (event) => {
  event.preventDefault();
  const data = formData(event.target);
  const body = {
    ...data, classroom_id: Number(data.classroom_id),
    room_equipment_id: data.room_equipment_id ? Number(data.room_equipment_id) : null,
    description: data.description ?? "", reporter_name: data.reporter_name ?? "", reporter_contact: data.reporter_contact ?? "",
  };
  withBusy(submitterOf(event), async () => {
    const created = await api.post("/issues", body);
    if (state.original) await api.post(`/issues/${created.id}/duplicate`, { original_id: state.original, version: created.version });
    toast(`${created.issue_id} reported. Admins have been notified.`);
    location.href = `issues.html?id=${created.id}`;
  }).catch((error) => showFormError(event.target, error));
});

$("btn-report").addEventListener("click", () => { $("report").scrollIntoView({ behavior: "smooth" }); $("rd").focus(); });

// ---- start --------------------------------------------------------------------------------------

const [rooms, users, items] = await Promise.all([api.get("/classrooms"), loadUsers(user), loadItems().catch(() => new Map())]);
state.rooms = new Map(rooms.map((r) => [r.id, r]));
state.users = users;
state.items = items;
const roomOptions = rooms.map((r) => html`<option value="${r.id}">${roomName(r)}</option>`).join("");
$("f-room").insertAdjacentHTML("beforeend", roomOptions);
$("rc").innerHTML = rooms.filter((r) => r.is_active).map((r) => html`<option value="${r.id}">${roomName(r)}</option>`).join("");
$("rr").value = user.full_name;
await loadReportEquipment();
if (issueId) {
  try { await loadDetail(); } catch (error) { toast(error.message, "bad"); }
}
await loadList();
