"""SQLite persistence layer for tasks and subjects.

The database file is stored at ``~/.local/share/academic-tasks/tasks.db``
following the XDG Base Directory Specification.
"""

from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path
from typing import Generator, Optional

from models.enums import TaskStatus
from models.subject import Subject
from models.task import Task

# Default storage location (XDG data dir)
_DEFAULT_DIR = Path(os.environ.get(
    "XDG_DATA_HOME",
    Path.home() / ".local" / "share",
)) / "academic-tasks"

_DEFAULT_DB = _DEFAULT_DIR / "tasks.db"


class Database:
    """Thin wrapper around SQLite for academic-task persistence."""

    def __init__(self, db_path: Path | str | None = None) -> None:
        self._path = Path(db_path) if db_path else _DEFAULT_DB
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: sqlite3.Connection | None = None
        self._connect()
        self._create_tables()

    # ── connection management ────────────────────────────────────────

    def _connect(self) -> None:
        self._conn = sqlite3.connect(
            str(self._path),
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
        )
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._conn.row_factory = sqlite3.Row

    @contextmanager
    def _cursor(self) -> Generator[sqlite3.Cursor, None, None]:
        assert self._conn is not None
        cur = self._conn.cursor()
        try:
            yield cur
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            raise
        finally:
            cur.close()

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    # ── schema ───────────────────────────────────────────────────────

    def _create_tables(self) -> None:
        assert self._conn is not None
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS subjects (
                id   INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            );

            CREATE TABLE IF NOT EXISTS tasks (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                title      TEXT    NOT NULL,
                subject_id INTEGER NOT NULL REFERENCES subjects(id)
                           ON DELETE RESTRICT,
                status     INTEGER NOT NULL DEFAULT 0,
                due_date   TEXT,
                notes      TEXT    NOT NULL DEFAULT '',
                created_at TEXT    NOT NULL,
                updated_at TEXT    NOT NULL,
                sort_order INTEGER NOT NULL DEFAULT 0
            );

            CREATE INDEX IF NOT EXISTS idx_tasks_status
                ON tasks(status);
            CREATE INDEX IF NOT EXISTS idx_tasks_subject
                ON tasks(subject_id);
        """)

    # ── subject CRUD ─────────────────────────────────────────────────

    def add_subject(self, subject: Subject) -> Subject:
        with self._cursor() as cur:
            cur.execute(
                "INSERT INTO subjects (name) VALUES (?)",
                (subject.name,),
            )
            subject.id = cur.lastrowid
        return subject

    def get_subject(self, subject_id: int) -> Optional[Subject]:
        with self._cursor() as cur:
            cur.execute("SELECT id, name FROM subjects WHERE id = ?", (subject_id,))
            row = cur.fetchone()
            if row is None:
                return None
            return Subject(id=row["id"], name=row["name"])

    def get_subject_by_name(self, name: str) -> Optional[Subject]:
        with self._cursor() as cur:
            cur.execute("SELECT id, name FROM subjects WHERE name = ?", (name,))
            row = cur.fetchone()
            if row is None:
                return None
            return Subject(id=row["id"], name=row["name"])

    def get_all_subjects(self) -> list[Subject]:
        with self._cursor() as cur:
            cur.execute("SELECT id, name FROM subjects ORDER BY name")
            return [Subject(id=r["id"], name=r["name"]) for r in cur.fetchall()]

    def update_subject(self, subject: Subject) -> None:
        with self._cursor() as cur:
            cur.execute(
                "UPDATE subjects SET name = ? WHERE id = ?",
                (subject.name, subject.id),
            )

    def delete_subject(self, subject_id: int) -> bool:
        """Delete a subject. Returns False if incomplete tasks still reference it."""
        from models.enums import TaskStatus
        with self._cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) as cnt FROM tasks WHERE subject_id = ? AND status != ?",
                (subject_id, TaskStatus.COMPLETED.value),
            )
            if cur.fetchone()["cnt"] > 0:
                return False
            
            cur.execute("DELETE FROM tasks WHERE subject_id = ?", (subject_id,))
            cur.execute("DELETE FROM subjects WHERE id = ?", (subject_id,))
            return True

    # ── task CRUD ────────────────────────────────────────────────────

    def _row_to_task(self, row: sqlite3.Row) -> Task:
        due = None
        if row["due_date"]:
            due = date.fromisoformat(row["due_date"])
        return Task(
            id=row["id"],
            title=row["title"],
            subject_id=row["subject_id"],
            status=TaskStatus(row["status"]),
            due_date=due,
            notes=row["notes"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            sort_order=row["sort_order"],
        )

    def add_task(self, task: Task) -> Task:
        now = datetime.now().isoformat()
        task.created_at = datetime.fromisoformat(now)
        task.updated_at = task.created_at
        with self._cursor() as cur:
            # Auto-assign sort_order to end of its status group
            cur.execute(
                "SELECT COALESCE(MAX(sort_order), -1) + 1 AS next_order "
                "FROM tasks WHERE status = ?",
                (task.status.value,),
            )
            task.sort_order = cur.fetchone()["next_order"]
            cur.execute(
                """INSERT INTO tasks
                   (title, subject_id, status, due_date, notes,
                    created_at, updated_at, sort_order)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    task.title,
                    task.subject_id,
                    task.status.value,
                    task.due_date.isoformat() if task.due_date else None,
                    task.notes,
                    now,
                    now,
                    task.sort_order,
                ),
            )
            task.id = cur.lastrowid
        return task

    def get_task(self, task_id: int) -> Optional[Task]:
        with self._cursor() as cur:
            cur.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
            row = cur.fetchone()
            return self._row_to_task(row) if row else None

    def get_all_tasks(self) -> list[Task]:
        with self._cursor() as cur:
            cur.execute(
                "SELECT * FROM tasks ORDER BY status, sort_order, due_date NULLS LAST"
            )
            return [self._row_to_task(r) for r in cur.fetchall()]

    def update_task(self, task: Task) -> None:
        now = datetime.now().isoformat()
        task.updated_at = datetime.fromisoformat(now)
        with self._cursor() as cur:
            cur.execute(
                """UPDATE tasks SET
                       title      = ?,
                       subject_id = ?,
                       status     = ?,
                       due_date   = ?,
                       notes      = ?,
                       updated_at = ?,
                       sort_order = ?
                   WHERE id = ?""",
                (
                    task.title,
                    task.subject_id,
                    task.status.value,
                    task.due_date.isoformat() if task.due_date else None,
                    task.notes,
                    now,
                    task.sort_order,
                    task.id,
                ),
            )

    def update_task_status(self, task_id: int, status: TaskStatus) -> None:
        now = datetime.now().isoformat()
        with self._cursor() as cur:
            cur.execute(
                "UPDATE tasks SET status = ?, updated_at = ? WHERE id = ?",
                (status.value, now, task_id),
            )

    def delete_task(self, task_id: int) -> None:
        with self._cursor() as cur:
            cur.execute("DELETE FROM tasks WHERE id = ?", (task_id,))

    def update_sort_orders(self, id_order_pairs: list[tuple[int, int]]) -> None:
        """Batch-update sort_order values."""
        with self._cursor() as cur:
            cur.executemany(
                "UPDATE tasks SET sort_order = ? WHERE id = ?",
                [(order, tid) for tid, order in id_order_pairs],
            )

    def get_task_count_for_subject(self, subject_id: int) -> int:
        with self._cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) as cnt FROM tasks WHERE subject_id = ?",
                (subject_id,),
            )
            return cur.fetchone()["cnt"]

    def get_incomplete_task_count_for_subject(self, subject_id: int) -> int:
        from models.enums import TaskStatus
        with self._cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) as cnt FROM tasks WHERE subject_id = ? AND status != ?",
                (subject_id, TaskStatus.COMPLETED.value),
            )
            return cur.fetchone()["cnt"]

    # ── seed data ────────────────────────────────────────────────────

    def seed_sample_data(self) -> None:
        """Populate the database with example academic tasks (idempotent)."""
        with self._cursor() as cur:
            cur.execute("SELECT COUNT(*) as cnt FROM subjects")
            if cur.fetchone()["cnt"] > 0:
                return  # already seeded

        subjects = {
            "Mathematics III": None,
            "Networks": None,
            "Database II": None,
            "Programming": None,
            "Operating Systems": None,
        }
        for name in subjects:
            s = self.add_subject(Subject(name=name))
            subjects[name] = s.id

        sample_tasks = [
            ("Practical Work 3 - Limits", "Mathematics III", TaskStatus.IN_PROGRESS,
             None, "Need to finish exercises 4–8.\nReview one-sided limits before continuing."),
            ("Continue studying Network Theory", "Networks", TaskStatus.IN_PROGRESS,
             None, ""),
            ("Practical Work 4 - Derivatives", "Mathematics III", TaskStatus.NOT_STARTED,
             date(2026, 10, 3), ""),
            ("Study normalization", "Database II", TaskStatus.NOT_STARTED,
             date(2026, 10, 1), "Focus on 3NF and BCNF."),
            ("Database Objects - Functions/Procedures", "Database II", TaskStatus.COMPLETED,
             None, ""),
            ("Practical Work 2 - Functions", "Mathematics III", TaskStatus.COMPLETED,
             None, ""),
            ("Read Chapter 5 - Processes", "Operating Systems", TaskStatus.NOT_STARTED,
             date(2026, 10, 5), "Pay attention to scheduling algorithms."),
            ("Practical Work 1 - Arrays", "Programming", TaskStatus.COMPLETED,
             None, ""),
        ]
        for title, subj_name, status, due, notes in sample_tasks:
            self.add_task(Task(
                title=title,
                subject_id=subjects[subj_name],
                status=status,
                due_date=due,
                notes=notes,
            ))
