// Small presentation helpers shared by the three #81 pages. All markup passes through html``.
import { html, raw, formData, showFormError, toast } from "../app.js";

export const $ = (selector) => document.querySelector(selector);
export const today = () => `${new Date().getFullYear()}-${String(new Date().getMonth() + 1).padStart(2, "0")}-${String(new Date().getDate()).padStart(2, "0")}`;
export const addDays = (value, days) => {
  const date = new Date(`${value}T12:00:00`);
  date.setDate(date.getDate() + days);
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
};
let fieldSequence = 0;
export function field(title, name, type = "text", value = "", required = false, extra = {}) {
  const id = `field-${name}-${++fieldSequence}`;
  return raw(html`<div><label class="lbl" for="${id}">${title}${required ? " *" : ""}</label><input class="input" id="${id}" name="${name}" type="${type}" value="${value ?? ""}" ${raw(required ? html`required` : html``)} ${raw(extra.min === undefined ? html`` : html`min="${extra.min}"`)} ${raw(extra.max === undefined ? html`` : html`max="${extra.max}"`)} ${raw(type === "number" ? html`step="1"` : html``)}></div>`);
}
export function select(title, name, options, value = "", required = true, multiple = false) {
  const id = `field-${name}-${++fieldSequence}`;
  return raw(html`<div><label class="lbl" for="${id}">${title}${required ? " *" : ""}</label><select class="input" id="${id}" name="${name}" ${raw(required ? html`required` : html``)} ${raw(multiple ? html`multiple size="5"` : html``)}>${raw(options.map(([id, text]) => html`<option value="${id}" ${raw((Array.isArray(value) ? value.map(String).includes(String(id)) : String(id) === String(value)) ? html`selected` : html``)}>${text}</option>`).join(""))}</select></div>`);
}
export function notes(value = "", name = "notes", title = "Notes", required = false) {
  const id = `field-${name}-${++fieldSequence}`;
  return raw(html`<div><label class="lbl" for="${id}">${title}${required ? " *" : ""}</label><textarea class="input" id="${id}" name="${name}" rows="3" ${raw(required ? html`required` : html``)}>${value ?? ""}</textarea></div>`);
}
export function checkbox(title, name, checked = false) {
  return raw(html`<label><input type="checkbox" name="${name}" ${raw(checked ? html`checked` : html``)}> ${title}</label>`);
}
export function payload(form) {
  const data = formData(form);
  for (const [name, value] of Object.entries(data)) {
    if (value === null) delete data[name];
    else if (["item_id", "borrower_id", "category_id", "location_id", "recipient_id"].includes(name)) data[name] = Number(value);
    else if (name.endsWith("_ids")) data[name] = value.map(Number);
  }
  return data;
}
export function bindForm(form, save) {
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const button = form.querySelector('[type="submit"]');
    form.querySelectorAll(".field-error").forEach((node) => node.remove());
    button.disabled = true;
    try { await save(payload(form), form); }
    catch (error) { showFormError(form, error); }
    finally { button.disabled = false; }
  });
}
export function table(headers, rows, emptyText) {
  return raw(rows.length ? html`<div style="overflow-x:auto"><table><thead><tr>${raw(headers.map((h) => html`<th scope="col">${h}</th>`).join(""))}</tr></thead><tbody>${raw(rows.join(""))}</tbody></table></div>` : html`<p class="empty">${emptyText}</p>`);
}
export function detail(title, entries) {
  return raw(html`<div class="card-h"><h2 class="card-t">${title}</h2></div><dl class="detail-grid">${raw(entries.map(([key, value]) => html`<div><dt class="muted">${key}</dt><dd>${value ?? "—"}</dd></div>`).join(""))}</dl>`);
}
export async function action(button, operation) {
  button.disabled = true;
  try { await operation(); } catch (error) { toast(error.message, "bad"); }
  finally { button.disabled = false; }
}
export function setQuery(values) {
  const url = new URL(location.href);
  url.search = "";
  for (const [key, value] of Object.entries(values)) if (value !== null && value !== undefined) url.searchParams.set(key, value);
  history.replaceState(null, "", url);
}
