"""PATCH semantics shared by the update services."""

from pydantic import BaseModel


class PatchChanges:
    """Turns a partial-update body into the changes to apply.

    Only fields the client sent count. ``null`` clears a field listed as clearable; on any other
    field (a required value such as a title or status) ``null`` is ignored.
    """

    @staticmethod
    def of(data: BaseModel, clearable: frozenset[str] = frozenset()) -> dict[str, object]:
        """The fields to set, with ``None`` kept only for clearable fields."""
        sent = data.model_dump(exclude_unset=True)
        return {field: value for field, value in sent.items() if value is not None or field in clearable}
