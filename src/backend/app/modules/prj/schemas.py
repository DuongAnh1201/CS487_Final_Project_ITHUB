"""PRJ request and response models."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.modules.prj.models import ProjectStatus, TaskPriority, TaskStatus


class ProjectCreate(BaseModel):
    """New project (US-PRJ-01)."""

    model_config = ConfigDict(json_schema_extra={"examples": [{"name": "Lab refresh", "description": "Replace the Room 101 PCs", "start_date": "2026-02-01", "due_date": "2026-03-01", "status": "ACTIVE", "member_ids": [2]}]})

    name: str = Field(min_length=1, max_length=150)
    description: str = ""
    start_date: date
    due_date: date | None = None
    status: ProjectStatus = ProjectStatus.PLANNED
    member_ids: list[int] = []


class ProjectFromTemplate(BaseModel):
    """New project built from a template (US-PRJ-02)."""

    model_config = ConfigDict(json_schema_extra={"examples": [{"template_id": 1, "name": "Fall setup", "description": "", "start_date": "2026-08-10", "due_date": "2026-09-10", "status": "PLANNED", "member_ids": []}]})

    template_id: int
    name: str = Field(min_length=1, max_length=150)
    description: str = ""
    start_date: date
    due_date: date | None = None
    status: ProjectStatus = ProjectStatus.PLANNED
    member_ids: list[int] = []


class ProjectUpdate(BaseModel):
    """Partial project update; ``status`` COMPLETED / reopen (FR-PRJ-07)."""

    model_config = ConfigDict(json_schema_extra={"examples": [{"description": "Replace the Room 101 and 102 PCs", "due_date": "2026-03-15", "status": "ACTIVE"}]})

    name: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = None
    start_date: date | None = None
    due_date: date | None = None
    status: ProjectStatus | None = None


class MemberAdd(BaseModel):
    """Add a member to a project (US-NTF-06)."""

    model_config = ConfigDict(json_schema_extra={"examples": [{"user_id": 2}]})

    user_id: int


class TaskCreate(BaseModel):
    """New task, standalone or linked (US-PRJ-03)."""

    model_config = ConfigDict(json_schema_extra={"examples": [{"title": "Image the new PCs", "description": "Use the Fall image", "status": "TODO", "priority": "HIGH", "due_date": "2026-02-10", "project_id": 1, "assignee_ids": [2]}]})

    title: str = Field(min_length=1, max_length=200)
    description: str = ""
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: date | None = None
    project_id: int | None = None
    assignee_ids: list[int] = []


class TaskUpdate(BaseModel):
    """Partial task update; ``project_id`` links a standalone task later (BR-14)."""

    model_config = ConfigDict(json_schema_extra={"examples": [{"title": "Image the new PCs (Room 101)", "priority": "MEDIUM", "due_date": "2026-02-12", "project_id": 1}]})

    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    priority: TaskPriority | None = None
    due_date: date | None = None
    project_id: int | None = None


class TaskStatusUpdate(BaseModel):
    """New status (US-PRJ-05)."""

    model_config = ConfigDict(json_schema_extra={"examples": [{"status": "IN_PROGRESS"}]})

    status: TaskStatus


class AssigneesUpdate(BaseModel):
    """Full set of assignees (at least one, BR-14)."""

    model_config = ConfigDict(json_schema_extra={"examples": [{"user_ids": [2, 3]}]})

    user_ids: list[int] = Field(min_length=1)


class HandoffRequest(BaseModel):
    """Hand an unfinished task to another user (US-PRJ-07)."""

    model_config = ConfigDict(json_schema_extra={"examples": [{"to_user_id": 3}]})

    to_user_id: int


class TaskRead(BaseModel):
    """A task with its current assignees."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int | None
    title: str
    description: str
    status: TaskStatus
    priority: TaskPriority
    due_date: date | None
    assignee_ids: list[int]
    created_by: int
    created_at: datetime
    updated_at: datetime


class AssignmentRead(BaseModel):
    """One row of a task's assignment history."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    assigned_by: int
    assigned_at: datetime
    ended_at: datetime | None
    ended_by: int | None
    active: bool


class ProjectRead(BaseModel):
    """A project with its progress."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
    start_date: date
    due_date: date | None
    status: ProjectStatus
    template_id: int | None
    created_by: int
    created_at: datetime
    updated_at: datetime
    total_tasks: int
    completed_tasks: int
    progress: float


class ProjectDetail(ProjectRead):
    """Project plus its tasks."""

    tasks: list[TaskRead]


class TemplateTaskIn(BaseModel):
    """One task definition in a template."""

    title: str = Field(min_length=1, max_length=200)
    description: str = ""
    relative_due_days: int | None = Field(default=None, ge=0)
    default_priority: TaskPriority = TaskPriority.MEDIUM


class TemplateWrite(BaseModel):
    """Create or replace a template (US-PRJ-02)."""

    model_config = ConfigDict(json_schema_extra={"examples": [{"name": "Semester setup", "description": "Recurring start-of-term work", "tasks": [{"title": "Inventory check", "description": "", "relative_due_days": 3, "default_priority": "HIGH"}, {"title": "Update images"}]}]})

    name: str = Field(min_length=1, max_length=150)
    description: str = ""
    tasks: list[TemplateTaskIn] = Field(min_length=1)


class TemplateTaskRead(TemplateTaskIn):
    """A stored task definition."""

    model_config = ConfigDict(from_attributes=True)

    id: int


class TemplateRead(BaseModel):
    """A stored template."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
    created_by: int
    created_at: datetime
    updated_at: datetime
    tasks: list[TemplateTaskRead]
