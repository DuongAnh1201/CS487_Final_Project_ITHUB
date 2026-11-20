// Home / dashboard: one widget per area, each loaded independently so one failure does not blank the page.
import { api, badge, fmtDate, html, label, raw, startPage, timeAgo, toast } from "../app.js";

const ROWS_PER_WIDGET = 5;
const OPEN_ISSUE_STATUSES = new Set(["OPEN", "ASSIGNED", "IN_PROGRESS"]);
const OPEN_ORDER_STATUSES = new Set(["REQUESTED", "ORDERED", "PARTIALLY_ARRIVED"]);

/** Where a notification's related record lives. */
export function linkFor(relatedType, relatedId) {
  const page = {
    Order: "orders.html", Report: "reports.html", Issue: "issues.html", Project: "projects.html",
    Task: "projects.html", Asset: "inventory.html", Item: "inventory.html", Classroom: "classrooms.html",
  }[relatedType] ?? "notifications.html";
  const parameter = relatedType === "Task" ? "task" : "id";
  return relatedId ? `${page}?${parameter}=${relatedId}` : page;
}

/** Replace a widget's sample rows and count. `total` defaults to the number of rows. */
function fill(name, rows, emptyText, total = rows.length) {
  const section = document.querySelector(`[data-widget="${name}"]`);
  section.querySelectorAll(".li, .empty").forEach((el) => el.remove());
  const footer = section.querySelector(".bf");
  const markup = rows.length ? rows.slice(0, ROWS_PER_WIDGET).join("") : html`<p class="empty">${emptyText}</p>`;
  footer.insertAdjacentHTML("beforebegin", markup);
  const count = section.querySelector(".cnt");
  const suffix = count.querySelector(".muted");
  count.textContent = String(total);
  if (suffix) count.append(suffix);
  return section;
}

function fail(name, error) {
  fill(name, [], `Could not load: ${error.message}`, 0);
}

const sub = (text) => raw(html`<div class="muted" style="font-size:12px">${text}</div>`);

// ---- widgets ------------------------------------------------------------------------------------

async function tasks(user) {
  const today = new Date().toISOString().slice(0, 10);
  const [all, projects] = await Promise.all([api.get("/tasks", { assignee_id: user.id }), api.get("/projects")]);
  const names = Object.fromEntries(projects.map((p) => [p.id, p.name]));
  const open = all.filter((t) => t.status !== "COMPLETE")
    .sort((a, b) => (a.due_date ?? "9999").localeCompare(b.due_date ?? "9999"));
  const section = fill("tasks", open.map((t) => {
    const due = !t.due_date ? "No due date"
      : t.due_date < today ? raw(html`<span style="color:#8A1C2B;font-weight:600">Overdue · ${fmtDate(t.due_date)}</span>`)
        : t.due_date === today ? raw(html`<span style="color:#8A1C2B;font-weight:600">Due today</span>`)
          : fmtDate(t.due_date);
    return html`<div class="li"><input type="checkbox" data-task="${t.id}" aria-label="Mark ${t.title} complete" style="width:18px;height:18px;flex:none"><div style="flex:1;min-width:0"><div style="font-weight:600">${t.title}</div><div class="muted" style="font-size:12px">${names[t.project_id] ?? "Standalone"} · ${due}</div></div>${badge(t.priority)}</div>`;
  }), "No open tasks. Nice work!");
  section.querySelectorAll("[data-task]").forEach((box) => box.addEventListener("change", async () => {
    box.disabled = true;
    try {
      await api.put(`/tasks/${box.dataset.task}/status`, { status: "COMPLETE" });
      toast("Task completed.");
      tasks(user);
    } catch (error) {
      box.checked = false;
      box.disabled = false;
      toast(error.message, "bad");
    }
  }));
}

async function notifications() {
  const unread = await api.get("/notifications", { unread_only: true });
  fill("notifications", unread.map((n) => html`<a class="li" href="${linkFor(n.related_type, n.related_id)}"><span style="width:8px;height:8px;border-radius:50%;background:#1F6B7A;flex:none"></span><div style="flex:1;min-width:0"><div>${n.message}</div>${sub(timeAgo(n.created_at))}</div></a>`),
  "You're all caught up.");
}

async function overdue() {
  const loans = await api.get("/ast/overdue");
  loans.sort((a, b) => b.days_overdue - a.days_overdue);
  fill("overdue", loans.map(({ loan, borrower, item, days_overdue: days }) => html`<a class="li" href="inventory.html?loan=${loan.id}"><div style="flex:1;min-width:0"><div style="font-weight:600">${borrower.full_name}</div>${sub(`${item.asset_tag} · ${item.model} · due ${fmtDate(loan.due_date)}`)}</div>${badge(`${days} day${days === 1 ? "" : "s"}`, days > 1 ? "bad" : "warn")}</a>`),
  "No overdue loans.");
}

async function issues(rooms) {
  const page = await api.get("/issues", { page_size: 50 });
  const open = page.items.filter((i) => OPEN_ISSUE_STATUSES.has(i.status));
  const rank = { CRITICAL: 0, HIGH: 1, MEDIUM: 2, LOW: 3 };
  open.sort((a, b) => rank[a.severity] - rank[b.severity] || b.created_at.localeCompare(a.created_at));
  fill("issues", open.map((i) => {
    const room = rooms[i.classroom_id] ?? `Room ${i.classroom_id}`;
    const where = i.room_equipment_id ? "one item" : "whole room";
    return html`<a class="li" href="issues.html?id=${i.id}"><div style="flex:1;min-width:0"><div style="font-weight:600">${i.issue_id} · ${label(i.category)}</div>${sub(`${room} · ${where} · ${i.reporter_name} · ${timeAgo(i.created_at)}`)}</div>${badge(i.severity)}</a>`;
  }), "No open issues.");
}

async function lowStock() {
  const [items, orders] = await Promise.all([api.get("/ast/consumables"), api.get("/orders")]);
  const openOrder = Object.fromEntries(orders.filter((o) => OPEN_ORDER_STATUSES.has(o.status)).map((o) => [o.item_id, o]));
  const low = items.filter((c) => c.quantity_on_hand < c.reorder_threshold);
  fill("low-stock", low.map((c) => {
    const ratio = c.reorder_threshold ? Math.min(100, Math.round((100 * c.quantity_on_hand) / c.reorder_threshold)) : 0;
    const colour = ratio < 50 ? ["#8A1C2B", "#E07A86"] : ["#7A4A00", "#EBA54E"];
    const order = openOrder[c.id];
    const note = order ? `Order #${order.id} ${order.requested_by ? "requested" : "created automatically"} · ${label(order.status)}` : "No open order";
    return html`<a class="li" href="inventory.html?consumable=${c.id}" style="flex-direction:column;align-items:stretch;gap:6px"><div style="display:flex;justify-content:space-between"><strong>${c.name}</strong><span style="font-size:13px"><strong style="color:${colour[0]}">${c.quantity_on_hand}</strong> <span class="muted">/ ${c.reorder_threshold} ${c.unit}</span></span></div><div class="mini"><span style="width:${ratio}%;background:${colour[1]}"></span></div><span class="muted" style="font-size:12px">${note}</span></a>`;
  }), "Every consumable is above its reorder threshold.");
}

async function roomsWidget(rooms) {
  const notAvailable = rooms.filter((r) => r.status !== "AVAILABLE");
  const section = fill("rooms", notAvailable.map((r) => {
    const why = r.closed_reason || (r.check_overdue ? "Room check overdue" : `${label(r.status)}: some desktops need attention`);
    return html`<a class="li" href="classrooms.html?id=${r.id}"><div style="flex:1;min-width:0"><div style="font-weight:600">${r.building}-${r.room} · ${label(r.room_type)}</div>${sub(why)}</div>${badge(r.status)}</a>`;
  }), "Every room is available.");
  const suffix = section.querySelector(".cnt .muted");
  if (suffix) suffix.textContent = ` / ${rooms.length}`;
}

// ---- page ---------------------------------------------------------------------------------------

function greet(user) {
  const hour = new Date().getHours();
  const part = hour < 12 ? "morning" : hour < 18 ? "afternoon" : "evening";
  document.getElementById("greeting").textContent = `Good ${part}, ${user.full_name.split(" ")[0]}`;
  const shift = hour < 12 ? "Morning shift" : hour < 17 ? "Afternoon shift" : "Evening shift";
  document.getElementById("today").textContent =
    `${new Date().toLocaleDateString(undefined, { weekday: "long", month: "long", day: "numeric" })} · ${shift}`;
}

const user = await startPage();
greet(user);

const run = (name, task) => task.catch((error) => fail(name, error));
run("tasks", tasks(user));
run("notifications", notifications());
run("overdue", overdue());
run("low-stock", lowStock());
const roomsPromise = api.get("/classrooms");
run("rooms", roomsPromise.then(roomsWidget));
run("issues", roomsPromise
  .catch(() => [])
  .then((rooms) => issues(Object.fromEntries(rooms.map((r) => [r.id, `${r.building}-${r.room}`])))));
