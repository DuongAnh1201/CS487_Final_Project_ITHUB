"""PRJ routes: /templates, /projects, /tasks. Any logged-in user has the same access (BR-09)."""

from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.clock import Clock
from app.core.database import get_db
from app.core.deps import get_audit_log, get_clock, get_current_user, get_event_publisher
from app.modules.prj.models import (
    Project,
    ProjectStatus,
    ProjectTemplate,
    Task,
    TaskAssignment,
    TaskStatus,
)
from app.modules.prj.repository import ProjectRepository, TaskRepository, TemplateRepository
from app.modules.prj.schemas import (
    AssigneesUpdate,
    AssignmentRead,
    HandoffRequest,
    MemberAdd,
    ProjectCreate,
    ProjectDetail,
    ProjectFromTemplate,
    ProjectRead,
    ProjectUpdate,
    TaskCreate,
    TaskRead,
    TaskStatusUpdate,
    TaskUpdate,
    TemplateRead,
    TemplateWrite,
)
from app.modules.prj.service import ProjectManager, TaskManager, TemplateManager
from app.modules.usr.models import User
from app.modules.usr.repository import UserRepository
from app.shared.audit import AuditLog
from app.shared.events import EventPublisher

templates_router = APIRouter(prefix="/templates", tags=["templates"])
projects_router = APIRouter(prefix="/projects", tags=["projects"])
tasks_router = APIRouter(prefix="/tasks", tags=["tasks"])


def get_project_manager(
    db: Session = Depends(get_db), audit: AuditLog = Depends(get_audit_log),
    publisher: EventPublisher = Depends(get_event_publisher), clock: Clock = Depends(get_clock),
) -> ProjectManager:
    """ProjectManager for the request."""
    return ProjectManager(ProjectRepository(db), TemplateRepository(db), UserRepository(db),
                          audit, publisher, clock)


def get_task_manager(
    db: Session = Depends(get_db), audit: AuditLog = Depends(get_audit_log),
    publisher: EventPublisher = Depends(get_event_publisher), clock: Clock = Depends(get_clock),
) -> TaskManager:
    """TaskManager for the request."""
    return TaskManager(TaskRepository(db), ProjectRepository(db), UserRepository(db),
                       audit, publisher, clock)


def get_template_manager(
    db: Session = Depends(get_db), audit: AuditLog = Depends(get_audit_log),
    publisher: EventPublisher = Depends(get_event_publisher), clock: Clock = Depends(get_clock),
) -> TemplateManager:
    """TemplateManager for the request."""
    return TemplateManager(TemplateRepository(db), UserRepository(db), audit, publisher, clock)


# ---- templates -------------------------------------------------------------

@templates_router.post("", response_model=TemplateRead, status_code=201)
def create_template(body: TemplateWrite, user: User = Depends(get_current_user),
                    manager: TemplateManager = Depends(get_template_manager)) -> ProjectTemplate:
    """Create a template with reusable task definitions."""
    return manager.create_template(user, body)


@templates_router.get("", response_model=list[TemplateRead])
def list_templates(user: User = Depends(get_current_user),
                   manager: TemplateManager = Depends(get_template_manager)) -> list[ProjectTemplate]:
    """List templates."""
    return manager.list_templates()


@templates_router.get("/{template_id}", response_model=TemplateRead)
def get_template(template_id: int, user: User = Depends(get_current_user),
                 manager: TemplateManager = Depends(get_template_manager)) -> ProjectTemplate:
    """One template."""
    return manager.get_template(template_id)


@templates_router.put("/{template_id}", response_model=TemplateRead)
def update_template(template_id: int, body: TemplateWrite, user: User = Depends(get_current_user),
                    manager: TemplateManager = Depends(get_template_manager)) -> ProjectTemplate:
    """Replace a template's content."""
    return manager.update_template(user, template_id, body)


# ---- projects --------------------------------------------------------------

@projects_router.post("", response_model=ProjectRead, status_code=201)
def create_project(body: ProjectCreate, user: User = Depends(get_current_user),
                   manager: ProjectManager = Depends(get_project_manager)) -> Project:
    """Create a project (FR-PRJ-01)."""
    return manager.create_project(user, body)


@projects_router.post("/from-template", response_model=ProjectDetail, status_code=201)
def create_from_template(body: ProjectFromTemplate, user: User = Depends(get_current_user),
                         manager: ProjectManager = Depends(get_project_manager)) -> Project:
    """Create a project and its tasks from a template (FR-PRJ-02)."""
    return manager.create_from_template(user, body)


@projects_router.get("", response_model=list[ProjectRead])
def search_projects(
    q: str | None = None, status: ProjectStatus | None = None, assignee_id: int | None = None,
    due_before: date | None = None, due_after: date | None = None,
    user: User = Depends(get_current_user),
    manager: ProjectManager = Depends(get_project_manager),
) -> list[Project]:
    """Search and filter projects (FR-PRJ-06)."""
    return manager.search(q=q, status=status, assignee_id=assignee_id,
                          due_before=due_before, due_after=due_after)


@projects_router.get("/{project_id}", response_model=ProjectDetail)
def get_project(project_id: int, user: User = Depends(get_current_user),
                manager: ProjectManager = Depends(get_project_manager)) -> Project:
    """One project with its tasks and progress."""
    return manager.get_project(project_id)


@projects_router.patch("/{project_id}", response_model=ProjectRead)
def update_project(project_id: int, body: ProjectUpdate, user: User = Depends(get_current_user),
                   manager: ProjectManager = Depends(get_project_manager)) -> Project:
    """Update a project, complete it or reopen it (FR-PRJ-07)."""
    return manager.update_project(user, project_id, body)


@projects_router.get("/{project_id}/members", response_model=list[int])
def list_members(project_id: int, user: User = Depends(get_current_user),
                 manager: ProjectManager = Depends(get_project_manager)) -> list[int]:
    """Member user ids."""
    return manager.members(project_id)


@projects_router.post("/{project_id}/members", response_model=list[int], status_code=201)
def add_member(project_id: int, body: MemberAdd, user: User = Depends(get_current_user),
               manager: ProjectManager = Depends(get_project_manager)) -> list[int]:
    """Add a member and notify the project's members (FR-NTF-06)."""
    return manager.add_member(user, project_id, body.user_id)


# ---- tasks -----------------------------------------------------------------

@tasks_router.post("", response_model=TaskRead, status_code=201)
def create_task(body: TaskCreate, user: User = Depends(get_current_user),
                manager: TaskManager = Depends(get_task_manager)) -> Task:
    """Create a standalone or project task (FR-PRJ-03)."""
    return manager.create_task(user, body)


@tasks_router.get("", response_model=list[TaskRead])
def search_tasks(
    q: str | None = None, status: TaskStatus | None = None, assignee_id: int | None = None,
    project_id: int | None = None, due_before: date | None = None, due_after: date | None = None,
    user: User = Depends(get_current_user),
    manager: TaskManager = Depends(get_task_manager),
) -> list[Task]:
    """Search and filter tasks (FR-PRJ-06)."""
    return manager.search(q=q, status=status, assignee_id=assignee_id, project_id=project_id,
                          due_before=due_before, due_after=due_after)


@tasks_router.get("/{task_id}", response_model=TaskRead)
def get_task(task_id: int, user: User = Depends(get_current_user),
             manager: TaskManager = Depends(get_task_manager)) -> Task:
    """One task."""
    return manager.get_task(task_id)


@tasks_router.patch("/{task_id}", response_model=TaskRead)
def update_task(task_id: int, body: TaskUpdate, user: User = Depends(get_current_user),
                manager: TaskManager = Depends(get_task_manager)) -> Task:
    """Edit a task or link it to a project."""
    return manager.update_task(user, task_id, body)


@tasks_router.put("/{task_id}/status", response_model=TaskRead)
def set_status(task_id: int, body: TaskStatusUpdate, user: User = Depends(get_current_user),
               manager: TaskManager = Depends(get_task_manager)) -> Task:
    """Update task progress (FR-PRJ-05)."""
    return manager.set_status(user, task_id, body.status)


@tasks_router.put("/{task_id}/assignees", response_model=TaskRead)
def assign_task(task_id: int, body: AssigneesUpdate, user: User = Depends(get_current_user),
                manager: TaskManager = Depends(get_task_manager)) -> Task:
    """Assign or reassign a task (FR-PRJ-04)."""
    return manager.assign(user, task_id, body.user_ids)


@tasks_router.post("/{task_id}/handoff", response_model=TaskRead)
def hand_off_task(task_id: int, body: HandoffRequest, user: User = Depends(get_current_user),
                  manager: TaskManager = Depends(get_task_manager)) -> Task:
    """Hand an unfinished task to another user (FR-PRJ-07)."""
    return manager.handoff(user, task_id, body.to_user_id)


@tasks_router.get("/{task_id}/assignments", response_model=list[AssignmentRead])
def assignment_history(task_id: int, user: User = Depends(get_current_user),
                       manager: TaskManager = Depends(get_task_manager)) -> list[TaskAssignment]:
    """Assignment history, oldest first."""
    return manager.history(task_id)
