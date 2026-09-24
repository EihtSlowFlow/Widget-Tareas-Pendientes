"""Status enumeration for academic tasks."""

from enum import IntEnum


class TaskStatus(IntEnum):
    """Task status values.

    The integer values define both persistence keys and the cycling order:
        Not started (0) → In progress (1) → Completed (2)
    """

    NOT_STARTED = 0
    IN_PROGRESS = 1
    COMPLETED = 2

    # ── display helpers ──────────────────────────────────────────────

    @property
    def label(self) -> str:
        """Human-readable label (title case)."""
        return {
            TaskStatus.NOT_STARTED: "Not started",
            TaskStatus.IN_PROGRESS: "In progress",
            TaskStatus.COMPLETED: "Completed",
        }[self]

    @property
    def group_label(self) -> str:
        """Uppercase label used as a section header."""
        return {
            TaskStatus.NOT_STARTED: "NOT STARTED",
            TaskStatus.IN_PROGRESS: "IN PROGRESS",
            TaskStatus.COMPLETED: "COMPLETED",
        }[self]

    @property
    def icon(self) -> str:
        """Unicode icon for visual status representation."""
        return {
            TaskStatus.NOT_STARTED: "○",
            TaskStatus.IN_PROGRESS: "◐",
            TaskStatus.COMPLETED: "✓",
        }[self]

    # ── cycling ──────────────────────────────────────────────────────

    def next(self) -> "TaskStatus":
        """Return the next status in the cycle."""
        members = list(TaskStatus)
        idx = members.index(self)
        return members[(idx + 1) % len(members)]
