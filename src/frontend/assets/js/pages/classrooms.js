// Classrooms: room search, room detail with seat map, equipment actions, room check, timetable, schedule import.
import {
  ApiError, api, badge, fmtDate, fmtDateTime, formData, html, label, raw, renderList, showFormError, startPage,
  toast, withBusy,
} from "../app.js";
import { hhmm, itemLabel, loadItems, loadUsers, roomName, submitterOf, userName, wireDialog } from "../lookups.js";

const SEAT_CLASS = { FAULTY: "seat-faulty", UNDER_REPAIR: "seat-repair", OUT_OF_SERVICE: "seat-oos", MISSING: "seat-missing" };
const DOT = { WORKING: "#5DB386", FAULTY: "#E07A86", UNDER_REPAIR: "#EBA54E", OUT_OF_SERVICE: "#3D4756", MISSING: "#5A6472" };
const DAYS = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"];
const LAST_IMPORT_KEY = "ithub.lastScheduleImport";
const $ = (id) => document.getElementById(id);

const user = await startPage();
const isAdminUser = user.role === "ADMIN";
const roomId = Number(new URLSearchParams(location.search).get("id")) || null;
const state = { room: null, equipment: [], items: new Map(), users: new Map(), seat: null, view: "day", rooms: [], entry: null };

document.querySelectorAll("dialog").forEach(wireDialog);

/** Run a write action; a 409 on a versioned action shows the "Reload?" banner. */
async function act(button, action, { versioned = false } = {}) {
  return withBusy(button, async () => {
    try { return await action(); } catch (error) {
      if (versioned && error instanceof ApiError && error.status === 409) {
        $("conflict").hidden = false;
        toast(error.message, "bad");
        return undefined;
      }
      throw error;
    }
  });
}

// ---- room list ----------------------------------------------------------------------------------

function filterQuery() {
  const data = formData($("filters"));
  const query = Object.fromEntries(Object.entries(data).filter(([, v]) => v !== null && v !== ""));
  const slot = ["slot_date", "start_time", "end_time"].filter((k) => query[k]);
  if (slot.length && slot.length < 3) throw new ApiError(422, "Free slot requires date, start time and end time.");
  return query;
}

function roomCard(room, equipment) {
  const desktops = (equipment ?? []).filter((e) => state.items.get(e.item_id)?.category.toUpperCase() === "DESKTOP");
  const working = desktops.filter((e) => e.condition === "WORKING").length;
  const detail = room.closed_reason && room.status === "CLOSED" ? room.closed_reason
    : !desktops.length ? "No desktops installed" : `${working} / ${desktops.length} desktops working`;
  const bar = desktops.length
    ? raw(html`<div class="bar"><span style="width:${Math.round((100 * working) / desktops.length)}%"></span></div>` ) : "";
  return html`<a class="room" href="classrooms.html?id=${room.id}"><div style="display:flex;justify-content:space-between;align-items:center"><strong style="font-size:15px">${roomName(room)}</strong>${badge(room.is_active ? room.status : "INACTIVE")}</div><span class="muted" style="font-size:13px">${label(room.room_type)} · ${room.capacity} seats</span>${bar}<span style="font-size:13px">${detail}</span>${room.check_overdue ? raw(html`<span class="b b-warn" style="align-self:flex-start">Room check overdue</span>`) : ""}</a>`;
}

async function loadList() {
  const grid = $("room-grid");
  let rooms;
  try { rooms = await api.get("/classrooms", filterQuery()); } catch (error) {
    grid.innerHTML = html`<p class="empty">${error.message}</p>`;
    return;
  }
  const equipment = await Promise.all(rooms.map((r) => api.get(`/classrooms/${r.id}/equipment`).catch(() => null)));
  renderList(grid, rooms.map((r, i) => roomCard(r, equipment[i])), (card) => card, "No rooms match these filters.");
}

async function startList() {
  state.rooms = await api.get("/classrooms");
  const buildings = [...new Set(state.rooms.map((r) => r.building))].sort();
  $("fb").insertAdjacentHTML("beforeend", buildings.map((b) => html`<option>${b}</option>`).join(""));
  $("filters").addEventListener("submit", (event) => { event.preventDefault(); loadList(); });
  $("filters").addEventListener("change", (event) => { if (!event.target.name?.match(/slot_date|_time/)) loadList(); });
  await loadList();
  const last = localStorage.getItem(LAST_IMPORT_KEY);
  if (last) showImport(await api.get(`/schedule/imports/${last}`).catch(() => null), $("import-view"), $("import-body-list"), $("import-title-list"));
}

// ---- room detail --------------------------------------------------------------------------------

async function loadRoom() {
  $("conflict").hidden = true;
  const [room, equipment] = await Promise.all([api.get(`/classrooms/${roomId}`), api.get(`/classrooms/${roomId}/equipment`)]);
  state.room = room;
  state.equipment = equipment.sort((a, b) =>
    (a.seat_label || `~${a.id}`).localeCompare(b.seat_label || `~${b.id}`, undefined, { numeric: true }));
  if (state.seat && !state.equipment.some((e) => e.id === state.seat)) state.seat = null;
  renderRoom();
  renderSeats();
  renderSeatPanel();
}

function renderRoom() {
  const room = state.room;
  document.title = `IT-Hub · ${roomName(room)}`;
  $("room-title").textContent = `${roomName(room)} (${room.classroom_id})`;
  $("room-status").innerHTML = badge(room.is_active ? room.status : "INACTIVE");
  $("room-sub").textContent = `Building ${room.building} · ${label(room.room_type)} · Capacity ${room.capacity}`
    + (room.last_checked_at ? ` · Last checked ${fmtDateTime(room.last_checked_at)}` : " · Never checked")
    + (room.check_overdue ? " (overdue)" : "");
  $("room-closed").hidden = !room.closed_reason;
  $("room-closed").textContent = room.closed_reason ? `Closed: ${room.closed_reason}` : "";
  const closure = $("btn-closure");
  closure.textContent = room.closed_for_maintenance ? "Reopen room" : "Close for maintenance";
  closure.style.color = room.closed_for_maintenance ? "" : "#8A1C2B";
  for (const id of ["btn-install", "btn-edit-room", "btn-closure", "btn-deactivate"]) $(id).disabled = !room.is_active;
}

function renderSeats() {
  renderList($("seats"), state.equipment, (e) => {
    const seat = e.seat_label || `#${e.id}`;
    const item = state.items.get(e.item_id);
    const kind = SEAT_CLASS[e.condition] ?? "";
    return html`<button type="button" class="seat ${kind} ${e.id === state.seat ? "seat-sel" : ""}" data-equipment="${e.id}" aria-label="Seat ${seat}, ${label(e.condition)}"><span style="display:flex;justify-content:space-between;align-items:center;width:100%"><strong>${seat}</strong><span class="dot"></span></span><span class="muted" style="font-size:11px">${item?.asset_tag ?? `Item #${e.item_id}`}${item && item.category.toUpperCase() !== "DESKTOP" ? ` (${item.category})` : ""}</span><span style="font-size:11px;font-weight:600">${label(e.condition)}</span></button>`;
  }, "No equipment installed yet. Use “Install equipment”.");
  $("seats").querySelectorAll(".seat").forEach((button) => button.addEventListener("click", () => {
    state.seat = Number(button.dataset.equipment);
    renderSeats();
    renderSeatPanel();
  }));
}

const selected = () => state.equipment.find((e) => e.id === state.seat);

function renderSeatPanel() {
  const e = selected();
  $("seat-empty").hidden = Boolean(e);
  $("seat-form").hidden = !e;
  $("seat-cond").innerHTML = e ? badge(e.condition) : "";
  if (!e) { $("seat-title").textContent = "Select a seat"; return; }
  $("seat-title").textContent = `Seat ${e.seat_label || `#${e.id}`} · ${itemLabel(state.items, e.item_id)}`;
  $("cc").value = e.condition;
  $("cr").value = "";
  loadSeatHistory(e.id);
}

const HISTORY_DOT = { INSTALL: "#5DB386", REMOVE: "#8A94A3", CONDITION: "#EBA54E" };

/** History of the item behind a seat: installs, condition changes, moves and removals. */
async function loadSeatHistory(equipmentId) {
  const box = $("seat-details");
  box.innerHTML = html`<strong style="font-size:13px;color:#181818">History</strong><p class="empty" style="padding:8px 0">Loading…</p>`;
  let rows;
  try { rows = await api.get(`/classroom-equipment/${equipmentId}/history`); } catch (error) {
    box.innerHTML = html`<strong style="font-size:13px;color:#181818">History</strong><p class="empty" style="padding:8px 0">${error.message}</p>`;
    return;
  }
  if (state.seat !== equipmentId) return;  // another seat was selected meanwhile
  const room = (id) => (state.rooms.find((r) => r.id === id) ? roomName(state.rooms.find((r) => r.id === id)) : `room #${id}`);
  const text = (r) => r.action === "CONDITION"
    ? raw(html`${label(r.old_condition)} → <strong>${label(r.new_condition)}</strong>${r.reason ? ` · ${r.reason}` : ""}${r.issue_id ? raw(html` · from issue <a href="issues.html?id=${r.issue_id}">#${r.issue_id}</a>`) : ""}`)
    : r.action === "INSTALL" ? `Installed in ${room(r.classroom_id)}` : `Removed from ${room(r.classroom_id)}`;
  box.innerHTML = html`<strong style="font-size:13px;color:#181818">History</strong>${[...rows].reverse().map((r) => raw(html`<div style="display:flex;gap:10px;margin-top:10px"><span style="width:8px;height:8px;border-radius:50%;background:${HISTORY_DOT[r.action] ?? "#8A94A3"};margin-top:6px;flex:none"></span><div><div>${text(r)}</div><div class="muted" style="font-size:12px">${fmtDateTime(r.timestamp)} · ${userName(state.users, r.user_id)}</div></div></div>`))}`;
}

$("seat-form").addEventListener("submit", (event) => {
  event.preventDefault();
  const e = selected();
  const { condition, reason } = formData(event.target);
  act(submitterOf(event), async () => {
    await api.post(`/classroom-equipment/${e.id}/condition`, { condition, reason: reason ?? "", version: e.version });
    toast("Condition saved.");
    await loadRoom();
  }, { versioned: true }).catch((error) => showFormError(event.target, error));
});

$("btn-remove").addEventListener("click", (event) => {
  const button = event.currentTarget;
  if (button.dataset.confirm !== "yes") {
    button.dataset.confirm = "yes";
    button.textContent = "Confirm remove";
    setTimeout(() => { button.dataset.confirm = ""; button.textContent = "Remove"; }, 5000);
    return;
  }
  const e = selected();
  button.dataset.confirm = "";
  button.textContent = "Remove";
  act(button, async () => {
    await api.post(`/classroom-equipment/${e.id}/remove`, { version: e.version });
    toast("Equipment removed from the room.");
    state.seat = null;
    await loadRoom();
  }, { versioned: true });
});

$("btn-move").addEventListener("click", async () => {
  const rooms = state.rooms.length ? state.rooms : (state.rooms = await api.get("/classrooms"));
  $("mr").innerHTML = rooms.filter((r) => r.id !== roomId && r.is_active)
    .map((r) => html`<option value="${r.id}">${roomName(r)} · ${label(r.room_type)}</option>`).join("");
  $("dlg-move").showModal();
});

$("form-move").addEventListener("submit", (event) => {
  event.preventDefault();
  const e = selected();
  act(submitterOf(event), async () => {
    await api.post(`/classroom-equipment/${e.id}/move`, { to_classroom_id: Number($("mr").value), version: e.version });
    $("dlg-move").close();
    toast("Equipment moved.");
    state.seat = null;
    await loadRoom();
  }, { versioned: true }).catch((error) => showFormError(event.target, error));
});

$("btn-reload").addEventListener("click", () => loadRoom());

// ---- install ------------------------------------------------------------------------------------

$("btn-install").addEventListener("click", async () => {
  const rooms = state.rooms.length ? state.rooms : (state.rooms = await api.get("/classrooms"));
  const [available, ...installed] = await Promise.all([
    api.get("/ast/items", { status: "Available" }), ...rooms.map((r) => api.get(`/classrooms/${r.id}/equipment`).catch(() => [])),
  ]);
  const taken = new Set(installed.flat().map((e) => e.item_id));
  state.items = await loadItems();
  const eligible = available.filter((i) => !taken.has(i.id)
    && ["DESKTOP", "MONITOR"].includes(state.items.get(i.id)?.category.toUpperCase()));
  $("ii").innerHTML = eligible.length
    ? eligible.map((i) => html`<option value="${i.id}">${i.asset_tag} · ${i.model} (${state.items.get(i.id).category})</option>`).join("")
    : html`<option value="">No available desktops or monitors</option>`;
  $("dlg-install").showModal();
});

$("form-install").addEventListener("submit", (event) => {
  event.preventDefault();
  const data = formData(event.target);
  act(submitterOf(event), async () => {
    await api.post(`/classrooms/${roomId}/equipment`, { item_id: Number(data.item_id), seat_label: data.seat_label ?? "" });
    $("dlg-install").close();
    event.target.reset();
    state.items = await loadItems();
    toast("Equipment installed.");
    await loadRoom();
  }).catch((error) => showFormError(event.target, error));
});

// ---- room check ---------------------------------------------------------------------------------

$("btn-check").addEventListener("click", () => {
  $("check-rows").innerHTML = state.equipment.length ? state.equipment.map((e) => html`<div class="g2" style="align-items:end" data-row="${e.id}"><div><span class="lbl">${e.seat_label || `#${e.id}`} · ${itemLabel(state.items, e.item_id)}</span><select class="input" name="observed_condition" aria-label="Observed condition">${["WORKING", "FAULTY", "UNDER_REPAIR", "OUT_OF_SERVICE", "MISSING"].map((c) => raw(html`<option value="${c}" ${c === e.condition ? "selected" : ""}>${label(c)}</option>`))}</select></div><input class="input" name="comment" placeholder="Comment (optional)" aria-label="Comment"></div>`).join("")
    : html`<p class="empty">No equipment is installed in this room.</p>`;
  $("dlg-check").showModal();
});

$("form-check").addEventListener("submit", (event) => {
  event.preventDefault();
  const results = [...$("check-rows").querySelectorAll("[data-row]")].map((row) => {
    const e = state.equipment.find((x) => x.id === Number(row.dataset.row));
    return {
      room_equipment_id: e.id, version: e.version,
      observed_condition: row.querySelector("[name=observed_condition]").value,
      comment: row.querySelector("[name=comment]").value.trim(),
    };
  });
  act(submitterOf(event), async () => {
    await api.post(`/classrooms/${roomId}/checks`, { notes: $("cn").value.trim(), results });
    $("dlg-check").close();
    event.target.reset();
    toast("Room check saved.");
    await loadRoom();
  }, { versioned: true }).catch((error) => showFormError(event.target, error));
});

// ---- admin: create/edit/close/deactivate --------------------------------------------------------

async function openRoomForm(room) {
  $("room-form-title").textContent = room ? `Edit ${roomName(room)}` : "New room";
  $("room-location-field").hidden = Boolean(room);
  $("rl").required = !room;
  if (!room) {
    const locations = await api.get("/ast/locations");
    $("rl").innerHTML = locations.map((l) => html`<option value="${l.id}">${l.building}-${l.room}${l.description ? ` · ${l.description}` : ""}</option>`).join("");
  }
  $("rcap").value = room?.capacity ?? "";
  $("rtype").value = room?.room_type ?? "LECTURE";
  $("form-room").dataset.mode = room ? "edit" : "create";
  $("dlg-room").showModal();
}

$("btn-new-room").addEventListener("click", () => openRoomForm(null));
$("btn-edit-room").addEventListener("click", () => openRoomForm(state.room));
$("form-room").addEventListener("submit", (event) => {
  event.preventDefault();
  const data = formData(event.target);
  const editing = event.target.dataset.mode === "edit";
  act(submitterOf(event), async () => {
    if (editing) {
      await api.patch(`/classrooms/${roomId}`, { capacity: data.capacity, room_type: data.room_type });
      toast("Room updated.");
      $("dlg-room").close();
      await loadRoom();
    } else {
      const created = await api.post("/classrooms", { location_id: Number(data.location_id), capacity: data.capacity, room_type: data.room_type });
      location.href = `classrooms.html?id=${created.id}`;
    }
  }).catch((error) => showFormError(event.target, error));
});

$("btn-closure").addEventListener("click", () => {
  const closing = !state.room.closed_for_maintenance;
  $("closure-title").textContent = closing ? "Close for maintenance" : "Reopen room";
  $("clr").closest("div").hidden = !closing;
  $("clr").value = "";
  $("dlg-closure").showModal();
});

$("form-closure").addEventListener("submit", (event) => {
  event.preventDefault();
  const closing = !state.room.closed_for_maintenance;
  act(submitterOf(event), async () => {
    await api.post(`/classrooms/${roomId}/closure`, { closed: closing, reason: closing ? $("clr").value.trim() : "" });
    $("dlg-closure").close();
    toast(closing ? "Room closed for maintenance." : "Room reopened.");
    await loadRoom();
  }).catch((error) => showFormError(event.target, error));
});

$("btn-deactivate").addEventListener("click", (event) => {
  const button = event.currentTarget;
  if (button.dataset.confirm !== "yes") {
    button.dataset.confirm = "yes";
    button.textContent = "Confirm deactivate";
    setTimeout(() => { button.dataset.confirm = ""; button.textContent = "Deactivate"; }, 5000);
    return;
  }
  act(button, async () => {
    await api.post(`/classrooms/${roomId}/deactivate`);
    toast("Room deactivated.");
    await loadRoom();
  });
});

// ---- timetable ----------------------------------------------------------------------------------

const today = () => new Date().toISOString().slice(0, 10);

function entryRow(entry, withDay) {
  const when = `${hhmm(entry.start_time)}–${hhmm(entry.end_time)}`;
  if (entry.status === "CANCELLED") {
    return html`<div class="entry" style="background:#F7F9FB;opacity:.75"><div style="width:84px;flex:none;font-size:12px;font-weight:700;color:#5A6472;text-decoration:line-through">${when}</div><div style="min-width:0"><div style="font-weight:600;color:#5A6472">${entry.course_code} · ${entry.course_title}</div><span class="b b-final">Cancelled</span></div></div>`;
  }
  const actions = isAdminUser ? raw(html`<span style="display:flex;gap:6px;margin-left:auto"><button class="btn" style="min-height:28px;padding:0 8px" data-edit="${entry.id}">Edit</button><button class="btn" style="min-height:28px;padding:0 8px;color:#8A1C2B" data-cancel="${entry.id}">Cancel</button></span>`) : "";
  return html`<div class="entry"><div style="width:84px;flex:none;font-size:12px;font-weight:700;color:#2B2F36">${when}</div><div style="min-width:0"><div style="font-weight:600">${entry.course_code} · ${entry.course_title}</div><div class="muted" style="font-size:12px">${entry.instructor_name}${withDay ? ` · ${label(entry.day_of_week)}` : ""}${entry.source === "IMPORT" ? " · imported" : ""}</div></div>${actions}</div>`;
}

async function loadTimetable() {
  const day = $("tt-date").value || today();
  document.querySelectorAll(".seg-btn").forEach((b) => {
    const on = b.dataset.view === state.view;
    b.setAttribute("aria-pressed", String(on));
    b.style.background = on ? "#BFE3D0" : "#fff";
    b.style.color = on ? "#173F2D" : "#3D4756";
  });
  $("tt-title").textContent = state.view === "day" ? `${fmtDate(day)} in ${roomName(state.room)}` : `Week of ${fmtDate(day)}`;
  let timetable;
  try { timetable = await api.get(`/classrooms/${roomId}/timetable`, { day, view: state.view, include_cancelled: true }); } catch (error) {
    $("timetable").innerHTML = html`<p class="empty">${error.message}</p>`;
    return;
  }
  state.entries = new Map(timetable.days.flatMap((d) => d.entries).map((e) => [e.id, e]));
  $("timetable").innerHTML = timetable.days.map((d) => html`${state.view === "week" ? raw(html`<strong style="font-size:12px;margin-top:6px">${new Date(`${d.day}T00:00:00`).toLocaleDateString(undefined, { weekday: "long", month: "short", day: "numeric" })}</strong>`) : ""}${d.entries.length ? d.entries.map((e) => raw(entryRow(e, false))) : raw(html`<div class="entry" style="background:none;border:1px dashed #C9D1DC"><span class="muted">${d.message ?? "No classes scheduled."}</span></div>`)}`).join("");
  $("timetable").querySelectorAll("[data-cancel]").forEach((b) => b.addEventListener("click", () => cancelEntry(b)));
  $("timetable").querySelectorAll("[data-edit]").forEach((b) => b.addEventListener("click", () => openEntryForm(state.entries.get(Number(b.dataset.edit)))));
}

function cancelEntry(button) {
  if (button.dataset.confirm !== "yes") {
    button.dataset.confirm = "yes";
    button.textContent = "Confirm cancel";
    return;
  }
  act(button, async () => {
    await api.post(`/schedule/entries/${button.dataset.cancel}/cancel`);
    toast("Meeting cancelled. The record is kept.");
    await loadTimetable();
  });
}

function openEntryForm(entry) {
  state.entry = entry ?? null;
  $("entry-title").textContent = entry ? `Edit ${entry.course_code}` : "Add meeting";
  const form = $("form-entry");
  form.reset();
  if (entry) {
    for (const name of ["course_code", "course_title", "instructor_name", "day_of_week", "term_start", "term_end"]) form.elements[name].value = entry[name];
    form.elements.start_time.value = hhmm(entry.start_time);
    form.elements.end_time.value = hhmm(entry.end_time);
  }
  $("dlg-entry").showModal();
}

$("btn-add-entry").addEventListener("click", () => openEntryForm(null));
$("form-entry").addEventListener("submit", (event) => {
  event.preventDefault();
  const body = { ...formData(event.target), classroom_id: roomId };
  act(submitterOf(event), async () => {
    if (state.entry) await api.put(`/schedule/entries/${state.entry.id}`, body);
    else await api.post("/schedule/entries", body);
    $("dlg-entry").close();
    toast(state.entry ? "Meeting updated." : "Meeting added.");
    await loadTimetable();
  }).catch((error) => showFormError(event.target, error));
});

document.querySelectorAll(".seg-btn").forEach((b) => b.addEventListener("click", () => { state.view = b.dataset.view; loadTimetable(); }));
$("tt-date").addEventListener("change", loadTimetable);

// ---- schedule import ----------------------------------------------------------------------------

function showImport(result, card, body, title) {
  if (!result) return;
  card.hidden = false;
  title.textContent = `Schedule import · ${result.file_name}`;
  body.innerHTML = html`<div style="display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px"><div style="padding:12px;border-radius:8px;background:#DDF2E6"><div style="font-size:24px;font-weight:800;color:#1F5A3B">${result.rows_accepted}</div><div style="font-size:12px;font-weight:600;color:#1F5A3B">rows accepted</div></div><div style="padding:12px;border-radius:8px;background:#FBDDE0"><div style="font-size:24px;font-weight:800;color:#8A1C2B">${result.rows_rejected}</div><div style="font-size:12px;font-weight:600;color:#8A1C2B">rows rejected</div></div></div>${result.rejected_rows.length ? raw(html`<ul style="margin:0;padding:0;list-style:none;font-size:13px;display:flex;flex-direction:column;gap:8px">${result.rejected_rows.map((r) => raw(html`<li style="display:flex;gap:10px"><span class="b b-neutral">Row ${r.row}</span><span>${r.reason}</span></li>`))}</ul>`) : raw(html`<p class="muted" style="margin:0;font-size:13px">Every row was accepted.</p>`)}<div class="muted" style="font-size:12px">Imported ${fmtDateTime(result.imported_at)}</div>`;
}

$("btn-import").addEventListener("click", () => $("dlg-import").showModal());
$("form-import").addEventListener("submit", (event) => {
  event.preventDefault();
  const file = $("cf").files[0];
  act(submitterOf(event), async () => {
    const result = await api.post("/schedule/imports", { file_name: file.name, content: await file.text() });
    localStorage.setItem(LAST_IMPORT_KEY, result.id);
    $("dlg-import").close();
    event.target.reset();
    toast(`Imported ${result.rows_accepted} row(s), rejected ${result.rows_rejected}.`, result.rows_rejected ? "info" : "good");
    if (roomId) { showImport(result, $("import-card"), $("import-body"), $("import-title")); await loadTimetable(); }
    else showImport(result, $("import-view"), $("import-body-list"), $("import-title-list"));
  }).catch((error) => showFormError(event.target, error));
});

// ---- start --------------------------------------------------------------------------------------

state.users = await loadUsers(user);
state.items = await loadItems().catch(() => new Map());
if (roomId) {
  state.rooms = await api.get("/classrooms").catch(() => []);
  $("filters").closest("section").hidden = true;
  $("room-grid").hidden = true;
  $("room-view").hidden = false;
  $("tt-date").value = today();
  try {
    await loadRoom();
    await loadTimetable();
    const last = localStorage.getItem(LAST_IMPORT_KEY);
    if (last) showImport(await api.get(`/schedule/imports/${last}`).catch(() => null), $("import-card"), $("import-body"), $("import-title"));
  } catch (error) {
    $("room-view").hidden = true;
    $("room-grid").hidden = false;
    $("room-grid").innerHTML = html`<p class="empty">${error.message} <a href="classrooms.html">Back to all rooms</a></p>`;
  }
} else {
  await startList();
}
