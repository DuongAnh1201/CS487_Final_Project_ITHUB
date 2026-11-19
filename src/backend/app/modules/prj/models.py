"""PRJ entities: Project, Task, ProjectTemplate, TemplateTask, TaskAssignment, ProjectMember."""

import enum
from datetime import date, datetime, timedelta

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ProjectStatus(str, enum.Enum):
    """Project lifecycle (FR-PRJ-01, FR-PRJ-07)."""

    PLANNED = "PLANNED"
    ACTIVE = "ACTIVE"
    ON_HOLD = "ON_HOLD"
    COMPLETED = "COMPLETED"


class TaskStatus(str, enum.Enum):
    """Task statuses (BR-15): To Do, In Progress, Complete."""

    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETE = "COMPLETE"


class TaskPriority(str, enum.Enum):
    """Task priority (SP5)."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class Project(Base):
    """A group of related tasks."""

    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    start_date: Mapped[date] = mapped_column(Date)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[ProjectStatus] = mapped_column(Enum(ProjectStatus), default=ProjectStatus.PLANNED)
    template_id: Mapped[int | None] = mapped_column(ForeignKey("project_templates.id"), nullable=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime)
    updated_at: Mapped[datetime] = mapped_column(DateTime)

    tasks: Mapped[list["Task"]] = relationship(back_populates="project", order_by="Task.id")

    @property
    def total_tasks(self) -> int:
        """Number of tasks in the project."""
        return len(self.tasks)

    @property
    def completed_tasks(self) -> int:
        """Number of Complete tasks."""
        return sum(1 for t in self.tasks if t.status == TaskStatus.COMPLETE)

    @property
    def progress(self) -> float:
        """Percent of tasks Complete (0 when there are no tasks)."""
        return round(100 * self.completed_tasks / self.total_tasks, 1) if self.tasks else 0.0

    @property
    def all_tasks_complete(self) -> bool:
        """BR-05: true when every task is Complete."""
        return all(t.status == TaskStatus.COMPLETE for t in self.tasks)


class Task(Base):
    """A unit of work, standalone or linked to one project (BR-14)."""

    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(200), index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus), default=TaskStatus.TODO)
    priority: Mapped[TaskPriority] = mapped_column(Enum(TaskPriority), default=TaskPriority.MEDIUM)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime)
    updated_at: Mapped[datetime] = mapped_column(DateTime)

    project: Mapped[Project | None] = relationship(back_populates="tasks")
    assignments: Mapped[list["TaskAssignment"]] = relationship(
        back_populates="task", order_by="TaskAssignment.id"
    )

    @property
    def assignee_ids(self) -> list[int]:
        """Current assignees."""
        return [a.user_id for a in self.assignments if a.ended_at is None]

    def is_overdue(self, today: date) -> bool:
        """Unfinished and past its due date."""
        return self.status != TaskStatus.COMPLETE and self.due_date is not None and self.due_date < today


class TaskAssignment(Base):
    """One assignee of a task; ended (never deleted) on reassignment, keeping history."""

    __tablename__ = "task_assignments"

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    assigned_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    assigned_at: Mapped[datetime] = mapped_column(DateTime)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ended_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    task: Mapped[Task] = relationship(back_populates="assignments")

    @property
    def active(self) -> bool:
        """True while this is a current assignment."""
        return self.ended_at is None


class ProjectMember(Base):
    """Membership that decides who gets project notifications (BR-16 / FR-NTF-06)."""

    __tablename__ = "project_members"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    added_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    added_at: Mapped[datetime] = mapped_column(DateTime)


class ProjectTemplate(Base):
    """Reusable set of task definitions (BR-13)."""

    __tablename__ = "project_templates"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime)
    updated_at: Mapped[datetime] = mapped_column(DateTime)

    tasks: Mapped[list["TemplateTask"]] = relationship(
        back_populates="template", order_by="TemplateTask.id", cascade="all, delete-orphan"
    )

    def create_project(self, name: str, description: str, start_date: date, due_date: date | None,
                       status: ProjectStatus, created_by: int, now: datetime) -> Project:
        """Factory: a new, independent Project with new Task copies (BR-13)."""
        project = Project(
            name=name, description=description, start_date=start_date, due_date=due_date,
            status=status, template_id=self.id, created_by=created_by,
            created_at=now, updated_at=now,
        )
        for definition in self.tasks:
            project.tasks.append(Task(
                title=definition.title, description=definition.description,
                priority=definition.default_priority, status=TaskStatus.TODO,
                due_date=(start_date + timedelta(days=definition.relative_due_days)
                          if definition.relative_due_days is not None else None),
                created_by=created_by, created_at=now, updated_at=now,
            ))
        return project


class TemplateTask(Base):
    """One reusable task definition inside a template."""

    __tablename__ = "template_tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    template_id: Mapped[int] = mapped_column(ForeignKey("project_templates.id"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    relative_due_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    default_priority: Mapped[TaskPriority] = mapped_column(
        Enum(TaskPriority), default=TaskPriority.MEDIUM
    )

    template: Mapped[ProjectTemplate] = relationship(back_populates="tasks")
