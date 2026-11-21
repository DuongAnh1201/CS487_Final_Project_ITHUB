"""PRJ business rules: ProjectManager, TaskManager, TemplateManager (US-PRJ-01..07)."""

from datetime import date

from app.core.clock import Clock
from app.core.exceptions import ConflictError, NotFoundError, ValidationRuleError
from app.modules.prj.models import (
    Project,
    ProjectMember,
    ProjectStatus,
    ProjectTemplate,
    Task,
    TaskAssignment,
    TaskStatus,
    TemplateTask,
)
from app.modules.prj.repository import ProjectRepository, TaskRepository, TemplateRepository
from app.modules.prj.schemas import (
    ProjectCreate,
    ProjectFromTemplate,
    ProjectUpdate,
    TaskCreate,
    TaskUpdate,
    TemplateWrite,
)
from app.modules.usr.models import User, UserStatus
from app.modules.usr.repository import UserRepository
from app.shared.audit import AuditLog
from app.shared.events import DomainEvent, EventPublisher, EventType
from app.shared.formatting import human_date, label
from app.shared.patch import PatchChanges

MSG_DATES = "Due date cannot be earlier than the start date."
MSG_NOT_COMPLETE = "A project can be completed only when all its tasks are Complete."
MSG_FINISHED = "Only unfinished tasks can be handed off."
MSG_BAD_ASSIGNEE = "Assignee must be an active user."
MSG_ALREADY_LINKED = "Task already belongs to a project."
CLEARABLE_PROJECT_FIELDS = frozenset({"due_date"})
CLEARABLE_TASK_FIELDS = frozenset({"due_date", "project_id"})  # project_id: only null on a standalone task
MSG_ALREADY_MEMBER = "User is already a project member."
MSG_ALREADY_ASSIGNED = "Task is already assigned to this user."


class _Base:
    """Shared helpers for the PRJ managers."""

    def __init__(self, users: UserRepository, audit: AuditLog, publisher: EventPublisher,
                 clock: Clock) -> None:
        self.users = users
        self.audit = audit
        self.publisher = publisher
        self.clock = clock

    def _active_user(self, user_id: int) -> User:
        user = self.users.get(user_id)
        if user is None:
            raise NotFoundError(self.users.not_found_message)
        if user.status != UserStatus.ACTIVE:
            raise ValidationRuleError(MSG_BAD_ASSIGNEE)
        return user

    @staticmethod
    def _check_dates(start: date | None, due: date | None) -> None:
        if start is not None and due is not None and due < start:
            raise ValidationRuleError(MSG_DATES)


class ProjectManager(_Base):
    """Projects, membership and creation from templates."""

    def __init__(self, projects: ProjectRepository, templates: TemplateRepository,
                 users: UserRepository, audit: AuditLog, publisher: EventPublisher,
                 clock: Clock) -> None:
        super().__init__(users, audit, publisher, clock)
        self.projects = projects
        self.templates = templates

    def create_project(self, actor: User, data: ProjectCreate) -> Project:
        """Create a project; the creator and listed users become members."""
        self._check_dates(data.start_date, data.due_date)
        self._check_status_for_new(data.status, 0)
        now = self.clock()
        project = self.projects.add(Project(
            name=data.name.strip(), description=data.description, start_date=data.start_date,
            due_date=data.due_date, status=data.status, created_by=actor.id,
            created_at=now, updated_at=now))
        self._finish_creation(actor, project, data.member_ids)
        return project

    def create_from_template(self, actor: User, data: ProjectFromTemplate) -> Project:
        """Atomically create a project and new task copies from a template (BR-13)."""
        template = self.templates.get_or_raise(data.template_id)
        self._check_dates(data.start_date, data.due_date)
        self._check_status_for_new(data.status, len(template.tasks))
        project = template.create_project(
            data.name.strip(), data.description, data.start_date, data.due_date, data.status,
            actor.id, self.clock())
        self.projects.add(project)
        self._finish_creation(actor, project, data.member_ids)
        for task in project.tasks:
            self.audit.record(actor, "CREATE", "Task", task.id, None,
                              {"title": task.title, "project_id": project.id})
        return project

    def update_project(self, actor: User, project_id: int, data: ProjectUpdate) -> Project:
        """Update details (null clears the due date); completing requires all tasks Complete (BR-15)."""
        project = self.projects.get_or_raise(project_id)
        changes = PatchChanges.of(data, CLEARABLE_PROJECT_FIELDS)
        self._check_dates(changes.get("start_date", project.start_date),
                          changes.get("due_date", project.due_date))
        if changes.get("status") == ProjectStatus.COMPLETED and not project.all_tasks_complete:
            raise ValidationRuleError(MSG_NOT_COMPLETE)
        old = self._snapshot(project)
        for field, value in changes.items():
            setattr(project, field, value.strip() if field == "name" else value)
        new = self._snapshot(project)
        if new != old:
            project.updated_at = self.clock()
            self.projects.flush()
            self.audit.record(actor, "UPDATE", "Project", project.id, old, new)
            self.publisher.publish(DomainEvent(
                EventType.PROJECT_UPDATED, f"Project '{project.name}' was updated.",
                actor_id=actor.id, related_type="Project", related_id=project.id,
                project_id=project.id))
        return project

    def add_member(self, actor: User, project_id: int, user_id: int) -> list[int]:
        """Add a user to a project and notify its members (FR-NTF-06)."""
        project = self.projects.get_or_raise(project_id)
        user = self._active_user(user_id)
        if self.projects.is_member(project.id, user.id):
            raise ConflictError(MSG_ALREADY_MEMBER)
        self._add_member(actor, project.id, user.id)
        self.audit.record(actor, "ADD_MEMBER", "Project", project.id, None, {"user_id": user.id})
        self.publisher.publish(DomainEvent(
            EventType.PROJECT_MEMBER_ADDED,
            f"{user.full_name} was added to project '{project.name}'.",
            actor_id=actor.id, related_type="Project", related_id=project.id,
            project_id=project.id))
        return self.projects.member_ids(project.id)

    def members(self, project_id: int) -> list[int]:
        """Member user ids."""
        return self.projects.member_ids(self.projects.get_or_raise(project_id).id)

    def get_project(self, project_id: int) -> Project:
        """One project."""
        return self.projects.get_or_raise(project_id)

    def search(self, **filters) -> list[Project]:
        """Search and filter projects (FR-PRJ-06)."""
        return self.projects.search(**filters)

    # ---- internals ----

    @staticmethod
    def _check_status_for_new(status: ProjectStatus, task_count: int) -> None:
        if status == ProjectStatus.COMPLETED and task_count > 0:
            raise ValidationRuleError(MSG_NOT_COMPLETE)

    def _finish_creation(self, actor: User, project: Project, member_ids: list[int]) -> None:
        for user_id in dict.fromkeys([actor.id, *member_ids]):
            self._add_member(actor, project.id, self._active_user(user_id).id)
        self.audit.record(actor, "CREATE", "Project", project.id, None, self._snapshot(project))
        self.publisher.publish(DomainEvent(
            EventType.PROJECT_CREATED, f"Project '{project.name}' was created.",
            actor_id=actor.id, related_type="Project", related_id=project.id,
            project_id=project.id))

    def _add_member(self, actor: User, project_id: int, user_id: int) -> None:
        self.projects.add_member(ProjectMember(
            project_id=project_id, user_id=user_id, added_by=actor.id, added_at=self.clock()))

    @staticmethod
    def _snapshot(project: Project) -> dict:
        return {
            "name": project.name, "description": project.description,
            "start_date": project.start_date.isoformat(),
            "due_date": project.due_date.isoformat() if project.due_date else None,
            "status": project.status.value,
        }


class TaskManager(_Base):
    """Tasks, assignment, hand-off and status (US-PRJ-03..07)."""

    def __init__(self, tasks: TaskRepository, projects: ProjectRepository, users: UserRepository,
                 audit: AuditLog, publisher: EventPublisher, clock: Clock) -> None:
        super().__init__(users, audit, publisher, clock)
        self.tasks = tasks
        self.projects = projects

    def create_task(self, actor: User, data: TaskCreate) -> Task:
        """Create a standalone or project task, optionally assigned."""
        project = self.projects.get_or_raise(data.project_id) if data.project_id else None
        assignees = [self._active_user(i) for i in dict.fromkeys(data.assignee_ids)]
        now = self.clock()
        task = self.tasks.add(Task(
            project_id=project.id if project else None, title=data.title.strip(),
            description=data.description, status=data.status, priority=data.priority,
            due_date=data.due_date, created_by=actor.id, created_at=now, updated_at=now))
        self.audit.record(actor, "CREATE", "Task", task.id, None, self._snapshot(task))
        if assignees:
            self._apply_assignees(actor, task, assignees)
        self._sync_project(actor, project)
        return task

    def update_task(self, actor: User, task_id: int, data: TaskUpdate) -> Task:
        """Edit a task (null clears the due date); ``project_id`` links a standalone task once (BR-14)."""
        task = self.tasks.get_or_raise(task_id)
        changes = PatchChanges.of(data, CLEARABLE_TASK_FIELDS)
        old = self._snapshot(task)
        old_project = task.project
        if "project_id" in changes and changes["project_id"] is None:
            if task.project_id is not None:
                raise ConflictError(MSG_ALREADY_LINKED)  # a link cannot be removed
            del changes["project_id"]
        if "project_id" in changes:
            if task.project_id is not None and changes["project_id"] != task.project_id:
                raise ConflictError(MSG_ALREADY_LINKED)
            self.projects.get_or_raise(changes["project_id"])
        for field, value in changes.items():
            setattr(task, field, value.strip() if field == "title" else value)
        self.tasks.flush()
        self.tasks.session.refresh(task)
        if self._snapshot(task) != old:
            task.updated_at = self.clock()
            self.audit.record(actor, "UPDATE", "Task", task.id, old, self._snapshot(task))
        if old_project is None and task.project is not None:
            for user_id in task.assignee_ids:
                self._ensure_member(actor, task.project.id, user_id)
        self._sync_project(actor, task.project or old_project)
        return task

    def set_status(self, actor: User, task_id: int, status: TaskStatus) -> Task:
        """Change a task's status and keep the project's completion consistent (BR-15)."""
        task = self.tasks.get_or_raise(task_id)
        if task.status != status:
            old = {"status": task.status.value}
            task.status = status
            task.updated_at = self.clock()
            self.tasks.flush()
            self.audit.record(actor, "STATUS_CHANGE", "Task", task.id, old, {"status": status.value})
            self._sync_project(actor, task.project)
        return task

    def assign(self, actor: User, task_id: int, user_ids: list[int]) -> Task:
        """Set the task's assignees; added users are notified (US-PRJ-04)."""
        task = self.tasks.get_or_raise(task_id)
        assignees = [self._active_user(i) for i in dict.fromkeys(user_ids)]
        self._apply_assignees(actor, task, assignees)
        return task

    def handoff(self, actor: User, task_id: int, to_user_id: int) -> Task:
        """Hand an unfinished task to another user, keeping status and history (FR-PRJ-07)."""
        task = self.tasks.get_or_raise(task_id)
        if task.status == TaskStatus.COMPLETE:
            raise ValidationRuleError(MSG_FINISHED)
        receiver = self._active_user(to_user_id)
        if task.assignee_ids == [receiver.id]:
            raise ConflictError(MSG_ALREADY_ASSIGNED)
        self._apply_assignees(actor, task, [receiver], action="HANDOFF")
        return task

    def history(self, task_id: int) -> list[TaskAssignment]:
        """Full assignment history, oldest first."""
        return list(self.tasks.get_or_raise(task_id).assignments)

    def get_task(self, task_id: int) -> Task:
        """One task."""
        return self.tasks.get_or_raise(task_id)

    def search(self, **filters) -> list[Task]:
        """Search and filter tasks (FR-PRJ-06)."""
        return self.tasks.search(**filters)

    # ---- internals ----

    def _apply_assignees(self, actor: User, task: Task, assignees: list[User],
                         action: str = "ASSIGN") -> None:
        """Replace the active assignee set; end removed rows, add new ones, notify new ones."""
        now = self.clock()
        before = task.assignee_ids
        wanted = {u.id for u in assignees}
        for row in task.assignments:
            if row.ended_at is None and row.user_id not in wanted:
                row.ended_at, row.ended_by = now, actor.id
        added = [u for u in assignees if u.id not in before]
        for user in added:
            self.tasks.add_assignment(TaskAssignment(
                task_id=task.id, user_id=user.id, assigned_by=actor.id, assigned_at=now))
        self.tasks.session.refresh(task)
        after = task.assignee_ids
        if after == before:
            return
        self.audit.record(actor, action, "Task", task.id, {"assignee_ids": before},
                          {"assignee_ids": after})
        if task.project_id is not None:
            for user in added:
                self._ensure_member(actor, task.project_id, user.id)
        if added:
            self.publisher.publish(DomainEvent(
                EventType.TASK_ASSIGNED, f"You were assigned task #{task.id}: {task.title}",
                actor_id=actor.id, recipient_ids=tuple(u.id for u in added),
                related_type="Task", related_id=task.id, project_id=task.project_id,
                details={
                    "assigner": actor.full_name, "task_title": task.title,
                    "task_description": task.description.strip(),
                    "project_name": task.project.name if task.project else "Standalone task",
                    "priority": label(task.priority), "due_date": human_date(task.due_date, "No due date"),
                }))

    def _ensure_member(self, actor: User, project_id: int, user_id: int) -> None:
        if not self.projects.is_member(project_id, user_id):
            self.projects.add_member(ProjectMember(
                project_id=project_id, user_id=user_id, added_by=actor.id, added_at=self.clock()))

    def _sync_project(self, actor: User, project: Project | None) -> None:
        """A COMPLETED project with an unfinished task goes back to ACTIVE (BR-15)."""
        if project is None:
            return
        self.projects.session.refresh(project)
        if project.status == ProjectStatus.COMPLETED and not project.all_tasks_complete:
            project.status = ProjectStatus.ACTIVE
            project.updated_at = self.clock()
            self.projects.flush()
            self.audit.record(actor, "UPDATE", "Project", project.id,
                              {"status": "COMPLETED"}, {"status": "ACTIVE"})

    @staticmethod
    def _snapshot(task: Task) -> dict:
        return {
            "title": task.title, "description": task.description, "status": task.status.value,
            "priority": task.priority.value,
            "due_date": task.due_date.isoformat() if task.due_date else None,
            "project_id": task.project_id,
        }


class TemplateManager(_Base):
    """Project templates (US-PRJ-02)."""

    def __init__(self, templates: TemplateRepository, users: UserRepository, audit: AuditLog,
                 publisher: EventPublisher, clock: Clock) -> None:
        super().__init__(users, audit, publisher, clock)
        self.templates = templates

    def create_template(self, actor: User, data: TemplateWrite) -> ProjectTemplate:
        """Create a template with its task definitions."""
        now = self.clock()
        template = ProjectTemplate(name=data.name.strip(), description=data.description,
                                   created_by=actor.id, created_at=now, updated_at=now)
        template.tasks = self._definitions(data)
        self.templates.add(template)
        self.audit.record(actor, "CREATE", "ProjectTemplate", template.id, None,
                          self._snapshot(template))
        return template

    def update_template(self, actor: User, template_id: int, data: TemplateWrite) -> ProjectTemplate:
        """Replace a template's content. Projects made from it are unaffected (BR-13)."""
        template = self.templates.get_or_raise(template_id)
        old = self._snapshot(template)
        template.name, template.description = data.name.strip(), data.description
        template.tasks = self._definitions(data)
        template.updated_at = self.clock()
        self.templates.flush()
        self.audit.record(actor, "UPDATE", "ProjectTemplate", template.id, old,
                          self._snapshot(template))
        return template

    def get_template(self, template_id: int) -> ProjectTemplate:
        """One template."""
        return self.templates.get_or_raise(template_id)

    def list_templates(self) -> list[ProjectTemplate]:
        """All templates."""
        return self.templates.list()

    @staticmethod
    def _definitions(data: TemplateWrite) -> list[TemplateTask]:
        return [TemplateTask(title=t.title.strip(), description=t.description,
                             relative_due_days=t.relative_due_days,
                             default_priority=t.default_priority) for t in data.tasks]

    @staticmethod
    def _snapshot(template: ProjectTemplate) -> dict:
        return {"name": template.name, "description": template.description,
                "tasks": [t.title for t in template.tasks]}
