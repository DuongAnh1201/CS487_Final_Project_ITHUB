// Orders: US-ORD-01–04. Stock changes are owned by the API, including partial receipts.
import { api, badge, fmtDate, fmtDateTime, html, raw, startPage, toast, label } from "../app.js";
import { $, action, bindForm, detail, field, payload, select, setQuery, table, today, addDays } from "./forms.js";

const user = await startPage();
const statuses = ["REQUESTED", "ORDERED", "PARTIALLY_ARRIVED", "ARRIVED", "CANCELLED"];
let selected = null;
let people = [];
let supplies = [];
let listRequest = 0;
const person = (id) => id === null ? "System" : people.find((p) => p.id === id)?.full_name ?? `User #${id}`;

function orderQuery() {
  const { period, ...query } = payload($("#order-filters"));
  if (period && period !== "custom") {
    query.date_from = addDays(today(), -Number(period));
    query.date_to = today();
  } else if (period !== "custom") { delete query.date_from; delete query.date_to; }
  return query;
}
async function loadList() {
  const request = ++listRequest;
  try {
    const [orders, summary] = await Promise.all([api.get("/orders", orderQuery()), api.get("/orders/summary")]);
    if (request !== listRequest) return;
    $("#order-summary").innerHTML = html`<a class="stat" href="orders.html" data-status="" style="border-right:1px solid #EDF0F4"><span class="muted">Total</span><strong style="font-size:24px;font-weight:800">${summary.total}</strong></a>${raw(statuses.map((status) => html`<a class="stat" href="orders.html?status=${status}" data-status="${status}" style="border-right:1px solid #EDF0F4"><span class="muted">${label(status)}</span><strong style="font-size:24px;font-weight:800;color:${({REQUESTED:"#7A4A00",ORDERED:"#1C4E7A",PARTIALLY_ARRIVED:"#1C4E7A",ARRIVED:"#1F5A3B",CANCELLED:"#4A3577"})[status]}">${summary.by_status[status] ?? 0}</strong></a>`).join(""))}`;
    $("#order-count").textContent = `${orders.length} orders`;
    $("#order-list").innerHTML = html`${table(["Order", "Item", "Qty", "Received", "Vendor", "Requested by", "Requested", "Status"], orders.map((o) => html`<tr class="${o.id === selected ? "selected-record" : ""}"><td><a href="orders.html?id=${o.id}" data-order="${o.id}">#${o.id}</a></td><td>${o.item_name}</td><td>${o.quantity_ordered}</td><td>${o.quantity_received}</td><td>${o.vendor || "—"}</td><td>${o.requested_by === null ? badge("System", "final") : person(o.requested_by)}</td><td>${fmtDate(o.requested_at)}</td><td>${badge(o.status)}</td></tr>`), "No orders match these filters.")}`;
  } catch (error) {
    if (request !== listRequest) return;
    $("#order-list").innerHTML = html`<p class="empty">${error.message}</p>`;
    toast(error.message, "bad");
  }
}

async function openOrder(id) {
  try {
    const [o, history] = await Promise.all([
      api.get(`/orders/${id}`),
      api.get("/audit", {entity_type:"Order", entity_id:id}).catch((error) => { toast(error.message, "bad"); return null; }),
    ]);
    selected = o.id;
    setQuery({ id: o.id });
    $("#editor").hidden = true;
    const canReceive = ["ORDERED", "PARTIALLY_ARRIVED"].includes(o.status);
    const states = ["REQUESTED", "ORDERED", "PARTIALLY_ARRIVED", "ARRIVED"];
    const current = states.indexOf(o.status);
    $("#order-detail").innerHTML = html`<div class="card-h"><div><h2 class="card-t">Order #${o.id} · ${o.item_name}</h2><p class="muted" style="margin:4px 0 0;font-size:13px">${o.requested_by === null ? "Created automatically from low stock" : `Requested by ${person(o.requested_by)}`} · Vendor ${o.vendor || "—"}</p></div></div><div class="fields">${raw(o.status === "CANCELLED" ? html`${badge(o.status)}` : html``)}<div class="path" role="list" aria-label="Order status">${raw(states.map((status,index) => html`<div class="step ${index < current ? "done" : index === current ? "cur" : "next"}" role="listitem" ${raw(index === current ? html`aria-current="step"` : html``)}>${label(status)}</div>`).join(""))}</div><div style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;text-align:center">${raw([[o.quantity_ordered,"Ordered","#F4F3EF","#181818"],[o.quantity_received,"Received","#DDF2E6","#1F5A3B"],[o.remaining_quantity,"Remaining","#FCEBCF","#7A4A00"]].map(([qty,name,background,color])=>html`<div style="padding:12px;border-radius:8px;background:${background};color:${color}"><div style="font-size:22px;font-weight:800">${qty}</div><div style="font-size:12px;font-weight:600">${name}</div></div>`).join(""))}</div>${raw(canReceive ? html`<form id="receive-order" style="display:flex;gap:10px;align-items:flex-end;flex-wrap:wrap"><div style="flex:1 1 140px">${field("Quantity received", "quantity", "number", "", true, {min:1,max:o.remaining_quantity})}</div><button type="submit" class="btn btn-brand" style="min-height:38px">Receive</button></form>` : html``)}<p class="muted" style="margin:0;font-size:12px">Stock goes up automatically. Cancel is only possible while Requested or Ordered.</p><div class="toolbar">${raw(o.status === "REQUESTED" ? html`<button class="btn btn-brand" data-order-action="place">Place order</button>` : html``)}${raw(["REQUESTED","ORDERED"].includes(o.status) ? html`<button class="btn" data-order-action="cancel">Cancel order</button>` : html``)}<button class="btn" id="close-order" style="min-height:28px">Close detail</button></div><a href="inventory.html?consumable=${o.item_id}" style="font-size:12px">View stock and movement history</a><div style="border-top:1px solid #EDF0F4;padding-top:12px;display:flex;flex-direction:column;gap:8px;font-size:13px"><strong>Status history</strong>${raw(history === null ? html`<p class="empty">History unavailable.</p>` : history.length ? history.map((entry)=>html`<div style="display:flex;justify-content:space-between;gap:8px"><span>${label(entry.action)}</span><span class="muted">${fmtDateTime(entry.timestamp)} · ${entry.actor_id === null ? "System" : person(entry.actor_id)}</span></div>`).join("") : html`<p class="empty">No status changes recorded.</p>`)}</div></div>`;
    $("#order-detail").hidden = false;
    $("#close-order").onclick = () => { selected = null; $("#order-detail").hidden = true; setQuery({}); };
    $("#order-detail").querySelectorAll("[data-order-action]").forEach((button) => button.onclick = () => action(button, async () => {
      const verb = button.dataset.orderAction;
      if (verb === "cancel" && !confirm(`Cancel order #${o.id}?`)) return;
      await api.post(`/orders/${o.id}/${verb}`);
      toast(verb === "cancel" ? "Order cancelled." : "Order placed.");
      await Promise.all([openOrder(o.id), loadList()]);
    }));
    if (canReceive) bindForm($("#receive-order"), async (data) => {
      await api.post(`/orders/${o.id}/receive`, data);
      toast("Receipt saved. Stock updated.");
      await Promise.all([openOrder(o.id), loadList()]);
    });
  } catch (error) { toast(error.message, "bad"); }
}

async function newOrder() {
  try {
    supplies = await api.get("/ast/consumables");
    const available = supplies.filter((s) => s.status !== "Retired");
    $("#order-detail").hidden = true;
    $("#editor").innerHTML = html`<div class="card-h"><h2 class="card-t">New order</h2><button class="btn" id="close-editor">Cancel</button></div>${raw(available.length ? html`<form class="fields" id="create-order">${select("Consumable", "item_id", available.map((s) => [s.id, `${s.name} · ${s.quantity_on_hand} ${s.unit} on hand`]))}<div style="display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px">${field("Quantity to order", "quantity", "number", "", true, { min: 1 })}${field("Vendor", "vendor")}</div><p class="muted">Each item can have only one open order.</p><button class="btn btn-brand" type="submit">Create order</button></form>` : html`<p class="empty">Create an active consumable in Inventory before ordering.</p><a class="btn" href="inventory.html?tab=consumables">Go to consumables</a>`)}`;
    $("#editor").hidden = false;
    $("#close-editor").onclick = () => { $("#editor").hidden = true; };
    if (available.length) bindForm($("#create-order"), async (data) => {
      const order = await api.post("/orders", data);
      toast("Order created.");
      await Promise.all([openOrder(order.id), loadList()]);
    });
  } catch (error) { toast(error.message, "bad"); }
}

$("#new-order").onclick = newOrder;
$("#order-filters").onsubmit = (event) => { event.preventDefault(); loadList(); };
let searchDelay;
$("#order-filters").oninput = () => { clearTimeout(searchDelay); searchDelay = setTimeout(loadList,250); };
$("#order-filters").onchange = () => { $("#order-custom-dates").hidden = $("#order-filters").elements.period.value !== "custom"; loadList(); };
$("#clear-orders").onclick = () => { $("#order-filters").reset(); $("#order-custom-dates").hidden = true; loadList(); };
$("#order-summary").onclick = (event) => {
  const button = event.target.closest("[data-status]");
  if (button) { event.preventDefault(); $("#order-filters").elements.status.value = button.dataset.status; loadList(); }
};
$("#order-list").onclick = (event) => {
  const link = event.target.closest("[data-order]");
  if (link) { event.preventDefault(); openOrder(Number(link.dataset.order)); }
};
$("#header-search").addEventListener("keydown", (event) => {
  if (event.key === "Enter") { $("#order-filters").elements.q.value = event.target.value; loadList(); }
});
try { people = await api.get("/users/directory"); } catch (error) { toast(error.message, "bad"); }
await loadList();
const id = new URLSearchParams(location.search).get("id");
if (id) await openOrder(Number(id));
else {
  const first = $("#order-list [data-order]");
  if (first) await openOrder(Number(first.dataset.order));
  else await newOrder();
}
