"""Filtering and sorting service for academic tasks."""

from __future__ import annotations

from typing import Optional

from models.enums import TaskStatus
from models.task import Task


def filter_tasks(
    tasks: list[Task],
    *,
    status: Optional[TaskStatus] = None,
    subject_id: Optional[int] = None,
    search_query: str = "",
    subject_names: Optional[dict[int, str]] = None,
) -> list[Task]:
    """Return tasks matching all given filters.

    Parameters:
        tasks:         Full task list.
        status:        If set, keep only tasks with this status.
        subject_id:    If set, keep only tasks belonging to this subject.
        search_query:  Free-text search (matches title, notes, subject name).
        subject_names: Mapping subject_id → name, needed for search.
    """
    result = tasks

    if status is not None:
        result = [t for t in result if t.status == status]

    if subject_id is not None:
        result = [t for t in result if t.subject_id == subject_id]

    if search_query:
        q = search_query.lower()
        filtered = []
        for t in result:
            if q in t.title.lower():
                filtered.append(t)
                continue
            if q in t.notes.lower():
                filtered.append(t)
                continue
            if subject_names:
                sname = subject_names.get(t.subject_id, "")
                if q in sname.lower():
                    filtered.append(t)
                    continue
        result = filtered

    return result


def sort_tasks(tasks: list[Task]) -> list[Task]:
    """Sort tasks within a flat list by sort_order, with due-date tasks first.

    Sorting key (ascending):
        1. Has no due date (False < True → dated tasks first)
        2. sort_order
        3. created_at (fallback)
    """
    return sorted(
        tasks,
        key=lambda t: (
            not t.has_due_date,
            t.sort_order,
            t.created_at or "",
        ),
    )


def group_by_status(tasks: list[Task]) -> dict[TaskStatus, list[Task]]:
    """Group tasks by status, preserving the canonical status order.

    Returns an OrderedDict-like plain dict with keys in the order:
        IN_PROGRESS → NOT_STARTED → COMPLETED
    """
    display_order = [
        TaskStatus.IN_PROGRESS,
        TaskStatus.NOT_STARTED,
        TaskStatus.COMPLETED,
    ]
    groups: dict[TaskStatus, list[Task]] = {s: [] for s in display_order}
    for t in tasks:
        groups[t.status].append(t)
    # sort within each group
    for s in groups:
        groups[s] = sort_tasks(groups[s])
    return groups
