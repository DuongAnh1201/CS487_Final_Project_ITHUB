"""Generic repository: the only layer that talks to the database."""

from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import Base
from app.core.exceptions import NotFoundError

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """Get / list / add for one entity. Records are never deleted (BR-02).

    Subclasses set ``model`` and may override ``not_found_message``.
    """

    model: type[ModelT]
    not_found_message = "Record not found."

    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, entity_id: int) -> ModelT | None:
        """Return the record with this id, or None."""
        return self.session.get(self.model, entity_id)

    def get_or_raise(self, entity_id: int) -> ModelT:
        """Return the record or raise NotFoundError."""
        entity = self.get(entity_id)
        if entity is None:
            raise NotFoundError(self.not_found_message)
        return entity

    def list(self) -> list[ModelT]:
        """Return every record ordered by id."""
        return list(self.session.scalars(select(self.model).order_by(self.model.id)))

    def add(self, entity: ModelT) -> ModelT:
        """Stage a new record and flush so its id is available."""
        self.session.add(entity)
        self.session.flush()
        return entity

    def flush(self) -> None:
        """Write pending changes inside the current transaction."""
        self.session.flush()

    def commit(self) -> None:
        """Commit now. Only for state that must survive a failing request."""
        self.session.commit()
