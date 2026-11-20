// Live projects, tasks and reusable templates (FR-PRJ-01–07, US-PRJ-01–07).
import { api, badge, fmtDate, fmtDateTime, html, raw, startPage, toast } from "../app.js";
import { actions, avatars, compactFilters, pageIcon, plusIcon, attr, forms, fragment, ids, input, options, people, personName, quickSearch, read, rows, select, textarea, today, values } from "./page-forms.js";

const user = await startPage();
const root = document.getElementById("page-content");
root.inert = true;
root.setAttribute("aria-busy", "true");
const state = { projects: [], allProjects: [], tasks: [], templates: [], directory: [], project: null, members: [], task: null, assignments: [], view: "projects", filters: {}, projectMembers: {}, taskView: "board", showAllComplete: false };
const projectStates = values(["PLANNED", "ACTIVE", "ON_HOLD", "COMPLETED"]);
const taskStates = [{ value: "TODO", text: "To Do" }, ...values(["IN_PROGRESS", "COMPLETE"])];
const priorities = values(["LOW", "MEDIUM", "HIGH"]);
const projectOptions = () => state.allProjects.map((p) => ({ value: p.id, text: p.name }));
const name = (id) => personName(state.directory, id);

function shell() {
  root.innerHTML = html`<section class="card" id="project-heading"><div class="page-heading">${pageIcon("projects")}<div class="heading-copy"><div class="eyebrow muted">Projects</div><h1>Projects &amp; tasks</h1></div><div class="actions"><button class="btn" data-action="new-task">New task</button><button class="btn" data-action="from-template">From template</button><button class="btn btn-brand" data-action="new-project">${plusIcon()} New project</button></div></div><nav class="page-tabs" aria-label="Project sections"><a class="tab on" href="projects.html" data-action="view" data-view="projects" aria-current="page">Projects</a><a class="tab" href="?view=tasks" data-action="view" data-view="tasks">Tasks</a><a class="tab" href="?view=templates" data-action="view" data-view="templates">Templates</a></nav>
  <form data-form="search-projects" id="project-filters" class="filter-bar">${input("Search projects", "q", "", "search")}${select("Status", "status", projectStates, null, "Any status")}${people("Assignee", "assignee_id", state.directory, [], false)}${input("Due from", "due_after", "", "date")}${input("Due to", "due_before", "", "date")}<button class="btn" type="submit">Search</button></form></section>
  <section id="project-editor" class="card" hidden></section><section id="template-editor" class="card" hidden></section>
  <section id="project-list" aria-label="Projects"><div id="projects" class="project-grid"></div></section>
  <section id="project-detail" class="card" hidden></section>
  <section id="tasks-view" class="card" hidden><div class="card-h"><h2 class="card-t">All tasks</h2><button class="btn btn-brand" data-action="new-task">New task</button></div><form data-form="search-tasks" class="filter-bar">${input("Search tasks", "q", "", "search")}${select("Status", "status", taskStates, null, "All statuses")}${people("Assignee", "assignee_id", state.directory, [], false)}${select("Project", "project_id", projectOptions(), null, "All projects")}<label class="inline-check"><input name="standalone" type="checkbox">Standalone only</label><button class="btn" type="submit">Search</button><details class="more-filters"><summary>More filters</summary><div class="fields">${input("Due from", "due_after", "", "date")}${input("Due to", "due_before", "", "date")}</div></details></form><div id="all-tasks" class="pad"></div></section>
  <div id="task-workspace" class="task-workspace" hidden><section id="task-editor" class="card"><div class="card-h"><h2 class="card-t">Task details</h2></div><p class="empty">Select a task to view its status, assignees and history.</p></section><section id="project-template-panel" class="card"><div class="card-h"><h2 class="card-t">Project templates</h2><button class="btn" data-action="new-template">New template</button></div><div id="template-preview" class="pad"></div></section></div>
  <section id="templates-view" class="card" hidden><div class="card-h"><h2 class="card-t">Project templates</h2><button class="btn" data-action="new-template">New template</button></div><div id="templates" class="pad"></div></section>`;
  compactFilters(root);
  quickSearch(root.querySelector('[data-form="search-projects"]'));
}

function renderProjects() {
  document.getElementById("projects").innerHTML = rows(state.projects, (p) => html`<a href="?id=${p.id}" class="card project-card${p.id === state.project?.id ? " is-open" : ""}" data-action="open-project" data-id="${p.id}"${attr(p.id === state.project?.id, 'aria-current="true"')}><div class="spread"><strong>${p.name}</strong>${badge(p.status)}</div><span class="muted project-description">${p.description || "No description"} · due ${fmtDate(p.due_date)}</span><div class="spread project-progress"><span>${p.completed_tasks} of ${p.total_tasks} tasks</span><strong>${Math.round(p.progress)}%</strong></div><div class="prog"><span style="width:${Math.max(0, Math.min(100, p.progress))}%"></span></div>${avatars(state.directory, state.projectMembers[p.id] ?? [])}</a>`, "No projects match your filters.");
}

function taskCard(task) {
  const complete = task.status === "COMPLETE";
  const due = task.due_date === today() ? "Due today" : `Due ${fmtDate(task.due_date)}`;
  const overdue = !complete && task.due_date && task.due_date < today();
  return html`<div class="tcard task-card${complete ? " is-complete" : ""}${overdue ? " is-overdue" : ""}"><div class="spread"><button class="record-link task-title" data-action="open-task" data-id="${task.id}">${task.title}</button>${badge(complete ? "Done" : task.priority, complete ? "good" : task.priority === "MEDIUM" ? "neutral" : task.priority === "HIGH" ? "bad" : "good")}</div><span class="task-due${!complete && (overdue || task.due_date === today()) ? " due-warning" : " muted"}">${complete ? `Updated ${fmtDate(task.updated_at)}` : due}</span>${complete ? "" : raw(html`<div class="spread">${avatars(state.directory, task.assignee_ids)}<button class="btn btn-small" data-action="task-handoff" data-id="${task.id}">Hand off</button></div>`)}</div>`;
}

function renderTasks(tasks = state.tasks) {
  document.getElementById("all-tasks").innerHTML = tasks.length ? html`<div class="table-scroll"><table><thead><tr><th>Task</th><th>Project</th><th>Assignees</th><th>Priority</th><th>Due</th><th>Status</th></tr></thead><tbody>${fragment(tasks.map((task) => html`<tr><td><a href="?task=${task.id}" data-action="open-task" data-id="${task.id}">${task.title}</a></td><td>${state.allProjects.find((p) => p.id === task.project_id)?.name ?? "Standalone"}</td><td>${avatars(state.directory, task.assignee_ids)}</td><td>${badge(task.priority)}</td><td>${fmtDate(task.due_date)}</td><td>${badge(task.status)}</td></tr>`))}</tbody></table></div>` : html`<p class="empty">No tasks match your filters.</p>`;
}

function renderTemplates() {
  const markup = rows(state.templates, (t) => html`<article class="tcard"><div class="spread"><strong>${t.name}</strong><span>${t.tasks.length} tasks</span></div><p class="muted">${t.description}</p><ul>${fragment(t.tasks.map((task) => html`<li>${task.title} · ${badge(task.default_priority)} · ${task.relative_due_days == null ? "No due date" : `Day ${task.relative_due_days}`}</li>`))}</ul><div class="actions"><button class="btn" data-action="edit-template" data-id="${t.id}">Edit template</button><button class="btn btn-brand" data-action="use-template" data-id="${t.id}">Create project</button></div></article>`, "No project templates yet.");
  document.getElementById("templates").innerHTML = markup;
  document.getElementById("template-preview").innerHTML = markup;
}
function view(next) {
  state.view = next;
  document.getElementById("project-filters").hidden = next !== "projects";
  document.getElementById("task-workspace").hidden = next === "templates" || (!state.project && !state.task);
  for (const [id, key] of [["project-list", "projects"], ["tasks-view", "tasks"], ["templates-view", "templates"]]) document.getElementById(id).hidden = key !== next;
  root.querySelectorAll('[data-action="view"]').forEach((button) => { button.classList.toggle("on", button.dataset.view === next); if (button.dataset.view === next) button.setAttribute("aria-current", "page"); else button.removeAttribute("aria-current"); });
  document.getElementById("project-detail").hidden = next !== "projects" || !state.project;
}
async function refresh() {
  [state.allProjects, state.tasks, state.templates] = await Promise.all([api.get("/projects"), api.get("/tasks"), api.get("/templates")]);
  state.projects = Object.values(state.filters).some((value) => value != null && value !== "") ? await api.get("/projects", state.filters) : state.allProjects;
  root.querySelector('#tasks-view [name="project_id"]').innerHTML = options(projectOptions(), null, "All projects");
  await Promise.all(state.allProjects.map(async (project) => { state.projectMembers[project.id] = await api.get(`/projects/${project.id}/members`); }));
  renderProjects(); renderTasks(); renderTemplates();
  if (state.project) await openProject(state.project.id, false, false);
}
function showEditor(id, markup) {
  const element = document.getElementById(id);
  element.innerHTML = markup;
  element.hidden = false;
  if (id === "task-editor") document.getElementById("task-workspace").hidden = false;
  element.scrollIntoView({ behavior: "smooth", block: "start" });
  element.querySelector("input, select, textarea")?.focus({ preventScroll: true });
}
function projectEditor(project = null, templateId = null) {
  const templateOptions = state.templates.map((t) => ({ value: t.id, text: t.name }));
  showEditor("project-editor", html`<div class="card-h"><h2 class="card-t">${project ? "Edit project" : "New project"}</h2><button class="btn" data-action="close" data-target="project-editor">Cancel</button></div><form data-form="project" data-id="${project?.id ?? ""}" class="pad stack">${project ? "" : select("Start from", "template_id", templateOptions, templateId, "Blank project") }<div class="fields">${input("Name", "name", project?.name, "text", true)}${input("Start date", "start_date", project?.start_date ?? today(), "date", true)}${input("Due date", "due_date", project?.due_date, "date")}<button class="btn" type="button" data-action="clear-due-date">Clear due date</button>${select("Status", "status", projectStates, project?.status ?? "PLANNED", null)}</div>${textarea("Description", "description", project?.description)}${project ? "" : people("Members", "member_ids", state.directory, [user.id])}<button class="btn btn-brand" type="submit">Save project</button></form>`);
}
async function openProject(id, updateUrl = true, activate = true) {
  if (state.project?.id !== id) { state.showAllComplete = false; state.task = null; }
  [state.project, state.members] = await Promise.all([api.get(`/projects/${id}`), api.get(`/projects/${id}/members`)]);
  state.projectMembers[id] = state.members;
  if (updateUrl) history.replaceState(null, "", `?id=${id}`);
  if (activate) view("projects");
  renderProjects();
  const p = state.project;
  const element = document.getElementById("project-detail");
  element.innerHTML = html`<div class="card-h"><div><h2 class="card-t">${p.name} · tasks</h2><p class="section-caption">${fmtDate(p.start_date)} – ${fmtDate(p.due_date)} · ${state.members.length} members · <a href="#project-members" data-action="toggle-members">Add member</a> · "Completed" unlocks when every task is Complete</p></div><div class="actions"><div class="seg" role="group" aria-label="Task view"><button data-action="task-view" data-mode="list" aria-pressed="${state.taskView === "list"}" class="${state.taskView === "list" ? "on" : ""}">List</button><button data-action="task-view" data-mode="board" aria-pressed="${state.taskView === "board"}" class="${state.taskView === "board" ? "on" : ""}">Board</button></div><button class="btn" data-action="edit-project">Edit project</button><button class="btn btn-brand" data-action="project-task">Add task</button></div></div><div id="project-members" class="pad" hidden><p>${p.description}</p><div class="spread"><span>${state.members.map(name).join(", ")}</span>${avatars(state.directory, state.members)}</div><form data-form="member" class="fields">${people("Add member", "user_id", state.directory.filter((person) => !state.members.includes(person.id)), [], false, true)}<button class="btn" type="submit">Add member</button></form></div><div id="project-tasks"></div>`;
  renderProjectTasks();
  element.hidden = state.view !== "projects";
}

function renderProjectTasks() {
  if (!state.project) return;
  const tasks = state.project.tasks;
  root.querySelectorAll('[data-action="task-view"]').forEach((button) => { const selected = button.dataset.mode === state.taskView; button.classList.toggle("on", selected); button.setAttribute("aria-pressed", String(selected)); });
  const target = document.getElementById("project-tasks");
  if (state.taskView === "list") {
    target.innerHTML = tasks.length ? html`<div class="table-scroll"><table><thead><tr><th>Task</th><th>Assignees</th><th>Priority</th><th>Due</th><th>Status</th><th></th></tr></thead><tbody>${fragment(tasks.map((task) => html`<tr class="${task.status === "COMPLETE" ? "is-complete" : ""}"><td><a class="task-title" href="?task=${task.id}" data-action="open-task" data-id="${task.id}">${task.title}</a></td><td>${avatars(state.directory, task.assignee_ids)}</td><td>${badge(task.priority)}</td><td>${fmtDate(task.due_date)}</td><td>${badge(task.status)}</td><td>${task.status === "COMPLETE" ? "" : raw(html`<button class="btn btn-small" data-action="task-handoff" data-id="${task.id}">Hand off</button>`)}</td></tr>`))}</tbody></table></div>` : html`<p class="empty">No tasks in this project.</p>`;
    return;
  }
  target.innerHTML = html`<div class="board">${fragment(taskStates.map(({ value, text }) => {
    const columnTasks = tasks.filter((task) => task.status === value);
    const shown = value === "COMPLETE" && !state.showAllComplete ? columnTasks.slice(0, 2) : columnTasks;
    const remaining = columnTasks.length - shown.length;
    return html`<div class="col" data-column="${value}"><div class="spread"><strong>${text}</strong>${badge(String(columnTasks.length), value === "COMPLETE" ? "good" : value === "IN_PROGRESS" ? "info" : "neutral")}</div>${rows(shown, taskCard, "No tasks in this column.")}${remaining ? raw(html`<button class="btn show-more" data-action="show-complete">Show ${remaining} more</button>`) : ""}</div>`;
  }))}</div>`;
}

async function openTask(id) {
  [state.task, state.assignments] = await Promise.all([api.get(`/tasks/${id}`), api.get(`/tasks/${id}/assignments`)]);
  history.replaceState(null, "", `?task=${id}`);
  taskEditor(state.task);
}
function taskEditor(task = null, projectId = null) {
  const fixedProject = task?.project_id != null;
  showEditor("task-editor", html`<div class="card-h"><h2 class="card-t">${task ? `Task · ${task.title}` : "New task"}</h2><button class="btn" data-action="close" data-target="task-editor">Close</button></div><form data-form="task" data-id="${task?.id ?? ""}" class="pad stack"><div class="fields">${input("Title", "title", task?.title, "text", true)}${select("Priority", "priority", priorities, task?.priority ?? "MEDIUM", null)}${input("Due date", "due_date", task?.due_date, "date")}<button class="btn" type="button" data-action="clear-due-date">Clear due date</button>${select("Project", "project_id", projectOptions(), task?.project_id ?? projectId, "None (standalone)")}${task ? "" : select("Status", "status", taskStates, "TODO", null)}</div>${fixedProject ? raw(html`<p class="muted">A linked task stays with its project.</p>`) : ""}${textarea("Description", "description", task?.description)}${task ? "" : people("Assignees", "assignee_ids", state.directory, [user.id], true, true)}<button class="btn btn-brand" type="submit">${task ? "Save task details" : "Create task"}</button></form>${task ? raw(html`<div class="pad stack"><form data-form="task-status" class="fields">${select("Status", "status", taskStates, task.status, null)}<button class="btn" type="submit">Update status</button></form><form data-form="task-assignees" class="stack">${people("Assignees", "user_ids", state.directory, task.assignee_ids, true, true)}<button class="btn" type="submit">Save assignees</button></form><form data-form="handoff" class="fields">${people("Hand off to", "to_user_id", state.directory, [], false, true)}<button class="btn" type="submit"${attr(task.status === "COMPLETE", "disabled")}>Hand off</button></form><h3>Assignment history</h3>${rows(state.assignments, (a) => html`<p>${name(a.user_id)} · ${fmtDateTime(a.assigned_at)} – ${a.active ? "now" : fmtDateTime(a.ended_at)} · assigned by ${name(a.assigned_by)}${a.ended_by ? ` · ended by ${name(a.ended_by)}` : ""}</p>`, "No assignment history.")}</div>`) : ""}`);
  if (fixedProject) document.querySelector('#task-editor [name="project_id"]').disabled = true;
}
function templateTask(task = {}) {
  return html`<fieldset data-template-task class="fields"><legend>Task definition</legend>${input("Title", "title", task.title, "text", true)}${textarea("Description", "description", task.description)}${input("Days after project start", "relative_due_days", task.relative_due_days, "number")}${select("Priority", "default_priority", priorities, task.default_priority ?? "MEDIUM", null)}<button class="btn" type="button" data-action="remove-definition">Remove task</button></fieldset>`;
}
function templateEditor(template = null) {
  showEditor("template-editor", html`<div class="card-h"><h2 class="card-t">${template ? "Edit template" : "New template"}</h2><button class="btn" data-action="close" data-target="template-editor">Cancel</button></div><form data-form="template" data-id="${template?.id ?? ""}" class="pad stack">${input("Name", "name", template?.name, "text", true)}${textarea("Description", "template_description", template?.description)}<div id="template-tasks" class="stack">${fragment((template?.tasks ?? [{}]).map(templateTask))}</div><div class="actions"><button class="btn" type="button" data-action="add-definition">Add task definition</button><button class="btn btn-brand" type="submit">Save template</button></div></form>`);
}
forms(root, {
  "search-projects": async (form) => { state.filters = read(form); state.projects = await api.get("/projects", state.filters); renderProjects(); },
  "search-tasks": async (form) => { const { standalone, ...query } = read(form); const tasks = await api.get("/tasks", query); renderTasks(standalone ? tasks.filter((t) => t.project_id == null) : tasks); },
  project: async (form) => {
    const data = read(form); const id = form.dataset.id; const templateId = data.template_id;
    delete data.template_id; data.description ??= "";
    if (!id) data.member_ids = ids(form, "member_ids");
    let saved;
    if (id) saved = await api.patch(`/projects/${id}`, data);
    else saved = await api.post(templateId ? "/projects/from-template" : "/projects", templateId ? { ...data, template_id: Number(templateId) } : data);
    document.getElementById("project-editor").hidden = true;
    state.project = saved; await refresh(); await openProject(saved.id); toast("Project saved.");
  },
  member: async (form) => { await api.post(`/projects/${state.project.id}/members`, { user_id: Number(read(form).user_id) }); await openProject(state.project.id); toast("Member added."); },
  task: async (form) => {
    const data = read(form); data.description ??= ""; data.project_id = data.project_id ? Number(data.project_id) : null;
    const id = form.dataset.id;
    if (!id) data.assignee_ids = ids(form, "assignee_ids");
    if (id && state.task.project_id != null) delete data.project_id;
    const task = id ? await api.patch(`/tasks/${id}`, data) : await api.post("/tasks", data);
    await refresh(); await openTask(task.id); toast("Task saved.");
  },
  "task-status": async (form) => { await api.put(`/tasks/${state.task.id}/status`, read(form)); await refresh(); await openTask(state.task.id); toast("Status updated."); },
  "task-assignees": async (form) => { await api.put(`/tasks/${state.task.id}/assignees`, { user_ids: ids(form, "user_ids") }); await refresh(); await openTask(state.task.id); toast("Assignees updated."); },
  handoff: async (form) => { await api.post(`/tasks/${state.task.id}/handoff`, { to_user_id: Number(read(form).to_user_id) }); await refresh(); await openTask(state.task.id); toast("Task handed off."); },
  template: async (form) => {
    const tasks = [...form.querySelectorAll("[data-template-task]")].map((fieldset) => ({
      title: fieldset.querySelector('[name="title"]').value.trim(), description: fieldset.querySelector('[name="description"]').value,
      relative_due_days: fieldset.querySelector('[name="relative_due_days"]').value === "" ? null : Number(fieldset.querySelector('[name="relative_due_days"]').value),
      default_priority: fieldset.querySelector('[name="default_priority"]').value,
    }));
    const data = { name: form.elements.name.value.trim(), description: form.elements.template_description.value, tasks };
    if (form.dataset.id) await api.put(`/templates/${form.dataset.id}`, data); else await api.post("/templates", data);
    document.getElementById("template-editor").hidden = true; await refresh(); toast("Template saved.");
  },
});
actions(root, {
  view: (button) => { view(button.dataset.view); history.replaceState(null, "", `?view=${button.dataset.view}`); },
  "clear-due-date": (button) => { const field = button.closest("form").elements.due_date; field.value = ""; field.focus(); },
  close: (button) => { document.getElementById(button.dataset.target).hidden = true; if (button.dataset.target === "task-editor") document.getElementById("task-workspace").hidden = true; },
  "from-template": () => projectEditor(null, state.templates[0]?.id),
  "toggle-members": () => { const panel = document.getElementById("project-members"); panel.hidden = !panel.hidden; if (!panel.hidden) panel.querySelector("select")?.focus(); },
  "task-view": (button) => { state.taskView = button.dataset.mode; renderProjectTasks(); },
  "show-complete": () => { state.showAllComplete = true; renderProjectTasks(); },
  "task-handoff": async (button) => { await openTask(Number(button.dataset.id)); const form = root.querySelector('[data-form="handoff"]'); form.scrollIntoView({ behavior: "smooth", block: "center" }); form.querySelector("select").focus({ preventScroll: true }); },
  "new-project": () => projectEditor(), "edit-project": () => projectEditor(state.project),
  "open-project": (button) => openProject(Number(button.dataset.id)),
  "new-task": () => { state.task = null; taskEditor(); },
  "project-task": () => { state.task = null; taskEditor(null, state.project.id); },
  "open-task": (button) => openTask(Number(button.dataset.id)),
  "new-template": () => templateEditor(),
  "edit-template": async (button) => templateEditor(await api.get(`/templates/${button.dataset.id}`)),
  "use-template": (button) => projectEditor(null, Number(button.dataset.id)),
  "add-definition": () => document.getElementById("template-tasks").insertAdjacentHTML("beforeend", templateTask()),
  "remove-definition": (button) => button.closest("fieldset").remove(),
});
try {
  state.directory = await api.get("/users/directory");
  shell(); await refresh(); view(state.view);
  const query = new URLSearchParams(location.search);
  if (["projects", "tasks", "templates"].includes(query.get("view"))) view(query.get("view"));
  if (query.has("task")) await openTask(Number(query.get("task")));
  else if (query.has("id")) await openProject(Number(query.get("id")));
} catch (error) { toast(error.message, "bad"); root.insertAdjacentHTML("beforeend", html`<p class="empty" role="alert">${error.message} <a href="projects.html">Reload projects</a></p>`); }
finally { root.inert = false; root.removeAttribute("aria-busy"); }
