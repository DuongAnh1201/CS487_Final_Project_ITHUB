// Daily reports, review workflow, templates and monthly summaries (US-RPT-01–08).
import { api, badge, fmtDate, fmtDateTime, html, label, raw, startPage, toast } from "../app.js";
import { actions, compactFilters, pageIcon, plusIcon, attr, forms, fragment, ids, input, people, personName, quickSearch, read, rows, select, textarea, values } from "./page-forms.js";

const user = await startPage();
const root = document.getElementById("page-content");
root.inert = true;
root.setAttribute("aria-busy", "true");
const state = { reports: [], projects: [], tasks: [], templates: [], directory: [], report: null, view: "mine", filters: {}, reviewerSelections: {} };
const name = (id) => personName(state.directory, id);
const projectName = (id) => state.projects.find((project) => project.id === id)?.name ?? (id == null ? "No project" : `Project #${id}`);
const projectOptions = () => state.projects.map((project) => ({ value: project.id, text: project.name }));
const taskOptions = () => state.tasks.map((task) => ({ value: task.id, text: task.title }));
const statuses = values(["DRAFT", "SUBMITTED", "REVIEWED", "REJECTED", "PASSED"]);

function shell() {
  root.innerHTML = html`<section class="card"><div class="page-heading">${pageIcon("reports")}<div class="heading-copy"><div class="eyebrow muted">Reports</div><h1>Daily reports &amp; reviews</h1></div><div class="actions"><button class="btn" data-action="new-blank">Blank report</button><button class="btn btn-brand" data-action="new-report">${plusIcon()} New from template</button></div></div><nav class="page-tabs" aria-label="Report sections">${fragment([["mine", "My reports"], ["all", "All reports"], ["projects", "By project"], ["inbox", "Reviewer inbox"], ["templates", "Templates"], ["monthly", "Monthly summary"]].map(([key, title]) => html`<a class="tab" href="?view=${key}" data-action="view" data-view="${key}">${title}</a>`))}</nav></section>
  <section id="template-editor" class="card" hidden></section>
  <div id="report-workspace" class="report-workspace"><section id="report-list" class="card"><form data-form="search" class="report-filters"><div class="filter-bar">${input("Report # or keyword", "q", "", "search")}${select("Status", "status", statuses, null, "Any status")}${select("Type", "report_type", values(["DAILY", "MONTHLY_SUMMARY"]), null, "All types")}${select("Project", "project_id", projectOptions(), null, "Any project")}<button class="btn" type="submit">Search</button></div><details class="more-filters"><summary>More filters</summary><div class="fields">${people("Author", "author_id", state.directory, [], false)}${input("From", "date_from", "", "date")}${input("To", "date_to", "", "date")}</div></details></form><div id="report-results"></div></section><aside id="report-sidebar"><section id="new-report" class="card" hidden></section><section id="report-detail" class="card"><div class="card-h"><h2 class="card-t">Report details</h2></div><p class="empty">Select a report to view or edit it.</p></section></aside></div>
  <div id="report-followup" class="report-workspace" hidden><section id="report-review" class="card"></section><section id="report-history" class="card"></section></div>
  <section id="templates-view" class="card" hidden><div class="card-h"><h2 class="card-t">Report templates</h2><button class="btn" data-action="new-template">New template</button></div><div id="templates" class="pad"></div></section>
  <section id="monthly-view" class="card" hidden><div class="card-h"><h2 class="card-t">Monthly summary</h2></div><div class="pad"><p class="muted">Generate once per month, on or after its last day. Active Admins are the reviewers.</p><form data-form="monthly" class="fields">${input("Month", "month", new Date().getMonth() + 1, "number", true)}${input("Year", "year", new Date().getFullYear(), "number", true)}<button class="btn btn-brand" type="submit">Generate summary</button></form></div></section>`;
  root.querySelector('[name="month"]').min = "1"; root.querySelector('[name="month"]').max = "12";
  root.querySelector('[name="year"]').min = "2000"; root.querySelector('[name="year"]').max = "2100";
  compactFilters(root);
  quickSearch(root.querySelector('[data-form="search"]'));
}

function reportTable(reports) {
  if (!reports.length) return html`<p class="empty">No reports match this view.</p>`;
  return html`<div class="table-scroll"><table><thead><tr><th>Report</th><th>Title</th><th>Shift</th><th>Project</th><th>Reviewers</th><th>Date</th><th>Status</th></tr></thead><tbody>${fragment(reports.map((r) => html`<tr class="${r.id === state.report?.id ? "selected-row" : ""}"><td><a href="?id=${r.id}" data-action="open-report" data-id="${r.id}">RPT-${r.id}</a></td><td title="${personName(state.directory, r.author_id)}">${r.title}</td><td>${label(r.shift) || "—"}</td><td>${projectName(r.project_id)}</td><td>${r.reviewer_ids.map(name).join(", ") || "—"}</td><td>${fmtDate(r.created_at)}</td><td>${badge(r.status)}</td></tr>`))}</tbody></table></div>`;
}

async function renderReports() {
  const result = document.getElementById("report-results");
  let reports = state.reports;
  if (state.view === "mine") reports = reports.filter((report) => report.author_id === user.id);
  if (state.view === "inbox") reports = reports.filter((report) => report.status === "SUBMITTED" && report.reviewer_ids.includes(user.id));
  if (state.view === "projects") {
    const groups = await api.get("/reports/by-project");
    const matches = new Set(reports.map((report) => report.id));
    const visible = groups.map((group) => ({ ...group, reports: group.reports.filter((report) => matches.has(report.id)) })).filter((group) => group.reports.length);
    result.innerHTML = rows(visible, (group) => html`<section><h3>${projectName(group.project_id)}</h3>${raw(reportTable(group.reports))}</section>`, "No reports match your filters.");
  } else result.innerHTML = reportTable(reports);
}
function renderTemplates() {
  document.getElementById("templates").innerHTML = rows(state.templates, (template) => html`<article class="tcard"><div class="spread"><strong>${template.name}</strong><span>${template.checklist_items.length} items</span></div><p>${template.description}</p><ul>${fragment(template.checklist_items.map((item) => html`<li>${item}</li>`))}</ul><div class="actions"><button class="btn" data-action="edit-template" data-id="${template.id}">Edit template</button><button class="btn btn-brand" data-action="use-template" data-id="${template.id}">New report</button></div></article>`, "No report templates yet.");
}
async function refresh() {
  [state.reports, state.templates] = await Promise.all([api.get("/reports", state.filters), api.get("/report-templates")]);
  state.reports.sort((a, b) => b.created_at.localeCompare(a.created_at) || b.id - a.id);
  await renderReports(); renderTemplates();
}
async function view(next, selectFirst = true) {
  state.view = next;
  const listView = !["templates", "monthly"].includes(next);
  document.getElementById("report-workspace").hidden = !listView;
  document.getElementById("report-followup").hidden = true;
  document.getElementById("templates-view").hidden = next !== "templates";
  document.getElementById("monthly-view").hidden = next !== "monthly";
  document.getElementById("new-report").hidden = true;
  root.querySelectorAll('[data-action="view"]').forEach((tab) => { const selected = tab.dataset.view === next; tab.classList.toggle("on", selected); if (selected) tab.setAttribute("aria-current", "page"); else tab.removeAttribute("aria-current"); });
  await renderReports();
  if (listView && selectFirst) {
    const reports = state.reports.filter((report) => next === "mine" ? report.author_id === user.id : next === "inbox" ? report.status === "SUBMITTED" && report.reviewer_ids.includes(user.id) : true);
    if (reports.length) await openReport(reports[0].id, false);
    else { state.report = null; document.getElementById("report-detail").innerHTML = html`<div class="card-h"><h2 class="card-t">Report details</h2></div><p class="empty">Select a report to view or edit it.</p>`; }
  }
}

function show(id, markup) {
  const element = document.getElementById(id); element.innerHTML = markup; element.hidden = false;
  if (!element.closest("#report-sidebar") || matchMedia("(max-width: 950px)").matches) element.scrollIntoView({ behavior: "smooth", block: "start" });
  element.querySelector("input,select,textarea")?.focus({ preventScroll: true });
}

async function newReport(templateId = null, blank = false) {
  await view("mine", false);
  document.getElementById("report-detail").hidden = true;
  show("new-report", html`<div class="card-h"><h2 class="card-t">New draft</h2><button class="btn" data-action="close" data-target="new-report">Cancel</button></div><form data-form="create" class="pad stack">${select("Template", "template_id", state.templates.map((t) => ({ value: t.id, text: t.name })), templateId ?? (blank ? null : state.templates[0]?.id), "Blank report")}${input("Title (required for a blank report)", "title")}${textarea("Description", "description")}<div class="fields">${select("Shift", "shift", values(["MORNING", "AFTERNOON", "EVENING"]), null, "No shift")}${select("Project", "project_id", projectOptions(), null, "No project")}${select("Task", "task_id", taskOptions(), null, "No task")}</div><button class="btn btn-brand" type="submit">Create draft</button></form>`);
}
async function openReport(id, updateUrl = true) {
  const [report, historyRows] = await Promise.all([api.get(`/reports/${id}`), api.get(`/reports/${id}/history`)]);
  if (["templates", "monthly"].includes(state.view)) await view("all", false);
  state.report = report;
  if (updateUrl) history.replaceState(null, "", `?id=${id}`);
  document.getElementById("report-workspace").hidden = false;
  document.getElementById("new-report").hidden = true;
  const editable = ["DRAFT", "REVIEWED"].includes(report.status);
  const reviewable = report.status === "SUBMITTED" && report.reviewer_ids.includes(user.id);
  show("report-detail", html`<div class="card-h"><div><h2 class="card-t">RPT-${report.id} · ${report.title}</h2><p class="section-caption">${editable ? "Stays a Draft until submitted" : personName(state.directory, report.author_id)} · ${fmtDateTime(report.created_at)}</p></div>${badge(report.status)}</div><div class="pad stack">${editable ? raw(html`<form data-form="edit-report" class="stack"><div class="form-row"><label><span class="lbl">Shift</span><input class="input" aria-label="Shift" value="${label(report.shift) || "No shift"}" readonly></label>${select("Linked project", "project_id", projectOptions(), report.project_id, report.project_id == null ? "No project" : "Clear project link")}</div>${select("Linked task", "task_id", taskOptions(), report.task_id, report.task_id == null ? "No task" : "Clear task link")}<details><summary>Edit title</summary>${input("Title", "title", report.title, "text", true)}</details>${report.checklist_answers && Object.keys(report.checklist_answers).length ? raw(html`<div class="checklist"><span class="lbl">Checklist</span>${fragment(Object.entries(report.checklist_answers).map(([item, answer]) => checklistItem(item, answer)))}</div>`) : ""}${textarea("Notes on issues found", "description", report.description)}${people("Reviewers", "reviewer_ids", state.directory, state.reviewerSelections[report.id] ?? report.reviewer_ids)}<p class="section-caption">Choose at least one. Reviewers are notified.</p><div class="actions report-save"><button class="btn btn-brand" type="submit" value="submit">Submit for review</button><button class="btn" type="submit" value="save">Save draft</button></div></form>`) : raw(html`<div class="form-row"><div><span class="lbl">Shift</span>${label(report.shift) || "—"}</div><div><span class="lbl">Project / task</span>${projectName(report.project_id)}${report.task_id ? ` · Task #${report.task_id}` : ""}</div></div><p>${report.description || "No notes."}</p><span class="lbl">Reviewers</span><div class="reviewer-chips">${fragment(report.reviewer_ids.map((id) => html`<span class="b b-neutral">${name(id)}</span>`))}</div>`)}</div>`);
  document.getElementById("report-followup").hidden = false;
  document.getElementById("report-review").innerHTML = reviewable ? html`<div class="card-h"><div><h2 class="card-t">Review · RPT-${report.id}</h2><p class="section-caption">${report.title} by ${name(report.author_id)} · you are a reviewer</p></div>${badge(report.status)}</div><form data-form="review" class="pad stack"><div class="review-outcomes" role="radiogroup" aria-label="Review outcome">${fragment([["PASSED", "Passed", "Final"], ["REVIEWED", "Needs changes", 'Status “Reviewed” · author can resubmit'], ["REJECTED", "Rejected", "Final · comment required"]].map(([value, title, hint]) => html`<label class="out${value === "REVIEWED" ? " on" : ""}"><input type="radio" name="status" value="${value}"${attr(value === "REVIEWED", "checked")}><strong>${title}</strong><span class="muted">${hint}</span></label>`))}</div>${textarea("Comment", "comment", "", true)}<button class="btn btn-brand" type="submit">Send review</button></form>` : html`<div class="card-h"><h2 class="card-t">Report content</h2></div><pre class="report-content pad">${report.content || "No content yet."}</pre>`;
  document.getElementById("report-history").innerHTML = html`<div class="card-h"><h2 class="card-t">History · RPT-${report.id}</h2></div><div class="pad stack">${rows(historyRows.slice().reverse(), (entry) => html`<div class="history-entry">${badge(entry.new_status)}<div><p>${entry.comment || `${entry.old_status ?? "Created"} → ${entry.new_status}`}</p><span class="muted">${name(entry.changed_by)} · ${fmtDateTime(entry.changed_at)}</span></div></div>`, "No history yet.")}</div>`;
  await renderReports();
}

function checklistItem(item, answer) {
  if (/notes?|comments?|details/i.test(item)) return html`<label class="checklist-note"><span class="lbl">${item}</span><textarea class="input" data-answer="${item}" rows="2">${answer}</textarea></label>`;
  const normalized = String(answer).trim().toLowerCase();
  const checked = ["yes", "true", "1", "done", "checked"].includes(normalized);
  const custom = normalized && !["yes", "true", "1", "done", "checked", "no", "false", "0", "unchecked"].includes(normalized);
  return html`<div><label class="chk"><input type="checkbox" data-answer="${item}" data-answer-kind="checkbox" data-original-answer="${answer}"${attr(checked, "checked")}><span>${item}</span></label>${custom ? raw(html`<details class="answer-note"><summary>Saved answer</summary><textarea class="input" data-answer-note="${item}">${answer}</textarea></details>`) : ""}</div>`;
}

function checklistAnswers(form) {
  return Object.fromEntries([...form.querySelectorAll("[data-answer]")].map((control) => {
    if (control.dataset.answerKind !== "checkbox") return [control.dataset.answer, control.value];
    const note = [...form.querySelectorAll("[data-answer-note]")].find((element) => element.dataset.answerNote === control.dataset.answer);
    const value = control.dataset.dirty ? (control.checked ? "yes" : "no") : note?.value ?? control.dataset.originalAnswer;
    return [control.dataset.answer, value];
  }));
}

function templateEditor(template = null) {
  show("template-editor", html`<div class="card-h"><h2 class="card-t">${template ? "Edit report template" : "New report template"}</h2><button class="btn" data-action="close" data-target="template-editor">Cancel</button></div><form data-form="template" data-id="${template?.id ?? ""}" class="pad stack">${input("Name", "name", template?.name, "text", true)}${textarea("Description", "description", template?.description)}${textarea("Checklist (one item per line)", "checklist_items", template?.checklist_items.join("\n"), true)}<button class="btn btn-brand" type="submit">Save template</button></form>`);
}
root.addEventListener("change", (event) => {
  if (event.target.matches('[data-answer-kind="checkbox"]')) event.target.dataset.dirty = "true";
  if (event.target.matches('[data-form="review"] [name="status"]')) {
    const form = event.target.closest("form");
    form.querySelectorAll(".out").forEach((option) => option.classList.toggle("on", option.querySelector("input").checked));
    form.elements.comment.required = event.target.value !== "PASSED";
  }
});
forms(root, {
  search: async (form) => { state.filters = read(form); state.reports = await api.get("/reports", state.filters); state.reports.sort((a, b) => b.created_at.localeCompare(a.created_at) || b.id - a.id); await renderReports(); },
  create: async (form) => {
    const data = read(form); for (const key of ["template_id", "project_id", "task_id"]) data[key] = data[key] ? Number(data[key]) : null;
    data.description ??= "";
    const report = await api.post("/reports", data);
    document.getElementById("new-report").hidden = true; await refresh(); await openReport(report.id); toast("Draft created.");
  },
  "edit-report": async (form, button) => {
    const data = read(form); const reviewerIds = ids(form, "reviewer_ids"); state.reviewerSelections[state.report.id] = reviewerIds; delete data.reviewer_ids;
    data.description ??= ""; for (const key of ["project_id", "task_id"]) data[key] = data[key] ? Number(data[key]) : null;
    await api.patch(`/reports/${state.report.id}`, data);
    const answers = checklistAnswers(form);
    if (state.report.checklist_answers) await api.put(`/reports/${state.report.id}/answers`, { answers });
    if (button.value === "submit") { await api.post(`/reports/${state.report.id}/submit`, { reviewer_ids: reviewerIds }); delete state.reviewerSelections[state.report.id]; }
    await refresh(); await openReport(state.report.id); toast(button.value === "submit" ? "Report submitted." : "Draft saved.");
  },
  review: async (form) => { await api.post(`/reports/${state.report.id}/review`, { ...read(form), comment: read(form).comment ?? "" }); await refresh(); await openReport(state.report.id); toast("Review sent."); },
  template: async (form) => {
    const data = read(form); data.description ??= ""; data.checklist_items = (data.checklist_items ?? "").split("\n").map((line) => line.trim()).filter(Boolean);
    if (form.dataset.id) await api.put(`/report-templates/${form.dataset.id}`, data); else await api.post("/report-templates", data);
    document.getElementById("template-editor").hidden = true; await refresh(); toast("Template saved.");
  },
  monthly: async (form) => { const report = await api.post("/reports/monthly-summary", read(form)); await refresh(); await openReport(report.id); toast("Monthly summary generated."); },
});
actions(root, {
  view: async (button) => { await view(button.dataset.view); history.replaceState(null, "", `?view=${button.dataset.view}`); }, close: (button) => { document.getElementById(button.dataset.target).hidden = true; if (button.dataset.target === "new-report") document.getElementById("report-detail").hidden = false; },
  "new-blank": () => newReport(null, true), "new-report": () => newReport(),
  "open-report": (button) => openReport(Number(button.dataset.id)),
  "new-template": () => templateEditor(), "edit-template": async (button) => templateEditor(await api.get(`/report-templates/${button.dataset.id}`)),
  "use-template": (button) => newReport(Number(button.dataset.id)),
});
try {
  [state.directory, state.projects, state.tasks] = await Promise.all([api.get("/users/directory"), api.get("/projects"), api.get("/tasks")]);
  shell(); await refresh();
  const query = new URLSearchParams(location.search);
  const initialView = ["mine", "all", "projects", "inbox", "templates", "monthly"].includes(query.get("view")) ? query.get("view") : state.view;
  await view(initialView);
  const id = query.get("id"); if (id) await openReport(Number(id));
} catch (error) { toast(error.message, "bad"); root.insertAdjacentHTML("beforeend", html`<p class="empty" role="alert">${error.message} <a href="reports.html">Reload reports</a></p>`); }
finally { root.inert = false; root.removeAttribute("aria-busy"); }
