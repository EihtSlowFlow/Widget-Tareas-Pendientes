"""Add / Edit task dialog."""

from __future__ import annotations

from datetime import date
from typing import Optional

from PyQt6.QtCore import Qt, QDate
from PyQt6.QtWidgets import (
    QCheckBox, QComboBox, QDateEdit, QDialog, QFormLayout,
    QHBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit,
    QVBoxLayout, QWidget,
)

from models.enums import TaskStatus
from models.subject import Subject
from models.task import Task
from services.task_service import TaskService


class TaskDialog(QDialog):
    """Modal dialog for creating or editing a task.

    Pass an existing *task* to edit it, or leave it ``None`` to create
    a new one.
    """

    def __init__(
        self,
        service: TaskService,
        task: Optional[Task] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._service = service
        self._task = task
        self._result_task: Optional[Task] = None

        self.setWindowTitle("Edit Task" if task else "New Task")
        self.setMinimumWidth(400)
        self.setModal(True)

        self._setup_ui()
        if task:
            self._populate(task)

    # ── public ───────────────────────────────────────────────────────

    @property
    def result_task(self) -> Optional[Task]:
        return self._result_task

    # ── UI setup ─────────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        # header
        header = QLabel("Edit Task" if self._task else "New Task")
        header.setObjectName("headerLabel")
        layout.addWidget(header)

        # form
        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # title
        self._title_edit = QLineEdit()
        self._title_edit.setPlaceholderText("e.g. Practical Work 3 - Limits")
        form.addRow("Title:", self._title_edit)

        # subject combo with editable option to create new
        self._subject_combo = QComboBox()
        self._subject_combo.setEditable(True)
        self._subject_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self._subject_combo.lineEdit().setPlaceholderText("Select or type a new subject")
        self._load_subjects()
        form.addRow("Subject:", self._subject_combo)

        # status
        self._status_combo = QComboBox()
        for s in TaskStatus:
            self._status_combo.addItem(f"{s.icon}  {s.label}", s.value)
        form.addRow("Status:", self._status_combo)

        # due date
        due_container = QWidget()
        due_layout = QHBoxLayout(due_container)
        due_layout.setContentsMargins(0, 0, 0, 0)
        due_layout.setSpacing(8)

        self._due_check = QCheckBox("Set due date")
        self._due_check.setChecked(False)
        self._due_check.toggled.connect(self._toggle_due_date)
        due_layout.addWidget(self._due_check)

        self._due_edit = QDateEdit()
        self._due_edit.setCalendarPopup(True)
        self._due_edit.setDate(QDate.currentDate().addDays(7))
        self._due_edit.setEnabled(False)
        self._due_edit.setDisplayFormat("dd/MM/yyyy")
        due_layout.addWidget(self._due_edit, 1)

        form.addRow("Due date:", due_container)

        # notes
        self._notes_edit = QTextEdit()
        self._notes_edit.setPlaceholderText("Additional notes (optional)")
        self._notes_edit.setMaximumHeight(100)
        form.addRow("Notes:", self._notes_edit)

        layout.addLayout(form)

        # buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        if self._task:
            delete_btn = QPushButton("Delete")
            delete_btn.setObjectName("dangerBtn")
            delete_btn.clicked.connect(self._on_delete)
            btn_layout.addWidget(delete_btn)

        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Save" if self._task else "Add Task")
        save_btn.setObjectName("addTaskBtn")
        save_btn.clicked.connect(self._on_save)
        save_btn.setDefault(True)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def _load_subjects(self) -> None:
        self._subject_combo.clear()
        subjects = self._service.get_all_subjects()
        for s in subjects:
            self._subject_combo.addItem(s.name, s.id)

    def _populate(self, task: Task) -> None:
        self._title_edit.setText(task.title)

        # set subject
        for i in range(self._subject_combo.count()):
            if self._subject_combo.itemData(i) == task.subject_id:
                self._subject_combo.setCurrentIndex(i)
                break

        # set status
        for i in range(self._status_combo.count()):
            if self._status_combo.itemData(i) == task.status.value:
                self._status_combo.setCurrentIndex(i)
                break

        # due date
        if task.due_date:
            self._due_check.setChecked(True)
            self._due_edit.setDate(QDate(
                task.due_date.year, task.due_date.month, task.due_date.day
            ))

        # notes
        self._notes_edit.setPlainText(task.notes)

    def _toggle_due_date(self, checked: bool) -> None:
        self._due_edit.setEnabled(checked)

    # ── actions ──────────────────────────────────────────────────────

    def _on_save(self) -> None:
        title = self._title_edit.text().strip()
        if not title:
            self._title_edit.setFocus()
            return

        # resolve subject
        subject_text = self._subject_combo.currentText().strip()
        subject_data = self._subject_combo.currentData()

        if not subject_text:
            self._subject_combo.setFocus()
            return

        # If the user typed a new subject name
        if subject_data is None or subject_text != self._subject_combo.itemText(
            self._subject_combo.currentIndex()
        ):
            subject = self._service.add_subject(subject_text)
            subject_id = subject.id
        else:
            subject_id = subject_data

        status = TaskStatus(self._status_combo.currentData())

        due_date: Optional[date] = None
        if self._due_check.isChecked():
            qdate = self._due_edit.date()
            due_date = date(qdate.year(), qdate.month(), qdate.day())

        notes = self._notes_edit.toPlainText().strip()

        if self._task:
            # editing
            self._task.title = title
            self._task.subject_id = subject_id
            self._task.status = status
            self._task.due_date = due_date
            self._task.notes = notes
            self._result_task = self._task
        else:
            # creating
            self._result_task = Task(
                title=title,
                subject_id=subject_id,
                status=status,
                due_date=due_date,
                notes=notes,
            )

        self.accept()

    def _on_delete(self) -> None:
        """Signal the caller to delete the task."""
        if self._task and self._task.id:
            self._result_task = None
            self.done(2)  # custom return code for delete
