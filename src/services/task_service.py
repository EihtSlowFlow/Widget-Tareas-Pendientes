"""Task service – central façade between UI and persistence."""

from __future__ import annotations

from typing import Optional

from models.enums import TaskStatus
from models.subject import Subject
from models.task import Task
from services.filter_service import filter_tasks, group_by_status
from storage.database import Database


class TaskService:
    """High-level operations on tasks and subjects.

    The UI should interact with this service instead of calling
    the database directly.
    """

    def __init__(self, db: Database) -> None:
        self._db = db

    # ── subjects ─────────────────────────────────────────────────────

    def get_all_subjects(self) -> list[Subject]:
        return self._db.get_all_subjects()

    def get_subject(self, subject_id: int) -> Optional[Subject]:
        return self._db.get_subject(subject_id)

    def add_subject(self, name: str) -> Subject:
        existing = self._db.get_subject_by_name(name)
        if existing:
            return existing
        return self._db.add_subject(Subject(name=name))

    def update_subject(self, subject: Subject) -> None:
        self._db.update_subject(subject)

    def delete_subject(self, subject_id: int) -> bool:
        return self._db.delete_subject(subject_id)

    def get_subject_names_map(self) -> dict[int, str]:
        return {s.id: s.name for s in self._db.get_all_subjects()}

    # ── tasks ────────────────────────────────────────────────────────

    def get_all_tasks(self) -> list[Task]:
        return self._db.get_all_tasks()

    def get_task(self, task_id: int) -> Optional[Task]:
        return self._db.get_task(task_id)

    def add_task(self, task: Task) -> Task:
        return self._db.add_task(task)

    def update_task(self, task: Task) -> None:
        self._db.update_task(task)

    def delete_task(self, task_id: int) -> None:
        self._db.delete_task(task_id)

    def cycle_task_status(self, task_id: int) -> Optional[Task]:
        task = self._db.get_task(task_id)
        if task is None:
            return None
        task.cycle_status()
        self._db.update_task(task)
        return task

    def set_task_status(self, task_id: int, status: TaskStatus) -> None:
        self._db.update_task_status(task_id, status)

    def reorder_tasks(self, id_order_pairs: list[tuple[int, int]]) -> None:
        self._db.update_sort_orders(id_order_pairs)

    # ── filtered / grouped views ─────────────────────────────────────

    def get_filtered_tasks(
        self,
        *,
        status: Optional[TaskStatus] = None,
        subject_id: Optional[int] = None,
        search_query: str = "",
    ) -> list[Task]:
        all_tasks = self._db.get_all_tasks()
        return filter_tasks(
            all_tasks,
            status=status,
            subject_id=subject_id,
            search_query=search_query,
            subject_names=self.get_subject_names_map(),
        )

    def get_grouped_tasks(
        self,
        *,
        status: Optional[TaskStatus] = None,
        subject_id: Optional[int] = None,
        search_query: str = "",
    ) -> dict[TaskStatus, list[Task]]:
        filtered = self.get_filtered_tasks(
            status=status,
            subject_id=subject_id,
            search_query=search_query,
        )
        return group_by_status(filtered)

    def get_task_count_for_subject(self, subject_id: int) -> int:
        return self._db.get_task_count_for_subject(subject_id)

    def get_incomplete_task_count_for_subject(self, subject_id: int) -> int:
        return self._db.get_incomplete_task_count_for_subject(subject_id)

    # ── seed ─────────────────────────────────────────────────────────

    def seed_sample_data(self) -> None:
        self._db.seed_sample_data()
