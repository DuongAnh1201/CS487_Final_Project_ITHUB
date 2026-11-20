// Inventory: US-AST-01–11. All lifecycle, eligibility and stock rules remain enforced by the API.
import { api, badge, fmtDate, fmtDateTime, html, raw, startPage, toast, isAdmin, label } from "../app.js";
import { $, action, addDays, bindForm, checkbox, detail, field, notes, payload, select, setQuery, table, today } from "./forms.js";

const user = await startPage();
const tabs = { equipment: "Equipment", consumables: "Consumables", loans: "Loans", overdue: "Overdue", borrowers: "Borrowers", lookups: "Categories & locations" };
const params = new URLSearchParams(location.search);
const state = { tab: params.get("tab") || "equipment", items: [], supplies: [], categories: [], locations: [], borrowers: [], loans: [], overdue: [], orders: [], people: [], installed: new Map(), installationError: false };
if (!tabs[state.tab]) state.tab = "equipment";
let searchRequest = 0;
let equipmentPage = 1;
let equipmentMatches = [];
const PAGE_SIZE = 20;
const byId = (items, id) => items.find((item) => item.id === Number(id));
const category = (id) => byId(state.categories, id)?.name ?? `Category #${id}`;
const locationName = (id) => { const l = byId(state.locations, id); return l ? `${l.building} · ${l.room}` : `Location #${id}`; };
const borrowerName = (id) => byId(state.borrowers, id)?.full_name ?? `Borrower #${id}`;
const itemName = (id) => { const item = byId(state.items, id); return item ? `${item.asset_tag} · ${item.model}` : `Item #${id}`; };
const activeOrders = new Set(["REQUESTED", "ORDERED", "PARTIALLY_ARRIVED"]);
const conditions = ["Good", "Fair", "Poor", "Damaged"].map((value) => [value, value]);
const itemOptions = () => state.items.filter((item) => !byId(state.supplies, item.id)).map((item) => [item.id, `${item.asset_tag} · ${item.model} · ${item.status}`]);
const categoryOptions = (consumable) => state.categories.filter((c) => c.is_consumable === consumable).map((c) => [c.id, c.name]);
const locationOptions = () => state.locations.map((l) => [l.id, locationName(l.id)]);
const borrowerOptions = () => state.borrowers.map((b) => [b.id, `${b.full_name} · ${b.school_id} · ${b.type}`]);

async function load() {
  const [items, supplies, categories, locations, borrowers, loans, overdue, orders, people] = await Promise.all([
    api.get("/ast/items"), api.get("/ast/consumables"), api.get("/ast/categories"), api.get("/ast/locations"),
    api.get("/ast/borrowers"), api.get("/ast/loans"), api.get("/ast/overdue"), api.get("/orders"), api.get("/users/directory"),
  ]);
  Object.assign(state, { items, supplies, categories, locations, borrowers, loans, overdue, orders, people });
}
async function loadInstallations() {
  // Classroom state is separate from ItemStatus (DD-CLS-01). Never pretend a failed lookup means uninstalled.
  try {
    const rooms = await api.get("/classrooms");
    const rows = await Promise.all(rooms.map(async (room) => [room, await api.get(`/classrooms/${room.id}/equipment`)]));
    state.installed = new Map();
    for (const [room, equipment] of rows) for (const e of equipment) state.installed.set(e.item_id, { room, equipment: e });
    state.installationError = false;
  } catch (error) { state.installationError = true; toast(error.message, "bad"); }
}
function renderTabs() {
  $("#inventory-tabs").innerHTML = html`${raw(Object.entries(tabs).map(([key, name]) => html`<a class="tab ${key === state.tab ? "on" : ""}" href="inventory.html?tab=${key}" data-tab="${key}" ${raw(key === state.tab ? html`aria-current="page"` : html``)}>${name}${key === "overdue" && state.overdue.length ? badge(state.overdue.length, "bad") : ""}</a>`).join(""))}`;
}
function chooseTab(tab, updateQuery = true) {
  state.tab = tab;
  $("#editor").hidden = true;
  $("#record").hidden = true;
  renderTabs();
  renderView();
  if (updateQuery) setQuery({ tab });
  if (tab === "equipment") defaultLendingSidebar();
}
function openLoan(id) {
  const loan = byId(state.loans, id);
  if (!loan) { toast("Loan not found.", "bad"); return; }
  if (state.tab !== "loans") { state.tab = "loans"; renderTabs(); renderView(); }
  const item = byId(state.items, loan.item_id);
  const borrower = byId(state.borrowers, loan.borrower_id);
  const overdue = state.overdue.find((row) => row.loan.id === loan.id);
  const editable = loan.status === "OPEN" && item?.status !== "Retired";
  setQuery({ loan: loan.id });
  $("#record").innerHTML = html`${detail(loan.status === "OPEN" ? `${item?.asset_tag || "Item #" + loan.item_id} · current loan` : `Loan #${loan.id} · ${item?.asset_tag || loan.item_id}`, [
    ["Borrower", borrowerName(loan.borrower_id)], ["Condition out", loan.condition_out], ["Checked out", fmtDate(loan.checkout_date)],
    ["Due", `${fmtDate(loan.due_date)}${overdue ? ` · ${overdue.days_overdue} days overdue` : ""}`],
    ...(loan.status !== "OPEN" ? [["Returned", fmtDate(loan.return_date)], ["Condition in", loan.condition_in]] : []),
  ])}<div class="toolbar" style="padding:0 16px 16px">${raw(editable ? html`<button class="btn btn-brand" data-return="${loan.id}">Return item</button>${raw(!loan.extended ? html`<button class="btn" data-extend="${loan.id}">Extend loan</button>` : html``)}<button class="btn" data-incident="${loan.item_id}">Report incident</button>` : html``)}<button class="btn" data-item="${loan.item_id}">Item history</button><button class="btn" data-close-record>Close</button></div><p class="muted" style="margin:0;padding:0 16px 16px;font-size:12px">${loan.extended ? "The one-time extension has been used." : "A loan can be extended once by up to 7 days."}${loan.notes ? ` ${loan.notes}` : ""}</p><p class="muted" style="margin:0;padding:0 16px 16px;font-size:12px">${borrower?.email || ""} · ${badge(loan.status)}</p>`;
  $("#record").hidden = false;
}

function openEditor(title, fields, save, setup, focus = true) {
  $("#record").hidden = true;
  $("#editor").innerHTML = html`<div class="card-h"><h2 class="card-t">${title}</h2><button class="btn" id="close-editor">Cancel</button></div><form class="fields" id="inventory-form">${fields}<button class="btn btn-brand" type="submit">${title}</button></form>`;
  $("#editor").hidden = false;
  $("#close-editor").onclick = () => { $("#editor").hidden = true; };
  bindForm($("#inventory-form"), save);
  setup?.($("#inventory-form"));
  if (focus) {
    $("#editor").scrollIntoView({ behavior: "smooth", block: "nearest" });
    $("#inventory-form").querySelector("input, select, textarea")?.focus({ preventScroll: true });
  }
}
async function afterSave(message) {
  toast(message);
  await load();
  renderTabs();
  renderView();
  $("#editor").hidden = true;
}
function installedCell(item) {
  const link = state.installed.get(item.id);
  return link ? raw(html`<a href="classrooms.html?id=${link.room.id}">${link.room.building} · ${link.room.room}${link.equipment.seat_label ? ` · Seat ${link.equipment.seat_label}` : ""}</a>`) : state.installationError ? "Unavailable" : "—";
}
function equipmentRows(items, resetPage = true) {
  if (resetPage) equipmentPage = 1;
  const supplyIds = new Set(state.supplies.map((c) => c.id));
  equipmentMatches = items.filter((item) => !supplyIds.has(item.id)).sort((a, b) => a.asset_tag.localeCompare(b.asset_tag));
  const start = (equipmentPage - 1) * PAGE_SIZE;
  const equipment = equipmentMatches.slice(start, start + PAGE_SIZE);
  $("#equipment-count").textContent = `${equipmentMatches.length} items · sorted by asset tag`;
  $("#equipment-statuses").innerHTML = html`${raw(["Available", "On Loan", "Lost", "Damaged", "Retired"].map((status) => html`${badge(`${status} ${equipmentMatches.filter((i) => i.status === status).length}`, {Available:"good", "On Loan":"info", Lost:"bad", Damaged:"warn", Retired:"final"}[status])}`).join(""))}`;
  $("#equipment-table").innerHTML = html`${table(["Asset tag", "Model", "Serial no.", "Category", "Location", "Status", "Installed in"], equipment.map((item) => html`<tr><td><a href="inventory.html?id=${item.id}" data-item="${item.id}" style="font-weight:700">${item.asset_tag}</a></td><td>${item.model}</td><td class="muted">${item.serial_number}</td><td>${category(item.category_id)}</td><td>${locationName(item.location_id)}</td><td>${badge(item.status)}</td><td>${installedCell(item)}</td></tr>`), "No equipment matches these filters.")}`;
  $("#equipment-pagination").innerHTML = html`<span class="muted" style="font-size:13px">Showing ${equipment.length ? start + 1 : 0}–${start + equipment.length} of ${equipmentMatches.length}</span><div class="toolbar"><button class="btn" data-page="previous" ${raw(equipmentPage === 1 ? html`disabled` : html``)}>Previous</button><button class="btn" data-page="next" ${raw(start + PAGE_SIZE >= equipmentMatches.length ? html`disabled` : html``)}>Next</button><button class="btn" data-clear-equipment>Clear filters</button></div>`;
}
function loanRows(loans) {
  return table(["Item", "Borrower", "Checkout", "Due", "Returned", "Condition out / in", "Status", ""], loans.map((loan) => html`<tr><td>${itemName(loan.item_id)}</td><td>${borrowerName(loan.borrower_id)}</td><td>${fmtDate(loan.checkout_date)}</td><td>${fmtDate(loan.due_date)}</td><td>${fmtDate(loan.return_date)}</td><td>${loan.condition_out} / ${loan.condition_in || "—"}</td><td>${badge(loan.status)}</td><td><a class="btn" href="inventory.html?loan=${loan.id}" data-loan="${loan.id}">Details</a></td></tr>`), "No loans match these filters.");
}
function stockWarning() {
  const low = state.supplies.filter((c) => c.status !== "Retired" && c.quantity_on_hand <= c.reorder_threshold);
  const system = state.orders.find((o) => o.requested_by === null && activeOrders.has(o.status) && low.some((c) => c.id === o.item_id));
  return raw(system ? html`<div role="status" style="display:flex;gap:10px;align-items:center;margin:14px 16px 0;padding:10px 14px;border-radius:8px;background:#FCEBCF;color:#7A4A00;font-size:13px;flex-wrap:wrap"><span><strong>Stock low:</strong> order <a href="orders.html?id=${system.id}">#${system.id}</a> created automatically for ${system.item_name}.</span></div>` : html``);
}
function renderConsumables() {
  $("#consumable-card").innerHTML = html`<div class="card-h"><h2 class="card-t"><span class="tile" style="background:#FCDDC7;color:#7A3D12;width:32px;height:32px"><svg aria-hidden="true" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 8l-9-5-9 5 9 5 9-5z"></path><path d="M3 8v8l9 5 9-5V8"></path></svg></span>Consumables</h2><div class="toolbar"><button class="btn" data-create="stock-in">Stock in</button><button class="btn" data-create="stock-out">Stock out</button><button class="btn btn-brand" data-create="consumable">New consumable</button></div></div>${stockWarning()}${table(["Name", "Category", "Location", "Unit", "On hand", "Reorder at", ""], state.supplies.map((c) => {
      const low = c.quantity_on_hand <= c.reorder_threshold;
      const order = state.orders.find((o) => o.item_id === c.id && activeOrders.has(o.status));
      return html`<tr class="${low ? "low-stock" : ""}"><td><a href="inventory.html?consumable=${c.id}" data-consumable="${c.id}">${c.name}</a></td><td>${category(c.category_id)}</td><td>${locationName(c.location_id)}</td><td>${c.unit}</td><td><strong>${c.quantity_on_hand}</strong></td><td>${c.reorder_threshold}</td><td>${c.status === "Retired" ? badge("Retired") : badge(low ? "At or below threshold" : "OK", low ? "bad" : "good")} ${order ? raw(html`<a href="orders.html?id=${order.id}">#${order.id} · ${order.requested_by === null ? "System · " : ""}${label(order.status)}</a>`) : "—"}</td></tr>`;
    }), "No consumables yet. Create a consumable category and a location to get started.")}`;

}
function defaultLendingSidebar() {
  if (state.borrowers.length && itemOptions().length) lendForm(undefined, false);
  else {
    $("#editor").innerHTML = html`<div class="card-h"><h2 class="card-t">Lend an item</h2></div><p class="empty">Register equipment and add a borrower before lending.</p><div class="toolbar" style="padding:0 16px 16px"><button class="btn" data-create="item">Register equipment</button><button class="btn" data-create="borrower">New borrower</button></div>`;
    $("#editor").hidden = false;
  }
}
function renderView() {
  ++searchRequest;
  $("#consumable-card").hidden = !["equipment", "consumables"].includes(state.tab);
  if (!$("#consumable-card").hidden) renderConsumables();
  const container = $("#list-card");
  container.hidden = state.tab === "consumables";
  if (state.tab === "equipment") {
    container.innerHTML = html`<form id="equipment-filters" class="filter-grid"><label class="search-field"><span class="sr">Search asset tag, serial or model</span><input class="input" name="q" type="search" placeholder="Asset tag, serial number or model"><button type="submit" aria-label="Search equipment">⌕</button></label>${select("Category", "category_id", [["", "All categories"], ...categoryOptions(false)], "", false)}${select("Location", "location_id", [["", "All locations"], ...locationOptions()], "", false)}${select("Status", "status", [["", "All statuses"], ...["Available", "On Loan", "Lost", "Damaged", "Retired"].map((v) => [v, v])], "", false)}</form><div style="padding:10px 16px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px"><span class="muted" style="font-size:13px" id="equipment-count"></span><div class="toolbar" id="equipment-statuses"></div></div><div id="equipment-table"></div><div id="equipment-pagination" style="display:flex;justify-content:space-between;align-items:center;padding:12px 16px;flex-wrap:wrap;gap:8px"></div>`;
    equipmentRows(state.items);
    let debounce;
    const search = async () => {
      const request = ++searchRequest;
      const { q, ...filters } = payload($("#equipment-filters"));
      try {
        const items = await api.get("/ast/items", filters);
        const query = (q || "").toLowerCase();
        if (request === searchRequest && state.tab === "equipment") equipmentRows(items.filter((i) => [i.asset_tag, i.serial_number, i.model].some((v) => v.toLowerCase().includes(query))));
      } catch (error) { toast(error.message, "bad"); }
    };
    $("#equipment-filters").onsubmit = (event) => { event.preventDefault(); clearTimeout(debounce); search(); };
    $("#equipment-filters").onchange = search;
    $("#equipment-filters").oninput = () => { clearTimeout(debounce); debounce = setTimeout(search, 250); };
  } else if (state.tab === "consumables") {
    return;
  } else if (state.tab === "loans") {
    container.innerHTML = html`<div class="card-h"><h2 class="card-t">Loan history</h2><button class="btn btn-brand" data-create="lend">Lend an item</button></div><form id="loan-filters" class="filter-grid">${select("Item", "item_id", [["", "All items"], ...itemOptions()], "", false)}${select("Borrower", "borrower_id", [["", "All borrowers"], ...borrowerOptions()], "", false)}<button class="btn" type="submit">Filter loans</button><button class="btn" type="reset">Clear filters</button></form><div id="loan-table">${loanRows(state.loans)}</div>`;
    $("#loan-filters").onsubmit = async (event) => {
      event.preventDefault();
      try { const loans = await api.get("/ast/loans", payload(event.currentTarget)); if (state.tab === "loans") $("#loan-table").innerHTML = html`${loanRows(loans)}`; }
      catch (error) { toast(error.message, "bad"); }
    };
    $("#loan-filters").onreset = () => { $("#loan-table").innerHTML = html`${loanRows(state.loans)}`; };
  } else if (state.tab === "overdue") {
    container.innerHTML = html`<div class="card-h"><h2 class="card-t">Overdue loans</h2><button class="btn" data-refresh>Refresh</button></div>${table(["Item", "Borrower", "Contact", "Due", "Days overdue", ""], state.overdue.map(({loan, item, borrower, days_overdue}) => html`<tr><td>${item.asset_tag} · ${item.model}</td><td>${borrower.full_name}</td><td><a href="mailto:${borrower.email}">${borrower.email}</a></td><td>${fmtDate(loan.due_date)}</td><td>${badge(days_overdue, "bad")}</td><td><a class="btn" href="inventory.html?loan=${loan.id}" data-loan="${loan.id}">Return / extend</a></td></tr>`), "No overdue loans.")}`;
  } else if (state.tab === "borrowers") {
    container.innerHTML = html`<div class="card-h"><h2 class="card-t">Borrowers</h2><button class="btn btn-brand" data-create="borrower">New borrower</button></div>${table(["School ID", "Name", "Email", "Type", "Department", "Open loans", ""], state.borrowers.map((b) => html`<tr><td>${b.school_id}</td><td>${b.full_name}</td><td><a href="mailto:${b.email}">${b.email}</a></td><td>${b.type}</td><td>${b.department || "—"}</td><td>${state.loans.filter((l) => l.borrower_id === b.id && !l.return_date).length}</td><td><button class="btn" data-borrower-history="${b.id}">Loan history</button></td></tr>`), "No borrowers yet.")}`;
  } else {
    container.innerHTML = html`<div class="card-h"><h2 class="card-t">Categories</h2>${raw(isAdmin(user) ? html`<button class="btn btn-brand" data-create="category" data-admin-only>New category</button>` : html``)}</div>${table(["Name", "Tracking"], state.categories.map((c) => html`<tr><td>${c.name}</td><td>${c.is_consumable ? "Consumable quantity" : "Individual equipment"}</td></tr>`), "No categories yet. Ask an Admin to create one.")}<div class="card-h"><h2 class="card-t">Locations</h2><button class="btn btn-brand" data-create="location">New location</button></div>${table(["Building", "Room", "Description"], state.locations.map((l) => html`<tr><td>${l.building}</td><td>${l.room}</td><td style="white-space:normal">${l.description || "—"}</td></tr>`), "No locations yet.")}`;
  }
}
async function openItem(id) {
  if (byId(state.supplies, id)) return openConsumable(id);
  try {
    const item = await api.get(`/ast/items/${id}`);
    const loans = await api.get("/ast/loans", { item_id: id });
    if (state.tab !== "equipment") { state.tab = "equipment"; renderTabs(); renderView(); }
    setQuery({ id: item.id });
    const current = loans.find((l) => l.status === "OPEN");
    $("#record").innerHTML = html`${detail(`${item.asset_tag} · ${item.model}`, [["Status", badge(item.status)], ["Serial number", item.serial_number], ["Manufacturer", item.manufacturer], ["Category", category(item.category_id)], ["Location", locationName(item.location_id)], ["Installed in", installedCell(item)], ["Purchased", fmtDate(item.purchase_date)], ["Warranty ends", fmtDate(item.warranty_end_date)], ["Notes", item.notes || "—"], ["Updated", fmtDateTime(item.updated_at)]])}<div class="fields"><div class="toolbar">${raw(item.status !== "Retired" ? html`<button class="btn" data-edit="${item.id}">Edit item</button><button class="btn" data-incident="${item.id}">Report incident</button>${raw(item.status === "Available" ? html`<button class="btn btn-brand" data-lend="${item.id}">Lend item</button>` : html``)}${raw(isAdmin(user) ? html`<button class="btn" data-retire="${item.id}" data-admin-only>Retire item</button>` : html``)}` : html`<p class="muted">Retired items are read-only. Their history is kept.</p>`)}${raw(current ? html`<button class="btn" data-loan="${current.id}">Current loan</button>` : html``)}<button class="btn" data-close-record>Close detail</button></div></div><div class="card-h"><h3 class="card-t">Loan history</h3></div>${loanRows(loans)}`;
    $("#record").hidden = false;
  } catch (error) { toast(error.message, "bad"); }
}
async function openConsumable(id) {
  try {
    const [item, movements, orders] = await Promise.all([api.get(`/ast/consumables/${id}`), api.get(`/ast/consumables/${id}/transactions`), api.get("/orders", { item_id: id })]);
    state.tab = "consumables"; renderTabs(); renderView(); setQuery({ consumable: item.id });
    const order = orders.find((o) => activeOrders.has(o.status));
    $("#record").innerHTML = html`${detail(item.name, [["Asset tag", item.asset_tag], ["Status", badge(item.status)], ["Category", category(item.category_id)], ["Location", locationName(item.location_id)], ["On hand", `${item.quantity_on_hand} ${item.unit}`], ["Reorder at", item.reorder_threshold], ["Stock", badge(item.quantity_on_hand <= item.reorder_threshold ? "At or below threshold" : "OK", item.quantity_on_hand <= item.reorder_threshold ? "bad" : "good")]])}<div class="fields">${raw(order ? html`<p class="form-help">${order.requested_by === null ? "System order" : "Open order"}: <a href="orders.html?id=${order.id}">#${order.id} · ${label(order.status)}</a></p>` : html`<p class="muted">No open order. <a href="orders.html">Manage orders</a></p>`)}<div class="toolbar">${raw(item.status !== "Retired" ? html`<button class="btn btn-brand" data-stock="in" data-stock-id="${item.id}">Stock in</button><button class="btn" data-stock="out" data-stock-id="${item.id}">Stock out</button>` : html``)}<button class="btn" data-close-record>Close detail</button></div></div><div class="card-h"><h3 class="card-t">Stock history</h3></div>${table(["When", "Type", "Quantity", "Recipient", "Performed by", "Note"], movements.map((m) => html`<tr><td>${fmtDateTime(m.timestamp)}</td><td>${m.type}</td><td>${m.quantity}</td><td>${m.issued_to || "—"}</td><td>${byId(state.people, m.performed_by)?.full_name ?? `User #${m.performed_by}`}</td><td style="white-space:normal">${m.note || "—"}</td></tr>`), "No stock movements yet.")}`;
    $("#record").hidden = false;
  } catch (error) { toast(error.message, "bad"); }
}
function itemForm(item = null) {
  if (!locationOptions().length || !categoryOptions(false).length) { chooseTab("lookups"); toast("Create an equipment category and a location first.", "info"); return; }
  openEditor(item ? "Save equipment" : "Register equipment", raw(html`${field("Asset tag", "asset_tag", "text", item?.asset_tag, true)}${field("Serial number", "serial_number", "text", item?.serial_number, true)}${field("Model", "model", "text", item?.model, true)}${field("Manufacturer", "manufacturer", "text", item?.manufacturer, true)}${select("Category", "category_id", categoryOptions(false), item?.category_id ?? categoryOptions(false)[0][0])}${select("Location", "location_id", locationOptions(), item?.location_id ?? locationOptions()[0][0])}${field("Purchase date", "purchase_date", "date", item?.purchase_date)}${field("Warranty ends", "warranty_end_date", "date", item?.warranty_end_date)}${notes(item?.notes)}`), async (data, form) => {
    if (item) {
      data.purchase_date = form.elements.purchase_date.value || null;
      data.warranty_end_date = form.elements.warranty_end_date.value || null;
      data.notes = form.elements.notes.value.trim();
    }
    const saved = item ? await api.patch(`/ast/items/${item.id}`, data) : await api.post("/ast/items", data);
    await afterSave(item ? "Equipment updated." : "Equipment registered."); await openItem(saved.id);
  });
}
function lendForm(itemId, focus = true) {
  if (!state.borrowers.length) { chooseTab("borrowers"); toast("Create a borrower first.", "info"); return; }
  if (!itemOptions().length) { toast("Register equipment first.", "info"); return; }
  const available = state.items.find((i) => i.status === "Available" && !byId(state.supplies, i.id));
  const chosen = itemId || available?.id || itemOptions()[0][0];
  openEditor("Lend item", raw(html`${select("Equipment", "item_id", itemOptions(), chosen)}${select("Borrower", "borrower_id", borrowerOptions(), state.borrowers[0].id)}<p class="form-help" id="borrower-policy"></p>${conditionPicker("condition_out", "Condition out")}<div style="display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px">${field("Checkout", "checkout_date", "date", today(), true)}${field("Due date", "due_date", "date", "", true)}</div>${notes()}`), async (data) => {
    const loan = await api.post("/ast/loans", data); await afterSave("Item lent."); openLoan(loan.id);
  }, (form) => {
    const update = () => {
      const b = byId(state.borrowers, form.elements.borrower_id.value);
      const days = b.type === "STUDENT" ? 7 : 30;
      const open = state.loans.filter((l) => l.borrower_id === b.id && !l.return_date).length;
      const overdue = state.overdue.some(({loan}) => loan.borrower_id === b.id);
      $("#borrower-policy").textContent = `${b.type === "STUDENT" ? "Students: up to 2 items, 7 days." : "Faculty/staff: up to 30 days."} ${b.full_name} has ${open} open loan(s).${overdue ? " This borrower has an overdue item and cannot borrow until it is returned." : ""} Installed classroom equipment cannot be lent.`;
      form.elements.due_date.value = addDays(form.elements.checkout_date.value || today(), days);
      form.elements.due_date.min = addDays(form.elements.checkout_date.value || today(), 1);
      form.elements.due_date.max = addDays(form.elements.checkout_date.value || today(), days);
    };
    form.elements.borrower_id.onchange = update; form.elements.checkout_date.onchange = update; update();
  }, focus);
  $("#editor .card-t").textContent = "Lend an item";
  if (!focus) $("#close-editor").remove();
}
function conditionPicker(name, title) {
  return raw(html`<div><span class="lbl">${title}</span><input type="hidden" name="${name}" value="Good"><div class="seg" role="group" aria-label="${title}">${raw(conditions.map(([v]) => html`<button type="button" class="${v === "Good" ? "on" : ""}" aria-pressed="${v === "Good"}" data-condition="${v}" data-condition-field="${name}">${v}</button>`).join(""))}</div></div>`);
}
function stockForm(kind) {
  const supplies = state.supplies.filter((c) => c.status !== "Retired");
  if (!supplies.length) { toast("Create an active consumable first.", "info"); return; }
  openEditor(kind === "in" ? "Stock in" : "Stock out", raw(html`${select("Consumable", "item_id", supplies.map((c) => [c.id, `${c.name} · ${c.quantity_on_hand} ${c.unit} on hand`]), supplies[0].id)}${field("Quantity", "quantity", "number", "", true, {min:1})}${raw(kind === "out" ? html`${field("Issued to", "issued_to", "text", "", true)}` : html``)}${notes("", "note", "Note")}`), async ({item_id, ...body}) => { await api.post(`/ast/consumables/${item_id}/stock-${kind}`, body); await afterSave("Stock movement saved."); await openConsumable(item_id); });
}
function create(kind) {
  if (kind === "item") return itemForm();
  if (kind === "stock-in" || kind === "stock-out") return stockForm(kind === "stock-in" ? "in" : "out");
  if (kind === "incident") return openEditor("Report incident", raw(html`${select("Equipment", "item_id", itemOptions())}${select("Type", "type", [["Lost","Lost"],["Damaged","Damaged"]], "Damaged")}${notes("", "description", "Description", true)}${field("Incident date", "date", "date", today(), true)}`), async ({item_id, ...data}) => { await api.post(`/ast/items/${item_id}/incidents`, data); await afterSave("Incident recorded."); await openItem(item_id); });
  if (kind === "lend") return lendForm();
  if (kind === "consumable") {
    if (!categoryOptions(true).length || !locationOptions().length) { chooseTab("lookups"); toast("Create a consumable category and location first.", "info"); return; }
    return openEditor("Create consumable", raw(html`${field("Name", "name", "text", "", true)}${select("Category", "category_id", categoryOptions(true), categoryOptions(true)[0][0])}${select("Location", "location_id", locationOptions(), locationOptions()[0][0])}${field("Reorder threshold", "reorder_threshold", "number", 0, true, { min: 0 })}${field("Unit", "unit", "text", "each", true)}`), async (data) => { const c = await api.post("/ast/consumables", data); await afterSave("Consumable created with zero stock."); await openConsumable(c.id); });
  }
  if (kind === "borrower") return openEditor("Create borrower", raw(html`${field("School ID", "school_id", "text", "", true)}${field("Full name", "full_name", "text", "", true)}${field("Email", "email", "email", "", true)}${select("Borrower type", "type", ["STUDENT", "FACULTY", "STAFF"].map((t) => [t, t]), "STUDENT")}${field("Department", "department")}`), async (data) => { await api.post("/ast/borrowers", data); await afterSave("Borrower created."); chooseTab("borrowers"); });
  if (kind === "category" && isAdmin(user)) return openEditor("Create category", raw(html`${field("Name", "name", "text", "", true)}${checkbox("Track as consumable quantity", "is_consumable")}`), async (data) => { await api.post("/ast/categories", data); await afterSave("Category created."); chooseTab("lookups"); });
  if (kind === "location") return openEditor("Create location", raw(html`${field("Building", "building", "text", "", true)}${field("Room", "room", "text", "", true)}${notes("", "description", "Description")}`), async (data) => { await api.post("/ast/locations", data); await afterSave("Location created."); chooseTab("lookups"); });
}
async function handle(event) {
  const button = event.target.closest("button, a"); if (!button) return;
  const d = button.dataset;
  if (d.tab) { event.preventDefault(); return chooseTab(d.tab); }
  if (d.condition) { const input = $("#inventory-form").elements[d.conditionField]; input.value = d.condition; button.closest(".seg").querySelectorAll("button").forEach((b) => { b.classList.toggle("on", b === button); b.setAttribute("aria-pressed", String(b === button)); }); return; }
  if (d.page) { equipmentPage += d.page === "next" ? 1 : -1; equipmentRows(equipmentMatches, false); return; }
  if (d.clearEquipment !== undefined) { $("#equipment-filters").reset(); ++searchRequest; equipmentRows(state.items); return; }
  if (d.page) { equipmentPage += d.page === "next" ? 1 : -1; equipmentRows(equipmentMatches, false); return; }
  if (d.clearEquipment !== undefined) { $("#equipment-filters").reset(); equipmentRows(state.items); return; }
  if (d.condition) { const form = $("#inventory-form"); form.elements[d.conditionField].value = d.condition; button.closest(".seg").querySelectorAll("button").forEach((b) => { b.classList.toggle("on", b === button); b.setAttribute("aria-pressed", String(b === button)); }); return; }
  if (d.create) return create(d.create);
  if (d.item) { event.preventDefault(); return openItem(Number(d.item)); }
  if (d.consumable) { event.preventDefault(); return openConsumable(Number(d.consumable)); }
  if (d.loan) { event.preventDefault(); return openLoan(Number(d.loan)); }
  if (d.closeRecord !== undefined) { $("#record").hidden = true; setQuery({ tab: state.tab }); return; }
  if (d.refresh !== undefined) return action(button, async () => { await load(); renderTabs(); renderView(); });
  if (d.edit) return itemForm(await api.get(`/ast/items/${d.edit}`));
  if (d.lend) return lendForm(Number(d.lend));
  if (d.incident) return openEditor("Report incident", raw(html`${select("Type", "type", [["Lost", "Lost"], ["Damaged", "Damaged"]], "Damaged")}${notes("", "description", "Description", true)}${field("Incident date", "date", "date", today(), true)}`), async (data) => { await api.post(`/ast/items/${d.incident}/incidents`, data); await afterSave("Incident recorded."); await openItem(Number(d.incident)); });
  if (d.retire && isAdmin(user)) return openEditor("Retire item", raw(html`${notes("", "reason", "Retirement reason", true)}${field("Retirement date", "date", "date", today(), true)}<p class="form-help">This makes the item read-only and removes classroom installation. History is kept.</p>`), async (data) => { await api.post(`/ast/items/${d.retire}/retire`, data); await afterSave("Item retired."); await loadInstallations(); await openItem(Number(d.retire)); });
  if (d.stock) {
    const c = await api.get(`/ast/consumables/${d.stockId}`);
    return openEditor(d.stock === "in" ? "Stock in" : "Stock out", raw(html`<p class="form-help">${c.name}: ${c.quantity_on_hand} ${c.unit} on hand; reorder at ${c.reorder_threshold}.</p>${field("Quantity", "quantity", "number", "", true, { min: 1, ...(d.stock === "out" ? { max: c.quantity_on_hand } : {}) })}${raw(d.stock === "out" ? html`${field("Issued to", "issued_to", "text", "", true)}` : html``)}${notes("", "note", "Note")}`), async (data) => { await api.post(`/ast/consumables/${c.id}/stock-${d.stock}`, data); await afterSave("Stock movement saved."); await openConsumable(c.id); });
  }
  if (d.return) {
    const loan = byId(state.loans, d.return);
    return openEditor("Return item", raw(html`${field("Return date", "return_date", "date", today(), true, { min: loan.checkout_date })}${select("Condition in", "condition_in", conditions, "Good")}${notes()}`), async (data) => { await api.post(`/ast/items/${loan.item_id}/return`, data); await afterSave("Item returned."); openLoan(loan.id); });
  }
  if (d.extend) {
    const loan = byId(state.loans, d.extend);
    return openEditor("Extend loan", raw(html`${field("New due date", "due_date", "date", addDays(loan.due_date, 7), true, { min: addDays(loan.due_date, 1), max: addDays(loan.due_date, 7) })}<p class="form-help">One extension only, up to 7 days beyond ${fmtDate(loan.due_date)}.</p>`), async (data) => { await api.post(`/ast/loans/${loan.id}/extend`, data); await afterSave("Loan extended."); openLoan(loan.id); });
  }
  if (d.borrowerHistory) {
    const id = Number(d.borrowerHistory);
    const loans = await api.get("/ast/loans", { borrower_id: id });
    $("#record").innerHTML = html`<div class="card-h"><h2 class="card-t">${borrowerName(id)} · history</h2><button class="btn" data-close-record>Close detail</button></div>${loanRows(loans)}`;
    $("#record").hidden = false;
  }
}
$("main").addEventListener("click", (event) => { handle(event).catch((error) => toast(error.message, "bad")); });
$("#header-search").addEventListener("keydown", (event) => {
  if (event.key === "Enter") { chooseTab("equipment"); $("#equipment-filters").elements.q.value = event.target.value; $("#equipment-filters").requestSubmit(); }
});
try {
  await Promise.all([load(), loadInstallations()]);
  renderTabs(); renderView();
  if (params.get("loan")) { chooseTab("loans", false); openLoan(Number(params.get("loan"))); }
  else if (params.get("consumable")) await openConsumable(Number(params.get("consumable")));
  else if (params.get("id")) await openItem(Number(params.get("id")));
  else if (state.tab === "equipment") defaultLendingSidebar();
} catch (error) { $("#list-card").innerHTML = html`<p class="empty">${error.message}</p><button class="btn" data-refresh>Retry loading inventory</button>`; toast(error.message, "bad"); }
