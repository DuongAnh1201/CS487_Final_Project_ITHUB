// Small rendering helpers shared only by the Projects, Reports and Account workflows (#82).
import { html, raw, formData, showFormError, toast, label } from "../app.js";

export const fragment = (rows) => raw(rows.join(""));
export const attr = (condition, name) => raw(condition ? ` ${name}` : "");
export const empty = (text) => html`<p class="empty">${text}</p>`;
export const today = () => {
  const date = new Date();
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
};
export const values = (names) => names.map((value) => ({ value, text: label(value) }));

/** All options come through html's escaping, including record names. */
export function options(items, selected = null, blank = "Choose…") {
  const chosen = new Set((Array.isArray(selected) ? selected : [selected]).map(String));
  return fragment([
    ...(blank === null ? [] : [html`<option value="">${blank}</option>`]),
    ...items.map(({ value, text }) => html`<option value="${value}"${attr(chosen.has(String(value)), "selected")}>${text}</option>`),
  ]);
}
export function input(title, name, value = "", type = "text", required = false) {
  return raw(html`<label><span class="lbl">${title}</span><input class="input" name="${name}" value="${value ?? ""}" type="${type}"${attr(required, "required")}></label>`);
}
export function textarea(title, name, value = "", required = false) {
  return raw(html`<label><span class="lbl">${title}</span><textarea class="input" name="${name}" rows="3"${attr(required, "required")}>${value ?? ""}</textarea></label>`);
}
export function select(title, name, items, value = null, blank = "Choose…", multiple = false, required = false) {
  return raw(html`<label><span class="lbl">${title}</span><select class="input" name="${name}"${attr(multiple, "multiple")}${attr(required, "required")}>${options(items, value, blank)}</select>${multiple ? raw(html`<span class="muted">Select one or more people (Ctrl/Command to select several).</span>`) : ""}</label>`);
}
export function people(title, name, directory, selected = [], multiple = true, required = false) {
  return select(title, name, directory.map((person) => ({ value: person.id, text: `${person.full_name} · ${label(person.role)}` })),
    selected, multiple ? null : "Choose a person", multiple, required);
}
export function ids(form, name) {
  return [...form.elements.namedItem(name).selectedOptions].map((option) => Number(option.value)).filter(Boolean);
}
export const read = (form) => formData(form);
export const rows = (records, render, message) => records.length ? fragment(records.map(render)) : raw(empty(message));
export const personName = (directory, id) => directory.find((person) => person.id === id)?.full_name ?? (id == null ? "System" : `User #${id}`);

/** Delegation survives view renders; errors stay with the form that caused them. */
export function forms(root, handlers) {
  root.addEventListener("submit", async (event) => {
    const form = event.target.closest("form[data-form]");
    if (!form || !handlers[form.dataset.form]) return;
    event.preventDefault();
    const button = event.submitter;
    if (button) button.disabled = true;
    form.querySelectorAll(".field-error").forEach((element) => element.remove());
    try { await handlers[form.dataset.form](form, button); }
    catch (error) { showFormError(form, error); }
    finally { if (button) button.disabled = false; }
  });
}
export function actions(root, handlers) {
  root.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-action]");
    if (!button || !handlers[button.dataset.action] || button.disabled) return;
    event.preventDefault();
    button.disabled = true;
    try { await handlers[button.dataset.action](button); }
    catch (error) { toast(error.message, "bad"); }
    finally { if (!button.hasAttribute("data-managed-disabled")) button.disabled = false; }
  });
}
export function quickSearch(form) {
  const search = document.querySelector('header input[type="search"]');
  if (!search || !form) return;
  search.placeholder = "Search this page…";
  search.addEventListener("search", () => { form.elements.q.value = search.value; form.requestSubmit(); });
  search.addEventListener("keydown", (event) => {
    if (event.key === "Enter") { event.preventDefault(); form.elements.q.value = search.value; form.requestSubmit(); }
  });
}
