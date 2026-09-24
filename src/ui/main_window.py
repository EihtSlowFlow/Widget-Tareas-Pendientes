"""Main application window – the expanded task-management view."""

from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt, QTimer, QSize, pyqtSlot
from PyQt6.QtGui import QAction, QFont, QIcon, QKeySequence
from PyQt6.QtWidgets import (
    QComboBox, QFrame, QHBoxLayout, QLabel, QLineEdit,
    QMainWindow, QMessageBox, QPushButton, QScrollArea,
    QSizePolicy, QSystemTrayIcon, QMenu, QVBoxLayout,
    QWidget, QApplication, QDialog,
)

from models.enums import TaskStatus
from models.task import Task
from services.task_service import TaskService
from ui.styles import get_stylesheet, get_colors
from ui.task_dialog import TaskDialog
from ui.task_item import TaskItemWidget
from ui.subject_manager import SubjectManagerDialog


class MainWindow(QMainWindow):
    """Academic Tasks – main application window."""

    COMPACT_SIZE = QSize(380, 620)
    EXPANDED_SIZE = QSize(480, 720)

    def __init__(self, service: TaskService) -> None:
        super().__init__()
        self._service = service
        self._current_status_filter: Optional[TaskStatus] = None
        self._current_subject_filter: Optional[int] = None
        self._search_query = ""
        self._task_widgets: list[TaskItemWidget] = []

        self._setup_window()
        self._setup_tray()
        self._setup_ui()
        self._setup_shortcuts()
        self._refresh_tasks()

    # ── window setup ─────────────────────────────────────────────────

    def _setup_window(self) -> None:
        self.setWindowTitle("Academic Tasks")
        self.setMinimumSize(self.COMPACT_SIZE)
        self.resize(self.EXPANDED_SIZE)
        self.setStyleSheet(get_stylesheet())

        # Window flags for widget-like behavior
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.WindowCloseButtonHint
        )

    def _setup_tray(self) -> None:
        """Set up system tray icon for quick access."""
        self._tray = QSystemTrayIcon(self)
        # Use a themed icon or fallback
        icon = QIcon.fromTheme("view-task", QIcon.fromTheme("checkbox"))
        if icon.isNull():
            icon = QIcon.fromTheme("text-x-generic")
        self._tray.setIcon(icon)
        self._tray.setToolTip("Academic Tasks")

        tray_menu = QMenu()

        show_action = tray_menu.addAction("Show")
        show_action.triggered.connect(self._show_window)

        add_action = tray_menu.addAction("Add Task")
        add_action.triggered.connect(self._open_add_dialog)

        tray_menu.addSeparator()

        quit_action = tray_menu.addAction("Quit")
        quit_action.triggered.connect(QApplication.quit)

        self._tray.setContextMenu(tray_menu)
        self._tray.activated.connect(self._on_tray_activated)
        self._tray.show()

    def _setup_shortcuts(self) -> None:
        # Ctrl+N → Add task
        add_shortcut = QAction(self)
        add_shortcut.setShortcut(QKeySequence("Ctrl+N"))
        add_shortcut.triggered.connect(self._open_add_dialog)
        self.addAction(add_shortcut)

        # Ctrl+F → Focus search
        search_shortcut = QAction(self)
        search_shortcut.setShortcut(QKeySequence("Ctrl+F"))
        search_shortcut.triggered.connect(lambda: self._search_edit.setFocus())
        self.addAction(search_shortcut)

        # Escape → Clear search / minimize
        esc_shortcut = QAction(self)
        esc_shortcut.setShortcut(QKeySequence("Escape"))
        esc_shortcut.triggered.connect(self._on_escape)
        self.addAction(esc_shortcut)

    # ── UI assembly ──────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(16, 16, 16, 12)
        root.setSpacing(12)

        # ── header ───────────────────────────────────────────────
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        title = QLabel("Academic Tasks")
        title.setObjectName("headerLabel")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # settings button
        settings_btn = QPushButton("⚙")
        settings_btn.setObjectName("flatBtn")
        settings_btn.setToolTip("Manage subjects")
        settings_btn.setFixedSize(QSize(32, 32))
        settings_btn.setFont(QFont("", 15))
        settings_btn.clicked.connect(self._open_subject_manager)
        header_layout.addWidget(settings_btn)

        # pin/unpin toggle
        self._pin_btn = QPushButton("📌")
        self._pin_btn.setObjectName("flatBtn")
        self._pin_btn.setToolTip("Unpin from top")
        self._pin_btn.setFixedSize(QSize(32, 32))
        self._pin_btn.setFont(QFont("", 14))
        self._pin_btn.clicked.connect(self._toggle_always_on_top)
        header_layout.addWidget(self._pin_btn)

        root.addLayout(header_layout)

        # ── search bar ───────────────────────────────────────────
        self._search_edit = QLineEdit()
        self._search_edit.setObjectName("searchBox")
        self._search_edit.setPlaceholderText("🔍  Search tasks...")
        self._search_edit.setClearButtonEnabled(True)
        self._search_edit.textChanged.connect(self._on_search_changed)
        root.addWidget(self._search_edit)

        # ── filter bar ───────────────────────────────────────────
        filter_frame = QFrame()
        filter_frame.setObjectName("filterBar")
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setContentsMargins(8, 6, 8, 6)
        filter_layout.setSpacing(10)

        filter_layout.addWidget(QLabel("Subject:"))
        self._subject_filter = QComboBox()
        self._subject_filter.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self._subject_filter.currentIndexChanged.connect(
            self._on_subject_filter_changed
        )
        filter_layout.addWidget(self._subject_filter, 1)

        filter_layout.addWidget(QLabel("Status:"))
        self._status_filter = QComboBox()
        self._status_filter.addItem("All", None)
        for s in TaskStatus:
            self._status_filter.addItem(f"{s.icon}  {s.label}", s.value)
        self._status_filter.currentIndexChanged.connect(
            self._on_status_filter_changed
        )
        filter_layout.addWidget(self._status_filter)

        root.addWidget(filter_frame)

        # ── task list (scrollable) ───────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        self._list_container = QWidget()
        self._list_layout = QVBoxLayout(self._list_container)
        self._list_layout.setContentsMargins(0, 0, 4, 0)
        self._list_layout.setSpacing(6)
        self._list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        scroll.setWidget(self._list_container)
        root.addWidget(scroll, 1)

        # ── bottom bar ───────────────────────────────────────────
        separator = QFrame()
        separator.setObjectName("separator")
        separator.setFrameShape(QFrame.Shape.HLine)
        root.addWidget(separator)

        bottom = QHBoxLayout()
        bottom.setSpacing(8)

        self._count_label = QLabel()
        self._count_label.setObjectName("countLabel")
        bottom.addWidget(self._count_label)

        bottom.addStretch()

        add_btn = QPushButton("＋  Add task")
        add_btn.setObjectName("addTaskBtn")
        add_btn.setToolTip("Add a new task (Ctrl+N)")
        add_btn.clicked.connect(self._open_add_dialog)
        bottom.addWidget(add_btn)

        root.addLayout(bottom)

    # ── data refresh ─────────────────────────────────────────────────

    def _refresh_subjects_filter(self) -> None:
        """Reload the subject filter combo."""
        blocked = self._subject_filter.blockSignals(True)
        current_id = self._current_subject_filter

        self._subject_filter.clear()
        self._subject_filter.addItem("All subjects", None)
        for s in self._service.get_all_subjects():
            self._subject_filter.addItem(s.name, s.id)

        # restore selection
        if current_id is not None:
            for i in range(self._subject_filter.count()):
                if self._subject_filter.itemData(i) == current_id:
                    self._subject_filter.setCurrentIndex(i)
                    break

        self._subject_filter.blockSignals(blocked)

    def _refresh_tasks(self) -> None:
        """Reload and render all tasks based on current filters."""
        self._refresh_subjects_filter()

        grouped = self._service.get_grouped_tasks(
            status=self._current_status_filter,
            subject_id=self._current_subject_filter,
            search_query=self._search_query,
        )
        subject_map = self._service.get_subject_names_map()

        # clear existing
        self._task_widgets.clear()
        while self._list_layout.count():
            item = self._list_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        total = 0
        for status, tasks in grouped.items():
            if not tasks and self._current_status_filter is None:
                continue  # skip empty groups when showing all

            # section header
            header_layout = QHBoxLayout()
            header_label = QLabel(status.group_label)
            header_label.setObjectName("sectionLabel")
            header_layout.addWidget(header_label)

            count_label = QLabel(f"({len(tasks)})")
            count_label.setObjectName("countLabel")
            header_layout.addWidget(count_label)
            header_layout.addStretch()

            header_widget = QWidget()
            header_widget.setLayout(header_layout)
            self._list_layout.addWidget(header_widget)

            for task in tasks:
                subj_name = subject_map.get(task.subject_id, "—")
                item = TaskItemWidget(task, subj_name)
                item.status_toggled.connect(self._on_status_toggled)
                item.edit_requested.connect(self._on_edit_requested)
                item.delete_requested.connect(self._on_delete_requested)
                self._list_layout.addWidget(item)
                self._task_widgets.append(item)

            total += len(tasks)

        # empty state
        if total == 0:
            empty = QLabel("No tasks found.\nClick '＋ Add task' to get started!")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setObjectName("subjectLabel")
            empty.setStyleSheet("padding: 40px;")
            self._list_layout.addWidget(empty)

        self._count_label.setText(f"{total} task{'s' if total != 1 else ''}")

    # ── filter handlers ──────────────────────────────────────────────

    def _on_search_changed(self, text: str) -> None:
        self._search_query = text.strip()
        # Debounce refresh
        if not hasattr(self, "_search_timer"):
            self._search_timer = QTimer()
            self._search_timer.setSingleShot(True)
            self._search_timer.timeout.connect(self._refresh_tasks)
        self._search_timer.start(200)

    def _on_subject_filter_changed(self, index: int) -> None:
        data = self._subject_filter.itemData(index)
        self._current_subject_filter = data
        self._refresh_tasks()

    def _on_status_filter_changed(self, index: int) -> None:
        data = self._status_filter.itemData(index)
        if data is None:
            self._current_status_filter = None
        else:
            self._current_status_filter = TaskStatus(data)
        self._refresh_tasks()

    # ── task actions ─────────────────────────────────────────────────

    def _on_status_toggled(self, task_id: int) -> None:
        self._service.cycle_task_status(task_id)
        self._refresh_tasks()

    def _on_edit_requested(self, task_id: int) -> None:
        task = self._service.get_task(task_id)
        if not task:
            return
        dialog = TaskDialog(self._service, task, self)
        result = dialog.exec()
        if result == QDialog.DialogCode.Accepted and dialog.result_task:
            self._service.update_task(dialog.result_task)
            self._refresh_tasks()
        elif result == 2:  # delete
            self._on_delete_requested(task_id)

    def _on_delete_requested(self, task_id: int) -> None:
        task = self._service.get_task(task_id)
        if not task:
            return
        reply = QMessageBox.question(
            self,
            "Delete task",
            f'Delete "{task.title}"?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._service.delete_task(task_id)
            self._refresh_tasks()

    def _open_add_dialog(self) -> None:
        dialog = TaskDialog(self._service, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.result_task:
            self._service.add_task(dialog.result_task)
            self._refresh_tasks()

    def _open_subject_manager(self) -> None:
        dialog = SubjectManagerDialog(self._service, self)
        dialog.exec()
        self._refresh_tasks()  # subjects may have changed

    # ── window behavior ──────────────────────────────────────────────

    def _toggle_always_on_top(self) -> None:
        flags = self.windowFlags()
        if flags & Qt.WindowType.WindowStaysOnTopHint:
            self.setWindowFlags(
                flags & ~Qt.WindowType.WindowStaysOnTopHint
            )
            self._pin_btn.setText("📌")
            self._pin_btn.setToolTip("Pin to top")
        else:
            self.setWindowFlags(
                flags | Qt.WindowType.WindowStaysOnTopHint
            )
            self._pin_btn.setText("📍")
            self._pin_btn.setToolTip("Unpin from top")
        self.show()  # re-show after flag change

    @pyqtSlot()
    def raise_window(self) -> None:
        """D-Bus slot: bring the existing window to the foreground."""
        self._show_window()
        self._refresh_tasks()

    def _show_window(self) -> None:
        self.showNormal()
        self.activateWindow()
        self.raise_()

    def _on_tray_activated(self, reason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self.isVisible() and not self.isMinimized():
                self.hide()
            else:
                self._show_window()

    def _on_escape(self) -> None:
        if self._search_edit.text():
            self._search_edit.clear()
        else:
            self.hide()

    def closeEvent(self, event) -> None:
        """Minimize to tray instead of closing."""
        event.ignore()
        self.hide()

    # ── needed for import in task_dialog ─────────────────────────────
