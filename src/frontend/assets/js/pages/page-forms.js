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
  const items = directory.map((person) => ({ value: person.id, text: person.full_name }));
  if (!multiple) return select(title, name, items, selected, "Choose a person", false, required);
  const chosen = new Set(selected.map(Number));
  return raw(html`<div class="people-picker" data-people-picker data-required="${required}"><span class="lbl">${title}</span><div class="chip-box"><div data-people-chips>${fragment(items.filter((item) => chosen.has(item.value)).map((item) => html`<span class="b b-neutral person-chip">${item.text}<button type="button" data-remove-person="${item.value}" aria-label="Remove ${item.text}">×</button></span>`))}</div><select class="input" data-add-person aria-label="Add ${title.toLowerCase()}"${attr(required && !chosen.size, "required")}>${options(items.filter((item) => !chosen.has(item.value)), null, "Add person")}</select></div><select name="${name}" multiple hidden data-people-value>${options(items, selected, null)}</select></div>`);
}

export function ids(form, name) {
  return [...form.elements.namedItem(name).selectedOptions].map((option) => Number(option.value)).filter(Boolean);
}
export const read = (form) => {
  const data = formData(form);
  form.querySelectorAll('input[type="radio"]:checked').forEach((control) => { data[control.name] = control.value; });
  return data;
};
export const rows = (records, render, message) => records.length ? fragment(records.map(render)) : raw(empty(message));
export const personName = (directory, id) => directory.find((person) => person.id === id)?.full_name ?? (id == null ? "System" : `User #${id}`);

/** Delegation survives view renders; errors stay with the form that caused them. */
export function forms(root, handlers) {
  root.addEventListener("change", (event) => {
    const picker = event.target.closest("[data-people-picker]");
    if (!picker) return;
    const backing = picker.querySelector("[data-people-value]");
    if (event.target.matches("[data-add-person]") && event.target.value) {
      [...backing.options].find((option) => option.value === event.target.value).selected = true;
    }
    renderPeoplePicker(picker);
  });
  root.addEventListener("click", (event) => {
    const button = event.target.closest("[data-remove-person]");
    if (!button) return;
    const picker = button.closest("[data-people-picker]");
    [...picker.querySelector("[data-people-value]").options].find((option) => option.value === button.dataset.removePerson).selected = false;
    renderPeoplePicker(picker);
  });
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

function renderPeoplePicker(picker) {
  const backing = picker.querySelector("[data-people-value]");
  const add = picker.querySelector("[data-add-person]");
  const selected = [...backing.selectedOptions];
  picker.querySelector("[data-people-chips]").innerHTML = fragment(selected.map((option) => html`<span class="b b-neutral person-chip">${option.textContent}<button type="button" data-remove-person="${option.value}" aria-label="Remove ${option.textContent}">×</button></span>`));
  add.innerHTML = options([...backing.options].filter((option) => !option.selected).map((option) => ({ value: option.value, text: option.textContent })), null, "Add person");
  add.required = picker.dataset.required === "true" && !selected.length;
}

/** Initials and colours match Tom's overlapping member avatars. */
export function avatars(directory, userIds) {
  return raw(html`<div class="avatar-stack" aria-label="Members">${fragment(userIds.map((id) => {
    const name = personName(directory, id);
    const initials = name.split(/\s+/).filter(Boolean).slice(0, 2).map((part) => part[0]).join("").toUpperCase();
    return html`<span class="av av-tone-${id % 3}" title="${name}" aria-label="${name}">${initials}</span>`;
  }))}</div>`);
}

/** Compact labels remain accessible to assistive technology. */
export function compactFilters(root) {
  root.querySelectorAll(".filter-bar label > .lbl").forEach((label) => {
    label.classList.replace("lbl", "sr");
    const input = label.parentElement.querySelector("input");
    if (input && input.type !== "checkbox") input.placeholder = label.textContent;
  });
}

/** Header tiles reuse the original mockup's SVGs. */
export function pageIcon(kind) {
  const drawings = {
    projects: html`<rect x="3" y="4" width="18" height="16" rx="2"></rect><path d="M8 9h8M8 13h5"></path>`,
    reports: html`<path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"></path><path d="M14 3v6h6M8 13h8M8 17h5"></path>`,
    admin: html`<circle cx="9" cy="8" r="4"></circle><path d="M2 21a7 7 0 0 1 14 0M17 11a3 3 0 1 0 0-6M22 21a6 6 0 0 0-4-5.6"></path>`,
  };
  return raw(html`<span class="tile heading-tile ${kind === "admin" ? "tile-blue" : "tile-purple"}"><svg aria-hidden="true" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${raw(drawings[kind])}</svg></span>`);
}

export function plusIcon() {
  return raw(html`<svg aria-hidden="true" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M12 5v14M5 12h14"></path></svg>`);
}
