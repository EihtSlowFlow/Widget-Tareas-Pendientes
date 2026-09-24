"""Subject management dialog."""

from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QMessageBox, QPushButton, QVBoxLayout,
    QWidget,
)

from services.task_service import TaskService


class SubjectManagerDialog(QDialog):
    """Dialog for viewing, adding, renaming, and deleting subjects."""

    def __init__(
        self,
        service: TaskService,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._service = service
        self.setWindowTitle("Manage Subjects")
        self.setMinimumSize(380, 420)
        self.setModal(True)
        self._setup_ui()
        self._load_subjects()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        header = QLabel("Subjects")
        header.setObjectName("headerLabel")
        layout.addWidget(header)

        desc = QLabel("Manage your university courses and subjects.")
        desc.setObjectName("subjectLabel")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # add new subject
        add_layout = QHBoxLayout()
        add_layout.setSpacing(8)
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("New subject name...")
        self._name_edit.returnPressed.connect(self._add_subject)
        add_layout.addWidget(self._name_edit, 1)

        add_btn = QPushButton("Add")
        add_btn.setObjectName("addTaskBtn")
        add_btn.clicked.connect(self._add_subject)
        add_layout.addWidget(add_btn)
        layout.addLayout(add_layout)

        # subject list
        self._list = QListWidget()
        self._list.setAlternatingRowColors(False)
        layout.addWidget(self._list, 1)

        # action buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        rename_btn = QPushButton("Rename")
        rename_btn.clicked.connect(self._rename_subject)
        btn_layout.addWidget(rename_btn)

        delete_btn = QPushButton("Delete")
        delete_btn.setObjectName("dangerBtn")
        delete_btn.clicked.connect(self._delete_subject)
        btn_layout.addWidget(delete_btn)

        btn_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

    def _load_subjects(self) -> None:
        self._list.clear()
        subjects = self._service.get_all_subjects()
        for s in subjects:
            count = self._service.get_task_count_for_subject(s.id)
            item = QListWidgetItem(f"{s.name}  ({count} tasks)")
            item.setData(Qt.ItemDataRole.UserRole, s.id)
            item.setData(Qt.ItemDataRole.UserRole + 1, s.name)
            self._list.addItem(item)

    def _add_subject(self) -> None:
        name = self._name_edit.text().strip()
        if not name:
            return
        self._service.add_subject(name)
        self._name_edit.clear()
        self._load_subjects()

    def _rename_subject(self) -> None:
        item = self._list.currentItem()
        if not item:
            return
        sid = item.data(Qt.ItemDataRole.UserRole)
        old_name = item.data(Qt.ItemDataRole.UserRole + 1)

        from PyQt6.QtWidgets import QInputDialog
        new_name, ok = QInputDialog.getText(
            self, "Rename Subject", "New name:", text=old_name
        )
        if ok and new_name.strip():
            subject = self._service.get_subject(sid)
            if subject:
                subject.name = new_name.strip()
                self._service.update_subject(subject)
                self._load_subjects()

    def _delete_subject(self) -> None:
        item = self._list.currentItem()
        if not item:
            return
        sid = item.data(Qt.ItemDataRole.UserRole)
        name = item.data(Qt.ItemDataRole.UserRole + 1)

        incomplete = self._service.get_incomplete_task_count_for_subject(sid)
        if incomplete > 0:
            QMessageBox.warning(
                self,
                "Cannot delete",
                f'"{name}" still has {incomplete} incomplete task(s).\n'
                "Complete, delete, or reassign those tasks first.",
            )
            return

        total = self._service.get_task_count_for_subject(sid)
        if total > 0:
            msg = f'"{name}" has {total} completed task(s).\nDeleting the subject will also permanently delete these tasks.\n\nAre you sure?'
        else:
            msg = f'Delete "{name}"?'

        reply = QMessageBox.question(
            self,
            "Delete subject",
            msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._service.delete_subject(sid)
            self._load_subjects()
