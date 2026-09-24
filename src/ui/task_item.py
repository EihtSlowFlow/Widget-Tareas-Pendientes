"""Individual task item widget – a single row in the task list."""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QCursor
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout,
    QMenu, QSizePolicy,
)

from models.enums import TaskStatus
from models.task import Task
from ui.styles import get_status_color


class TaskItemWidget(QFrame):
    """Compact card representing a single task.

    Signals:
        status_toggled(task_id):  emitted when the status indicator is clicked.
        edit_requested(task_id):  emitted on double-click / edit action.
        delete_requested(task_id): emitted from context menu.
    """

    status_toggled = pyqtSignal(int)
    edit_requested = pyqtSignal(int)
    delete_requested = pyqtSignal(int)

    def __init__(
        self,
        task: Task,
        subject_name: str,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._task = task
        self._subject_name = subject_name
        self._setup_ui()
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

    # ── public helpers ───────────────────────────────────────────────

    @property
    def task(self) -> Task:
        return self._task

    def update_task(self, task: Task, subject_name: str) -> None:
        self._task = task
        self._subject_name = subject_name
        self._refresh()

    # ── UI setup ─────────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        is_done = self._task.is_completed

        self.setObjectName("taskItemCompleted" if is_done else "taskItem")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 8, 10, 8)
        main_layout.setSpacing(10)

        # ── status indicator button ──────────────────────────────
        self._status_btn = QPushButton()
        self._apply_status_style()
        self._status_btn.setFixedSize(QSize(22, 22))
        self._status_btn.setToolTip(
            f"Click to change status\nCurrent: {self._task.status.label}"
        )
        self._status_btn.clicked.connect(
            lambda: self.status_toggled.emit(self._task.id)
        )
        self._status_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        main_layout.addWidget(self._status_btn, 0, Qt.AlignmentFlag.AlignVCenter)

        # ── text content ─────────────────────────────────────────
        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(3)

        # title
        self._title_label = QLabel(self._task.title)
        title_font = QFont()
        title_font.setPointSize(12)
        if is_done:
            title_font.setStrikeOut(True)
        self._title_label.setFont(title_font)
        if is_done:
            self._title_label.setStyleSheet(
                f"color: {get_status_color(TaskStatus.COMPLETED)}; background: transparent;"
            )
        else:
            self._title_label.setStyleSheet("background: transparent;")
        self._title_label.setWordWrap(True)
        text_layout.addWidget(self._title_label)

        # info row: subject + optional notes indicator
        info_layout = QHBoxLayout()
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(6)

        self._subject_label = QLabel(self._subject_name)
        self._subject_label.setObjectName("subjectTag")
        self._subject_label.setSizePolicy(
            QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed
        )
        info_layout.addWidget(self._subject_label)

        # notes indicator
        if self._task.notes:
            notes_icon = QLabel("📝")
            notes_icon.setToolTip(self._task.notes[:200])
            notes_icon.setStyleSheet("background: transparent; font-size: 11px;")
            notes_icon.setSizePolicy(
                QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed
            )
            info_layout.addWidget(notes_icon)

        info_layout.addStretch()
        text_layout.addLayout(info_layout)

        # due date (if any)
        due = self._task.due_label
        if due and not is_done:
            self._due_label = QLabel(f"📅 {due}")
            if self._task.is_overdue:
                self._due_label.setObjectName("overdueLabel")
            else:
                self._due_label.setObjectName("dueLabel")
            text_layout.addWidget(self._due_label)
        else:
            self._due_label = None

        main_layout.addLayout(text_layout, 1)

    def _apply_status_style(self) -> None:
        status = self._task.status
        if status == TaskStatus.NOT_STARTED:
            self._status_btn.setObjectName("statusNotStarted")
            self._status_btn.setText("")
        elif status == TaskStatus.IN_PROGRESS:
            self._status_btn.setObjectName("statusInProgress")
            self._status_btn.setText("◐")
        else:
            self._status_btn.setObjectName("statusCompleted")
            self._status_btn.setText("✓")
        self._status_btn.style().unpolish(self._status_btn)
        self._status_btn.style().polish(self._status_btn)

    def _refresh(self) -> None:
        """Rebuild the widget after data changes."""
        # Remove old layout
        old = self.layout()
        if old is not None:
            while old.count():
                item = old.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.deleteLater()
                sub = item.layout()
                if sub:
                    while sub.count():
                        sub_item = sub.takeAt(0)
                        w = sub_item.widget()
                        if w:
                            w.deleteLater()
            from PyQt6.QtWidgets import QWidget
            QWidget().setLayout(old)
        self._setup_ui()

    # ── events ───────────────────────────────────────────────────────

    def mouseDoubleClickEvent(self, event) -> None:
        self.edit_requested.emit(self._task.id)

    def _show_context_menu(self, pos) -> None:
        menu = QMenu(self)

        edit_action = menu.addAction("✏️  Edit task")
        edit_action.triggered.connect(
            lambda: self.edit_requested.emit(self._task.id)
        )

        menu.addSeparator()

        # Status sub-actions
        for s in TaskStatus:
            if s != self._task.status:
                action = menu.addAction(f"{s.icon}  Mark as {s.label}")
                action.triggered.connect(
                    lambda checked, st=s: self._set_status(st)
                )

        menu.addSeparator()

        delete_action = menu.addAction("🗑️  Delete task")
        delete_action.triggered.connect(
            lambda: self.delete_requested.emit(self._task.id)
        )

        menu.exec(self.mapToGlobal(pos))

    def _set_status(self, status: TaskStatus) -> None:
        """Emit status_toggled after forcing a specific status."""
        self._task.status = status
        self.status_toggled.emit(self._task.id)
