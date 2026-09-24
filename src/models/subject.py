"""Subject (course) data model."""

from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class Subject:
    """Represents a university course / subject.

    Attributes:
        id:   Unique identifier (assigned by the database).
        name: Display name, e.g. 'Mathematics III'.
    """

    name: str
    id: int | None = field(default=None)

    # ── helpers ──────────────────────────────────────────────────────

    def __str__(self) -> str:
        return self.name

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Subject):
            return NotImplemented
        if self.id is not None and other.id is not None:
            return self.id == other.id
        return self.name == other.name

    def __hash__(self) -> int:
        return hash(self.id if self.id is not None else self.name)
