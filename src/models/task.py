"""Task data model."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional

from models.enums import TaskStatus


@dataclass
class Task:
    """Represents a single academic task.

    Attributes:
        id:         Unique identifier (assigned by the database).
        title:      Short description, e.g. 'Practical Work 3 - Limits'.
        subject_id: Foreign-key reference to a Subject.
        status:     Current workflow status.
        due_date:   Optional deadline.
        notes:      Free-form extra information.
        created_at: Timestamp of creation.
        updated_at: Timestamp of last modification.
        sort_order: Manual ordering within a status group.
    """

    title: str
    subject_id: int
    status: TaskStatus = TaskStatus.NOT_STARTED
    due_date: Optional[date] = None
    notes: str = ""
    id: Optional[int] = field(default=None)
    created_at: Optional[datetime] = field(default=None)
    updated_at: Optional[datetime] = field(default=None)
    sort_order: int = 0

    # ── convenience ──────────────────────────────────────────────────

    @property
    def has_due_date(self) -> bool:
        return self.due_date is not None

    @property
    def is_completed(self) -> bool:
        return self.status == TaskStatus.COMPLETED

    @property
    def is_overdue(self) -> bool:
        if self.due_date is None or self.is_completed:
            return False
        return self.due_date < date.today()

    @property
    def days_until_due(self) -> Optional[int]:
        """Days remaining until due date (negative = overdue)."""
        if self.due_date is None:
            return None
        return (self.due_date - date.today()).days

    @property
    def due_label(self) -> str:
        """Human-friendly due-date label."""
        if self.due_date is None:
            return ""
        days = self.days_until_due
        if days is None:
            return ""
        if days < 0:
            return f"Overdue ({-days}d)"
        if days == 0:
            return "Due: Today"
        if days == 1:
            return "Due: Tomorrow"
        if days <= 7:
            return f"Due in {days} days"
        return f"Due: {self.due_date.strftime('%b %d')}"

    def cycle_status(self) -> None:
        """Advance status to the next value in the cycle."""
        self.status = self.status.next()
