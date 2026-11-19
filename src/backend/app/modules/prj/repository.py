"""PRJ storage."""

from datetime import date

from sqlalchemy import or_, select

from app.modules.ntf.ports import ScheduledWork
from app.modules.prj.models import (
    Project,
    ProjectMember,
    ProjectStatus,
    ProjectTemplate,
    Task,
    TaskAssignment,
    TaskStatus,
)
from app.shared.repository import BaseRepository


class ProjectRepository(BaseRepository[Project]):
    """Projects and their members."""

    model = Project
    not_found_message = "Project not found."

    def search(self, q: str | None = None, status: ProjectStatus | None = None,
               assignee_id: int | None = None, due_before: date | None = None,
               due_after: date | None = None) -> list[Project]:
        """Projects matching text and every given filter (FR-PRJ-06)."""
        stmt = select(Project).order_by(Project.id)
        if q:
            like = f"%{q.strip()}%"
            stmt = stmt.where(or_(Project.name.ilike(like), Project.description.ilike(like)))
        if status is not None:
            stmt = stmt.where(Project.status == status)
        if assignee_id is not None:
            stmt = stmt.where(Project.id.in_(
                select(Task.project_id).join(TaskAssignment).where(
                    TaskAssignment.user_id == assignee_id, TaskAssignment.ended_at.is_(None))))
        if due_before is not None:
            stmt = stmt.where(Project.due_date <= due_before)
        if due_after is not None:
            stmt = stmt.where(Project.due_date >= due_after)
        return list(self.session.scalars(stmt))

    def member_ids(self, project_id: int) -> list[int]:
        """User ids of the project's members."""
        return list(self.session.scalars(
            select(ProjectMember.user_id).where(ProjectMember.project_id == project_id)
            .order_by(ProjectMember.id)))

    def is_member(self, project_id: int, user_id: int) -> bool:
        """Whether the user belongs to the project."""
        return user_id in self.member_ids(project_id)

    def add_member(self, member: ProjectMember) -> ProjectMember:
        """Store a membership."""
        self.session.add(member)
        self.session.flush()
        return member


class TaskRepository(BaseRepository[Task]):
    """Tasks and assignments."""

    model = Task
    not_found_message = "Task not found."

    def search(self, q: str | None = None, status: TaskStatus | None = None,
               assignee_id: int | None = None, project_id: int | None = None,
               due_before: date | None = None, due_after: date | None = None) -> list[Task]:
        """Tasks matching text and every given filter (FR-PRJ-06)."""
        stmt = select(Task).order_by(Task.id)
        if q:
            like = f"%{q.strip()}%"
            stmt = stmt.where(or_(Task.title.ilike(like), Task.description.ilike(like)))
        if status is not None:
            stmt = stmt.where(Task.status == status)
        if project_id is not None:
            stmt = stmt.where(Task.project_id == project_id)
        if assignee_id is not None:
            stmt = stmt.where(Task.id.in_(
                select(TaskAssignment.task_id).where(
                    TaskAssignment.user_id == assignee_id, TaskAssignment.ended_at.is_(None))))
        if due_before is not None:
            stmt = stmt.where(Task.due_date <= due_before)
        if due_after is not None:
            stmt = stmt.where(Task.due_date >= due_after)
        return list(self.session.scalars(stmt))

    def open_tasks_for_user(self, user_id: int, due_on_or_before: date) -> list[Task]:
        """Unfinished tasks assigned to the user and due on/before the date (shift summary)."""
        return list(self.session.scalars(
            select(Task).where(
                Task.status != TaskStatus.COMPLETE,
                Task.due_date.is_not(None), Task.due_date <= due_on_or_before,
                Task.id.in_(select(TaskAssignment.task_id).where(
                    TaskAssignment.user_id == user_id, TaskAssignment.ended_at.is_(None))),
            ).order_by(Task.due_date, Task.id)))

    def add_assignment(self, assignment: TaskAssignment) -> TaskAssignment:
        """Store an assignment row."""
        self.session.add(assignment)
        self.session.flush()
        return assignment


class TemplateRepository(BaseRepository[ProjectTemplate]):
    """Project templates."""

    model = ProjectTemplate
    not_found_message = "Template not found."


class TaskWorkSource:
    """Supplies NTF's shift summary with each user's unfinished tasks (ScheduledWorkSource)."""

    def __init__(self, tasks: TaskRepository) -> None:
        self.tasks = tasks

    def open_work_for_user(self, user_id: int, due_on_or_before: date) -> list[ScheduledWork]:
        """Unfinished assigned tasks due on or before the date."""
        return [ScheduledWork(t.id, t.title, t.due_date)
                for t in self.tasks.open_tasks_for_user(user_id, due_on_or_before)]
