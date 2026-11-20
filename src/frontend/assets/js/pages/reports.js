// Daily reports, review workflow, templates and monthly summaries (US-RPT-01–08).
import { api, badge, fmtDate, fmtDateTime, html, raw, startPage, toast } from "../app.js";
import { actions, attr, forms, fragment, ids, input, people, personName, quickSearch, read, rows, select, textarea, values } from "./page-forms.js";

const user = await startPage();
const root = document.getElementById("page-content");
const state = { reports: [], projects: [], tasks: [], templates: [], directory: [], report: null, view: "mine", filters: {} };
const name = (id) => personName(state.directory, id);
const projectName = (id) => state.projects.find((project) => project.id === id)?.name ?? (id == null ? "No project" : `Project #${id}`);
const projectOptions = () => state.projects.map((project) => ({ value: project.id, text: project.name }));
const taskOptions = () => state.tasks.map((task) => ({ value: task.id, text: task.title }));
const statuses = values(["DRAFT", "SUBMITTED", "REVIEWED", "REJECTED", "PASSED"]);

function shell() {
  root.innerHTML = html`<section class="card"><div class="card-h"><div><div class="muted">Reports</div><h1>Daily reports &amp; reviews</h1></div><div class="actions"><button class="btn" data-action="new-blank">Blank report</button><button class="btn btn-brand" data-action="new-report">New from template</button></div></div><nav class="page-tabs">${fragment([["mine", "My reports"], ["all", "All reports"], ["projects", "By project"], ["inbox", "Reviewer inbox"], ["templates", "Templates"], ["monthly", "Monthly summary"]].map(([key, title]) => html`<button class="btn" data-action="view" data-view="${key}">${title}</button>`))}</nav></section>
  <section id="new-report" class="card" hidden></section><section id="template-editor" class="card" hidden></section>
  <section id="report-list" class="card"><form class="fields" data-form="search">${input("Report # or keyword", "q", "", "search")}${select("Status", "status", statuses, null, "All statuses")}${select("Type", "report_type", values(["DAILY", "MONTHLY_SUMMARY"]), null, "All types")}${select("Project", "project_id", projectOptions(), null, "Any project")}${people("Author", "author_id", state.directory, [], false)}${input("From", "date_from", "", "date")}${input("To", "date_to", "", "date")}<button class="btn" type="submit">Search</button></form><div id="report-results" class="pad"></div></section>
  <section id="report-detail" class="card" hidden></section>
  <section id="templates-view" class="card" hidden><div class="card-h"><h2 class="card-t">Report templates</h2><button class="btn" data-action="new-template">New template</button></div><div id="templates" class="pad"></div></section>
  <section id="monthly-view" class="card" hidden><div class="card-h"><h2 class="card-t">Monthly summary</h2></div><div class="pad"><p class="muted">Generate once per month, on or after its last day. Active Admins are the reviewers.</p><form data-form="monthly" class="fields">${input("Month", "month", new Date().getMonth() + 1, "number", true)}${input("Year", "year", new Date().getFullYear(), "number", true)}<button class="btn btn-brand" type="submit">Generate summary</button></form></div></section>`;
  root.querySelector('[name="month"]').min = "1"; root.querySelector('[name="month"]').max = "12";
  root.querySelector('[name="year"]').min = "2000"; root.querySelector('[name="year"]').max = "2100";
  quickSearch(root.querySelector('[data-form="search"]'));
}
function reportTable(reports) {
  if (!reports.length) return html`<p class="empty">No reports match this view.</p>`;
  return html`<div class="table-scroll"><table><thead><tr><th>Report</th><th>Title</th><th>Author / shift</th><th>Project</th><th>Reviewers</th><th>Date</th><th>Status</th></tr></thead><tbody>${fragment(reports.map((r) => html`<tr><td><a href="?id=${r.id}" data-action="open-report" data-id="${r.id}">RPT-${r.id}</a></td><td>${r.title}</td><td>${name(r.author_id)} · ${r.shift ?? "—"}</td><td>${projectName(r.project_id)}</td><td>${r.reviewer_ids.map(name).join(", ") || "—"}</td><td>${fmtDate(r.created_at)}</td><td>${badge(r.status)}</td></tr>`))}</tbody></table></div>`;
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
  await renderReports(); renderTemplates();
}
async function view(next) {
  state.view = next;
  document.getElementById("report-list").hidden = ["templates", "monthly"].includes(next);
  document.getElementById("templates-view").hidden = next !== "templates";
  document.getElementById("monthly-view").hidden = next !== "monthly";
  document.getElementById("report-detail").hidden = true;
  root.querySelectorAll('[data-action="view"]').forEach((button) => button.setAttribute("aria-pressed", String(button.dataset.view === next)));
  await renderReports();
}
function show(id, markup) {
  const element = document.getElementById(id); element.innerHTML = markup; element.hidden = false;
  element.scrollIntoView({ behavior: "smooth", block: "start" });
  element.querySelector("input,select,textarea")?.focus({ preventScroll: true });
}
function newReport(templateId = null, blank = false) {
  show("new-report", html`<div class="card-h"><h2 class="card-t">New draft</h2><button class="btn" data-action="close" data-target="new-report">Cancel</button></div><form data-form="create" class="pad stack">${select("Template", "template_id", state.templates.map((t) => ({ value: t.id, text: t.name })), templateId ?? (blank ? null : state.templates[0]?.id), "Blank report")}${input("Title (required for a blank report)", "title")}${textarea("Description", "description")}<div class="fields">${select("Shift", "shift", values(["MORNING", "AFTERNOON", "EVENING"]), null, "No shift")}${select("Project", "project_id", projectOptions(), null, "No project")}${select("Task", "task_id", taskOptions(), null, "No task")}</div><button class="btn btn-brand" type="submit">Create draft</button></form>`);
}
async function openReport(id) {
  const [report, historyRows] = await Promise.all([api.get(`/reports/${id}`), api.get(`/reports/${id}/history`)]);
  state.report = report;
  history.replaceState(null, "", `?id=${id}`);
  const editable = ["DRAFT", "REVIEWED"].includes(report.status);
  const reviewable = report.status === "SUBMITTED" && report.reviewer_ids.includes(user.id);
  show("report-detail", html`<div class="card-h"><div><h2 class="card-t">RPT-${report.id} · ${report.title}</h2><p class="muted">${name(report.author_id)} · ${fmtDateTime(report.created_at)} · ${projectName(report.project_id)}${report.task_id ? ` · Task #${report.task_id}` : ""}</p></div><div class="actions">${badge(report.status)}<button class="btn" data-action="close" data-target="report-detail">Close</button></div></div><div class="pad stack">${editable ? raw(html`<form data-form="edit-report" class="stack">${input("Title", "title", report.title, "text", true)}${textarea("Description", "description", report.description)}<div class="fields">${select("Project", "project_id", projectOptions(), report.project_id, report.project_id == null ? "No project" : "Clear project link")}${select("Task", "task_id", taskOptions(), report.task_id, report.task_id == null ? "No task" : "Clear task link")}</div>${report.checklist_answers ? raw(html`<fieldset class="stack"><legend>Checklist answers</legend>${fragment(Object.entries(report.checklist_answers).map(([item, answer]) => html`<label class="chk stack"><span>${item}</span><input class="input" data-answer="${item}" value="${answer}"></label>`))}</fieldset>`) : ""}${people("Reviewers", "reviewer_ids", state.directory, report.reviewer_ids)}<div class="actions"><button class="btn" type="submit" value="save">Save draft</button><button class="btn btn-brand" type="submit" value="submit">Submit for review</button></div></form>`) : raw(html`<p>${report.description}</p><p><strong>Reviewers:</strong> ${report.reviewer_ids.map(name).join(", ") || "None"}</p>`) }
  ${reviewable ? raw(html`<form data-form="review" class="stack"><h3>Review this report</h3>${select("Outcome", "status", [{value:"PASSED",text:"Passed (final)"},{value:"REVIEWED",text:"Reviewed — needs changes"},{value:"REJECTED",text:"Rejected (final)"}], "REVIEWED", null)}${textarea("Comment (required for Reviewed / Rejected)", "comment")}<button class="btn btn-brand" type="submit">Send review</button></form>`) : ""}
  <details open><summary>Report content</summary><pre class="report-content">${report.content || "No content yet."}</pre></details><h3>History</h3>${rows(historyRows, (entry) => html`<div class="history-entry">${badge(entry.new_status)}<div><p>${entry.comment || `${entry.old_status ?? "Created"} → ${entry.new_status}`}</p><span class="muted">${name(entry.changed_by)} · ${fmtDateTime(entry.changed_at)}</span></div></div>`, "No history yet.")}</div>`);
}
function templateEditor(template = null) {
  show("template-editor", html`<div class="card-h"><h2 class="card-t">${template ? "Edit report template" : "New report template"}</h2><button class="btn" data-action="close" data-target="template-editor">Cancel</button></div><form data-form="template" data-id="${template?.id ?? ""}" class="pad stack">${input("Name", "name", template?.name, "text", true)}${textarea("Description", "description", template?.description)}${textarea("Checklist (one item per line)", "checklist_items", template?.checklist_items.join("\n"), true)}<button class="btn btn-brand" type="submit">Save template</button></form>`);
}
forms(root, {
  search: async (form) => { state.filters = read(form); state.reports = await api.get("/reports", state.filters); await renderReports(); },
  create: async (form) => {
    const data = read(form); for (const key of ["template_id", "project_id", "task_id"]) data[key] = data[key] ? Number(data[key]) : null;
    data.description ??= "";
    const report = await api.post("/reports", data);
    document.getElementById("new-report").hidden = true; await refresh(); await openReport(report.id); toast("Draft created.");
  },
  "edit-report": async (form, button) => {
    const data = read(form); const reviewerIds = ids(form, "reviewer_ids"); delete data.reviewer_ids;
    data.description ??= ""; for (const key of ["project_id", "task_id"]) data[key] = data[key] ? Number(data[key]) : null;
    await api.patch(`/reports/${state.report.id}`, data);
    const answers = Object.fromEntries([...form.querySelectorAll("[data-answer]")].map((input) => [input.dataset.answer, input.value]));
    if (state.report.checklist_answers) await api.put(`/reports/${state.report.id}/answers`, { answers });
    if (button.value === "submit") await api.post(`/reports/${state.report.id}/submit`, { reviewer_ids: reviewerIds });
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
  view: (button) => view(button.dataset.view), close: (button) => { document.getElementById(button.dataset.target).hidden = true; },
  "new-blank": () => newReport(null, true), "new-report": () => newReport(),
  "open-report": (button) => openReport(Number(button.dataset.id)),
  "new-template": () => templateEditor(), "edit-template": async (button) => templateEditor(await api.get(`/report-templates/${button.dataset.id}`)),
  "use-template": (button) => newReport(Number(button.dataset.id)),
});
try {
  [state.directory, state.projects, state.tasks] = await Promise.all([api.get("/users/directory"), api.get("/projects"), api.get("/tasks")]);
  shell(); await refresh(); await view("mine");
  const id = new URLSearchParams(location.search).get("id"); if (id) await openReport(Number(id));
} catch (error) { toast(error.message, "bad"); root.insertAdjacentHTML("beforeend", html`<p class="empty" role="alert">${error.message} <a href="reports.html">Reload reports</a></p>`); }
